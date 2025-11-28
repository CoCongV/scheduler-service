<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NButton,
  NSpace,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NDatePicker,
  NText,
  useMessage,
  NTag,
  NInputGroup,
  NRadioGroup,
  NRadioButton
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { format } from 'date-fns'
import { getTasks, createTask, deleteTask, type Task, type CreateTaskParams } from '../api/task'

const message = useMessage()

const showModal = ref(false)
// const isEdit = ref(false) // Backend API currently doesn't support editing

interface TaskForm extends Partial<Task> {
  start_time_ts?: number
  request_protocol?: string
  request_path?: string
  callback_protocol?: string
  callback_path?: string
  header_str?: string
  body_str?: string
}

const currentTask = ref<TaskForm>({})
const taskType = ref<'once' | 'cron'>('once')
const loading = ref(false)

const tasks = ref<Task[]>([])

const columns: DataTableColumns<Task> = [
  {
    title: 'ID',
    key: 'id'
  },
  {
    title: '任务名称',
    key: 'name'
  },
  {
    title: '请求方法',
    key: 'method',
    render(row) {
      return h(
        NTag,
        {
          style: {
            marginRight: '6px'
          },
          type: methodTagType(row.method),
          bordered: false
        },
        {
          default: () => row.method
        }
      )
    }
  },
  {
    title: '请求URL',
    key: 'request_url'
  },
  {
    title: '计划时间/Cron',
    key: 'cron',
    render(row) {
      let timeDisplay = ''
      if (row.cron) {
        timeDisplay = row.cron
      } else if (row.start_time) {
         // start_time is in seconds, convert to milliseconds
         timeDisplay = format(new Date(Number(row.start_time) * 1000), 'yyyy-MM-dd HH:mm:ss')
      }
      return h(
        NText,
        {},
        { default: () => timeDisplay }
      )
    }
  },
  {
    title: '状态',
    key: 'status',
    render(row) {
      return h(
        NTag,
        {
          type: statusTagType(row.status),
          bordered: false
        },
        {
          default: () => row.status
        }
      )
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      return h(
        NSpace,
        {},
        {
          default: () => [
            // h(
            //   NButton,
            //   {
            //     size: 'small',
            //     onClick: () => handleEdit(row)
            //   },
            //   { default: () => '编辑' }
            // ),
            h(
              NButton,
              {
                size: 'small',
                type: 'error',
                onClick: () => handleDelete(row.id)
              },
              { default: () => '删除' }
            )
          ]
        }
      )
    }
  }
]

function statusTagType(status: string) {
  switch (status) {
    case 'PENDING':
      return 'info'
    case 'RUNNING':
      return 'warning'
    case 'COMPLETED':
      return 'success'
    case 'FAILED':
      return 'error'
    default:
      return 'default'
  }
}

function methodTagType(method: string) {
  switch (method) {
    case 'GET':
      return 'info'
    case 'POST':
      return 'success'
    case 'PUT':
      return 'warning'
    case 'DELETE':
      return 'error'
    case 'PATCH':
      return 'primary'
    default:
      return 'default'
  }
}


function handleCreate() {
  // isEdit.value = false
  currentTask.value = { 
    method: 'GET',
    request_protocol: 'http://',
    callback_protocol: 'http://'
  } 
  taskType.value = 'once'
  showModal.value = true
}

// function handleEdit(task: Task) {
//   isEdit.value = true
//   // Deep copy to avoid direct mutation
//   currentTask.value = { ...task }
//   // Convert string start_time to Date object for NDatePicker
//   if (currentTask.value.start_time && typeof currentTask.value.start_time === 'string') {
//     currentTask.value.start_time_ts = new Date(currentTask.value.start_time).getTime()
//   }
//   showModal.value = true
// }

async function handleDelete(id: number) {
  try {
    await deleteTask(id)
    message.success(`删除任务 ${id}`)
    await fetchTasks()
  } catch (error: any) {
    console.error(error)
    // Error handled by interceptor mostly, but we can add specific handling if needed
  }
}

