<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-4 py-12">
    <div class="max-w-3xl w-full text-center">
      <h1 class="text-5xl font-bold text-primary mb-4">
        AI Search
      </h1>
      <p class="text-lg text-slate-600 mb-12">
        智能搜索引擎，为你带来深度信息分析
      </p>

      <div class="relative mb-8 search-history-wrapper">
        <form @submit.prevent="handleSearch" class="relative">
          <input
            v-model="query"
            ref="searchInputRef"
            type="text"
            placeholder="输入你的问题..."
            class="w-full px-6 py-4 text-lg border-2 border-slate-200 rounded-2xl focus:outline-none focus:border-secondary focus:ring-4 focus:ring-blue-50 transition-all shadow-sm"
            @focus="showHistory = true"
            @keydown.escape="query = ''"
          />
          <button
            type="submit"
            class="absolute right-2 top-1/2 -translate-y-1/2 bg-primary hover:bg-slate-800 text-white px-6 py-2 rounded-xl transition-all shadow-md hover:shadow-lg"
            :disabled="!query.trim() || isLoading"
          >
            <span v-if="!isLoading">搜索</span>
            <span v-else class="animate-pulse">搜索中...</span>
          </button>
        </form>

        <!-- 搜索历史 -->
        <div
          v-if="showHistory && history.length > 0"
          class="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-xl shadow-lg z-10 overflow-hidden"
        >
          <div class="flex items-center justify-between px-4 py-2 bg-slate-50 border-b border-slate-100">
            <span class="text-sm text-slate-500">搜索历史</span>
            <button @click="clearHistory" class="text-xs text-slate-400 hover:text-slate-600">
              清除
            </button>
          </div>
          <div class="max-h-60 overflow-y-auto">
            <button
              v-for="item in history"
              :key="item"
              @click="searchFromHistory(item)"
              class="w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors text-slate-700"
            >
              <span class="text-sm">🕐</span>
              <span class="ml-2">{{ item }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 示例问题 -->
      <div class="flex flex-wrap justify-center gap-3">
        <button
          v-for="example in examples"
          :key="example"
          @click="searchFromHistory(example)"
          class="px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-full hover:border-secondary hover:text-secondary transition-all"
        >
          {{ example }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchHistory, addToHistory, clearHistory } from '@/composables/useSearchHistory'

const router = useRouter()
const { history } = useSearchHistory()

const query = ref('')
const isLoading = ref(false)
const showHistory = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

const examples = [
  '最新的 AI 技术发展',
  '如何学习 Python 编程',
  '今天的天气预报',
  '最新的科技新闻'
]

const handleSearch = async () => {
  if (!query.value.trim()) return

  isLoading.value = true
  addToHistory(query.value)
  showHistory.value = false

  try {
    await router.push({
      path: '/search',
      query: { q: query.value }
    })
  } finally {
    isLoading.value = false
  }
}

const searchFromHistory = (q: string) => {
  query.value = q
  handleSearch()
}

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  const wrapper = document.querySelector('.search-history-wrapper')
  if (wrapper && !wrapper.contains(target)) {
    showHistory.value = false
  }
}

const handleGlobalKeyDown = (e: KeyboardEvent) => {
  if (e.key === '/' && document.activeElement?.tagName !== 'INPUT') {
    e.preventDefault()
    searchInputRef.value?.focus()
  }
}

document.addEventListener('click', handleClickOutside)
document.addEventListener('keydown', handleGlobalKeyDown)

onMounted(() => {
  searchInputRef.value?.focus()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleGlobalKeyDown)
})
</script>
