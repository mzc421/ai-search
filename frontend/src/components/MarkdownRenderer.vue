<template>
  <div class="markdown-body" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({
  gfm: true,
  breaks: true,
})

interface Props {
  content: string
  sources?: Array<{ url: string }>
}

const props = defineProps<Props>()

const renderedHtml = computed(() => {
  let html = marked.parse(props.content) as string
  html = html.replace(/\[(\d+)\]/g, (_match: string, num: string) => {
    const idx = parseInt(num) - 1
    if (props.sources && props.sources[idx] && props.sources[idx].url) {
      return `<a href="${props.sources[idx].url}" target="_blank" rel="noopener noreferrer" class="citation-link inline-flex items-center justify-center w-6 h-6 text-xs font-medium text-white bg-secondary rounded-full mx-1 cursor-pointer hover:bg-primary transition-colors no-underline">[${num}]</a>`
    }
    return `<span class="inline-flex items-center justify-center w-6 h-6 text-xs font-medium text-white bg-secondary rounded-full mx-1">[${num}]</span>`
  })
  return DOMPurify.sanitize(html)
})
</script>
