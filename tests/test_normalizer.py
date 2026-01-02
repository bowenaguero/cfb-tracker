"""Tests for the normalizer module."""

from cfb_tracker.normalizer import (
    generate_id,
    get_name_key,
    normalize_name,
    normalize_position,
)


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_lowercase_and_strip(self):
        assert normalize_name("  John Smith  ") == "john smith"

    def test_removes_accents(self):
        assert normalize_name("José García") == "jose garcia"

    def test_removes_punctuation(self):
        assert normalize_name("John Smith, Jr.") == "john smith jr"

    def test_preserves_hyphens(self):
        assert normalize_name("John Smith-Jones") == "john smith-jones"

    def test_collapses_whitespace(self):
        assert normalize_name("John    Smith") == "john smith"

    def test_unicode_normalization(self):
        # Test NFKD normalization (e.g., ligatures)
        assert normalize_name("ﬁrst") == "first"


class TestNormalizePosition:
    """Tests for normalize_position function."""

    def test_quarterback(self):
        assert normalize_position("Quarterback") == "qb"
        assert normalize_position("QUARTERBACK") == "qb"

    def test_running_back(self):
        assert normalize_position("Running Back") == "rb"

    def test_wide_receiver(self):
        assert normalize_position("Wide Receiver") == "wr"

    def test_tight_end(self):
        assert normalize_position("Tight End") == "te"

    def test_offensive_line(self):
        assert normalize_position("Offensive Tackle") == "ot"
        assert normalize_position("Offensive Guard") == "og"
        assert normalize_position("Offensive Line") == "ol"
        assert normalize_position("Center") == "c"

    def test_defensive_line(self):
        assert normalize_position("Defensive End") == "de"
        assert normalize_position("Defensive Tackle") == "dt"
        assert normalize_position("Defensive Line") == "dl"

    def test_linebacker(self):
        assert normalize_position("Linebacker") == "lb"
        assert normalize_position("Inside Linebacker") == "ilb"
        assert normalize_position("Outside Linebacker") == "olb"

    def test_secondary(self):
        assert normalize_position("Cornerback") == "cb"
        assert normalize_position("Safety") == "s"
        assert normalize_position("Free Safety") == "fs"
        assert normalize_position("Strong Safety") == "ss"

    def test_special_teams(self):
        assert normalize_position("Kicker") == "k"
        assert normalize_position("Punter") == "p"
        assert normalize_position("Long Snapper") == "ls"

    def test_athlete(self):
        assert normalize_position("Athlete") == "ath"

    def test_edge(self):
        assert normalize_position("Edge") == "edge"

    def test_unknown_position_passthrough(self):
        # Unknown positions should be lowercased and returned as-is
        assert normalize_position("Unknown Position") == "unknown position"
        assert normalize_position("QB") == "qb"


class TestGetNameKey:
    """Tests for get_name_key function."""

    def test_basic_name(self):
        # First letter of first name + last name
        assert get_name_key("John Smith") == "jsmith"

    def test_removes_suffix_jr(self):
        assert get_name_key("John Smith Jr") == "jsmith"
        assert get_name_key("John Smith Jr.") == "jsmith"

    def test_removes_suffix_sr(self):
        assert get_name_key("John Smith Sr") == "jsmith"

    def test_removes_suffix_ii(self):
        assert get_name_key("John Smith II") == "jsmith"

    def test_removes_suffix_iii(self):
        assert get_name_key("John Smith III") == "jsmith"

    def test_removes_suffix_iv(self):
        assert get_name_key("John Smith IV") == "jsmith"

    def test_hyphenated_lastname_uses_last_part(self):
        assert get_name_key("John Smith-Jones") == "jjones"

    def test_handles_single_name(self):
        # Single names return normalized form
        assert get_name_key("Madonna") == "madonna"

    def test_handles_middle_names(self):
        # Should still use first letter + last name
        assert get_name_key("John Michael Smith") == "jsmith"

    def test_complex_case(self):
        # Hyphenated last name with suffix
        assert get_name_key("Kensly Ladour-Foustin III") == "kfoustin"


class TestGenerateId:
    """Tests for generate_id function."""

    def test_generates_hex_string(self):
        result = generate_id("John Smith")
        assert isinstance(result, str)
        assert len(result) == 16
        # Should be valid hex
        int(result, 16)

    def test_same_name_same_id(self):
        id1 = generate_id("John Smith")
        id2 = generate_id("John Smith")
        assert id1 == id2

    def test_different_names_different_ids(self):
        id1 = generate_id("John Smith")
        id2 = generate_id("Mike Johnson")
        assert id1 != id2

    def test_name_variations_same_id(self):
        # These should all produce the same ID due to name key normalization
        id1 = generate_id("John Smith")
        id2 = generate_id("John Smith Jr")
        id3 = generate_id("John Smith Jr.")
        id4 = generate_id("  John  Smith  ")
        assert id1 == id2 == id3 == id4

    def test_case_insensitive(self):
        id1 = generate_id("John Smith")
        id2 = generate_id("JOHN SMITH")
        id3 = generate_id("john smith")
        assert id1 == id2 == id3

    def test_hyphenated_names(self):
        # Hyphenated names with same last part should match
        id1 = generate_id("Kensly Foustin")
        id2 = generate_id("Kensly Ladour-Foustin")
        assert id1 == id2
