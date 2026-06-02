"""FastAPI backend for the chat UI."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env

load_lab_env(ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"

app = FastAPI(title="Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store: id -> {meta, history, transcript}
_conversations: dict[str, dict[str, Any]] = {}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "run"


def json_text(value: Any, *, max_chars: int | None = None) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def trim_history(history: list[dict], window: int) -> list[dict]:
    if window <= 0:
        return []
    return history[-window * 2:]


def execute_tool_call(call: Any) -> dict[str, Any]:
    from providers.base import ToolCall
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {"tool": call.name, "args": call.args,
                "result": {"error": "unknown_tool", "message": f"No local implementation for {call.name}"}}
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}


def assistant_tool_message(response_text: str | None, calls: list) -> dict:
    call_summary = [{"name": c.name, "args": c.args} for c in calls]
    content = response_text or "I will call the selected tool(s)."
    return {"role": "assistant", "content": f"{content}\n\nTOOL_CALLS_JSON:\n{json_text(call_summary)}"}


def tool_results_message(events: list[dict]) -> dict:
    return {
        "role": "user",
        "content": (
            "TOOL_RESULTS_JSON:\n"
            f"{json_text(events, max_chars=24000)}\n\n"
            "Use only these tool results. If the user asked for a digest and the items are ready, "
            "call the formatting tool. Otherwise answer the user directly with cited sources when available."
        ),
    }


def run_model_tool_loop(*, provider, messages, tools, model, max_tool_rounds) -> dict[str, Any]:
    working = list(messages)
    rounds: list[dict] = []
    all_events: list[dict] = []

    for idx in range(1, max_tool_rounds + 1):
        response = provider.complete(working, tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_rec: dict[str, Any] = {
            "round": idx,
            "assistant_text": response.text,
            "tool_calls": [{"name": c.name, "args": c.args} for c in calls],
            "tool_results": [],
        }

        if not calls:
            rounds.append(round_rec)
            return {"status": "answered", "assistant_text": response.text or "", "rounds": rounds, "tool_events": all_events}

        working.append(assistant_tool_message(response.text, calls))

        non_clarification: list[dict] = []
        for call in calls:
            event = execute_tool_call(call)
            round_rec["tool_results"].append(event)
            all_events.append(event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Please provide more information."
                rounds.append(round_rec)
                return {"status": "waiting_for_user", "assistant_text": question, "rounds": rounds, "tool_events": all_events}

            non_clarification.append(event)

        rounds.append(round_rec)
        working.append(tool_results_message(non_clarification))

    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Stopped after {max_tool_rounds} tool rounds.",
        "rounds": rounds,
        "tool_events": all_events,
    }


# ── Models ────────────────────────────────────────────────────────────────────

class NewConversationRequest(BaseModel):
    provider: str = "openrouter"
    model: str | None = None
    version: str = "v0"
    history_window: int = 5
    max_tool_rounds: int = 4


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class ConversationMeta(BaseModel):
    id: str
    provider: str
    model: str | None
    version: str
    history_window: int
    max_tool_rounds: int
    created_at: str
    updated_at: str
    turn_count: int
    title: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/conversations")
def list_conversations() -> list[dict]:
    result = []
    for cid, conv in _conversations.items():
        meta = conv["meta"]
        turns = conv["transcript"]["turns"]
        title = turns[0]["user"][:60] if turns else "New conversation"
        result.append({
            "id": cid,
            "provider": meta["provider"],
            "model": meta["model"],
            "version": meta["version"],
            "history_window": meta["history_window"],
            "max_tool_rounds": meta["max_tool_rounds"],
            "created_at": meta["created_at"],
            "updated_at": meta["updated_at"],
            "turn_count": len(turns),
            "title": title,
        })
    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return result


@app.post("/conversations")
def new_conversation(req: NewConversationRequest) -> dict:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    cid = f"{safe_slug(req.version)}_{safe_slug(req.provider)}_{timestamp}"

    try:
        provider = make_provider(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    selected_model = req.model or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(req.version, ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")

    meta = {
        "id": cid,
        "provider": req.provider,
        "model": selected_model,
        "version": req.version,
        "history_window": req.history_window,
        "max_tool_rounds": req.max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        **artifact_version_dict(artifact_version),
    }
    transcript = {
        "transcript_id": cid,
        **meta,
        "turns": [],
    }
    _conversations[cid] = {
        "meta": meta,
        "history": [],
        "transcript": transcript,
        "provider": provider,
        "selected_model": selected_model,
    }
    return {"id": cid, **meta, "turn_count": 0, "title": "New conversation"}


@app.get("/conversations/{cid}")
def get_conversation(cid: str) -> dict:
    conv = _conversations.get(cid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    turns = conv["transcript"]["turns"]
    title = turns[0]["user"][:60] if turns else "New conversation"
    return {**conv["meta"], "turn_count": len(turns), "title": title, "turns": turns}


@app.delete("/conversations/{cid}")
def delete_conversation(cid: str) -> dict:
    if cid not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del _conversations[cid]
    return {"deleted": cid}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    conv = _conversations.get(req.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    meta = conv["meta"]
    provider = conv["provider"]
    selected_model = conv["selected_model"]

    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(tool_declarations)

    history = conv["history"]
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(history, meta["history_window"]),
        {"role": "user", "content": req.message},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": len(conv["transcript"]["turns"]) + 1,
        "started_at": now_iso(),
        "user": req.message,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=selected_model,
            max_tool_rounds=meta["max_tool_rounds"],
        )
        turn_record.update(result)
        assistant_text = result["assistant_text"]
        history.append({"role": "user", "content": req.message})
        history.append({"role": "assistant", "content": assistant_text})
    except Exception as exc:
        turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {str(exc)}"})
        turn_record["ended_at"] = now_iso()
        conv["transcript"]["turns"].append(turn_record)
        meta["updated_at"] = now_iso()
        raise HTTPException(status_code=500, detail=turn_record["error"])

    turn_record["ended_at"] = now_iso()
    conv["transcript"]["turns"].append(turn_record)
    meta["updated_at"] = now_iso()

    return {
        "turn_index": turn_record["turn_index"],
        "user": req.message,
        "assistant_text": assistant_text,
        "status": result["status"],
        "rounds": result["rounds"],
        "tool_events": result["tool_events"],
    }


@app.get("/providers")
def list_providers() -> dict:
    return {
        "providers": [
            {"id": "openrouter", "label": "OpenRouter", "default_model": "openai/gpt-4o-mini"},
            {"id": "openai",     "label": "OpenAI",     "default_model": "gpt-4o-mini"},
            {"id": "anthropic",  "label": "Anthropic",  "default_model": "claude-haiku-4-5-20251001"},
            {"id": "gemini",     "label": "Gemini",     "default_model": "gemini-3.5-flash"},
        ]
    }
