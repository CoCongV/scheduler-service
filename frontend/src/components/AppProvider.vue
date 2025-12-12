<script setup lang="ts">
import { useLoadingBar, useDialog, useMessage, useNotification } from 'naive-ui'

// 挂载到 window 对象
window.$loadingBar = useLoadingBar()
window.$dialog = useDialog()
window.$message = useMessage()
window.$notification = useNotification()
</script>

<template>
  <slot />
</template>
