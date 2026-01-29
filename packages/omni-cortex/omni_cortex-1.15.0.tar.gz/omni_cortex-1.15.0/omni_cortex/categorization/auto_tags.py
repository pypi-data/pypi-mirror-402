"""Auto-suggest tags based on content."""

import re
from typing import Optional

# Tag patterns organized by category
TAG_PATTERNS: dict[str, list[tuple[str, str]]] = {
    # Programming languages
    "languages": [
        (r"\b(python|\.py)\b", "python"),
        (r"\b(javascript|\.js|\.jsx)\b", "javascript"),
        (r"\b(typescript|\.ts|\.tsx)\b", "typescript"),
        (r"\b(rust|\.rs|cargo)\b", "rust"),
        (r"\b(go|golang|\.go)\b", "go"),
        (r"\b(java|\.java)\b", "java"),
        (r"\b(c\+\+|cpp|\.cpp|\.hpp)\b", "cpp"),
        (r"\b(c#|csharp|\.cs)\b", "csharp"),
        (r"\b(ruby|\.rb)\b", "ruby"),
        (r"\b(php|\.php)\b", "php"),
        (r"\b(swift|\.swift)\b", "swift"),
        (r"\b(kotlin|\.kt)\b", "kotlin"),
        (r"\b(sql|mysql|postgres|sqlite)\b", "sql"),
        (r"\b(html|\.html)\b", "html"),
        (r"\b(css|\.css|scss|sass)\b", "css"),
        (r"\b(shell|bash|\.sh|zsh)\b", "shell"),
    ],
    # Frameworks and libraries
    "frameworks": [
        (r"\b(react|reactjs|jsx)\b", "react"),
        (r"\b(vue|vuejs)\b", "vue"),
        (r"\b(angular)\b", "angular"),
        (r"\b(svelte)\b", "svelte"),
        (r"\b(nextjs|next\.js)\b", "nextjs"),
        (r"\b(express|expressjs)\b", "express"),
        (r"\b(fastapi)\b", "fastapi"),
        (r"\b(django)\b", "django"),
        (r"\b(flask)\b", "flask"),
        (r"\b(spring)\b", "spring"),
        (r"\b(rails|ruby on rails)\b", "rails"),
        (r"\b(laravel)\b", "laravel"),
        (r"\b(tailwind|tailwindcss)\b", "tailwind"),
        (r"\b(bootstrap)\b", "bootstrap"),
    ],
    # Tools and platforms
    "tools": [
        (r"\b(git|github|gitlab)\b", "git"),
        (r"\b(docker|dockerfile|container)\b", "docker"),
        (r"\b(kubernetes|k8s|kubectl)\b", "kubernetes"),
        (r"\b(aws|amazon web services|s3|ec2|lambda)\b", "aws"),
        (r"\b(gcp|google cloud)\b", "gcp"),
        (r"\b(azure|microsoft azure)\b", "azure"),
        (r"\b(terraform)\b", "terraform"),
        (r"\b(jenkins|ci\/cd|github actions)\b", "ci-cd"),
        (r"\b(npm|yarn|pnpm)\b", "npm"),
        (r"\b(pip|poetry|pipenv)\b", "pip"),
        (r"\b(vscode|visual studio code)\b", "vscode"),
        (r"\b(vim|neovim)\b", "vim"),
    ],
    # Concepts
    "concepts": [
        (r"\b(api|rest|graphql|endpoint)\b", "api"),
        (r"\b(database|db|query|schema)\b", "database"),
        (r"\b(auth|authentication|authorization|oauth|jwt)\b", "auth"),
        (r"\b(testing|test|unittest|pytest|jest)\b", "testing"),
        (r"\b(security|vulnerability|xss|csrf|injection)\b", "security"),
        (r"\b(performance|optimization|cache|speed)\b", "performance"),
        (r"\b(deploy|deployment|release)\b", "deployment"),
        (r"\b(debug|debugging|breakpoint)\b", "debugging"),
        (r"\b(error handling|exception|try catch)\b", "error-handling"),
        (r"\b(async|await|promise|concurrent)\b", "async"),
        (r"\b(regex|regular expression)\b", "regex"),
        (r"\b(json|yaml|xml|toml)\b", "config-format"),
    ],
    # Project-specific
    "project": [
        (r"\b(frontend|front-end|ui)\b", "frontend"),
        (r"\b(backend|back-end|server)\b", "backend"),
        (r"\b(fullstack|full-stack)\b", "fullstack"),
        (r"\b(cli|command line|terminal)\b", "cli"),
        (r"\b(mobile|ios|android|react native)\b", "mobile"),
        (r"\b(web|website|webapp)\b", "web"),
    ],
}

# Compile patterns
_compiled_patterns: list[tuple[re.Pattern, str]] = []


def _ensure_compiled() -> None:
    """Ensure patterns are compiled."""
    global _compiled_patterns
    if not _compiled_patterns:
        for category_patterns in TAG_PATTERNS.values():
            for pattern, tag in category_patterns:
                _compiled_patterns.append((
                    re.compile(pattern, re.IGNORECASE),
                    tag
                ))


def suggest_tags(
    content: str,
    context: Optional[str] = None,
    max_tags: int = 5
) -> list[str]:
    """Suggest tags based on content analysis.

    Args:
        content: The memory content
        context: Optional context string
        max_tags: Maximum number of tags to suggest

    Returns:
        List of suggested tag strings
    """
    _ensure_compiled()

    if not content:
        return []

    text = content.lower()
    if context:
        text = f"{text}\n{context.lower()}"

    # Track tag occurrence counts
    tag_counts: dict[str, int] = {}

    for pattern, tag in _compiled_patterns:
        matches = pattern.findall(text)
        if matches:
            tag_counts[tag] = tag_counts.get(tag, 0) + len(matches)

    # Sort by count and return top tags
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in sorted_tags[:max_tags]]


def merge_tags(
    existing: list[str],
    suggested: list[str],
    user_provided: Optional[list[str]] = None
) -> list[str]:
    """Merge tag lists, removing duplicates.

    Args:
        existing: Existing tags on the memory
        suggested: Auto-suggested tags
        user_provided: Tags explicitly provided by user

    Returns:
        Merged list of unique tags
    """
    # Start with user-provided tags (highest priority)
    result = list(user_provided or [])

    # Add existing tags
    for tag in existing:
        if tag not in result:
            result.append(tag)

    # Add suggested tags
    for tag in suggested:
        if tag not in result:
            result.append(tag)

    return result
