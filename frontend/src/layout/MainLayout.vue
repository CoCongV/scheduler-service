<script setup lang="ts">
import { ref, h } from 'vue' // Added 'h' for renderIcon
import { RouterView, useRouter } from 'vue-router'
import {
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NSpace,
  NButton,
  NIcon,
  useMessage // Needed for error handling
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  SpeedometerOutline as DashboardIcon,
  ClipboardOutline as TasksIcon
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage() // Initialize useMessage

const menuOptions: MenuOption[] = [
  {
    label: '仪表盘',
    key: 'dashboard',
    icon: renderIcon(DashboardIcon),
    name: 'Dashboard' // Add name property for router push
  },
  {
    label: '任务管理',
    key: 'tasks',
    icon: renderIcon(TasksIcon),
    name: 'Tasks' // Add name property for router push
  }
]

const collapsed = ref(false)
const inverted = ref(false)

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

function handleUpdateValue(key: string, item: MenuOption) {
  router.push({ name: item.name as string }).catch(err => {
    message.error(`导航失败: ${err.message}`);
  });
}
function handleLogout() {
  localStorage.removeItem('token')
  message.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <n-layout has-sider style="min-height: 100vh">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      :collapsed="collapsed"
      show-trigger="arrow-circle"
      @collapse="collapsed = true"
      @expand="collapsed = false"
      :inverted="inverted"
    >
      <div style="height: 64px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #fff;">
        <span v-if="!collapsed">Scheduler Admin</span>
        <span v-else>SA</span>
      </div>
      <n-menu
        :inverted="inverted"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        @update:value="handleUpdateValue"
      />
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered style="padding: 16px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h2>{{ $route.meta.title || 'Scheduler Service' }}</h2>
        </div>
        <n-space>
          <n-button @click="$router.push('/profile')">个人设置</n-button>
          <n-button type="error" @click="handleLogout">退出登录</n-button>
        </n-space>
      </n-layout-header>
      <n-layout-content content-style="padding: 24px;">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
/* Add some basic styling if needed */
</style>