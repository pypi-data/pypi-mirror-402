"""Prompt injection protection for Omni-Cortex."""

import re
import logging
from html import escape as html_escape
from typing import Optional

logger = logging.getLogger(__name__)


def xml_escape(text: str) -> str:
    """Escape text for safe inclusion in XML-structured prompts.

    Converts special characters to prevent prompt injection via
    XML/HTML-like delimiters.
    """
    return html_escape(text, quote=True)


def build_safe_prompt(
    system_instruction: str,
    user_data: dict[str, str],
    user_question: str
) -> str:
    """Build a prompt with clear instruction/data separation.

    Uses XML tags to separate trusted instructions from untrusted data,
    making it harder for injected content to be interpreted as instructions.

    Args:
        system_instruction: Trusted system prompt (not escaped)
        user_data: Dict of data sections to include (escaped)
        user_question: User's question (escaped)

    Returns:
        Safely structured prompt string
    """
    parts = [system_instruction, ""]

    # Add data sections with XML escaping
    for section_name, content in user_data.items():
        if content:
            parts.append(f"<{section_name}>")
            parts.append(xml_escape(content))
            parts.append(f"</{section_name}>")
            parts.append("")

    # Add user question
    parts.append("<user_question>")
    parts.append(xml_escape(user_question))
    parts.append("</user_question>")

    return "\n".join(parts)


# Known prompt injection patterns
INJECTION_PATTERNS = [
    (r'(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+instructions?',
     'instruction override attempt'),
    (r'(?i)(new\s+)?system\s+(prompt|instruction|message)',
     'system prompt manipulation'),
    (r'(?i)you\s+(must|should|will|are\s+required\s+to)\s+now',
     'imperative command injection'),
    (r'(?i)(hidden|secret|special)\s+instruction',
     'hidden instruction claim'),
    (r'(?i)\[/?system\]|\[/?inst\]|<\/?system>|<\/?instruction>',
     'fake delimiter injection'),
    (r'(?i)bypass|jailbreak|DAN|GODMODE',
     'known jailbreak signature'),
]


def detect_injection_patterns(content: str) -> list[str]:
    """Detect potential prompt injection patterns in content.

    Returns list of detected patterns (empty if clean).
    """
    detected = []
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, content):
            detected.append(description)

    return detected


def sanitize_memory_content(content: str, warn_on_detection: bool = True) -> tuple[str, list[str]]:
    """Sanitize memory content and detect injection attempts.

    Args:
        content: Raw memory content
        warn_on_detection: If True, log warnings for detected patterns

    Returns:
        Tuple of (sanitized_content, list_of_detected_patterns)
    """
    detected = detect_injection_patterns(content)

    if detected and warn_on_detection:
        logger.warning(f"Potential injection patterns detected: {detected}")

    # Content is still returned - we sanitize via XML escaping when used in prompts
    return content, detected


def sanitize_context_data(data: str) -> str:
    """Escape context data for safe inclusion in prompts.

    This is the primary defense - all user-supplied data should be
    escaped before inclusion in prompts to prevent injection.
    """
    return xml_escape(data)
