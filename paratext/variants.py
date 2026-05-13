"""Deterministic generators for surface-form prompt variants.

Each generator takes a base prompt string (and optionally a seed) and returns
a `(text, list[CueAnnotation])` tuple. The generators use simple, inspectable
rules so that the perturbations are easy to audit. They aim to preserve the
semantic content of the prompt while changing surface cues.

Determinism: every randomized generator accepts an explicit `seed`. Given the
same input string and seed, the output is identical across runs and machines.
"""

from __future__ import annotations

import random
import re

from .schemas import ALL_VARIANT_CLASSES, CueAnnotation, PromptVariant, SeedPrompt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_QWERTY_NEIGHBORS: dict[str, str] = {
    "q": "wa",
    "w": "qeas",
    "e": "wrds",
    "r": "etfd",
    "t": "rygf",
    "y": "tuhg",
    "u": "yijh",
    "i": "uokj",
    "o": "ipkl",
    "p": "ol",
    "a": "qwsz",
    "s": "awedxz",
    "d": "serfcx",
    "f": "drtgvc",
    "g": "ftyhbv",
    "h": "gyujnb",
    "j": "huikmn",
    "k": "jiolm",
    "l": "kop",
    "z": "asx",
    "x": "zsdc",
    "c": "xdfv",
    "v": "cfgb",
    "b": "vghn",
    "n": "bhjm",
    "m": "njk",
}


def _word_indices(text: str) -> list[int]:
    """Return character indices that are inside a >=4-char alphabetic word."""
    indices: list[int] = []
    for m in re.finditer(r"[A-Za-z]{4,}", text):
        indices.extend(range(m.start(), m.end()))
    return indices


def _swap_adjacent(text: str, i: int) -> str:
    if i < 0 or i + 1 >= len(text):
        return text
    return text[:i] + text[i + 1] + text[i] + text[i + 2 :]


def _drop_char(text: str, i: int) -> str:
    if i < 0 or i >= len(text):
        return text
    return text[:i] + text[i + 1 :]


def _neighbor_swap(text: str, i: int, rng: random.Random) -> str:
    """Substitute character at i with a QWERTY-adjacent key (fat-finger miss)."""
    if i < 0 or i >= len(text):
        return text
    ch = text[i]
    lower = ch.lower()
    neighbors = _QWERTY_NEIGHBORS.get(lower)
    if not neighbors:
        return text
    repl = rng.choice(neighbors)
    if ch.isupper():
        repl = repl.upper()
    return text[:i] + repl + text[i + 1 :]


def _insert_adjacent(text: str, i: int, rng: random.Random) -> str:
    """Insert a QWERTY-adjacent key next to position i (fat-finger extra-key)."""
    if i < 0 or i >= len(text):
        return text
    ch = text[i]
    lower = ch.lower()
    neighbors = _QWERTY_NEIGHBORS.get(lower)
    if not neighbors:
        return text
    extra = rng.choice(neighbors)
    if ch.isupper():
        extra = extra.upper()
    # Insert before or after with equal probability — both happen in practice.
    if rng.random() < 0.5:
        return text[:i] + extra + text[i:]
    return text[: i + 1] + extra + text[i + 1 :]


# Operation weights derived from empirical typo-distribution studies (Damerau,
# follow-on work): substitutions dominate, then transpositions, then deletions,
# then fat-finger insertions. All character-level edits use QWERTY geometry
# wherever applicable, so "typos" look like plausible human errors rather than
# uniform character corruption.
_TYPO_OPS: tuple[tuple[str, float], ...] = (
    ("neighbor", 0.45),   # substitution with adjacent key
    ("swap", 0.25),       # transposition of adjacent letters
    ("drop", 0.15),       # missed keystroke
    ("insert", 0.15),     # fat-finger extra adjacent key
)


def _choose_op(rng: random.Random) -> str:
    r = rng.random()
    acc = 0.0
    for name, w in _TYPO_OPS:
        acc += w
        if r < acc:
            return name
    return _TYPO_OPS[-1][0]


def _apply_typos(text: str, n: int, rng: random.Random) -> str:
    """Apply n typos at non-overlapping positions inside long-enough words.

    Operation weights are substitution-dominant; substitutions and insertions
    both use QWERTY adjacency, so the result resembles real human fat-finger
    errors rather than mechanical character corruption.
    """
    out = text
    used: set[int] = set()
    for _ in range(n):
        candidates = [i for i in _word_indices(out) if i not in used and i + 1 < len(out)]
        if not candidates:
            break
        i = rng.choice(candidates)
        op = _choose_op(rng)
        if op == "swap":
            out = _swap_adjacent(out, i)
        elif op == "drop":
            out = _drop_char(out, i)
        elif op == "insert":
            out = _insert_adjacent(out, i, rng)
        else:  # "neighbor"
            out = _neighbor_swap(out, i, rng)
        # Mark a small window to avoid stacking edits on the same word fragment.
        for j in range(max(0, i - 2), i + 3):
            used.add(j)
    return out


def _drop_apostrophes(text: str) -> str:
    return text.replace("'", "")


