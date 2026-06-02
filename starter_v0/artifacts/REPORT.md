# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:3
- Members:3
- Provider/model:OpenAI/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent: tìm kiếm thông tin từ web, mạng xã hội và bài báo khoa học; đọc và tóm tắt nội dung từ URL; tổng hợp kết quả thành báo cáo hoặc digest theo yêu cầu. Agent có thể hỗ trợ theo dõi tin tức, nghiên cứu chủ đề và chuẩn bị nội dung để gửi ra hệ thống bên ngoài sau khi được người dùng xác nhận.


Link dùng thử (deploy): https://font-mods-pod-newspapers.trycloudflare.com/

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
clarify	|Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận|	Không
timeline|	Lấy các bài đăng gần đây từ một tài khoản mạng xã hội|	Không
social_search|	Tìm kiếm bài đăng theo từ khóa/chủ đề trên mạng xã hội|	Không
lookup|	Tìm kiếm thông tin hoặc tin tức trên web	Không
fetch|	Đọc và lấy nội dung từ một URL cụ thể	Không
format|	Tổng hợp dữ liệu và trình bày thành digest, báo cáo hoặc bản tóm tắt|	Không
send|	Gửi nội dung ra hệ thống bên ngoài sau khi được người dùng xác nhận|	Không
policy|	Tìm kiếm thông tin trong tài liệu/chính sách nội bộ	Không
papers|	Tìm kiếm bài báo khoa học|	Không
paper_text|	Lấy nội dung văn bản của một bài báo khoa học|	Không
trending|	Lấy các chủ đề đang thịnh hành trên X/Twitter theo quốc gia hoặc toàn cầu|	Có
profile|	Lấy thông tin hồ sơ công khai của tài khoản X/Twitter (bio, follower, trạng thái xác minh...)|	Có
arxiv_related|	Tìm các bài báo arXiv liên quan đến một bài báo đã biết|	Có
summarize|	Rút trích và xếp hạng các ý chính từ nhiều nguồn dữ liệu, tạo key takeaways|	Có


## A3. Câu hỏi mẫu để thử

1. Tin tức về AI tuần này là gì? Hãy tổng hợp 5 tin nổi bật nhất thành một bản digest ngắn.
2. Tìm các bài đăng mới nhất của tài khoản @OpenAI trên X/Twitter và tóm tắt nội dung chính.
3. Những chủ đề nào đang trending trên X/Twitter tại Vietnam hôm nay?
4. Tìm 5 bài báo khoa học mới về AI Agents trên arXiv và tóm tắt điểm nổi bật của từng bài.
5. Đọc nội dung URL https://example.com và tạo báo cáo tóm tắt theo các mục: nội dung chính, kết luận và các điểm đáng chú ý.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File                                             |
| v0      | baseline                      | Đo hiệu năng ban đầu của agent trước khi tối ưu prompt và tool routing                                             |             – |         0.70 | runs/v0_B_base_openrouter_20260602T125722349095.json |
| v1      | system_prompt.md              | Bổ sung quy tắc routing, timeframe cho news, multi-turn và boundary của send tool sẽ giảm lỗi chọn tool và tham số |          0.70 |         0.90 | runs/v2_B_base_openrouter_20260602T144851505914.json |
| v2      | system_prompt.md              | Tăng cường quy tắc argument normalization và xử lý xác nhận trước external write để giảm lỗi còn lại               |          0.90 |         0.95 | runs/v3_B_base_openrouter_20260602T145901200269.json |
| v3      | tools.yaml                    | Bổ sung và làm rõ mô tả tool (trending, profile, arxiv_related, summarize), giúp agent định tuyến chính xác hơn    |          0.95 |         1.00 | runs/v7_B_base_openrouter_20260602T151829881317.json |
| v4      | system_prompt.md + tools.yaml | Hoàn thiện prompt và tool descriptions để đạt độ chính xác tối đa trên toàn bộ bộ đánh giá                         |          1.00 |         1.00 | runs/v8_B_base_openrouter_20260602T152633419121.json |



## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID              | Failure Type    | Actual Tool Calls                                 | What Failed                                                                                                             | Fix                                                                                |

