import { ref } from 'vue'

const STORAGE_KEY = 'ai-search-history'

let loaded = false
const history = ref<string[]>([])

export function useSearchHistory() {
  if (!loaded) {
    loadHistory()
    loaded = true
  }

  return {
    history,
    addToHistory,
    clearHistory
  }
}

function loadHistory() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      history.value = JSON.parse(stored)
    }
  } catch (e) {
    console.error('Failed to load search history:', e)
  }
}

function saveHistory() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value))
  } catch (e) {
    console.error('Failed to save search history:', e)
  }
}

export function addToHistory(query: string) {
  if (!query.trim()) return
  const filtered = history.value.filter(q => q !== query)
  history.value = [query, ...filtered].slice(0, 20)
  saveHistory()
}

export function clearHistory() {
  history.value = []
  saveHistory()
}
