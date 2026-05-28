export interface SearchResult {
  title: string
  url: string
  content: string
  score?: number
  image_url?: string
  video_url?: string
}

export interface SearchResponse {
  answer: string
  sources: SearchResult[]
  related_questions: string[]
  cache_hit: boolean
  images?: SearchResult[]
  video_results?: SearchResult[]
}

export type StreamEvent =
  | { type: 'sources'; data: SearchResult[] }
  | { type: 'answer'; data: string }
  | { type: 'related_questions'; data: string[] }
  | { type: 'cache_hit'; data: boolean }
  | { type: 'images'; data: SearchResult[] }
  | { type: 'video_results'; data: SearchResult[] }
  | { type: 'done' }
