#!/usr/bin/env python3
"""Reference logic for webcam login verification.

This module implements the deterministic parts of ``docs/WEBCAM_LOGIN_RBAC.md``:
vector math, centroid construction and drift-safe updates, quality/liveness
gates, three-band decisions, and a hash-chained audit helper.

It is intentionally dependency-free and deliberately does **not** capture a
camera, call a face model, store images, or talk to Snowflake. ``HashingEmbedder``
is a deterministic stand-in for tests only; replace it with the approved model
behind the same interface. See the design guide before using any of this with
real biometric data.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

EMBEDDING_DIM = 512
DEFAULT_MODEL_ID = "arcface-reference@1"
FLOAT_TOLERANCE = 1e-9


class EmbeddingError(ValueError):
    """Raised when a vector is malformed or cannot be normalized."""


def _validate_vector(vector: Sequence[float], dim: Optional[int] = None) -> None:
    if dim is not None and len(vector) != dim:
        raise EmbeddingError(f"expected {dim} dimensions, got {len(vector)}")
    if not vector:
        raise EmbeddingError("embedding must not be empty")
    for value in vector:
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise EmbeddingError("embedding contains a non-finite value")


def l2_normalize(vector: Sequence[float]) -> Tuple[float, ...]:
    """Return a unit-length copy of ``vector``.

    Face models are compared with cosine similarity, so every stored vector is
    normalized at the boundary. A zero vector is rejected rather than silently
    treated as a match.
    """
    _validate_vector(vector)
    norm = math.sqrt(sum(float(value) * float(value) for value in vector))
    if norm <= FLOAT_TOLERANCE:
        raise EmbeddingError("cannot normalize a zero-length embedding")
    return tuple(float(value) / norm for value in vector)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Cosine similarity in [-1, 1], with 1.0 meaning identical direction."""
    if len(left) != len(right):
        raise EmbeddingError(f"dimension mismatch: {len(left)} vs {len(right)}")
    a = l2_normalize(left)
    b = l2_normalize(right)
    score = sum(x * y for x, y in zip(a, b))
    return max(-1.0, min(1.0, score))


def cosine_distance(left: Sequence[float], right: Sequence[float]) -> float:
    """Distance in [0, 2]; 0.0 means identical direction."""
    return 1.0 - cosine_similarity(left, right)


def build_centroid(embeddings: Iterable[Sequence[float]]) -> Tuple[float, ...]:
    """Return the normalized mean of one employee's enrollment embeddings."""
    vectors = [l2_normalize(vector) for vector in embeddings]
    if not vectors:
        raise EmbeddingError("at least one embedding is required")
    dim = len(vectors[0])
    if any(len(vector) != dim for vector in vectors):
        raise EmbeddingError("all embeddings must have the same dimension")
    mean = [sum(vector[i] for vector in vectors) / len(vectors) for i in range(dim)]
    return l2_normalize(mean)


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        raise EmbeddingError("percentile requires at least one value")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


@dataclass(frozen=True)
class IntraUserStats:
    centroid: Tuple[float, ...]
    sample_count: int
    p50_distance: float
    p95_distance: float
    suggested_accept_threshold: float


def intra_user_stats(
    embeddings: Iterable[Sequence[float]],
    floor: float = 0.68,
    ceiling: float = 0.95,
    margin: float = 0.05,
) -> IntraUserStats:
    """Summarize enrollment consistency and suggest a starting threshold.

    The suggestion is a calibration aid, not an approval. Production thresholds
    must come from a consented pilot and the approved risk appetite.
    """
    vectors = [l2_normalize(vector) for vector in embeddings]
    centroid = build_centroid(vectors)
    distances = [cosine_distance(vector, centroid) for vector in vectors]
    p50 = _percentile(distances, 0.50)
    p95 = _percentile(distances, 0.95)
    suggested = max(floor, min(ceiling, 1.0 - p95 - margin))
    return IntraUserStats(
        centroid=centroid,
        sample_count=len(vectors),
        p50_distance=p50,
        p95_distance=p95,
        suggested_accept_threshold=suggested,
    )


@dataclass(frozen=True)
class VerificationThresholds:
    accept: float = 0.68
    review: float = 0.58

    def __post_init__(self) -> None:
        if not -1.0 <= self.review < self.accept <= 1.0:
            raise ValueError("thresholds must satisfy -1 <= review < accept <= 1")


@dataclass(frozen=True)
class Decision:
    decision: str
    similarity: float
    reason_code: str
    threshold_used: float


