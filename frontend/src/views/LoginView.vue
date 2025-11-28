<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  useMessage,
  NTabs,
  NTabPane
} from 'naive-ui'
import { login, register } from '../api/user'

const router = useRouter()
const message = useMessage()

const activeTab = ref('login')

// Login Data
const loginForm = ref({
  username: '',
  password: ''
})

// Register Data
const registerForm = ref({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    message.warning('请输入用户名/邮箱和密码')
    return
  }

  loading.value = true
  try {
    // Detect if input is email or username
    const isEmail = loginForm.value.username.includes('@')
    const payload = {
      password: loginForm.value.password,
      ...(isEmail ? { email: loginForm.value.username } : { name: loginForm.value.username })
    }

    const res: any = await login(payload)
    const token = res.token
    if (token) {
      localStorage.setItem('token', token)
      message.success('登录成功')
      router.push('/dashboard')
    } else {
      message.error('登录失败: 未获取到Token')
    }
  } catch (error: any) {
    console.error(error)
    // Error is handled by interceptor mostly, but we can catch specific cases
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
    if (!registerForm.value.name || !registerForm.value.email || !registerForm.value.password) {
        message.warning('请填写所有必填项')
        return
    }
    if (registerForm.value.password !== registerForm.value.confirmPassword) {
        message.warning('两次输入的密码不一致')
        return
    }

    loading.value = true
    try {
        await register({
            name: registerForm.value.name,
            email: registerForm.value.email,
            password: registerForm.value.password
        })
        message.success('注册成功，请登录')
        activeTab.value = 'login'
        loginForm.value.username = registerForm.value.email // auto fill email
    } catch (error) {
        console.error(error)
    } finally {
        loading.value = false
    }
}
</script>

<template>
  <div class="login-container">
    <n-card class="login-card">
      <n-tabs v-model:value="activeTab" size="large" justify-content="space-evenly">
        <n-tab-pane name="login" tab="登录">
          <n-form>
            <n-form-item label="用户名 / 邮箱">
              <n-input v-model:value="loginForm.username" placeholder="请输入用户名或邮箱" @keydown.enter="handleLogin" />
            </n-form-item>
            <n-form-item label="密码">
              <n-input
                v-model:value="loginForm.password"
                type="password"
                show-password-on="click"
                placeholder="请输入密码"
                @keydown.enter="handleLogin"
              />
            </n-form-item>
            <n-button type="primary" block :loading="loading" @click="handleLogin">
              登录
            </n-button>
          </n-form>
        </n-tab-pane>
        <n-tab-pane name="register" tab="注册">
            <n-form>
                <n-form-item label="用户名">
                    <n-input v-model:value="registerForm.name" placeholder="请输入用户名" />
                </n-form-item>
                <n-form-item label="邮箱">
                    <n-input v-model:value="registerForm.email" placeholder="请输入邮箱" />
                </n-form-item>
                <n-form-item label="密码">
                    <n-input v-model:value="registerForm.password" type="password" show-password-on="click" placeholder="请输入密码" />
                </n-form-item>
                <n-form-item label="确认密码">
                    <n-input v-model:value="registerForm.confirmPassword" type="password" show-password-on="click" placeholder="请再次输入密码" />
                </n-form-item>
                <n-button type="primary" block :loading="loading" @click="handleRegister">
                    注册
                </n-button>
            </n-form>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.login-card {
  width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Dark mode adaptation if needed */
@media (prefers-color-scheme: dark) {
  .login-container {
    background-color: #101014;
  }
}
</style>
