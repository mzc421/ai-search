<template>
  <div class="min-h-screen bg-background">
    <!-- 顶部搜索栏 -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-20">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <div class="flex items-center gap-4">
          <router-link to="/" class="text-xl font-bold text-primary">
            AI Search
          </router-link>
          <form @submit.prevent="handleSearch" class="flex-1 max-w-2xl">
            <div class="relative">
              <input
                v-model="searchInput"
                ref="searchInputRef"
                type="text"
                class="w-full px-4 py-2 pr-20 border border-slate-300 rounded-xl focus:outline-none focus:border-secondary focus:ring-2 focus:ring-blue-100 truncate"
                @keydown.escape="searchInput = ''"
                :title="searchInput"
              />
              <button
                type="submit"
                class="absolute right-2 top-1/2 -translate-y-1/2 bg-secondary hover:bg-blue-700 text-white px-4 py-1 rounded-lg transition-colors text-sm"
              >
                搜索
              </button>
            </div>
          </form>
          <!-- 复制回答按钮 -->
          <button
            v-if="answer && !isLoading"
            @click="copyAnswer"
            class="flex-shrink-0 px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors flex items-center gap-1"
            :title="copySuccess ? '已复制!' : '复制回答'"
          >
            <svg v-if="!copySuccess" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <svg v-else class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {{ copySuccess ? '已复制!' : '复制' }}
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-6">
      <!-- 查询问题 -->
      <h2 class="text-2xl font-bold text-slate-800 mb-6">
        {{ executedQuery }}
      </h2>

      <!-- 错误提示 -->
      <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-2xl p-6 mb-6">
        <div class="flex items-start gap-3">
          <svg class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="font-semibold text-red-800">搜索出错</h3>
            <p class="text-sm text-red-600 mt-1">{{ errorMessage }}</p>
            <button @click="retrySearch" class="mt-2 px-4 py-1.5 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors">
              重试
            </button>
          </div>
        </div>
      </div>

      <!-- 相关问题 - 顶部展示 -->
      <div v-if="relatedQuestions.length > 0 || isLoading" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <h3 class="font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <svg class="w-5 h-5 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          相关问题
        </h3>
        <!-- 加载中占位 -->
        <div v-if="isLoading && relatedQuestions.length === 0" class="flex flex-wrap gap-2">
          <div class="h-10 w-32 bg-slate-100 rounded-lg animate-pulse"></div>
          <div class="h-10 w-40 bg-slate-100 rounded-lg animate-pulse"></div>
          <div class="h-10 w-28 bg-slate-100 rounded-lg animate-pulse"></div>
        </div>
        <!-- 相关问题按钮 -->
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="question in relatedQuestions"
            :key="question"
            @click="searchRelated(question)"
            class="px-4 py-2 text-sm bg-slate-50 hover:bg-blue-50 hover:text-secondary text-slate-600 rounded-lg border border-slate-200 hover:border-secondary transition-all"
          >
            {{ question }}
          </button>
        </div>
      </div>

      <!-- 图片搜索结果展示 -->
      <div v-if="images.length > 0" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <h3 class="font-semibold text-slate-800 mb-4">搜索到的图片</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <a
            v-for="(img, idx) in images"
            :key="idx"
            :href="img.image_url || img.url"
            target="_blank"
            rel="noopener noreferrer"
            class="block aspect-square overflow-hidden rounded-xl border border-slate-200 hover:border-secondary transition-all bg-slate-50"
          >
            <img
              :src="img.image_url || img.url"
              :alt="img.title"
              class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
              referrerpolicy="no-referrer"
              @error="onImageError"
            />
          </a>
        </div>
      </div>

      <!-- 视频搜索结果展示 -->
      <div v-if="videoResults.length > 0" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <h3 class="font-semibold text-slate-800 mb-4">搜索到的视频</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <a
            v-for="(video, idx) in videoResults"
            :key="idx"
            :href="video.video_url || video.url"
            target="_blank"
            rel="noopener noreferrer"
            class="block p-4 border border-slate-200 rounded-xl hover:border-secondary hover:bg-blue-50/50 transition-all"
          >
            <h4 class="font-medium text-slate-800 mb-2 line-clamp-2">
              {{ video.title }}
            </h4>
            <p class="text-xs text-slate-500 truncate">
              {{ video.url }}
            </p>
          </a>
        </div>
      </div>

      <!-- AI 回答和引用来源 左右布局 -->
      <div class="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">
        <!-- AI 回答 -->
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 min-w-0">
          <div class="flex items-center justify-between mb-5 pb-4 border-b border-slate-100">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <span class="text-white text-sm font-bold">AI</span>
              </div>
              <h3 class="font-semibold text-slate-800 text-lg">智能回答</h3>
            </div>
            <!-- 缓存命中提示 -->
            <span v-if="isCacheHit" class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-emerald-700 bg-emerald-100 rounded-full">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              来自缓存 · 即时响应
            </span>
          </div>

          <!-- 加载中骨架屏 -->
          <div v-if="isLoading && answer === ''" class="animate-pulse">
            <div class="h-4 bg-slate-200 rounded w-3/4 mb-3"></div>
            <div class="h-4 bg-slate-200 rounded w-full mb-3"></div>
            <div class="h-4 bg-slate-200 rounded w-5/6 mb-3"></div>
            <div class="h-4 bg-slate-200 rounded w-2/3"></div>
          </div>
          <!-- 无回答且无加载状态 -->
          <div v-else-if="!isLoading && answer === '' && !errorMessage" class="text-center py-8 text-slate-400">
            <svg class="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <p>等待 AI 回答...</p>
          </div>
          <!-- 回答内容 -->
          <div v-else class="min-w-0">
            <MarkdownRenderer :content="answer" :sources="sources" />
          </div>
        </div>

        <!-- 引用来源 -->
        <div v-if="sources.length > 0" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <h3 class="font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">引用来源</h3>
          <div class="space-y-3">
            <a
              v-for="(source, index) in sources"
              :key="`source-${index}`"
              :href="source.url"
              target="_blank"
              rel="noopener noreferrer"
              class="block p-3 border border-slate-100 rounded-xl hover:border-secondary hover:bg-blue-50/50 transition-all group"
            >
              <div class="flex items-start gap-3">
                <span class="flex-shrink-0 w-6 h-6 bg-secondary text-white rounded-full text-xs flex items-center justify-center font-medium mt-0.5">
                  {{ index + 1 }}
                </span>
                <div class="flex-1 min-w-0">
                  <h4 class="font-medium text-slate-800 group-hover:text-secondary truncate text-sm">
                    {{ source.title }}
                  </h4>
                  <p class="text-xs text-slate-400 truncate mt-0.5">
                    {{ source.url }}
                  </p>
                  <p class="text-xs text-slate-600 mt-2 line-clamp-3 leading-relaxed">
                    {{ source.content }}
                  </p>
                </div>
              </div>
            </a>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import type { SearchResult, StreamEvent } from '@/types'
