import re
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DOMAIN_AUTHORITY = {
    "gov.cn": 1.0,
    "edu.cn": 0.95,
    "gov": 0.95,
    "edu": 0.90,
    "wikipedia.org": 0.90,
    "arxiv.org": 0.88,
    "baike.baidu.com": 0.85,
    "github.com": 0.85,
    "stackoverflow.com": 0.82,
    "medium.com": 0.75,
    "dev.to": 0.70,
    "zhihu.com": 0.72,
    "jianshu.com": 0.62,
    "csdn.net": 0.68,
    "cnblogs.com": 0.65,
    "juejin.cn": 0.68,
    "infoq.cn": 0.75,
    "36kr.com": 0.68,
    "huxiu.com": 0.65,
    "ifeng.com": 0.55,
    "163.com": 0.55,
    "sina.com.cn": 0.55,
    "qq.com": 0.55,
    "sohu.com": 0.53,
    "bbc.com": 0.85,
    "bbc.co.uk": 0.85,
    "nytimes.com": 0.88,
    "reuters.com": 0.90,
    "economist.com": 0.85,
    "nature.com": 0.92,
    "science.org": 0.92,
    "ieee.org": 0.90,
    "acm.org": 0.90,
    "springer.com": 0.85,
    "pubmed.ncbi.nlm.nih.gov": 0.95,
    "who.int": 0.95,
    "un.org": 0.95,
    "worldbank.org": 0.92,
    "imf.org": 0.92,
    "microsoft.com": 0.82,
    "apple.com": 0.82,
    "google.com": 0.80,
    "aws.amazon.com": 0.80,
    "developer.mozilla.org": 0.88,
    "docs.python.org": 0.85,
    "nodejs.org": 0.82,
    "react.dev": 0.82,
    "vuejs.org": 0.80,
    "angular.io": 0.80,
    "pypi.org": 0.78,
    "npmjs.com": 0.78,
    "docker.com": 0.78,
    "kubernetes.io": 0.80,
    "youtube.com": 0.65,
    "bilibili.com": 0.62,
    "douyin.com": 0.50,
    "weixin.qq.com": 0.55,
    "mp.weixin.qq.com": 0.60,
    "toutiao.com": 0.50,
}

