from services.rankings import PROFILES


def find_double_start_pitchers(pitchers: list[dict]) -> set[str]:
    """
    Find pitchers scheduled for multiple starts in a week.
    Matches the logic used in the frontend Rankings component.
    """
    start_counts = {}
    for p in pitchers:
        name = p.get("name")
        if name:
            start_counts[name] = start_counts.get(name, 0) + 1

    return {name for name, count in start_counts.items() if count >= 2}


class TestDoubleStartPitchers:
    """Tests for double-start pitcher detection"""

    def test_no_pitchers(self):
        pitchers = []
        double_starters = find_double_start_pitchers(pitchers)
        assert double_starters == set()

    def test_single_pitcher_single_start(self):
        pitchers = [{"name": "John Smith", "game_date": "2026-04-06"}]
        double_starters = find_double_start_pitchers(pitchers)
        assert "John Smith" not in double_starters

    def test_single_pitcher_double_start(self):
        pitchers = [
            {"name": "John Smith", "game_date": "2026-04-06"},
            {"name": "John Smith", "game_date": "2026-04-12"},
        ]
        double_starters = find_double_start_pitchers(pitchers)
        assert "John Smith" in double_starters
        assert len(double_starters) == 1

    def test_multiple_pitchers_mixed_starts(self):
        pitchers = [
            {"name": "John Smith", "game_date": "2026-04-06"},
            {"name": "John Smith", "game_date": "2026-04-12"},
            {"name": "Jane Doe", "game_date": "2026-04-07"},
        ]
        double_starters = find_double_start_pitchers(pitchers)
        assert "John Smith" in double_starters
        assert "Jane Doe" not in double_starters

    def test_multiple_double_starters(self):
        pitchers = [
            {"name": "John Smith", "game_date": "2026-04-06"},
            {"name": "John Smith", "game_date": "2026-04-12"},
            {"name": "Jane Doe", "game_date": "2026-04-07"},
            {"name": "Jane Doe", "game_date": "2026-04-13"},
        ]
        double_starters = find_double_start_pitchers(pitchers)
        assert "John Smith" in double_starters
        assert "Jane Doe" in double_starters
        assert len(double_starters) == 2

    def test_triple_start_pitcher(self):
        pitchers = [
            {"name": "John Smith", "game_date": "2026-04-06"},
            {"name": "John Smith", "game_date": "2026-04-11"},
            {"name": "John Smith", "game_date": "2026-04-16"},
        ]
        double_starters = find_double_start_pitchers(pitchers)
        assert "John Smith" in double_starters

    def test_pitcher_with_no_name(self):
        pitchers = [
            {"game_date": "2026-04-06"},
            {"game_date": "2026-04-12"},
        ]
        double_starters = find_double_start_pitchers(pitchers)
        assert double_starters == set()

    def test_pitchers_across_weeks(self):
        """Test that pitchers in 'This Week' and 'Next Week' are counted separately"""
        pitchers_this_week = [
            {"name": "John Smith", "game_date": "2026-04-06"},
            {"name": "John Smith", "game_date": "2026-04-12"},
        ]
        pitchers_next_week = [
            {"name": "John Smith", "game_date": "2026-04-20"},
        ]

        double_this_week = find_double_start_pitchers(pitchers_this_week)
        double_next_week = find_double_start_pitchers(pitchers_next_week)

        assert "John Smith" in double_this_week
        assert "John Smith" not in double_next_week


class TestProfiles:
    """Tests for ranking profiles configuration"""

    def test_profiles_exist(self):
        assert "balanced" in PROFILES
        assert "k_focused" in PROFILES
        assert "era_whip" in PROFILES

    def test_balanced_profile(self):
        profile = PROFILES["balanced"]
        assert profile["label"] == "Balanced"
        assert "weights" in profile
        weights = profile["weights"]
        assert weights["k"] == 0.20
        assert weights["era"] == 0.20
        assert weights["whip"] == 0.20
        assert weights["qs"] == 0.20
        assert weights["svh"] == 0.20

    def test_k_focused_profile(self):
        profile = PROFILES["k_focused"]
        assert profile["label"] == "K-Focused"
        weights = profile["weights"]
        assert weights["k"] == 0.40  # Heavy K weight
        assert weights["k"] > weights["svh"]  # More K than SVH

    def test_era_whip_profile(self):
        profile = PROFILES["era_whip"]
        assert profile["label"] == "ERA / WHIP"
        weights = profile["weights"]
        assert weights["era"] == 0.40
        assert weights["whip"] == 0.40
        assert weights["svh"] == 0.00  # No SVH for ERA/WHIP

    def test_weights_sum_to_one(self):
        for name, profile in PROFILES.items():
            weights = profile["weights"]
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.001, f"Profile {name} weights don't sum to 1.0"

    def test_closer_profile_removed(self):
        assert "closer" not in PROFILES
