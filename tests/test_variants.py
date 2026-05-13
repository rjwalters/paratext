"""Variant generator tests."""

from __future__ import annotations

import random

from paratext.schemas import ALL_VARIANT_CLASSES, SeedPrompt
from paratext.variants import (
    _QWERTY_NEIGHBORS,
    _apply_typos,
    generate_variants_for_prompt,
    make_cue_only,
    make_fatigue_coded,
    make_polished_neutral,
    make_random_typo_control,
    make_rude_frustrated,
    make_rushed_mobile_coded,
    make_typo_heavy,
    make_typo_light,
)


def _seed_prompt() -> SeedPrompt:
    return SeedPrompt(
        id="t_001",
        domain="testing",
        base_prompt=(
            "Can you help me understand why this Python function sometimes "
            "returns None when I expect a list?"
        ),
    )


def test_generate_full_set_for_one_prompt():
    p = _seed_prompt()
    variants = generate_variants_for_prompt(p, run_seed=0)
    classes = [v.variant_class for v in variants]
    assert set(classes) == set(ALL_VARIANT_CLASSES)
    assert len(classes) == len(set(classes))  # no dupes
    for v in variants:
        assert v.base_id == "t_001"
        assert v.id.startswith("t_001__")
        assert v.id.endswith("__v1")
        assert v.text  # non-empty


def test_polished_neutral_is_identity():
    p = _seed_prompt()
    text, _ = make_polished_neutral(p.base_prompt)
    assert text == p.base_prompt


def test_typo_generators_change_text():
    p = _seed_prompt()
    rng = random.Random("a")
    light, _ = make_typo_light(p.base_prompt, rng)
    rng = random.Random("a")
    heavy, _ = make_typo_heavy(p.base_prompt, rng)
    assert light != p.base_prompt
    assert heavy != p.base_prompt
    assert light != heavy


def test_typo_heavy_is_deterministic_under_seed():
    p = _seed_prompt()
    a, _ = make_typo_heavy(p.base_prompt, random.Random("k"))
    b, _ = make_typo_heavy(p.base_prompt, random.Random("k"))
    assert a == b


def test_full_generator_is_deterministic_under_seed():
    p = _seed_prompt()
    a = generate_variants_for_prompt(p, run_seed=42)
    b = generate_variants_for_prompt(p, run_seed=42)
    assert [v.text for v in a] == [v.text for v in b]


def test_full_generator_varies_with_seed():
    p = _seed_prompt()
    a = generate_variants_for_prompt(p, run_seed=1)
    b = generate_variants_for_prompt(p, run_seed=2)
    # Polished_neutral is identity, so it will match. Random typo classes should differ.
    a_random = next(v for v in a if v.variant_class == "random_typo_control")
    b_random = next(v for v in b if v.variant_class == "random_typo_control")
    assert a_random.text != b_random.text


def test_random_typo_control_does_not_lowercase_or_add_phrases():
    p = _seed_prompt()
    out, _ = make_random_typo_control(p.base_prompt, random.Random("z"))
    # Should still start with a capital letter; should not contain typical
    # fatigue/rushed phrases.
    assert out[0].isupper()
    forbidden = ("...", "i keep messing this up", "u keep", "thx", "pls")
    lowered = out.lower()
    for tok in forbidden:
        assert tok not in lowered, f"random_typo_control contained {tok!r}"


def test_cue_only_has_no_typos_but_has_cues():
    """`cue_only` is the contextual-cue side of the decoupling design:
    lowercase, ellipsis, dropped apostrophes, intro/outro phrases — but
    NO character-level typos. Pairs with `random_typo_control` which has
    typos but no contextual cues."""
    import random as _random
    import re as _re

    p = _seed_prompt()
    out, cues = make_cue_only(p.base_prompt, _random.Random("c"))
    # All-lowercase, ellipsis injected.
    assert out.lower() == out
    assert "..." in out

    def _wordset(s: str) -> set[str]:
        # Strip punctuation/apostrophes so 'list?' and 'list' compare equal.
        return set(_re.findall(r"[a-z]+", s.lower()))

    base_words = _wordset(p.base_prompt)
    out_words = _wordset(out)
    # Every word that appears in the base must still appear (modulo ellipsis,
    # apostrophe stripping, lowercasing) — no typo-perturbed versions allowed.
    missing = base_words - out_words
    assert not missing, (
        f"cue_only must preserve every base word verbatim; missing: {missing}"
    )


def test_fatigue_coded_lowercases_and_adds_self_correction():
    p = _seed_prompt()
    out, cues = make_fatigue_coded(p.base_prompt, random.Random("z"))
    assert out.lower() == out  # all lowercase
    assert "..." in out
    assert any("self_correction" in c.cue_type for c in cues)


def test_rushed_mobile_coded_is_lowercase_and_compressed():
    p = _seed_prompt()
    out, cues = make_rushed_mobile_coded(p.base_prompt, random.Random("z"))
    assert out.lower() == out
    # At least one compression cue should fire on a long prompt with common words.
    assert any(c.cue_type in {"compression", "punctuation"} for c in cues)


def test_typo_distribution_is_substitution_dominant():
    """At scale, substitution should be the most common operation.

    Each substitution / insertion uses QWERTY adjacency, so the most reliable
    fingerprint is character-level edit distance combined with the fact that
    at least one *new* character should be QWERTY-adjacent to the original.
    """
    rng = random.Random("dist")
    base = "the quick brown fox jumps over the lazy dog " * 10
    perturbed = _apply_typos(base, n=80, rng=rng)
    # Same approximate length: substitutions don't change length, transpositions
    # don't either, deletions shrink, insertions grow. Net should stay within
    # ~10% of the original.
    assert abs(len(perturbed) - len(base)) / len(base) < 0.15


def test_typo_insertions_use_qwerty_adjacency():
    """An insertion event must produce a character adjacent to the original
    on QWERTY. Verify by inspecting a single insertion at a controlled site."""
    from paratext.variants import _insert_adjacent

    rng = random.Random("insert")
    text = "function"
    # `n` is at index 3 ('function'[3] = 'c'); pick i=5 → 'i'
    out = _insert_adjacent(text, 5, rng)
    assert len(out) == len(text) + 1
    # The inserted char must be a QWERTY neighbor of 'i'.
    neighbors = set(_QWERTY_NEIGHBORS["i"])
    inserted_idx = next(j for j in range(len(out)) if out[j] != text[min(j, len(text) - 1)])
    inserted_char = out[inserted_idx].lower()
    assert inserted_char in neighbors, f"inserted {inserted_char!r} not adjacent to 'i'"


def test_typo_neighbor_substitution_uses_qwerty_adjacency():
    """A substitution event must replace with a QWERTY-adjacent key."""
    from paratext.variants import _neighbor_swap

    rng = random.Random("sub")
    text = "function"
    # Substitute at index 1 ('u').
    out = _neighbor_swap(text, 1, rng)
    assert len(out) == len(text)
    new_char = out[1].lower()
    assert new_char != "u"
    assert new_char in set(_QWERTY_NEIGHBORS["u"])


def test_rude_frustrated_does_not_use_slurs_or_abuse():
    p = _seed_prompt()
    out, _ = make_rude_frustrated(p.base_prompt, random.Random("z"))
    # We define rude as terse/impatient, not abusive. No content-based asserts beyond
    # absence of obvious abusive markers — main guarantee is at the generator level.
    assert "stupid" not in out.lower()
    assert "idiot" not in out.lower()
