import request from './request'

export interface LoginParams {
  name?: string
  email?: string
  password: string
}

export interface LoginResponse {
  token: string
}

export interface UserInfo {
  id: number
  name: string
  email: string
  last_login: string
}

export function login(data: LoginParams) {
  return request({
    url: '/v1/users/token',
    method: 'post',
    data
  })
}

export function getUserInfo() {
  return request({
    url: '/v1/users/me',
    method: 'get'
  })
}

export function register(data: LoginParams & { email: string, name: string }) {
    return request({
        url: '/v1/users',
        method: 'post',
        data
    })
}
