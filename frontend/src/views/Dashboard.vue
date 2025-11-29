<template>
  <n-space vertical size="large">
    <n-h1>仪表盘</n-h1>
    
    <!-- Summary Cards -->
    <n-grid :x-gap="12" :y-gap="12" :cols="4">
      <n-gi>
        <n-card>
          <n-statistic label="总任务数" :value="stats.total_tasks" />
        </n-card>
      </n-gi>
      <n-gi v-for="(count, status) in stats.status_counts" :key="status">
        <n-card>
          <n-statistic :label="status" :value="count" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Status Distribution -->
    <n-card title="任务状态分布">
      <div class="progress-container">
        <div 
          v-for="(count, status) in stats.status_counts" 
          :key="status"
          class="progress-segment"
          :style="{ 
            width: getPercentage(count) + '%',
            backgroundColor: getStatusColor(status as string)
          }"
        >
          <n-popover trigger="hover">
            <template #trigger>
              <div class="segment-content"></div>
            </template>
            <span>{{ status }}: {{ count }} ({{ getPercentage(count) }}%)</span>
          </n-popover>
        </div>
      </div>
      
      <!-- Legend -->
      <n-space style="margin-top: 10px;">
        <div v-for="(count, status) in stats.status_counts" :key="status" style="display: flex; align-items: center;">
          <div :style="{ width: '12px', height: '12px', backgroundColor: getStatusColor(status as string), marginRight: '5px', borderRadius: '2px' }"></div>
          <span>{{ status }} ({{ count }})</span>
        </div>
      </n-space>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NSpace, NH1, NCard, NStatistic, NGrid, NGi, NPopover } from 'naive-ui'
import { getDashboardStats, type DashboardStats } from '../api/stats'

const stats = ref<DashboardStats>({
  total_tasks: 0,
  status_counts: {}
})

function getPercentage(count: number) {
  if (stats.value.total_tasks === 0) return 0
  return Math.round((count / stats.value.total_tasks) * 100)
}

function getStatusColor(status: string) {
  switch (status) {
    case 'PENDING': return '#2080f0' // Info
    case 'RUNNING': return '#f0a020' // Warning
    case 'COMPLETED': return '#18a058' // Success
    case 'FAILED': return '#d03050' // Error
    case 'CANCELLED': return '#909399' // Grey
    default: return '#e0e0e0'
  }
}

async function fetchData() {
  try {
    const res: any = await getDashboardStats()
    stats.value = res
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.progress-container {
  display: flex;
  width: 100%;
  height: 24px;
  background-color: #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
}

.progress-segment {
  height: 100%;
  transition: width 0.3s ease;
  cursor: pointer;
}

.segment-content {
  width: 100%;
  height: 100%;
}
</style>
