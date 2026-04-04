from mlb.client import is_quality_start


class TestQualityStart:
    """Tests for QS detection (6+ IP, <3 ER)"""

    def test_qs_true_6_ip_2_er(self):
        assert is_quality_start(6.0, 2) is True

    def test_qs_true_7_ip_1_er(self):
        assert is_quality_start(7.0, 1) is True

    def test_qs_true_6_ip_0_er(self):
        assert is_quality_start(6.0, 0) is True

    def test_qs_true_string_inputs(self):
        assert is_quality_start("6.0", "2") is True

    def test_qs_false_5_ip_2_er(self):
        assert is_quality_start(5.0, 2) is False

    def test_qs_false_6_ip_3_er(self):
        assert is_quality_start(6.0, 3) is False

    def test_qs_false_6_ip_4_er(self):
        assert is_quality_start(6.0, 4) is False

    def test_qs_false_5_1_ip(self):
        assert is_quality_start(5.1, 1) is False

    def test_qs_false_5_2_ip(self):
        assert is_quality_start(5.2, 2) is False

    def test_qs_false_none_ip(self):
        assert is_quality_start(None, 2) is False

    def test_qs_false_none_er(self):
        assert is_quality_start(6.0, None) is False

    def test_qs_false_both_none(self):
        assert is_quality_start(None, None) is False

    def test_qs_false_invalid_ip(self):
        assert is_quality_start("invalid", 2) is False

    def test_qs_false_invalid_er(self):
        assert is_quality_start(6.0, "invalid") is False

    def test_qs_true_6_2_ip_2_er(self):
        assert is_quality_start(6.2, 2) is True

    def test_qs_true_6_1_ip_2_er(self):
        assert is_quality_start(6.1, 2) is True
