<template>
  <n-space vertical>
    <n-h1>仪表盘</n-h1>
    <n-card>
      <n-statistic label="总任务数" value="100" />
    </n-card>
    <n-card>
      <n-statistic label="正在运行的任务" value="10" />
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { NSpace, NH1, NCard, NStatistic } from 'naive-ui'
// Add logic for fetching dashboard data here later
</script>

<style scoped>
</style>
