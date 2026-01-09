<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { 
  NButton, NDataTable, NSpace, NModal, NForm, NFormItem, NInput, 
  useMessage, NPopconfirm, NCard, NResult, NText 
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { getApiKeys, createApiKey, revokeApiKey } from '../api/apikey'
import type { ApiKey } from '../api/apikey'

const message = useMessage()
const loading = ref(false)
const data = ref<ApiKey[]>([])

const showCreateModal = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)
const createModel = ref({
  name: ''
})

const showResultModal = ref(false)
const newKey = ref('')

const columns: DataTableColumns<ApiKey> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '名称',
    key: 'name'
  },
  {
    title: '前缀',
    key: 'prefix',
    render(row) {
      return h(NText, { code: true }, { default: () => row.prefix + '...' })
    }
  },
  {
    title: '创建时间',
    key: 'created_at'
  },
  {
    title: '状态',
    key: 'is_active',
    render(row) {
      return row.is_active ? '活跃' : '已撤销'
    }
  },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      if (!row.is_active) return null
      return h(
        NPopconfirm,
        {
          onPositiveClick: () => handleRevoke(row)
        },
        {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '撤销' }),
          default: () => '确定要撤销这个 API Key 吗？撤销后无法恢复。'
        }
      )
    }
  }
]

async function loadData() {
  loading.value = true
  try {
    const res = await getApiKeys()
    data.value = res as any // The interceptor returns data directly
  } catch (error: any) {
    message.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createModel.value.name) {
    message.warning('请输入名称')
    return
  }
  createLoading.value = true
  try {
    const res = await createApiKey({ name: createModel.value.name })
    newKey.value = (res as any).key // The interceptor returns data directly
    showCreateModal.value = false
    showResultModal.value = true
    createModel.value.name = ''
    loadData()
  } catch (error: any) {
    message.error(error.message || '创建失败')
  } finally {
    createLoading.value = false
  }
}

async function handleRevoke(row: ApiKey) {
  try {
    await revokeApiKey(row.id)
    message.success('已撤销')
    loadData()
  } catch (error: any) {
    message.error(error.message || '撤销失败')
  }
}

function copyKey() {
  navigator.clipboard.writeText(newKey.value)
  message.success('已复制到剪贴板')
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="apikey-page">
    <n-space vertical size="large">
      <n-space justify="space-between">
        <h2>API Keys</h2>
        <n-button type="primary" @click="showCreateModal = true">
          创建 API Key
        </n-button>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="data"
        :loading="loading"
        :bordered="false"
        :single-line="false"
      />
    </n-space>

    <!-- Create Modal -->
    <n-modal v-model:show="showCreateModal">
      <n-card
        style="width: 600px"
        title="创建 API Key"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-form ref="createFormRef" :model="createModel">
          <n-form-item label="名称" path="name">
            <n-input v-model:value="createModel.name" placeholder="例如：Billing Service" />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showCreateModal = false">取消</n-button>
            <n-button type="primary" :loading="createLoading" @click="handleCreate">
              创建
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- Result Modal -->
    <n-modal v-model:show="showResultModal" :mask-closable="false">
      <n-card
        style="width: 600px"
        title="API Key 已创建"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-result status="success" title="创建成功" description="请立即复制并保存您的 API Key。出于安全原因，它将不会再次显示。">
          <template #footer>
            <n-space vertical>
              <n-input :value="newKey" readonly type="textarea" autosize />
              <n-space justify="center">
                <n-button type="primary" @click="copyKey">复制</n-button>
                <n-button @click="showResultModal = false">关闭</n-button>
              </n-space>
            </n-space>
          </template>
        </n-result>
      </n-card>
    </n-modal>
  </div>
</template>
