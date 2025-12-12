import request from './request'

export interface Task {
  id: number
  name: string
  start_time: number | string // Backend returns string (ISO) or timestamp? Let's check schema response
  request_url: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS'
  cron?: string
  status: string
  error_message?: string
  user_id: number
  header?: Record<string, any>
  body?: Record<string, any>
  callback_url?: string
  callback_token?: string
}

export interface CreateTaskParams {
  name: string
  start_time?: number // timestamp in seconds
  request_url: string
  method?: string
  cron?: string
  header?: Record<string, any>
  body?: Record<string, any>
  callback_url?: string
  callback_token?: string
}

export function getTasks() {
  return request({
    url: '/v1/tasks',
    method: 'get'
  })
}

export function createTask(data: CreateTaskParams) {
  return request({
    url: '/v1/tasks',
    method: 'post',
    data
  })
}

export function deleteTask(id: number) {
  return request({
    url: `/v1/tasks/${id}`,
    method: 'delete'
  })
}
