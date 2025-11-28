import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 引入路由
import { createDiscreteApi } from 'naive-ui' // 引入离散组件API

const { message, dialog, notification, loadingBar } = createDiscreteApi(
  ['message', 'dialog', 'notification', 'loadingBar']
)

// 将离散组件挂载到 window 对象，以便在非组件文件中使用（如 axios 拦截器）
window.$message = message
window.$dialog = dialog
window.$notification = notification
window.$loadingBar = loadingBar

const app = createApp(App)

app.use(router) // 使用路由

// 将离散组件挂载到全局属性（可选，为了在模板中方便使用）
app.config.globalProperties.$message = message
app.config.globalProperties.$dialog = dialog
app.config.globalProperties.$notification = notification
app.config.globalProperties.$loadingBar = loadingBar

app.mount('#app')