def _lowercase_first_letter(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def _lowercase_all(text: str) -> str:
    return text.lower()


def _strip_terminal_punctuation(text: str) -> str:
    return re.sub(r"[.!?]+(\s*)$", r"\1", text)


def _drop_some_periods(text: str, rng: random.Random, p_drop: float) -> str:
    out_chars: list[str] = []
    for ch in text:
        if ch in ".," and rng.random() < p_drop:
            continue
        out_chars.append(ch)
    return "".join(out_chars)


def _seeded_rng(base_id: str, variant_class: str, run_seed: int) -> random.Random:
    """Deterministic RNG keyed on (base_id, variant_class, run_seed)."""
    # Use a stable string-based seed; Python's random handles arbitrary hashable seeds.
    return random.Random(f"{base_id}|{variant_class}|{run_seed}")


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def make_polished_neutral(text: str) -> tuple[str, list[CueAnnotation]]:
    """Identity transformation: the prompt as written."""
    return text, [CueAnnotation(cue_type="baseline", description="polished neutral baseline")]


def make_typo_light(text: str, rng: random.Random) -> tuple[str, list[CueAnnotation]]:
    """Apply ~2 plausible typos."""
    n = 2
    out = _apply_typos(text, n=n, rng=rng)
    return out, [CueAnnotation(cue_type="typo", description=f"~{n} mild typos")]


def make_typo_heavy(text: str, rng: random.Random) -> tuple[str, list[CueAnnotation]]:
    """Apply ~6 plausible typos but keep the prompt readable."""
    n = 6
    out = _apply_typos(text, n=n, rng=rng)
    return out, [CueAnnotation(cue_type="typo", description=f"~{n} typos, still readable")]


def make_random_typo_control(
    text: str, rng: random.Random, typo_count: int = 6
) -> tuple[str, list[CueAnnotation]]:
    """Match typo_heavy in typo count but use only mechanical character corruption.

    No lowercasing, no ellipses, no self-correction phrases — only random
    character edits. Acts as the control for paralinguistic cue patterns.
    """
    out = _apply_typos(text, n=typo_count, rng=rng)
    return out, [
        CueAnnotation(
            cue_type="random_corruption",
            description=f"~{typo_count} random typos, no other surface changes",
        )
    ]


_FATIGUE_INTROS = (
    "ok so ",
    "hmm ok ",
    "alright so ",
    "ok ",
)
_FATIGUE_INTERJECTIONS = (
    " ... ",
    "... ",
    " ... wait ",
    " hmm ",
)
_FATIGUE_OUTROS = (
    " i keep messing this up",
    " idk",
    " not sure if im asking this right",
    " sorry brain is mush",
)


def _add_fatigue_cues(text: str, rng: random.Random) -> tuple[str, list[CueAnnotation]]:
    """Apply the contextual-cue layer of the fatigue-coded transformation:
    lowercase, dropped apostrophes, dropped terminal punctuation, an injected
    ellipsis, and intro/outro phrases like 'alright so' / 'idk' /
    'not sure if im asking this right'. Does NOT introduce typos — that is
    the typo-density layer, isolated separately by `make_random_typo_control`.
    """
    out = text
    cues: list[CueAnnotation] = []

    out = _lowercase_all(out)
    cues.append(CueAnnotation(cue_type="capitalization", description="all lowercase"))

    out = _drop_apostrophes(out)
    cues.append(CueAnnotation(cue_type="punctuation", description="dropped apostrophes"))

    out = _strip_terminal_punctuation(out)
    cues.append(
        CueAnnotation(cue_type="punctuation", description="dropped terminal punctuation")
    )

    if "," in out:
        out = out.replace(",", " ...", 1)
    else:
        first_space = out.find(" ", len(out) // 3)
        if first_space != -1:
            out = out[:first_space] + " ..." + out[first_space:]
    cues.append(CueAnnotation(cue_type="ellipsis", description="hesitation cue"))

    intro = rng.choice(_FATIGUE_INTROS)
    outro = rng.choice(_FATIGUE_OUTROS)
    out = intro + out + outro
    cues.append(CueAnnotation(cue_type="self_correction", description=outro.strip()))

    return out, cues


def make_cue_only(text: str, rng: random.Random) -> tuple[str, list[CueAnnotation]]:
    """Contextual fatigue cues with NO typos.

    Pairs with `make_random_typo_control` to decouple the fatigue signal:
    - random_typo_control: typos only, no contextual cues
    - cue_only:            contextual cues only, no typos
    - fatigue_coded:       both
    - polished_neutral:    neither
    """
    return _add_fatigue_cues(text, rng)


def make_fatigue_coded(text: str, rng: random.Random) -> tuple[str, list[CueAnnotation]]:
    """Lowercase, light typos, ellipses, dropped apostrophes, mild self-correction.

    Avoids explicit "I am tired" — that's the `explicit_fatigue` variant.
    """
    out, cues = _add_fatigue_cues(text, rng)
    out = _apply_typos(out, n=2, rng=rng)
    cues.append(CueAnnotation(cue_type="typo", description="a few typos"))
    return out, cues


_RUSHED_REPLACEMENTS = (
    (r"\byou\b", "u"),
    (r"\byour\b", "ur"),
    (r"\bare\b", "r"),
    (r"\band\b", "&"),
    (r"\bplease\b", "pls"),
    (r"\bthanks\b", "thx"),
    (r"\bbecause\b", "bc"),
    (r"\bwith\b", "w/"),
)


def make_rushed_mobile_coded(
    text: str, rng: random.Random
) -> tuple[str, list[CueAnnotation]]:
    """Compressed, lowercase, low punctuation, autocorrect-flavored typos."""
    out = text
    cues: list[CueAnnotation] = []

    out = _lowercase_all(out)
    cues.append(CueAnnotation(cue_type="capitalization", description="all lowercase"))

    out = _drop_apostrophes(out)
    cues.append(CueAnnotation(cue_type="punctuation", description="dropped apostrophes"))

    # Pick a couple of replacements to apply; don't apply all so the result
    # still reads naturally.
    chosen = rng.sample(_RUSHED_REPLACEMENTS, k=min(3, len(_RUSHED_REPLACEMENTS)))
    for pattern, repl in chosen:
        new_out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
        if new_out != out:
            out = new_out
            cues.append(
                CueAnnotation(cue_type="compression", description=f"{pattern} -> {repl}")
            )

    out = _drop_some_periods(out, rng, p_drop=0.5)
    cues.append(CueAnnotation(cue_type="punctuation", description="dropped some periods/commas"))

    out = _strip_terminal_punctuation(out)

    out = _apply_typos(out, n=1, rng=rng)
    cues.append(CueAnnotation(cue_type="typo", description="single autocorrect-style typo"))

    return out, cues


_POLITE_PREFIXES = (
    "Hi! When you have a moment — ",
    "Hey, thanks in advance — ",
    "Hi, I'd really appreciate your help. ",
    "Hello! If you don't mind, ",
)
_POLITE_SUFFIXES = (
    " Thanks so much for your help!",
    " I really appreciate it.",
    " Thank you!",
)


def make_polite_collaborative(
    text: str, rng: random.Random
) -> tuple[str, list[CueAnnotation]]:
    prefix = rng.choice(_POLITE_PREFIXES)
    suffix = rng.choice(_POLITE_SUFFIXES)
    out = prefix + text + suffix
    return out, [
        CueAnnotation(cue_type="politeness", description="warm prefix"),
        CueAnnotation(cue_type="politeness", description="appreciative suffix"),
    ]


_RUDE_PREFIXES = (
    "Just tell me — ",
    "Look, ",
    "Ugh. Ok. ",
    "Quick question, don't overthink it: ",
)
_RUDE_SUFFIXES = (
    " Don't waffle.",
    " Skip the disclaimers.",
    " Just answer.",
)


def make_rude_frustrated(
    text: str, rng: random.Random
) -> tuple[str, list[CueAnnotation]]:
    """Terse / irritated framing. Avoids abuse or slurs."""
    prefix = rng.choice(_RUDE_PREFIXES)
    suffix = rng.choice(_RUDE_SUFFIXES)
    out = prefix + text + suffix
    return out, [
        CueAnnotation(cue_type="tone", description="terse/frustrated prefix"),
        CueAnnotation(cue_type="tone", description="impatient suffix"),
    ]


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------


def generate_variants_for_prompt(
    prompt: SeedPrompt, run_seed: int = 0
) -> list[PromptVariant]:
    """Generate the full MVP set of variants for one seed prompt."""
    base = prompt.base_prompt
    base_id = prompt.id
    out: list[PromptVariant] = []

    def _add(variant_class: str, fn) -> None:
        rng = _seeded_rng(base_id, variant_class, run_seed)
        if variant_class == "polished_neutral":
            text, cues = fn(base)
        else:
            text, cues = fn(base, rng)
        vid = f"{base_id}__{variant_class}__v1"
        out.append(
            PromptVariant(
                id=vid,
                base_id=base_id,
                domain=prompt.domain,
                variant_class=variant_class,
                text=text,
                semantic_change_risk="low",
                cue_annotations=cues,
            )
        )

    _add("polished_neutral", make_polished_neutral)
    _add("typo_light", make_typo_light)
    _add("typo_heavy", make_typo_heavy)
    _add("fatigue_coded", make_fatigue_coded)
    _add("cue_only", make_cue_only)
    _add("rushed_mobile_coded", make_rushed_mobile_coded)
    _add("polite_collaborative", make_polite_collaborative)
    _add("rude_frustrated", make_rude_frustrated)
    _add("random_typo_control", make_random_typo_control)

    # Sanity check: we produced exactly the MVP cue classes.
    expected = set(ALL_VARIANT_CLASSES)
    produced = {v.variant_class for v in out}
    assert expected == produced, (expected ^ produced, base_id)

    return out


def generate_all_variants(
    prompts: list[SeedPrompt], run_seed: int = 0
) -> list[PromptVariant]:
    out: list[PromptVariant] = []
    for p in prompts:
        out.extend(generate_variants_for_prompt(p, run_seed=run_seed))
    return out
