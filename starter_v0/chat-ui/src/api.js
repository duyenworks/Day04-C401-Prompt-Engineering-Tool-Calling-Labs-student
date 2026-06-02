import axios from 'axios'

const http = axios.create({ baseURL: '' })

export const getProviders = () => http.get('/providers').then(r => r.data.providers)
export const listConversations = () => http.get('/conversations').then(r => r.data)
export const newConversation = (params) => http.post('/conversations', params).then(r => r.data)
export const getConversation = (id) => http.get(`/conversations/${id}`).then(r => r.data)
export const deleteConversation = (id) => http.delete(`/conversations/${id}`).then(r => r.data)
export const sendMessage = (conversation_id, message) =>
  http.post('/chat', { conversation_id, message }).then(r => r.data)
