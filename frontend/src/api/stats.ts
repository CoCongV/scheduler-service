import request from './request'

export interface DashboardStats {
    total_tasks: number
    status_counts: Record<string, number>
}

export function getDashboardStats() {
    return request({
        url: '/v1/stats/dashboard',
        method: 'get'
    })
}