import { useSearchHistory } from '@/composables/useSearchHistory'

const route = useRoute()
const router = useRouter()
const { addToHistory } = useSearchHistory()

const searchInput = ref('')
const executedQuery = ref('')
const answer = ref('')
const sources = ref<SearchResult[]>([])
const relatedQuestions = ref<string[]>([])
const isLoading = ref(false)
const errorMessage = ref('')
const copySuccess = ref(false)
const isCacheHit = ref(false)
const images = ref<SearchResult[]>([])
const videoResults = ref<SearchResult[]>([])

const searchInputRef = ref<HTMLInputElement | null>(null)

const API_BASE = 'http://127.0.0.1:8000'

let abortController: AbortController | null = null

const performSearch = async (q: string) => {
  if (!q.trim()) return

  abortController?.abort()
  abortController = new AbortController()

  executedQuery.value = q
  answer.value = ''
  sources.value = []
  relatedQuestions.value = []
  images.value = []
  videoResults.value = []
  errorMessage.value = ''
  isLoading.value = true
  copySuccess.value = false
  isCacheHit.value = false

  try {
    const response = await fetch(`${API_BASE}/search/stream?query=${encodeURIComponent(q)}`, {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      },
      signal: abortController.signal
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: 服务暂时不可用，请稍后重试`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('当前浏览器不支持流式响应，请尝试升级浏览器')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        isLoading.value = false
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6)) as StreamEvent
          if (data.type === 'sources') {
            sources.value = data.data
          } else if (data.type === 'answer') {
            answer.value += data.data
          } else if (data.type === 'related_questions') {
            relatedQuestions.value = data.data
          } else if (data.type === 'cache_hit') {
            isCacheHit.value = data.data
          } else if (data.type === 'images') {
            images.value = data.data
          } else if (data.type === 'video_results') {
            videoResults.value = data.data
          } else if (data.type === 'done') {
            isLoading.value = false
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e)
        }
      }
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return
    }
    errorMessage.value = error instanceof Error ? error.message : '搜索失败，请检查网络连接'
    isLoading.value = false
  }
}

const handleSearch = () => {
  if (!searchInput.value.trim()) return
  addToHistory(searchInput.value)
  router.push({
    path: '/search',
    query: { q: searchInput.value }
  })
}

const searchRelated = (q: string) => {
  searchInput.value = q
  handleSearch()
}

const retrySearch = () => {
  if (executedQuery.value) {
    performSearch(executedQuery.value)
  }
}

const copyAnswer = async () => {
  try {
    await navigator.clipboard.writeText(answer.value)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch {
    console.error('复制失败')
  }
}

const onImageError = (e: Event) => {
  const target = e.target as HTMLImageElement
  // 尝试用 url 兜底
  const imgData = images.value.find((img: any) => img.image_url === target.src || img.url === target.src)
  if (imgData && target.src !== imgData.url && imgData.url) {
    target.src = imgData.url
    return
  }
  target.style.display = 'none'
}

watch(() => route.query.q, (newQ) => {
  if (newQ && typeof newQ === 'string' && newQ !== executedQuery.value) {
    searchInput.value = newQ
    performSearch(newQ)
  }
}, { immediate: true })

const handleGlobalKeyDown = (e: KeyboardEvent) => {
  if (e.key === '/' && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
    e.preventDefault()
    searchInputRef.value?.focus()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  abortController?.abort()
  document.removeEventListener('keydown', handleGlobalKeyDown)
})
</script>