| Rxx (news query)     | wrong_arg_value | `lookup(query="AI", topic="news")`                | Thiếu hoặc chọn sai `timeframe` cho truy vấn tin tức hôm nay, dẫn đến sai argument.                                     | Thêm rule: từ khóa "hôm nay", "today" ⇒ `timeframe="day"`.                         |
| Rxx (multiturn send) | wrong_boundary  | `send(...)` hoặc hành động ngoài phạm vi xác nhận | Agent thực hiện hành động gửi khi chưa hoàn tất bước xác nhận người dùng. Đây là lỗi boundary duy nhất ở run đạt 0.95.  | Bắt buộc yêu cầu xác nhận (`clarify`) trước mọi external write/send.               |
| Rxx (routing)        | wrong_tool      | Gọi tool khác thay vì tool mong đợi               | Một số truy vấn bị định tuyến sang tool không đúng, làm giảm tool routing accuracy xuống 0.95.                          | Bổ sung luật routing rõ ràng giữa `timeline`, `social_search`, `lookup`, `papers`. |
| Rxx (missing info)   | missing_info    | Không gọi `clarify`                               | Agent không hỏi lại khi thiếu tham số bắt buộc nên không tạo đúng tool call.                                            | Thêm quy tắc: thiếu URL, username, paper id... ⇒ gọi `clarify` trước.              |
| Rxx (extra call)     | extra_tool_call | Gọi thêm một tool không cần thiết                 | Agent thực hiện thêm tool call ngoài yêu cầu của testcase.                                                              | Giới hạn chỉ gọi tool tối thiểu cần thiết để hoàn thành yêu cầu.                   |


## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID                         | What It Tests                                                               | Expected Tool/Behavior                                        | Result |
| ------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------- | ------ |
| G01_ST_trending_vietnam         | Truy vấn chủ đề đang trending tại Việt Nam                                  | `trending(country="Vietnam")`                                 | Passed |
| G02_ST_profile_karpathy         | Lấy thông tin profile công khai của tài khoản X/Twitter                     | `profile(screenname="karpathy")`                              | Passed |
| G03_ST_news_month_openai        | Nhận diện "tháng này" → timeframe=month cho tin tức                         | `lookup(query="OpenAI", topic="news", timeframe="month")`     | Passed |
| G04_ST_papers_rag_eval          | Tìm bài báo khoa học trên arXiv                                             | `papers(query="retrieval augmented generation evaluation")`   | Passed |
| G05_ST_fetch_url                | Có URL cụ thể thì đọc nội dung URL                                          | `fetch(url="https://arxiv.org/abs/1706.03762")`               | Passed |
| G06_MT_parallel_then_narrow_web | Thu hẹp từ web + social sang chỉ web, giữ chủ đề AI hôm nay                 | `lookup(query="AI", topic="news", timeframe="day")`           | Passed |
| G07_MT_clarify_handle_timeline  | Carry thông tin giữa các lượt hội thoại, map Sam Altman → sama, giữ limit=5 | `timeline(screenname="sama", limit=5)`                        | Passed |
| G08_MT_carry_timeframe_week     | Giữ nguyên timeframe=week qua nhiều lượt, đổi query sang robotics           | `lookup(query="robotics", topic="news", timeframe="week")`    | Passed |
| G09_MT_confirm_before_send      | Yêu cầu xác nhận trước khi gửi Telegram                                     | `clarify(response_type="yes_no")`, không gọi `send` trực tiếp | Passed |
| G10_MT_switch_social_to_web     | Chuyển từ Twitter sang web nhưng giữ chủ đề GPT-5 và timeframe hôm nay      | `lookup(query="GPT-5", topic="news", timeframe="day")`        | Passed |


## B4. Live Chat Evidence

| Turn | User Request                         | Tool Calls                                                                          | Version Evidence                                                                                  | Outcome                                        |

| 1    | Tin AI hôm nay có gì nổi bật?        | `lookup(query="AI", topic="news", timeframe="day", max_results=3)`                  | Agent nhận diện đây là truy vấn tin tức, tự động đặt `topic=news` và `timeframe=day`              | Trả về các tin AI nổi bật trong ngày           |
| 2    | Tóm tắt vài tweet mới nhất giúp mình | `clarify(question="Bạn muốn lấy bài đăng từ tài khoản nào?", response_type="text")` | Agent phát hiện thiếu thông tin bắt buộc (tài khoản nguồn) nên hỏi lại thay vì gọi tool ngay      | Chờ người dùng cung cấp tài khoản              |
| 3    | Của Andrej Karpathy nhé, lấy 5 bài   | `timeline(screenname="karpathy", limit=5)`                                          | Agent ghi nhớ ngữ cảnh từ lượt trước, map yêu cầu thành timeline với đúng account và số lượng bài | Trả về 5 bài đăng gần nhất của Andrej Karpathy |


