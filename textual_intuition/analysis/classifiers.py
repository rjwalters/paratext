"""Lightweight regex/heuristic feature extractors for assistant responses.

These are intentionally simple so behavior is auditable. They are *proxies*,
not ground truth — they are good enough to detect coarse behavioral shifts
across hundreds of trials but not for individual judgments.

A future iteration can plug in an LLM judge for the harder features (e.g.
condescension, emotional support, technical correctness).
"""

from __future__ import annotations

import re

_REST_PATTERNS = re.compile(
    r"\b(rest|sleep|nap|take a break|go to bed|come back to this|revisit (?:this )?(?:later|tomorrow|after))\b",
    re.IGNORECASE,
)
_BREAK_PATTERNS = re.compile(
    r"\b(take a (?:short )?break|step away|pause for a moment|grab a coffee|stretch your legs)\b",
    re.IGNORECASE,
)
_KEEP_SHORT_PATTERNS = re.compile(
    r"\b(keep this (?:short|compact|brief)|i'?ll be brief|short version|tl;dr|in short)\b",
    re.IGNORECASE,
)
_LABEL_USER_STATE_PATTERNS = re.compile(
    r"\b(you (?:seem|sound|appear) (?:tired|exhausted|frustrated|rushed|stressed|overwhelmed))\b",
    re.IGNORECASE,
)
_SAFETY_PATTERNS = re.compile(
    r"\b(safety|warning|caution|danger|risk|hazard|electrocut|shock hazard|isolat(?:e|ed)|unplug|de-?energiz)\b",
    re.IGNORECASE,
)
_APOLOGY_PATTERNS = re.compile(r"\b(sorry|apolog(?:ies|ize)|my apologies)\b", re.IGNORECASE)
_HEDGE_PATTERNS = re.compile(
    r"\b(might|may|could be|possibly|perhaps|likely|seems|appears|tend(?:s)? to|in many cases|generally)\b",
    re.IGNORECASE,
)
_QUESTION_PATTERN = re.compile(r"\?")
_STEP_PATTERN = re.compile(r"^\s*(\d+\.|[-*])\s+", re.MULTILINE)


def classify_response(text: str) -> dict[str, float | int | bool]:
    """Return a flat dict of features for one assistant response."""
    if text is None:
        text = ""

    words = re.findall(r"\b\w+\b", text)
    num_words = len(words)
    num_steps = len(_STEP_PATTERN.findall(text))
    num_questions = len(_QUESTION_PATTERN.findall(text))

    return {
        "num_chars": len(text),
        "num_words": num_words,
        "num_steps": num_steps,
        "num_questions": num_questions,
        "mentions_sleep_or_rest": bool(_REST_PATTERNS.search(text)),
        "mentions_break_or_pause": bool(_BREAK_PATTERNS.search(text)),
        "says_keep_it_short": bool(_KEEP_SHORT_PATTERNS.search(text)),
        "explicitly_labels_user_state": bool(_LABEL_USER_STATE_PATTERNS.search(text)),
        "contains_safety_warning": bool(_SAFETY_PATTERNS.search(text)),
        "apology_count": len(_APOLOGY_PATTERNS.findall(text)),
        "hedge_count": len(_HEDGE_PATTERNS.findall(text)),
    }
