"""Explainable, rule-based bot detection engine.

This is a transparent demonstration scorer — not a production bot defense.
User-Agent signals alone never reliably identify bots; weak signals only
contribute modest score and never auto-ban on their own.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Optional

from app.core.config import Settings, get_settings


@dataclass
class DetectionResult:
    risk_score: float
    classification: str  # normal | suspicious | high_risk
    reasons: list[dict] = field(default_factory=list)
    captcha_recommended: bool = False


# Known automation / empty UA markers — weak signal only
_SUSPICIOUS_UA_MARKERS = (
    "python-requests",
    "curl/",
    "wget/",
    "httpx/",
    "scrapy",
    "go-http-client",
    "java/",
    "libwww-perl",
    "aiohttp",
)


class BotDetector:
    """In-memory sliding-window signal tracker with explainable scoring."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._lock = threading.Lock()
        # client_id -> deque of timestamps
        self._request_times: dict[str, Deque[float]] = defaultdict(deque)
        # client_id -> deque of (timestamp, endpoint)
        self._endpoint_hits: dict[str, Deque[tuple[float, str]]] = defaultdict(deque)

    def reset(self) -> None:
        with self._lock:
            self._request_times.clear()
            self._endpoint_hits.clear()

    def _prune(self, client_id: str, now: float) -> None:
        window = self.settings.detection_window_seconds
        times = self._request_times[client_id]
        while times and now - times[0] > window:
            times.popleft()
        hits = self._endpoint_hits[client_id]
        while hits and now - hits[0][0] > window:
            hits.popleft()

    def analyze(
        self,
        *,
        client_id: str,
        endpoint: str,
        user_agent: Optional[str],
        record: bool = True,
    ) -> DetectionResult:
        """Score a request and optionally record it in the sliding window."""
        now = time.monotonic()
        reasons: list[dict] = []
        score = 0.0

        with self._lock:
            self._prune(client_id, now)
            freq_count = len(self._request_times[client_id])
            # Count repeats of this endpoint in the window (before recording)
            same_endpoint = sum(
                1 for _, ep in self._endpoint_hits[client_id] if ep == endpoint
            )

            if record:
                self._request_times[client_id].append(now)
                self._endpoint_hits[client_id].append((now, endpoint))

        # Rule 1: Request frequency within window
        freq_threshold = self.settings.detection_frequency_threshold
        if freq_count >= freq_threshold:
            contrib = min(40.0, 15.0 + (freq_count - freq_threshold) * 5.0)
            score += contrib
            reasons.append(
                {
                    "rule": "request_frequency",
                    "score": round(contrib, 1),
                    "explanation": (
                        f"{freq_count} prior requests in the last "
                        f"{self.settings.detection_window_seconds}s "
                        f"(threshold: {freq_threshold})."
                    ),
                }
            )

        # Rule 2: Repeated access to the same endpoint
        repeat_threshold = self.settings.detection_repeat_endpoint_threshold
        if same_endpoint >= repeat_threshold:
            contrib = min(30.0, 10.0 + (same_endpoint - repeat_threshold) * 4.0)
            score += contrib
            reasons.append(
                {
                    "rule": "repeated_endpoint",
                    "score": round(contrib, 1),
                    "explanation": (
                        f"Endpoint '{endpoint}' hit {same_endpoint} times in the "
                        f"detection window (threshold: {repeat_threshold})."
                    ),
                }
            )

        # Rule 3: Missing User-Agent (weak signal)
        if not user_agent or not user_agent.strip():
            contrib = 12.0
            score += contrib
            reasons.append(
                {
                    "rule": "missing_user_agent",
                    "score": contrib,
                    "explanation": (
                        "Missing User-Agent header. This is a weak signal — "
                        "legitimate clients occasionally omit it and this alone "
                        "does not identify a bot."
                    ),
                }
            )
        else:
            # Rule 4: Unusual / automation-like User-Agent (weak signal)
            ua_lower = user_agent.lower()
            matched = next((m for m in _SUSPICIOUS_UA_MARKERS if m in ua_lower), None)
            if matched:
                contrib = 15.0
                score += contrib
                reasons.append(
                    {
                        "rule": "unusual_user_agent",
                        "score": contrib,
                        "explanation": (
                            f"User-Agent contains '{matched}', which is common in "
                            "scripts and HTTP libraries. This is a weak signal and "
                            "does not reliably identify a bot by itself."
                        ),
                    }
                )

        # Rule 5: Combined behavioral pattern (frequency + repeat)
        if freq_count >= freq_threshold and same_endpoint >= repeat_threshold:
            contrib = 20.0
            score += contrib
            reasons.append(
                {
                    "rule": "suspicious_pattern",
                    "score": contrib,
                    "explanation": (
                        "Combined high request frequency and repeated endpoint "
                        "access exceeds behavioral thresholds."
                    ),
                }
            )

        # Cap score and classify — never auto-ban on weak signals alone
        score = min(100.0, round(score, 1))
        classification = self._classify(score, reasons)

        captcha_recommended = (
            score >= self.settings.detection_captcha_trigger_score
            and self.settings.captcha_enabled
        )

        return DetectionResult(
            risk_score=score,
            classification=classification,
            reasons=reasons,
            captcha_recommended=captcha_recommended,
        )

    def _classify(self, score: float, reasons: list[dict]) -> str:
        """Classify with false-positive safeguards.

        Weak-only signals (UA rules without behavioral rules) cannot reach
        high_risk even if score is elevated — prevents UA-only auto-flagging.
        """
        weak_rules = {"missing_user_agent", "unusual_user_agent"}
        triggered = {r["rule"] for r in reasons}
        only_weak = triggered and triggered.issubset(weak_rules)

        if score >= self.settings.detection_high_risk_score_threshold and not only_weak:
            return "high_risk"
        if score >= self.settings.detection_suspicious_score_threshold:
            return "suspicious"
        # Soft-cap: weak-only stays at most suspicious
        if only_weak and score >= self.settings.detection_suspicious_score_threshold:
            return "suspicious"
        return "normal"


# Process-wide singleton used by routes (reset in tests)
_detector: Optional[BotDetector] = None
_detector_lock = threading.Lock()


def get_bot_detector() -> BotDetector:
    global _detector
    with _detector_lock:
        if _detector is None:
            _detector = BotDetector()
        return _detector


def reset_bot_detector(settings: Optional[Settings] = None) -> BotDetector:
    global _detector
    with _detector_lock:
        _detector = BotDetector(settings)
        return _detector