async function handleSaveTask() {
  // Validate required fields
  if (!currentTask.value.name || !currentTask.value.request_path) {
    message.error('请填写完整信息')
    return
  }
  
  // if (!currentTask.value.cron && !currentTask.value.start_time_ts) {
  //     message.error('请选择开始时间或填写Cron表达式')
  //     return
  // }

  // Parse JSON fields
  let header = undefined
  if (currentTask.value.header_str) {
    try {
      header = JSON.parse(currentTask.value.header_str)
    } catch (e) {
      message.error('Header 格式错误，请输入有效的 JSON')
      return
    }
  }

  let body = undefined
  if (currentTask.value.body_str) {
    try {
      body = JSON.parse(currentTask.value.body_str)
    } catch (e) {
      message.error('Body 格式错误，请输入有效的 JSON')
      return
    }
  }

  loading.value = true
  try {
      // Create task
      const startTime = (taskType.value === 'once' && currentTask.value.start_time_ts) 
        ? currentTask.value.start_time_ts / 1000 
        : undefined;
      
      const fullRequestUrl = (currentTask.value.request_protocol || 'http://') + currentTask.value.request_path
      
      let fullCallbackUrl = undefined
      if (currentTask.value.callback_path) {
        fullCallbackUrl = (currentTask.value.callback_protocol || 'http://') + currentTask.value.callback_path
      }

      const params: CreateTaskParams = {
        name: currentTask.value.name!,
        start_time: startTime, // Convert to seconds
        request_url: fullRequestUrl,
        method: currentTask.value.method,
        cron: taskType.value === 'cron' ? currentTask.value.cron : undefined,
        header: header,
        body: body,
        callback_url: fullCallbackUrl,
        callback_token: currentTask.value.callback_token
      }

      await createTask(params)
      message.success('任务创建成功')
      showModal.value = false
      currentTask.value = {}
      await fetchTasks()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function fetchTasks() {
  loading.value = true
  try {
    const res: any = await getTasks()
    tasks.value = res.tasks || []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTasks()
})
</script>

<template>
  <n-space vertical>
    <n-h1>任务管理</n-h1>
    <n-space>
      <n-button type="primary" @click="handleCreate">创建任务</n-button>
      <n-button @click="fetchTasks">刷新</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="tasks" :pagination="{ pageSize: 10 }" :loading="loading" />

    <n-modal v-model:show="showModal" preset="dialog" title="创建任务" :mask-closable="false">
      <n-form :model="currentTask" label-placement="left" label-width="80px">
        <n-form-item label="任务名称">
          <n-input v-model:value="currentTask.name" placeholder="输入任务名称" />
        </n-form-item>
        <n-form-item label="请求方法">
          <n-select
            v-model:value="currentTask.method"
            :options="[
              { label: 'GET', value: 'GET' },
              { label: 'POST', value: 'POST' },
              { label: 'PUT', value: 'PUT' },
              { label: 'DELETE', value: 'DELETE' },
              { label: 'PATCH', value: 'PATCH' },
              { label: 'HEAD', value: 'HEAD' },
              { label: 'OPTIONS', value: 'OPTIONS' }
            ]"
            placeholder="选择请求方法"
          />
        </n-form-item>
        <n-form-item label="请求URL">
          <n-input-group>
            <n-select
              :style="{ width: '30%' }"
              v-model:value="currentTask.request_protocol"
              :options="[
                { label: 'http://', value: 'http://' },
                { label: 'https://', value: 'https://' }
              ]"
            />
            <n-input :style="{ width: '70%' }" v-model:value="currentTask.request_path" placeholder="输入请求路径 (例如: example.com/api)" />
          </n-input-group>
        </n-form-item>
        <n-form-item label="任务类型">
          <n-radio-group v-model:value="taskType">
            <n-radio-button value="once">单次执行</n-radio-button>
            <n-radio-button value="cron">Cron 周期执行</n-radio-button>
          </n-radio-group>
        </n-form-item>

        <n-form-item label="Cron表达式" v-if="taskType === 'cron'">
          <n-input v-model:value="currentTask.cron" placeholder="例如: 0 0 * * *" />
        </n-form-item>
        <n-form-item label="开始时间" v-if="taskType === 'once'">
          <n-date-picker
            v-model:value="currentTask.start_time_ts"
            type="datetime"
            clearable
            placeholder="留空则立即执行"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="Header (JSON)">
          <n-input
            v-model:value="currentTask.header_str"
            type="textarea"
            placeholder="输入 JSON 格式的 Header"
          />
        </n-form-item>
        <n-form-item label="Body (JSON)">
          <n-input
            v-model:value="currentTask.body_str"
            type="textarea"
            placeholder="输入 JSON 格式的 Body"
          />
        </n-form-item>
        <n-form-item label="回调 URL">
          <n-input-group>
            <n-select
              :style="{ width: '30%' }"
              v-model:value="currentTask.callback_protocol"
              :options="[
                { label: 'http://', value: 'http://' },
                { label: 'https://', value: 'https://' }
              ]"
            />
            <n-input :style="{ width: '70%' }" v-model:value="currentTask.callback_path" placeholder="输入回调路径" />
          </n-input-group>
        </n-form-item>
        <n-form-item label="回调 Token">
          <n-input v-model:value="currentTask.callback_token" placeholder="输入回调 Token" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" :loading="loading" @click="handleSaveTask">保存</n-button>
      </template>
    </n-modal>
  </n-space>
</template>

<style scoped>
</style>
