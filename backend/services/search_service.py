import os
import json
import time
import logging
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any, AsyncGenerator
from core.config import settings
from core.cache_manager import CacheManager, CacheEntry, compute_sources_similarity
from services.rank_service import rerank_results

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

SYSTEM_PROMPT = """你是一个专业的AI搜索引擎助手。请基于以下搜索结果回答用户的问题。

要求：
1. 回答要全面、准确、有深度
2. 在回答中引用来源时使用 [1], [2] 这样的格式标注
3. 回答使用 Markdown 格式
4. 如果搜索结果中包含图片，请在回答的合适位置用 Markdown 图片语法 `![描述](图片URL)` 嵌入图片，让图片和文本内容紧密结合
5. 如果搜索结果中包含视频相关内容，在回答中适当提及

搜索结果：
{context}"""

VIDEO_DOMAINS = [
    "youtube.com", "youtu.be", "bilibili.com", "vimeo.com",
    "douyin.com", "ixigua.com", "youku.com", "iqiyi.com",
]

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico']


class SearchService:
    def __init__(self):
        self.tavily_search = TavilySearch(
            max_results=settings.tavily_max_results,
            search_depth=settings.tavily_search_depth,
            include_images=settings.tavily_include_images,
            include_image_descriptions=settings.tavily_include_image_descriptions,
            include_favicon=settings.tavily_include_favicon,
            include_usage=settings.tavily_include_usage,
        )
        self.llm = ChatOpenAI(
            model=settings.deepseek_model_name,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=settings.deepseek_temperature,
            reasoning_effort=settings.deepseek_reasoning_effort,
            streaming=True,
        )
        self.output_parser = StrOutputParser()
        self.cache = CacheManager()
        self._prompt_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        self._answer_chain = self._prompt_template | self.llm | self.output_parser

    async def _do_tavily_search(self, query: str) -> Dict[str, Any]:
        logger.info(f"[TAVILY] Starting search for: {query}")
        try:
            result = await self.tavily_search.ainvoke({"query": query})
            logger.info(f"[TAVILY] Result type: {type(result).__name__}, repr: {repr(result)[:300]}")

            if isinstance(result, dict):
                if "results" in result and isinstance(result["results"], list):
                    logger.info(f"[TAVILY] Got {len(result['results'])} results")
                    return result
                elif "error" in result:
                    err = result["error"]
                    logger.error(f"[TAVILY] API returned error: {err}")
                    return {"results": [], "_error": str(err)}
                else:
                    logger.warning(f"[TAVILY] Unexpected dict format, keys: {list(result.keys())}")
                    return {"results": []}

            if hasattr(result, 'content'):
                content = result.content
            elif isinstance(result, str):
                content = result
            else:
                content = str(result)

            if isinstance(content, dict):
                if "results" in content:
                    return content
                return {"results": []}

            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and "results" in parsed:
                        return parsed
                    return {"results": []}
                except json.JSONDecodeError:
                    return {"results": []}

            return {"results": []}

        except Exception as e:
            logger.error(f"[TAVILY] Search exception: {type(e).__name__}: {e}", exc_info=True)
            return {"results": [], "_error": str(e)}

    def _normalize_results(self, raw_results: List[Dict], raw_response: Dict = None) -> List[Dict]:
        normalized = []
        for i, r in enumerate(raw_results):
            image_url = (
                r.get("image_url") or r.get("image") or r.get("img_src") or ""
            )
            if not image_url and "url" in r:
                url_lower = r.get("url", "").lower()
                if any(ext in url_lower for ext in IMAGE_EXTENSIONS):
                    image_url = r["url"]

            video_url = r.get("video_url") or r.get("video") or ""

            normalized.append({
                "title": r.get("title", f"Source {i+1}"),
                "url": r.get("url", ""),
                "content": r.get("content", r.get("raw_content", "")),
                "score": r.get("score"),
                "image_url": image_url,
                "video_url": video_url,
            })

        if raw_response and "images" in raw_response:
            raw_images = raw_response.get("images", [])
            if isinstance(raw_images, list):
                for img_url in raw_images:
                    if isinstance(img_url, str) and img_url:
                        normalized.append({
                            "title": f"图片 {len(normalized) + 1}",
                            "url": img_url,
                            "content": "",
                            "score": 0.6,
                            "image_url": img_url,
                            "video_url": "",
                        })

        return normalized

    def _extract_images(self, sources: List[Dict]) -> List[Dict]:
        images = [r for r in sources if r.get("image_url")]
        if images:
            logger.info(f"[SEARCH] Extracted {len(images)} images from results")
        return images

    def _extract_videos(self, sources: List[Dict]) -> List[Dict]:
        videos = [
            r for r in sources
            if r.get("video_url") or any(
                domain in r.get("url", "").lower() for domain in VIDEO_DOMAINS
            )
        ]
        if videos:
            logger.info(f"[SEARCH] Identified {len(videos)} video results")
        return videos

    async def _do_search_pipeline(self, query: str) -> Dict[str, Any]:
        raw_result = await self._do_tavily_search(query)
        results = raw_result.get("results", [])
        normalized = self._normalize_results(results, raw_result)
        reranked = rerank_results(normalized, query)
        formatted_context = self._format_search_results(reranked)

        answer = await self._answer_chain.ainvoke({
            "context": formatted_context,
            "query": query
        })

        related_questions = await self._generate_related_questions(query, answer)

        images = self._extract_images(reranked)
        video_results = self._extract_videos(reranked)

        return {
            "answer": answer,
            "sources": reranked,
            "related_questions": related_questions,
            "images": images,
            "video_results": video_results,
        }

    async def search_stream(self, query: str) -> AsyncGenerator[str, None]:
        cached = self.cache.get(query)

        if cached is not None:
            new_result = await self._do_tavily_search(query)
            new_normalized = self._normalize_results(new_result.get("results", []), new_result)
            similarity = compute_sources_similarity(cached.sources, new_normalized)

            if similarity >= settings.sim_threshold:
                logger.info(f"[CACHE] Serving cached answer (similarity={similarity:.2f})")
                yield f"data: {json.dumps({'type': 'sources', 'data': cached.sources}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'answer', 'data': cached.answer}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'related_questions', 'data': cached.related_questions}, ensure_ascii=False)}\n\n"

                images = self._extract_images(cached.sources)
                if images:
                    yield f"data: {json.dumps({'type': 'images', 'data': images}, ensure_ascii=False)}\n\n"
                video_results = self._extract_videos(cached.sources)
                if video_results:
                    yield f"data: {json.dumps({'type': 'video_results', 'data': video_results}, ensure_ascii=False)}\n\n"

                yield f"data: {json.dumps({'type': 'cache_hit', 'data': True}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                return
            else:
                logger.info(f"[CACHE] Similarity too low ({similarity:.2f}), regenerating")

        raw_result = await self._do_tavily_search(query)
        results = raw_result.get("results", [])
        normalized = self._normalize_results(results, raw_result)
        reranked = rerank_results(normalized, query)
        logger.info(f"[STREAM] Sending sources event with {len(reranked)} results")
        yield f"data: {json.dumps({'type': 'sources', 'data': reranked}, ensure_ascii=False)}\n\n"

        images = self._extract_images(reranked)
        if images:
            yield f"data: {json.dumps({'type': 'images', 'data': images}, ensure_ascii=False)}\n\n"
            logger.info(f"[STREAM] Sent {len(images)} images")

        video_results = self._extract_videos(reranked)
        if video_results:
            yield f"data: {json.dumps({'type': 'video_results', 'data': video_results}, ensure_ascii=False)}\n\n"
            logger.info(f"[STREAM] Sent {len(video_results)} video results")

        formatted_context = self._format_search_results(reranked)

        answer_parts: List[str] = []
        async for chunk in self._answer_chain.astream({
            "context": formatted_context,
            "query": query
        }):
            answer_parts.append(chunk)
            yield f"data: {json.dumps({'type': 'answer', 'data': chunk}, ensure_ascii=False)}\n\n"

        full_answer = "".join(answer_parts)

        related_questions = await self._generate_related_questions(query, full_answer)
        yield f"data: {json.dumps({'type': 'related_questions', 'data': related_questions}, ensure_ascii=False)}\n\n"

        query_hash = self.cache._compute_hash(query)
        cache_entry = CacheEntry(
            query_hash=query_hash,
            query_text=query,
            sources=reranked,
            answer=full_answer,
            related_questions=related_questions,
            created_at=time.time(),
            updated_at=time.time(),
        )
        self.cache.put(cache_entry)
        self.cache.enforce_max_entries(500)

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    async def search(self, query: str) -> Dict[str, Any]:
        cached = self.cache.get(query)
        if cached is not None:
            new_result = await self._do_tavily_search(query)
            new_sources = self._normalize_results(new_result.get("results", []), new_result)
            similarity = compute_sources_similarity(cached.sources, new_sources)

            if similarity >= settings.sim_threshold:
                logger.info(f"[CACHE] Serving cached answer (similarity={similarity:.2f})")
                return {
                    "answer": cached.answer,
                    "sources": cached.sources,
                    "related_questions": cached.related_questions,
                    "images": self._extract_images(cached.sources),
                    "video_results": self._extract_videos(cached.sources),
                    "cache_hit": True,
                }
            else:
                logger.info(f"[CACHE] Similarity too low ({similarity:.2f}), regenerating")

        result = await self._do_search_pipeline(query)
        query_hash = self.cache._compute_hash(query)
        cache_entry = CacheEntry(
            query_hash=query_hash,
            query_text=query,
            sources=result["sources"],
            answer=result["answer"],
            related_questions=result["related_questions"],
            created_at=time.time(),
            updated_at=time.time(),
        )
        self.cache.put(cache_entry)
        self.cache.enforce_max_entries(500)
        result["cache_hit"] = False
        return result

    def _format_search_results(self, results: List[Dict]) -> str:
        if not results:
            return "(暂无搜索结果)"
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"[{i}] {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"内容: {result.get('content', 'No content')}\n"
            )
        return "\n".join(formatted)

    async def _generate_related_questions(self, query: str, answer: str) -> List[str]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "基于用户的问题和AI的回答，生成 3-5 个相关的后续问题供用户继续探索。每个问题单独一行。"),
            ("human", "用户问题: {query}\n\nAI回答: {answer}")
        ])

        chain = prompt | self.llm | self.output_parser
        result = await chain.ainvoke({"query": query, "answer": answer})

        questions = [q.strip() for q in result.split("\n") if q.strip()]
        return questions[:5]
