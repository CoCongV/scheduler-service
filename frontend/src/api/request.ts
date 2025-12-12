import axios from 'axios'
import router from '../router' // Import router to handle redirection

// Extend Window interface to include Naive UI discrete APIs
declare global {
  interface Window {
    $message: any
    $dialog: any
    $notification: any
    $loadingBar: any
  }
}

const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api', // Vite 环境变量，通常是 /api
  timeout: 5000 // 请求超时时间
})

// request interceptor
service.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.log(error) // for debug
    return Promise.reject(error)
  }
)

// response interceptor
service.interceptors.response.use(
  response => {
    const res = response.data
    // 这里的错误判断逻辑需要根据你的后端API设计来调整
    // 注意：有些API在业务错误时返回200，通过code字段区分；有些直接返回HTTP错误码
    // 如果后端总是返回200，则这里需要判断 res.code
    
    // 基于目前后端代码，成功时直接返回数据对象，没有 code 字段包裹（例如 token 接口返回 {token: ...}）
    // 除非是特定的封装格式。如果遇到非200状态码，axios会进入 error 分支。
    // 所以这里如果 status 是 2xx，直接返回 res
    return res
  },
  error => {
    console.log('err' + error) // for debug
    const status = error.response ? error.response.status : null
    
    if (status === 401) {
      if (window.$message) {
        window.$message.error('登录已过期，请重新登录')
      }
      localStorage.removeItem('token')
      router.push('/login')
      return Promise.reject(error)
    }

    const message = error.response?.data?.detail || error.message || 'Error'

    if (window.$message) {
      window.$message.error(message)
    } else {
      console.error(message)
    }
    return Promise.reject(error)
  }
)

export default service
