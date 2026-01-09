import request from './request'

export interface ApiKey {
    id: number
    prefix: string
    name: string
    created_at: string
    is_active: boolean
}

export interface ApiKeyCreate {
    name: string
}

export interface ApiKeyCreated extends ApiKey {
    key: string
}

export function getApiKeys() {
    return request.get<ApiKey[]>('/v1/apikeys')
}

export function createApiKey(data: ApiKeyCreate) {
    return request.post<ApiKeyCreated>('/v1/apikeys', data)
}

export function revokeApiKey(id: number) {
    return request.delete(`/v1/apikeys/${id}`)
}
