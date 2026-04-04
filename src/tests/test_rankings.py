from services.rankings import PROFILES


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
