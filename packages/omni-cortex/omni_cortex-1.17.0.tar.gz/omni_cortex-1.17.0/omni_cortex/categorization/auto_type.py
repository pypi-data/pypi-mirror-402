"""Auto-detect memory type based on content."""

import re
from typing import Optional

# Memory types
MEMORY_TYPES = [
    "warning",
    "tip",
    "config",
    "troubleshooting",
    "code",
    "error",
    "solution",
    "command",
    "concept",
    "decision",
    "general",
]

# Pattern definitions for each type (case-insensitive)
TYPE_PATTERNS: dict[str, list[str]] = {
    "warning": [
        r"\b(warning|caution|don't|dont|avoid|never|careful|danger|risk)\b",
        r"\b(do not|should not|shouldn't|mustn't|must not)\b",
        r"\b(beware|watch out|important note)\b",
    ],
    "tip": [
        r"\b(tip|trick|best practice|recommend|suggestion|pro tip)\b",
        r"\b(you can|try|consider|it's better|better to)\b",
        r"\b(shortcut|hack|optimization|improve)\b",
    ],
    "config": [
        r"\b(config|configuration|setting|setup|environment|env)\b",
        r"\b(\.env|\.yaml|\.json|\.toml|\.ini)\b",
        r"\b(variable|parameter|option|flag)\b",
        r"(API_KEY|DATABASE_URL|SECRET|TOKEN)",
    ],
    "troubleshooting": [
        r"\b(fix|solve|debug|troubleshoot|resolve|workaround)\b",
        r"\b(issue|problem|bug|broken|not working)\b",
        r"\b(symptoms?|cause|root cause)\b",
    ],
    "code": [
        r"```[\w]*\n",  # Code block
        r"\b(function|def|class|const|let|var|import|export)\s+\w+",
        r"\b(async|await|return|yield)\b",
        r"^\s*(public|private|protected)\s+",
    ],
    "error": [
        r"\b(error|exception|failed|failure|crash)\b",
        r"\b(traceback|stack trace|line \d+)\b",
        r"\b(TypeError|ValueError|ImportError|SyntaxError)\b",
        r"\b(500|404|403|401)\s+(error|status)\b",
    ],
    "solution": [
        r"\b(solution|solved|fixed|resolved|works?)\b",
        r"\b(answer|resolution|the fix|working now)\b",
        r"\b(here's how|the way to|correct approach)\b",
    ],
    "command": [
        r"^\s*[$>]\s+\S+",  # Shell prompt
        r"\b(npm|pip|git|docker|kubectl|yarn|pnpm)\s+\w+",
        r"\b(run|install|build|start|test|deploy)\s+",
        r"^(curl|wget|ssh|scp)\s+",
    ],
    "concept": [
        r"\b(is|are|means|defined as|refers to)\b",
        r"\b(concept|definition|explanation|understanding)\b",
        r"\b(basically|essentially|in other words)\b",
    ],
    "decision": [
        r"\b(decided|decision|approach|choice|chose|choosing)\b",
        r"\b(we will|going to|plan to|opted for)\b",
        r"\b(strategy|architecture|design|pattern)\b",
    ],
}

# Compiled patterns (case-insensitive)
_compiled_patterns: dict[str, list[re.Pattern]] = {}


def _get_patterns(mem_type: str) -> list[re.Pattern]:
    """Get compiled patterns for a memory type."""
    if mem_type not in _compiled_patterns:
        patterns = TYPE_PATTERNS.get(mem_type, [])
        _compiled_patterns[mem_type] = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in patterns
        ]
    return _compiled_patterns[mem_type]


def detect_memory_type(content: str, context: Optional[str] = None) -> str:
    """Detect the most likely memory type from content.

    Args:
        content: The memory content
        context: Optional context string

    Returns:
        Memory type string
    """
    if not content:
        return "general"

    # Combine content and context for analysis
    text = content
    if context:
        text = f"{content}\n{context}"

    # Track match scores
    scores: dict[str, int] = {t: 0 for t in MEMORY_TYPES if t != "general"}

    # Check each type's patterns
    for mem_type, patterns in TYPE_PATTERNS.items():
        for pattern in _get_patterns(mem_type):
            matches = pattern.findall(text)
            if matches:
                scores[mem_type] += len(matches)

    # Find the type with highest score
    if scores:
        best_type = max(scores.items(), key=lambda x: x[1])
        if best_type[1] > 0:
            return best_type[0]

    return "general"


def get_type_confidence(content: str, context: Optional[str] = None) -> dict[str, float]:
    """Get confidence scores for each memory type.

    Args:
        content: The memory content
        context: Optional context string

    Returns:
        Dictionary of type -> confidence (0.0 to 1.0)
    """
    if not content:
        return {"general": 1.0}

    text = content
    if context:
        text = f"{content}\n{context}"

    # Track raw scores
    scores: dict[str, int] = {t: 0 for t in MEMORY_TYPES if t != "general"}

    for mem_type, patterns in TYPE_PATTERNS.items():
        for pattern in _get_patterns(mem_type):
            matches = pattern.findall(text)
            scores[mem_type] += len(matches)

    # Normalize to confidence
    total = sum(scores.values())
    if total == 0:
        return {"general": 1.0}

    confidences = {t: s / total for t, s in scores.items() if s > 0}
    if not confidences:
        return {"general": 1.0}

    return confidences
