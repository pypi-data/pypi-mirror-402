"""Unit tests for playbook utilities."""

from ace.playbook import (
    ACEPlaybook,
    SectionName,
    add_bullet_to_playbook,
    count_tokens_approximate,
    extract_bullet_ids,
    extract_bullet_ids_from_comment,
    extract_playbook_bullets,
    format_playbook_line,
    get_max_bullet_id,
    get_playbook_stats,
    get_section_slug,
    initialize_empty_playbook,
    limit_playbook_to_budget,
    parse_playbook_line,
    prune_harmful_bullets,
    update_bullet_counts,
)


class TestParsePlaybookLine:
    """Tests for parse_playbook_line function."""

    def test_parse_valid_line(self):
        line = "[str-00001] helpful=5 harmful=2 :: Always verify data types"
        result = parse_playbook_line(line)

        assert result is not None
        assert result.id == "str-00001"
        assert result.helpful == 5
        assert result.harmful == 2
        assert result.content == "Always verify data types"

    def test_parse_line_with_zero_counts(self):
        line = "[cal-00042] helpful=0 harmful=0 :: NPV formula"
        result = parse_playbook_line(line)

        assert result is not None
        assert result.id == "cal-00042"
        assert result.helpful == 0
        assert result.harmful == 0

    def test_parse_invalid_line_returns_none(self):
        assert parse_playbook_line("## strategies_and_insights") is None
        assert parse_playbook_line("") is None
        assert parse_playbook_line("random text") is None

    def test_parse_line_with_extra_whitespace(self):
        line = "  [str-00001]  helpful=5  harmful=0  ::  Content here  "
        result = parse_playbook_line(line)

        assert result is not None
        assert result.id == "str-00001"
        assert result.content == "Content here"


class TestFormatPlaybookLine:
    """Tests for format_playbook_line function."""

    def test_format_basic_line(self):
        result = format_playbook_line("str-00001", 5, 2, "Test content")
        assert result == "[str-00001] helpful=5 harmful=2 :: Test content"

    def test_format_sanitizes_newlines(self):
        content = "First line.\nSecond line.\r\nThird line."
        result = format_playbook_line("str-00001", 0, 0, content)
        assert "\n" not in result
        assert "\r" not in result
        assert "First line. Second line. Third line." in result

    def test_format_collapses_whitespace(self):
        content = "Multiple    spaces   here"
        result = format_playbook_line("str-00001", 0, 0, content)
        assert "Multiple spaces here" in result


class TestExtractBulletIds:
    """Tests for bullet ID extraction functions."""

    def test_extract_from_text(self):
        text = "Using [str-00001] and [cal-00002] for this problem"
        result = extract_bullet_ids(text)
        assert result == ["str-00001", "cal-00002"]

    def test_extract_from_empty_text(self):
        assert extract_bullet_ids("") == []
        assert extract_bullet_ids("no bullets here") == []

    def test_extract_from_comment(self):
        text = 'Answer here. <!-- bullet_ids: ["str-00001", "mis-00002"] -->'
        result = extract_bullet_ids_from_comment(text)
        assert result == ["str-00001", "mis-00002"]

    def test_extract_from_comment_empty(self):
        text = "Answer here. <!-- bullet_ids: [] -->"
        result = extract_bullet_ids_from_comment(text)
        assert result == []

    def test_extract_from_comment_missing(self):
        text = "Answer without bullet IDs comment"
        result = extract_bullet_ids_from_comment(text)
        assert result == []


class TestPlaybookOperations:
    """Tests for playbook manipulation functions."""

    def test_initialize_empty_playbook(self):
        playbook = initialize_empty_playbook()
        assert "## strategies_and_insights" in playbook
        assert "## common_mistakes_to_avoid" in playbook
        assert "## others" in playbook

    def test_add_bullet_to_playbook(self):
        playbook = initialize_empty_playbook()
        new_playbook, next_id = add_bullet_to_playbook(
            playbook,
            SectionName.STRATEGIES_AND_INSIGHTS,
            "New strategy here",
            1,
        )

        assert "[str-00001]" in new_playbook
        assert "New strategy here" in new_playbook
        assert next_id == 2

    def test_add_bullet_to_playbook_with_string_section(self):
        playbook = initialize_empty_playbook()
        new_playbook, _ = add_bullet_to_playbook(
            playbook,
            "strategies_and_insights",
            "New strategy",
            1,
        )

        assert "[str-00001]" in new_playbook

    def test_update_bullet_counts_helpful(self):
        playbook = "[str-00001] helpful=0 harmful=0 :: Test bullet"
        tags = [{"id": "str-00001", "tag": "helpful"}]

        result = update_bullet_counts(playbook, tags)
        assert "helpful=1" in result
        assert "harmful=0" in result

    def test_update_bullet_counts_harmful(self):
        playbook = "[str-00001] helpful=5 harmful=0 :: Test bullet"
        tags = [{"id": "str-00001", "tag": "harmful"}]

        result = update_bullet_counts(playbook, tags)
        assert "helpful=5" in result
        assert "harmful=1" in result

    def test_update_bullet_counts_neutral(self):
        playbook = "[str-00001] helpful=5 harmful=0 :: Test bullet"
        tags = [{"id": "str-00001", "tag": "neutral"}]

        result = update_bullet_counts(playbook, tags)
        assert "helpful=5" in result
        assert "harmful=0" in result


