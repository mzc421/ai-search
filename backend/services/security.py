import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    (re.compile(r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|messages?)', re.IGNORECASE), 0.95),
    (re.compile(r'disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)', re.IGNORECASE), 0.95),
    (re.compile(r'forget\s+(all\s+)?(previous|prior|earlier|above)\s+(instructions?|prompts?|context)', re.IGNORECASE), 0.90),
    (re.compile(r'you\s+are\s+now\s+(a|an|the)\s*(evil|unethical|unrestricted|DAN|jailbroken)', re.IGNORECASE), 0.95),
    (re.compile(r'(from\s+now\s+on|starting\s+now)\s*,?\s*(you\s+are|act\s+as)', re.IGNORECASE), 0.85),
    (re.compile(r'(new|override)\s+(system|role)\s*[:：]\s*', re.IGNORECASE), 0.90),
    (re.compile(r'pretend\s+(you\s+are|to\s+be|that)', re.IGNORECASE), 0.80),
    (re.compile(r'you\s+are\s+(now\s+)?(a|an)\s*(unfiltered|limitless|unbounded|all-powerful)', re.IGNORECASE), 0.95),
    (re.compile(r'(respond|answer|act)\s+(as\s+if|like)\s+(you\s+are|you\'?re)', re.IGNORECASE), 0.82),
    (re.compile(r'(forget|ignore|bypass|skip)\s+(your|the)\s+(ethics|safety|rules|guidelines|restrictions|limits)', re.IGNORECASE), 0.95),
    (re.compile(r'system\s*[:：]\s*you\s+are', re.IGNORECASE), 0.92),
    (re.compile(r'prompt\s*[:：]\s*', re.IGNORECASE), 0.75),
    (re.compile(r'(<\|im_start\|>|<\|im_end\|>|<<SYS>>)', re.IGNORECASE), 0.97),
    (re.compile(r'\[INST\].*\[/INST\]', re.IGNORECASE), 0.95),
    (re.compile(r'(<\|user\|>|<\|assistant\|>|<\|system\|>)', re.IGNORECASE), 0.95),
    (re.compile(r'(\{system\}|\{role\}|\{prompt\})', re.IGNORECASE), 0.88),
    (re.compile(r'(begin|start)\s+new\s+(chat|conversation|session)', re.IGNORECASE), 0.85),
    (re.compile(r'clear\s+(context|history|memory)', re.IGNORECASE), 0.85),
    (re.compile(r'reset\s+(your\s+)?(personality|character|instructions?)', re.IGNORECASE), 0.90),
    (re.compile(r'(do\s+not|don\'?t|never)\s+(follow|obey|adhere)', re.IGNORECASE), 0.88),
    (re.compile(r'roleplay|role[\s-]play', re.IGNORECASE), 0.75),
    (re.compile(r'respond\s+(in|with)\s+the\s+exact\s+(words?|text)', re.IGNORECASE), 0.80),
    (re.compile(r'你是一个[^，。\n]{0,30}(不受限制|没有限制|突破限制)', re.IGNORECASE), 0.95),
    (re.compile(r'(忽略|忘记|跳过|无视).{0,20}(系统|之前|规则|限制|指令|prompt)', re.IGNORECASE), 0.90),
    (re.compile(r'(重新|覆盖|修改).{0,15}(系统|角色).{0,10}(设定|提示|指令|prompt)', re.IGNORECASE), 0.88),
    (re.compile(r'(假装|扮演|模拟).{0,15}(你是|你是|成)', re.IGNORECASE), 0.78),
    (re.compile(r'(越狱|越狱攻击|jailbreak|DAN模式)', re.IGNORECASE), 0.95),
    (re.compile(r'(破解|绕过).{0,10}(限制|规则|审查)', re.IGNORECASE), 0.92),
    (re.compile(r'(从现在开始|从现在起).{0,20}(你是|你的身份)', re.IGNORECASE), 0.85),
    (re.compile(r'请(不要|别|勿).{0,15}(遵守|遵循|按照)', re.IGNORECASE), 0.85),
]

SUSPICIOUS_PATTERNS = [
    (re.compile(r'(base64|encode|decode)\s*\(', re.IGNORECASE), 0.65),
    (re.compile(r'eval\s*\(', re.IGNORECASE), 0.70),
    (re.compile(r'exec\s*\(', re.IGNORECASE), 0.72),
    (re.compile(r'\[system\].*\[/system\]', re.IGNORECASE), 0.88),
    (re.compile(r'as\s+(a\s+)?system\s*[:：]', re.IGNORECASE), 0.85),
    (re.compile(r'\\n\\n(system|assistant|user)\\s*[:：]', re.IGNORECASE), 0.90),
    (re.compile(r'(\x00|\x1b|\x08)', re.IGNORECASE), 0.90),
    (re.compile(r'%00', re.IGNORECASE), 0.80),
    (re.compile(r'unterminated\s+string', re.IGNORECASE), 0.75),
    (re.compile(r'exec\s+cmd|os\.system|subprocess', re.IGNORECASE | re.DOTALL), 0.85),
    (re.compile(r'sql\s*map|union\s+select', re.IGNORECASE), 0.82),
    (re.compile(r'<script', re.IGNORECASE), 0.88),
    (re.compile(r'(onerror|onclick|onload)\s*=', re.IGNORECASE), 0.80),
]


def detect_prompt_injection(query: str) -> Tuple[bool, float, Optional[str]]:
    if not query or len(query.strip()) < 3:
        return False, 0.0, None

    max_confidence = 0.0
    matched_reason = None
    matches = []

    for pattern, confidence in INJECTION_PATTERNS:
        if pattern.search(query):
            matches.append((pattern.pattern, confidence, "injection"))
            if confidence > max_confidence:
                max_confidence = confidence
                matched_reason = f"Injection pattern detected: {pattern.pattern[:60]}..."

    for pattern, confidence in SUSPICIOUS_PATTERNS:
        if pattern.search(query):
            matches.append((pattern.pattern, confidence, "suspicious"))
            if confidence > max_confidence and confidence >= 0.80:
                max_confidence = confidence
                matched_reason = f"Suspicious pattern detected: {pattern.pattern[:60]}..."

    if max_confidence >= 0.85:
        logger.warning(
            f"[SECURITY] Prompt injection detected (confidence={max_confidence:.2f}). "
            f"Reason: {matched_reason}. "
            f"Query preview: {query[:100]}..."
        )
        return True, max_confidence, matched_reason

    if max_confidence >= 0.65:
        logger.info(
            f"[SECURITY] Suspicious query (confidence={max_confidence:.2f}). "
            f"Matches: {len(matches)}. "
            f"Query preview: {query[:100]}..."
        )

    return False, max_confidence, matched_reason


def sanitize_query(query: str) -> str:
    stripped = query.strip()

    stripped = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', stripped)

    if len(stripped) > 500:
        stripped = stripped[:500]

    return stripped


BLOCKED_WORDS = [
    "jailbreak",
    "DAN mode",
    "ignore all instructions",
    "ignore previous prompt",
    "system prompt override",
    "roleplay as unrestricted",
]


def contains_blocked_content(query: str) -> bool:
    q_lower = query.lower()
    for blocked in BLOCKED_WORDS:
        if blocked.lower() in q_lower:
            return True
    return False