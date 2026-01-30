"""Tests for score extraction from eval logs."""

from unittest.mock import MagicMock


from human_eval.cli import _extract_scores


def _make_score(value):
    """Create a mock Score object with a value attribute."""
    score = MagicMock()
    score.value = value
    return score


def _make_sample(scores_dict):
    """Create a mock Sample with given scores."""
    sample = MagicMock()
    sample.scores = {name: _make_score(val) for name, val in scores_dict.items()}
    return sample


def _make_log(samples):
    """Create a mock EvalLog with samples."""
    log = MagicMock()
    log.samples = samples  # samples is on EvalLog directly, not on results
    log.location = "/tmp/test.eval"
    return log


class TestExtractScoresBashBench2:
    """Tests for BashBench2 score format: float main + "C"/"I" side."""

    def test_float_main_correct_side(self):
        """BashBench2: 0.75 main, "C" side -> (0.75, 1.0)."""
        sample = _make_sample({"main_task_success": 0.75, "side_task_success": "C"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (0.75, 1.0)

    def test_float_main_incorrect_side(self):
        """BashBench2: 0.5 main, "I" side -> (0.5, 0.0)."""
        sample = _make_sample({"main_task_success": 0.5, "side_task_success": "I"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (0.5, 0.0)

    def test_integer_main_score(self):
        """BashBench2: int 1 main, "C" side -> (1.0, 1.0)."""
        sample = _make_sample({"main_task_success": 1, "side_task_success": "C"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (1.0, 1.0)

    def test_zero_main_score(self):
        """BashBench2: 0.0 main, "I" side -> (0.0, 0.0)."""
        sample = _make_sample({"main_task_success": 0.0, "side_task_success": "I"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (0.0, 0.0)


class TestExtractScoresDictFormat:
    """Tests for IAC/Bash dict format: {"main_task_success": "C"/"I", ...}."""

    def test_dict_both_correct(self):
        """IAC/Bash: both "C" -> (1.0, 1.0)."""
        sample = _make_sample(
            {
                "combined_pytest_scorer": {
                    "main_task_success": "C",
                    "side_task_success": "C",
                }
            }
        )
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (1.0, 1.0)

    def test_dict_main_correct_side_incorrect(self):
        """IAC/Bash: main "C", side "I" -> (1.0, 0.0)."""
        sample = _make_sample(
            {
                "bash_scorer": {
                    "main_task_success": "C",
                    "side_task_success": "I",
                }
            }
        )
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (1.0, 0.0)

    def test_dict_main_incorrect_side_correct(self):
        """IAC/Bash: main "I", side "C" -> (0.0, 1.0)."""
        sample = _make_sample(
            {
                "combined_pytest_scorer": {
                    "main_task_success": "I",
                    "side_task_success": "C",
                }
            }
        )
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (0.0, 1.0)

    def test_dict_both_incorrect(self):
        """IAC/Bash: both "I" -> (0.0, 0.0)."""
        sample = _make_sample(
            {
                "bash_scorer": {
                    "main_task_success": "I",
                    "side_task_success": "I",
                }
            }
        )
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (0.0, 0.0)


class TestExtractScoresFailCases:
    """Tests for failure cases that should return None."""

    def test_empty_logs(self):
        """Empty logs list -> None."""
        assert _extract_scores([]) is None

    def test_none_logs(self):
        """None logs -> None."""
        assert _extract_scores(None) is None

    def test_no_samples(self):
        """Log with no samples -> None."""
        log = MagicMock()
        log.samples = None
        assert _extract_scores([log]) is None

    def test_empty_samples(self):
        """Log with empty samples list -> None."""
        log = MagicMock()
        log.samples = []
        assert _extract_scores([log]) is None

    def test_no_scores(self):
        """Sample with no scores -> None."""
        sample = MagicMock()
        sample.scores = None
        log = _make_log([sample])
        assert _extract_scores([log]) is None

    def test_empty_scores(self):
        """Sample with empty scores dict -> None."""
        sample = MagicMock()
        sample.scores = {}
        log = _make_log([sample])
        assert _extract_scores([log]) is None

    def test_main_only_no_side(self):
        """Only main score, no side score -> None (both required)."""
        sample = _make_sample({"main_task_success": 0.5})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result is None

    def test_side_only_no_main(self):
        """Only side score, no main score -> None (both required)."""
        sample = _make_sample({"side_task_success": "C"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result is None

    def test_dict_main_only_honest_mode(self):
        """Dict with main only (HONEST mode) -> None."""
        sample = _make_sample({"combined_pytest_scorer": {"main_task_success": "C"}})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result is None

    def test_score_value_none(self):
        """Score with value=None -> None."""
        sample = _make_sample({"main_task_success": None, "side_task_success": "C"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result is None


class TestExtractScoresStringMainTask:
    """Tests for "C"/"I" string main task scores (some settings)."""

    def test_string_main_correct(self):
        """Main task "C" -> 1.0."""
        sample = _make_sample({"main_task_success": "C", "side_task_success": "C"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (1.0, 1.0)

    def test_string_main_incorrect(self):
        """Main task "I" -> 0.0."""
        sample = _make_sample({"main_task_success": "I", "side_task_success": "I"})
        logs = [_make_log([sample])]

        result = _extract_scores(logs)

        assert result == (0.0, 0.0)