@dataclass(frozen=True)
class QualitySignals:
    face_count: int = 1
    face_px: int = 240
    brightness: float = 0.55
    blur_variance: float = 220.0
    yaw_degrees: float = 5.0
    pitch_degrees: float = 3.0


@dataclass(frozen=True)
class QualityResult:
    passed: bool
    score: float
    failures: Tuple[str, ...]


def quality_gate(
    signals: QualitySignals,
    min_face_px: int = 160,
    min_blur_variance: float = 100.0,
    min_brightness: float = 0.25,
    max_brightness: float = 0.85,
    max_yaw: float = 20.0,
    max_pitch: float = 15.0,
) -> QualityResult:
    """Check whether a frame is suitable for embedding.

    Rejected frames should not be retained by default. Record only the failure
    reasons needed for support and monitoring.
    """
    failures: List[str] = []
    if signals.face_count != 1:
        failures.append("FACE_COUNT")
    if signals.face_px < min_face_px:
        failures.append("FACE_TOO_SMALL")
    if not min_brightness <= signals.brightness <= max_brightness:
        failures.append("BRIGHTNESS")
    if signals.blur_variance < min_blur_variance:
        failures.append("BLUR")
    if abs(signals.yaw_degrees) > max_yaw:
        failures.append("YAW")
    if abs(signals.pitch_degrees) > max_pitch:
        failures.append("PITCH")
    checks = 6
    score = (checks - len(failures)) / checks
    return QualityResult(passed=not failures, score=score, failures=tuple(failures))


@dataclass(frozen=True)
class LivenessResult:
    passed: bool
    score: float
    reason_code: str


def liveness_gate(
    passive_score: float,
    challenge_ok: bool,
    min_passive: float = 0.80,
) -> LivenessResult:
    """Combine passive anti-spoof and the server's active challenge."""
    if not math.isfinite(passive_score):
        return LivenessResult(False, 0.0, "LIVENESS_INVALID")
    if not challenge_ok:
        return LivenessResult(False, passive_score, "CHALLENGE_FAILED")
    if passive_score < min_passive:
        return LivenessResult(False, passive_score, "SPOOF_SUSPECTED")
    return LivenessResult(True, passive_score, "LIVENESS_OK")


def verify_embedding(
    probe: Sequence[float],
    centroid: Sequence[float],
    templates: Iterable[Sequence[float]] = (),
    *,
    quality: Optional[QualityResult] = None,
    liveness: Optional[LivenessResult] = None,
    thresholds: VerificationThresholds = VerificationThresholds(),
) -> Decision:
    """Run the three-band 1:1 decision against a centroid and active templates.

    Liveness and quality failures override similarity: a high-scoring spoof is
    still a deny. The returned similarity belongs in the audit record, never in
    the browser response.
    """
    if quality is not None and not quality.passed:
        return Decision("deny", 0.0, f"QUALITY:{quality.failures[0]}", thresholds.accept)
    if liveness is not None and not liveness.passed:
        return Decision("deny", 0.0, f"LIVENESS:{liveness.reason_code}", thresholds.accept)

    similarity = cosine_similarity(probe, centroid)
    for template in templates:
        similarity = max(similarity, cosine_similarity(probe, template))

    if similarity >= thresholds.accept:
        return Decision("accept", similarity, "MATCH", thresholds.accept)
    if similarity >= thresholds.review:
        return Decision("review", similarity, "REVIEW_BAND", thresholds.review)
    return Decision("deny", similarity, "NO_MATCH", thresholds.review)


@dataclass(frozen=True)
class CentroidUpdate:
    updated: bool
    centroid: Tuple[float, ...]
    sample_count: int
    alpha: float
    reason_code: str


