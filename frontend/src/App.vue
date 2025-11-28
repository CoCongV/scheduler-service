<script setup lang="ts">
import { NConfigProvider, NGlobalStyle, darkTheme, NMessageProvider } from 'naive-ui'
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <n-global-style />
    <n-message-provider>
      <router-view />
    </n-message-provider>
  </n-config-provider>
</template>

<style scoped>
</style>