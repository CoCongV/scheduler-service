<template>
  <n-space vertical size="large">
    <n-h1>个人设置</n-h1>
    <n-card>
      <n-form
        ref="formRef"
        :model="formValue"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
        size="medium"
        style="max-width: 640px"
      >
        <n-form-item label="用户名" path="name">
          <n-input v-model:value="formValue.name" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="formValue.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="新密码" path="password">
          <n-input
            v-model:value="formValue.password"
            type="password"
            show-password-on="click"
            placeholder="如果不修改密码请留空"
          />
        </n-form-item>
        <n-form-item>
          <n-button type="primary" @click="handleValidateClick" :loading="loading">
            保存修改
          </n-button>
        </n-form-item>
      </n-form>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage, type FormInst, type FormRules } from 'naive-ui'
import { getUserInfo, updateUser, type UserUpdateParams } from '../api/user'

const formRef = ref<FormInst | null>(null)
const message = useMessage()
const loading = ref(false)

const formValue = ref<UserUpdateParams>({
  name: '',
  email: '',
  password: ''
})

const rules: FormRules = {
  name: {
    required: true,
    message: '请输入用户名',
    trigger: 'blur'
  },
  email: {
    required: true,
    message: '请输入邮箱',
    trigger: 'blur'
  }
}

async function fetchUserInfo() {
  try {
    const res: any = await getUserInfo()
    formValue.value.name = res.name
    formValue.value.email = res.email
  } catch (error) {
    console.error(error)
  }
}

function handleValidateClick(e: MouseEvent) {
  e.preventDefault()
  formRef.value?.validate(async (errors) => {
    if (!errors) {
      loading.value = true
      try {
        const updateData: UserUpdateParams = {
          name: formValue.value.name,
          email: formValue.value.email
        }
        if (formValue.value.password) {
          updateData.password = formValue.value.password
        }
        
        await updateUser(updateData)
        message.success('更新成功')
        // Clear password field after successful update
        formValue.value.password = ''
      } catch (error) {
        console.error(error)
      } finally {
        loading.value = false
      }
    } else {
      console.log(errors)
      message.error('请检查输入')
    }
  })
}

onMounted(() => {
  fetchUserInfo()
})
</script>
