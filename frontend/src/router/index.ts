import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘', requiresAuth: true }
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('../views/TaskView.vue'),
        meta: { title: '任务管理', requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '个人设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  // 如果去往登录页，且已有token，跳转到首页（可选）
  if (to.path === '/login' && token) {
    next('/')
    return
  }

  // 检查是否需要认证
  if (to.matched.some(record => record.meta.requiresAuth !== false)) {
    // 默认所有路由都需要认证，除了明确标记不需要的，或者登录页
    // 这里我们的逻辑是：如果不在白名单（如 /login），都需要 token
    if (to.path !== '/login' && !token) {
      next('/login')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
