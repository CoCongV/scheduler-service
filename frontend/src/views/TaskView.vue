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
  NInputNumber,
  NDatePicker,
  NText,
  useMessage,
  NTag
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { format } from 'date-fns'
import { getTasks, createTask, deleteTask, type Task, type CreateTaskParams } from '../api/task'

const message = useMessage()

const showModal = ref(false)
// const isEdit = ref(false) // Backend API currently doesn't support editing
const currentTask = ref<Partial<Task> & { start_time_ts?: number }>({})
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
         timeDisplay = format(new Date(row.start_time), 'yyyy-MM-dd HH:mm:ss')
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
  currentTask.value = { method: 'GET' } // Default method
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
  if (!currentTask.value.name || !currentTask.value.request_url) {
    message.error('请填写完整信息')
    return
  }
  
  if (!currentTask.value.cron && !currentTask.value.start_time_ts) {
      message.error('请选择开始时间或填写Cron表达式')
      return
  }

  loading.value = true
  try {
      // Create task
      const startTime = currentTask.value.start_time_ts ? currentTask.value.start_time_ts / 1000 : Date.now() / 1000;

      const params: CreateTaskParams = {
        name: currentTask.value.name!,
        start_time: startTime, // Convert to seconds
        request_url: currentTask.value.request_url!,
        method: currentTask.value.method,
        cron: currentTask.value.cron || undefined,
        // header: currentTask.value.header, // TODO: Add UI for header/body
        // body: currentTask.value.body
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
          <n-input v-model:value="currentTask.request_url" placeholder="输入请求URL" />
        </n-form-item>
        <n-form-item label="Cron表达式">
          <n-input v-model:value="currentTask.cron" placeholder="可选，例如: 0 0 * * *" />
        </n-form-item>
        <n-form-item label="开始时间" v-if="!currentTask.cron">
          <n-date-picker
            v-model:value="currentTask.start_time_ts"
            type="datetime"
            clearable
            placeholder="选择任务开始时间"
            style="width: 100%"
          />
        </n-form-item>
        <!-- Add more fields as needed, e.g., header, body, callback_url, etc. -->
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
