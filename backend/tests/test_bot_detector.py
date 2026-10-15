from app.core.config import Settings
from app.services.bot_detector import BotDetector


def _settings(**overrides) -> Settings:
    base = dict(
        app_env="test",
        detection_window_seconds=60,
        detection_frequency_threshold=3,
        detection_repeat_endpoint_threshold=3,
        detection_suspicious_score_threshold=40,
        detection_high_risk_score_threshold=70,
        detection_captcha_trigger_score=40,
        captcha_enabled=False,
    )
    base.update(overrides)
    return Settings(**base)


def test_normal_request_low_score():
    det = BotDetector(_settings())
    result = det.analyze(
        client_id="c1",
        endpoint="demo",
        user_agent="Mozilla/5.0 (Windows NT 10.0) Chrome/120.0",
    )
    assert result.risk_score == 0
    assert result.classification == "normal"
    assert result.reasons == []


def test_missing_user_agent_weak_signal():
    det = BotDetector(_settings())
    result = det.analyze(client_id="c2", endpoint="demo", user_agent=None)
    assert result.risk_score == 12
    assert any(r["rule"] == "missing_user_agent" for r in result.reasons)
    # Weak-only must not be high_risk
    assert result.classification == "normal"


def test_unusual_user_agent_weak_signal():
    det = BotDetector(_settings())
    result = det.analyze(
        client_id="c3", endpoint="demo", user_agent="python-requests/2.31.0"
    )
    assert any(r["rule"] == "unusual_user_agent" for r in result.reasons)
    assert result.classification == "normal"
    assert result.risk_score < 40


def test_frequency_rule():
    det = BotDetector(_settings(detection_frequency_threshold=3))
    for _ in range(3):
        det.analyze(client_id="c4", endpoint="demo", user_agent="Mozilla/5.0")
    result = det.analyze(client_id="c4", endpoint="demo", user_agent="Mozilla/5.0")
    assert any(r["rule"] == "request_frequency" for r in result.reasons)
    assert result.risk_score >= 15


def test_repeated_endpoint_rule():
    det = BotDetector(_settings(detection_repeat_endpoint_threshold=3))
    for _ in range(3):
        det.analyze(client_id="c5", endpoint="demo", user_agent="Mozilla/5.0")
    result = det.analyze(client_id="c5", endpoint="demo", user_agent="Mozilla/5.0")
    assert any(r["rule"] == "repeated_endpoint" for r in result.reasons)


def test_combined_pattern_high_risk():
    det = BotDetector(
        _settings(
            detection_frequency_threshold=2,
            detection_repeat_endpoint_threshold=2,
        )
    )
    for _ in range(5):
        det.analyze(
            client_id="c6",
            endpoint="demo",
            user_agent="python-requests/2.31.0",
        )
    result = det.analyze(
        client_id="c6",
        endpoint="demo",
        user_agent="python-requests/2.31.0",
    )
    assert result.risk_score >= 70 or result.classification in ("suspicious", "high_risk")
    assert any(r["rule"] == "suspicious_pattern" for r in result.reasons)
    assert len(result.reasons) >= 2


def test_weak_signals_never_high_risk_alone():
    det = BotDetector(
        _settings(
            detection_suspicious_score_threshold=10,
            detection_high_risk_score_threshold=20,
        )
    )
    result = det.analyze(client_id="c7", endpoint="demo", user_agent="")
    assert result.classification != "high_risk"