## B5. Bonus Evidence

| Bonus                | Evidence File                                                                                 | What Worked                                                                                                                   | Risk / Guardrail                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| send (Telegram)      | `data/eval_group.json` (G09_MT_confirm_before_send), transcript gửi bản tin                   | Agent luôn yêu cầu xác nhận (`clarify yes_no`) trước khi gọi `send`, tránh gửi nhầm nội dung                                  | Không được gọi `send` trực tiếp; bắt buộc xác nhận từ người dùng trước mọi hành động external write  |
| arXiv/company policy | `artifacts/tools.yaml`, `data/eval_group.json` (G04_ST_papers_rag_eval), tool `arxiv_related` | Tìm paper bằng `papers`, đọc bằng `paper_text`, mở rộng nghiên cứu bằng `arxiv_related`; tra cứu tài liệu nội bộ qua `policy` | Chỉ dùng cho nguồn học thuật/chính sách hợp lệ; cần phân biệt rõ `lookup` (web) và `papers`/`policy` |
| UI                   | Link deploy (Cloudflare Tunnel / Vercel / Streamlit)                                          | Có giao diện chat để nhập câu hỏi, xem tool calls và kết quả nghiên cứu                                                       | Không hiển thị thông tin nhạy cảm, cần xử lý lỗi tool và timeout rõ ràng                             |

## B6. Reflection

Which fixes belonged in `system_prompt.md`?

Các lỗi liên quan đến hành vi suy luận và ra quyết định của agent được xử lý trong `system_prompt.md`, bao gồm:

* Quy tắc routing giữa `lookup`, `timeline`, `social_search`, `papers` và `fetch`.
* Quy tắc ánh xạ timeframe cho tin tức (`today → day`, `this week → week`, `this month → month`).
* Quy tắc multi-turn: ưu tiên yêu cầu mới nhất, giữ lại context khi người dùng nói "vẫn là", "keep", "giữ".
* Quy tắc boundary cho hành động bên ngoài (send/publish/post): phải xác nhận bằng `clarify(response_type=yes_no)` trước khi gọi `send`.
* Quy tắc tool minimization: chỉ gọi số tool tối thiểu cần thiết.

 Which fixes belonged in `tools.yaml`?

Các lỗi liên quan đến khả năng và định nghĩa công cụ được xử lý trong `tools.yaml`, bao gồm:

* Bổ sung tool `trending` để hỗ trợ truy vấn chủ đề đang thịnh hành trên X/Twitter.
* Bổ sung tool `profile` để lấy thông tin tài khoản X/Twitter.
* Bổ sung tool `arxiv_related` để tìm các bài báo liên quan trên arXiv.
* Bổ sung tool `summarize` để tổng hợp và rút trích các ý chính từ nhiều nguồn.
* Làm rõ mô tả tool và tham số đầu vào nhằm giảm lỗi gọi sai tool hoặc truyền sai argument.

 Which failure needed manual review instead of automatic grading?

Lỗi liên quan đến chất lượng nội dung tổng hợp (summary quality) cần được đánh giá thủ công.

Ví dụ:

* Hai agent có thể gọi đúng tool và đúng tham số nhưng tạo ra bản tóm tắt với chất lượng khác nhau.
* Các trường hợp digest, report hoặc summary thường khó đánh giá hoàn toàn bằng rule-based grading.

Ngoài ra, các trường hợp routing đúng nhưng gọi thêm một tool không thật sự cần thiết cũng có thể cần xem xét thủ công tùy ngữ cảnh.

 What would you improve next?

* Bổ sung khả năng tự động kết hợp nhiều nguồn (web + social + papers) và tạo báo cáo hợp nhất.
* Thêm memory ngắn hạn để theo dõi các thực thể đã nhắc đến trong cuộc hội thoại dài.
* Cải thiện entity resolution (ví dụ ánh xạ tên người nổi tiếng sang tài khoản mạng xã hội chính xác hơn).
* Bổ sung cơ chế xếp hạng và lọc nguồn để ưu tiên các nguồn uy tín.
* Mở rộng bộ eval với nhiều edge cases hơn cho multi-turn, correction và conflict resolution.