DATE_PATTERNS = [
    (re.compile(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日号]?'), 'ymd'),
    (re.compile(r'(\d{1,2})[-/月](\d{1,2})[-/日号]?,?\s*(\d{4})年?'), 'mdy'),
    (re.compile(r'(\w{3,9})\s+(\d{1,2}),?\s*(\d{4})'), 'month_name'),
    (re.compile(r'(\d{1,2})\s+(\w{3,9})\s+(\d{4})'), 'dmy_month'),
    (re.compile(r'(\d{4})年(\d{1,2})月'), 'ym'),
    (re.compile(r'(\d{2})小时前|(\d+)小时前'), 'hours_ago'),
    (re.compile(r'(\d{2})分钟前|(\d+)分钟前'), 'mins_ago'),
    (re.compile(r'(\d{1,2})天前'), 'days_ago'),
    (re.compile(r'昨天'), 'yesterday'),
    (re.compile(r'今天'), 'today'),
]

MONTH_NAMES = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def _get_domain_authority(url: str) -> float:
    if not url:
        return 0.5
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        return 0.5

    best_score = 0.5
    for known_domain, score in DOMAIN_AUTHORITY.items():
        if known_domain in domain:
            if score > best_score:
                best_score = score

    if domain.endswith(".gov") or domain.endswith(".gov.cn"):
        best_score = max(best_score, 0.95)
    elif domain.endswith(".edu") or domain.endswith(".edu.cn") or domain.endswith(".ac.cn"):
        best_score = max(best_score, 0.90)
    elif domain.endswith(".org") or domain.endswith(".org.cn"):
        best_score = max(best_score, 0.75)

    return best_score


def _extract_date(content: str) -> Optional[datetime]:
    if not content:
        return None

    text = content[:500]

    for pattern, ptype in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue

        try:
            if ptype == 'ymd':
                y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 2010 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31:
                    return datetime(y, m, d, tzinfo=timezone.utc)
            elif ptype == 'mdy':
                m, d, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 2010 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31:
                    return datetime(y, m, d, tzinfo=timezone.utc)
            elif ptype == 'month_name':
                month_name = match.group(1).lower()
                d, y = int(match.group(2)), int(match.group(3))
                m = MONTH_NAMES.get(month_name)
                if m and 2010 <= y <= 2030 and 1 <= d <= 31:
                    return datetime(y, m, d, tzinfo=timezone.utc)
            elif ptype == 'dmy_month':
                d, month_name, y = int(match.group(1)), match.group(2).lower(), int(match.group(3))
                m = MONTH_NAMES.get(month_name)
                if m and 2010 <= y <= 2030 and 1 <= d <= 31:
                    return datetime(y, m, d, tzinfo=timezone.utc)
            elif ptype == 'ym':
                y, m = int(match.group(1)), int(match.group(2))
                if 2010 <= y <= 2030 and 1 <= m <= 12:
                    return datetime(y, m, 15, tzinfo=timezone.utc)
            elif ptype == 'hours_ago':
                hours = int(match.group(1) or match.group(2))
                return datetime.now(timezone.utc) - timedelta(hours=hours)
            elif ptype == 'mins_ago':
                mins = int(match.group(1) or match.group(2))
                return datetime.now(timezone.utc) - timedelta(minutes=mins)
            elif ptype == 'days_ago':
                days = int(match.group(1))
                return datetime.now(timezone.utc) - timedelta(days=days)
            elif ptype == 'yesterday':
                return datetime.now(timezone.utc) - timedelta(days=1)
            elif ptype == 'today':
                return datetime.now(timezone.utc)
        except (ValueError, IndexError):
            continue

    return None


def _compute_freshness_score(publish_date: Optional[datetime]) -> float:
    if publish_date is None:
        return 0.5

    now = datetime.now(timezone.utc)
    age = now - publish_date
    hours = age.total_seconds() / 3600

    if hours <= 24:
        return 1.0
    elif hours <= 72:
        return 0.95
    elif hours <= 168:
        return 0.90
    elif hours <= 720:
        return 0.80
    elif hours <= 2160:
        return 0.65
    elif hours <= 8760:
        return 0.45
    else:
        return 0.10


def compute_rank_score(result: Dict, query: Optional[str] = None) -> float:
    url = result.get("url", "")
    content = result.get("content", "")
    title = result.get("title", "")
    original_score = result.get("score") or 0.5

    authority = _get_domain_authority(url)

    publish_date = _extract_date(content)
    freshness = _compute_freshness_score(publish_date)

    q_lower = (query or "").lower()
    title_lower = title.lower()
    keyword_match = 0.5
    if q_lower:
        query_words = [w for w in q_lower.split() if len(w) >= 2]
        if query_words:
            matches = sum(1 for w in query_words if w in title_lower)
            keyword_match = 0.5 + 0.5 * (matches / len(query_words))

    content_len = len(content) if content else 0
    content_richness = min(1.0, content_len / 1500)

    composite = (
        authority * 0.35
        + freshness * 0.25
        + (original_score if original_score is not None else 0.5) * 0.20
        + keyword_match * 0.10
        + content_richness * 0.10
    )

    return round(composite, 4)


def rerank_results(results: List[Dict], query: Optional[str] = None) -> List[Dict]:
    if not results:
        return results

    scored = []
    for r in results:
        score = compute_rank_score(r, query)
        r = dict(r)
        r["rank_score"] = score
        scored.append(r)

    scored.sort(key=lambda x: x["rank_score"], reverse=True)

    logger.info(
        f"[RANK] Reranked {len(scored)} results. "
        f"Top score: {scored[0]['rank_score']:.4f} "
        f"({scored[0].get('title', '')[:50]})"
    )

    return scored