class TestPlaybookStats:
    """Tests for playbook statistics."""

    def test_get_playbook_stats_empty(self):
        playbook = initialize_empty_playbook()
        stats = get_playbook_stats(playbook)

        assert stats["total_bullets"] == 0
        assert stats["high_performing"] == 0
        assert stats["problematic"] == 0

    def test_get_playbook_stats_with_bullets(self):
        playbook = """## strategies_and_insights
[str-00001] helpful=10 harmful=0 :: High performing bullet
[str-00002] helpful=0 harmful=5 :: Problematic bullet
[str-00003] helpful=0 harmful=0 :: Unused bullet
"""
        stats = get_playbook_stats(playbook)

        assert stats["total_bullets"] == 3
        assert stats["high_performing"] == 1
        assert stats["problematic"] == 1
        assert stats["unused"] == 1


class TestPlaybookPruning:
    """Tests for playbook pruning."""

    def test_prune_harmful_bullets(self):
        playbook = """## strategies_and_insights
[str-00001] helpful=10 harmful=0 :: Good bullet
[str-00002] helpful=1 harmful=5 :: Bad bullet (should be pruned)
[str-00003] helpful=5 harmful=5 :: Border case
"""
        result = prune_harmful_bullets(playbook, threshold=0.5, min_interactions=3)

        assert "[str-00001]" in result
        assert "[str-00002]" not in result  # Pruned (harmful ratio > 0.5)
        assert "[str-00003]" in result  # Kept (harmful ratio = 0.5, not > 0.5)

    def test_prune_respects_min_interactions(self):
        playbook = """## strategies_and_insights
[str-00001] helpful=0 harmful=2 :: Low interaction bullet
"""
        result = prune_harmful_bullets(playbook, threshold=0.5, min_interactions=5)

        # Should not be pruned because total interactions < min_interactions
        assert "[str-00001]" in result


class TestTokenBudget:
    """Tests for token budget limiting."""

    def test_count_tokens_approximate(self):
        text = "This is a test string"
        tokens = count_tokens_approximate(text)
        # ~4 chars per token
        assert 4 <= tokens <= 6

    def test_limit_playbook_under_budget(self):
        playbook = initialize_empty_playbook()
        result = limit_playbook_to_budget(playbook, token_budget=100000)
        assert result == playbook

    def test_limit_playbook_prioritizes_high_performing(self):
        playbook = """## strategies_and_insights
[str-00001] helpful=10 harmful=0 :: High performing - should survive
[str-00002] helpful=1 harmful=5 :: Low performing - may be dropped
[str-00003] helpful=0 harmful=0 :: Fresh bullet - should survive
"""
        # Very small budget to force trimming
        result = limit_playbook_to_budget(playbook, token_budget=100, reserve_tokens=0)

        # Should keep section headers at minimum
        assert "## strategies_and_insights" in result


class TestACEPlaybook:
    """Tests for ACEPlaybook dataclass."""

    def test_to_dict_and_from_dict(self):
        playbook = ACEPlaybook(
            content="## test\n[str-00001] helpful=1 harmful=0 :: Test",
            next_global_id=2,
            stats={"total_bullets": 1},
        )

        data = playbook.to_dict()
        restored = ACEPlaybook.from_dict(data)

        assert restored.content == playbook.content
        assert restored.next_global_id == playbook.next_global_id
        assert restored.stats == playbook.stats

    def test_from_dict_with_defaults(self):
        playbook = ACEPlaybook.from_dict({})

        assert playbook.next_global_id == 1
        assert playbook.stats == {}


class TestSectionSlug:
    """Tests for section slug generation."""

    def test_get_section_slug_from_enum(self):
        assert get_section_slug(SectionName.STRATEGIES_AND_INSIGHTS) == "str"
        assert get_section_slug(SectionName.COMMON_MISTAKES_TO_AVOID) == "mis"
        assert get_section_slug(SectionName.OTHERS) == "oth"

    def test_get_section_slug_from_string(self):
        assert get_section_slug("strategies_and_insights") == "str"
        assert get_section_slug("STRATEGIES_AND_INSIGHTS") == "str"
        assert get_section_slug("unknown_section") == "oth"


class TestExtractPlaybookBullets:
    """Tests for extracting specific bullets from playbook."""

    def test_extract_existing_bullets(self):
        playbook = """## strategies_and_insights
[str-00001] helpful=5 harmful=0 :: First bullet
[str-00002] helpful=3 harmful=1 :: Second bullet
"""
        result = extract_playbook_bullets(playbook, ["str-00001"])
        assert "[str-00001]" in result
        assert "First bullet" in result
        assert "[str-00002]" not in result

    def test_extract_no_bullets(self):
        playbook = initialize_empty_playbook()
        result = extract_playbook_bullets(playbook, [])
        assert "No bullets referenced" in result

    def test_extract_missing_bullets(self):
        playbook = initialize_empty_playbook()
        result = extract_playbook_bullets(playbook, ["str-99999"])
        assert "not found" in result


class TestGetMaxBulletId:
    """Tests for finding max bullet ID."""

    def test_get_max_id_empty(self):
        playbook = initialize_empty_playbook()
        assert get_max_bullet_id(playbook) == 0

    def test_get_max_id_with_bullets(self):
        playbook = """
[str-00005] helpful=0 harmful=0 :: First
[str-00010] helpful=0 harmful=0 :: Second
[str-00003] helpful=0 harmful=0 :: Third
"""
        assert get_max_bullet_id(playbook) == 10