def plan_centroid_update(
    current_centroid: Sequence[float],
    accepted_embedding: Sequence[float],
    sample_count: int,
    similarity: float,
    liveness_score: float,
    quality_score: float,
    *,
    updates_today: int = 0,
    legal_hold: bool = False,
    quarantine: bool = False,
    alpha_min: float = 0.05,
    min_similarity: float = 0.72,
    min_liveness: float = 0.80,
    min_quality: float = 0.70,
    max_updates_per_day: int = 3,
    max_distance: float = 0.50,
) -> CentroidUpdate:
    """Apply the bounded EMA update only when every guard passes.

    The guard order is deliberate: a legal hold or quarantine wins over a good
    score, and a low-similarity sample never nudges the centroid.
    """
    current = l2_normalize(current_centroid)
    sample = l2_normalize(accepted_embedding)
    if len(current) != len(sample):
        raise EmbeddingError("centroid and sample dimensions differ")
    if legal_hold:
        return CentroidUpdate(False, current, sample_count, 0.0, "LEGAL_HOLD")
    if quarantine:
        return CentroidUpdate(False, current, sample_count, 0.0, "QUARANTINED")
    if updates_today >= max_updates_per_day:
        return CentroidUpdate(False, current, sample_count, 0.0, "DAILY_CAP")
    if similarity < min_similarity:
        return CentroidUpdate(False, current, sample_count, 0.0, "SIMILARITY_TOO_LOW")
    if liveness_score < min_liveness:
        return CentroidUpdate(False, current, sample_count, 0.0, "LIVENESS_TOO_LOW")
    if quality_score < min_quality:
        return CentroidUpdate(False, current, sample_count, 0.0, "QUALITY_TOO_LOW")

    distance = cosine_distance(sample, current)
    if distance > max_distance:
        return CentroidUpdate(False, current, sample_count, 0.0, "OUTLIER")

    alpha = max(alpha_min, 1.0 / (max(sample_count, 0) + 1))
    blended = tuple(
        (1.0 - alpha) * old + alpha * new for old, new in zip(current, sample)
    )
    updated = l2_normalize(blended)
    return CentroidUpdate(True, updated, sample_count + 1, alpha, "UPDATED")


def canonical_payload(payload: Mapping[str, Any]) -> str:
    """Serialize an audit payload deterministically for hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class AuditEvent:
    index: int
    prev_hash: str
    event_hash: str
    payload: str


class AuditChain:
    """Small append-only hash chain mirroring ``IDENTITY.verification_event``.

    The production chain is written transactionally in Snowflake and anchored
    periodically in immutable storage. This helper exists to test the algorithm
    and to keep the event schema honest.
    """

    GENESIS = "0" * 64

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    @property
    def events(self) -> Tuple[AuditEvent, ...]:
        return tuple(self._events)

    @property
    def head(self) -> str:
        return self._events[-1].event_hash if self._events else self.GENESIS

    def append(self, payload: Mapping[str, Any]) -> AuditEvent:
        serialized = canonical_payload(payload)
        prev_hash = self.head
        event_hash = hashlib.sha256(
            f"{prev_hash}:{serialized}".encode("utf-8")
        ).hexdigest()
        event = AuditEvent(
            index=len(self._events),
            prev_hash=prev_hash,
            event_hash=event_hash,
            payload=serialized,
        )
        self._events.append(event)
        return event

    def verify(self) -> bool:
        prev_hash = self.GENESIS
        for index, event in enumerate(self._events):
            expected = hashlib.sha256(
                f"{prev_hash}:{event.payload}".encode("utf-8")
            ).hexdigest()
            if (
                event.index != index
                or event.prev_hash != prev_hash
                or event.event_hash != expected
            ):
                return False
            prev_hash = event.event_hash
        return True


class HashingEmbedder:
    """Deterministic stand-in for a face model. Never use for real identity."""

    def __init__(self, dim: int = EMBEDDING_DIM):
        if dim < 8:
            raise ValueError("dim must be at least 8")
        self.dim = dim

    def embed(self, image_bytes: bytes) -> Tuple[float, ...]:
        if not image_bytes:
            raise EmbeddingError("image_bytes must not be empty")
        digest = hashlib.shake_256(image_bytes).digest(self.dim * 4)
        values = []
        for offset in range(0, len(digest), 4):
            chunk = int.from_bytes(digest[offset:offset + 4], "big", signed=False)
            values.append((chunk / 2**31) - 1.0)
        return l2_normalize(values)


def perturb_embedding(
    embedding: Sequence[float],
    magnitude: float = 0.05,
    seed: str = "test",
) -> Tuple[float, ...]:
    """Add deterministic noise to simulate natural frame-to-frame variation."""
    if magnitude < 0:
        raise ValueError("magnitude must be non-negative")
    base = l2_normalize(embedding)
    stream = hashlib.shake_256(seed.encode("utf-8")).digest(len(base) * 4)
    noise = []
    for offset in range(0, len(stream), 4):
        chunk = int.from_bytes(stream[offset:offset + 4], "big", signed=False)
        noise.append(((chunk / 2**31) - 1.0) * magnitude)
    return l2_normalize(tuple(value + delta for value, delta in zip(base, noise)))
