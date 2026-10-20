#!/usr/bin/env python3
"""Tests for the reference face-verification logic.

Run: python3 -m unittest poc/test_face_verification.py -v
"""
import math
import unittest

from poc import face_verification as fv


class VectorMathTests(unittest.TestCase):
    def test_normalize_produces_unit_length(self):
        vector = fv.l2_normalize([3.0, 4.0])
        self.assertAlmostEqual(vector[0], 0.6)
        self.assertAlmostEqual(vector[1], 0.8)
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in vector)), 1.0)

    def test_zero_vector_is_rejected(self):
        with self.assertRaises(fv.EmbeddingError):
            fv.l2_normalize([0.0, 0.0])

    def test_cosine_similarity_bounds(self):
        self.assertAlmostEqual(fv.cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(fv.cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)
        self.assertAlmostEqual(fv.cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0)

    def test_dimension_mismatch_is_rejected(self):
        with self.assertRaises(fv.EmbeddingError):
            fv.cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


class CentroidTests(unittest.TestCase):
    def test_centroid_of_identical_vectors_is_the_vector(self):
        vector = fv.l2_normalize([1.0, 2.0, 3.0])
        centroid = fv.build_centroid([vector, vector, vector])
        self.assertAlmostEqual(fv.cosine_similarity(centroid, vector), 1.0)

    def test_intra_user_stats_returns_suggested_threshold(self):
        embedder = fv.HashingEmbedder(dim=64)
        base = embedder.embed(b"employee-1")
        samples = [base] + [fv.perturb_embedding(base, 0.03, f"sample-{i}") for i in range(4)]
        stats = fv.intra_user_stats(samples)
        self.assertEqual(stats.sample_count, 5)
        self.assertGreaterEqual(stats.p95_distance, stats.p50_distance)
        self.assertGreaterEqual(stats.suggested_accept_threshold, 0.68)
        self.assertLessEqual(stats.suggested_accept_threshold, 0.95)

    def test_bounded_ema_moves_toward_sample(self):
        old = fv.l2_normalize([1.0, 0.0, 0.0])
        sample = fv.l2_normalize([1.0, 0.3, 0.0])
        update = fv.plan_centroid_update(
            old,
            sample,
            sample_count=10,
            similarity=0.95,
            liveness_score=0.99,
            quality_score=0.99,
        )
        self.assertTrue(update.updated)
        self.assertGreater(
            fv.cosine_similarity(update.centroid, sample),
            fv.cosine_similarity(old, sample),
        )
        self.assertLess(fv.cosine_similarity(update.centroid, old), 1.0)


class CentroidGuardTests(unittest.TestCase):
    def setUp(self):
        self.old = fv.l2_normalize([1.0, 0.0, 0.0])
        self.sample = fv.l2_normalize([1.0, 0.1, 0.0])
        self.kwargs = dict(
            sample_count=10,
            similarity=0.95,
            liveness_score=0.99,
            quality_score=0.99,
        )

    def test_legal_hold_blocks_update(self):
        update = fv.plan_centroid_update(self.old, self.sample, legal_hold=True, **self.kwargs)
        self.assertFalse(update.updated)
        self.assertEqual(update.reason_code, "LEGAL_HOLD")

    def test_quarantine_blocks_update(self):
        update = fv.plan_centroid_update(self.old, self.sample, quarantine=True, **self.kwargs)
        self.assertFalse(update.updated)
        self.assertEqual(update.reason_code, "QUARANTINED")

    def test_daily_cap_blocks_update(self):
        update = fv.plan_centroid_update(self.old, self.sample, updates_today=3, **self.kwargs)
        self.assertFalse(update.updated)
        self.assertEqual(update.reason_code, "DAILY_CAP")

    def test_low_similarity_blocks_update(self):
        update = fv.plan_centroid_update(self.old, self.sample, **{**self.kwargs, "similarity": 0.60})
        self.assertFalse(update.updated)
        self.assertEqual(update.reason_code, "SIMILARITY_TOO_LOW")

    def test_outlier_blocks_update(self):
        outlier = fv.l2_normalize([0.0, 1.0, 0.0])
        update = fv.plan_centroid_update(self.old, outlier, **self.kwargs)
        self.assertFalse(update.updated)
        self.assertEqual(update.reason_code, "OUTLIER")


class GateTests(unittest.TestCase):
    def test_quality_gate_passes_clean_frame(self):
        result = fv.quality_gate(fv.QualitySignals())
        self.assertTrue(result.passed)
        self.assertEqual(result.failures, ())

    def test_quality_gate_reports_each_failure(self):
        result = fv.quality_gate(
            fv.QualitySignals(face_count=2, face_px=50, brightness=0.05, blur_variance=1.0)
        )
        self.assertFalse(result.passed)
        self.assertIn("FACE_COUNT", result.failures)
        self.assertIn("FACE_TOO_SMALL", result.failures)
        self.assertIn("BRIGHTNESS", result.failures)
        self.assertIn("BLUR", result.failures)

    def test_liveness_requires_challenge_and_score(self):
        self.assertFalse(fv.liveness_gate(0.99, False).passed)
        self.assertFalse(fv.liveness_gate(0.10, True).passed)
        self.assertTrue(fv.liveness_gate(0.99, True).passed)


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.embedder = fv.HashingEmbedder(dim=64)
        self.enrolled = self.embedder.embed(b"employee-42")
        self.centroid = fv.build_centroid([self.enrolled])

    def test_same_employee_is_accepted(self):
        probe = fv.perturb_embedding(self.enrolled, 0.02, "login-1")
        decision = fv.verify_embedding(probe, self.centroid)
        self.assertEqual(decision.decision, "accept")
        self.assertEqual(decision.reason_code, "MATCH")

    def test_different_employee_is_denied(self):
        probe = self.embedder.embed(b"someone-else")
        decision = fv.verify_embedding(probe, self.centroid)
        self.assertEqual(decision.decision, "deny")

    def test_liveness_failure_overrides_good_match(self):
        decision = fv.verify_embedding(
            self.enrolled,
            self.centroid,
            liveness=fv.LivenessResult(False, 0.1, "SPOOF_SUSPECTED"),
        )
        self.assertEqual(decision.decision, "deny")
        self.assertIn("LIVENESS", decision.reason_code)

    def test_quality_failure_overrides_good_match(self):
        decision = fv.verify_embedding(
            self.enrolled,
            self.centroid,
            quality=fv.QualityResult(False, 0.1, ("BLUR",)),
        )
        self.assertEqual(decision.decision, "deny")
        self.assertIn("QUALITY", decision.reason_code)

    def test_review_band_does_not_auto_accept(self):
        thresholds = fv.VerificationThresholds(accept=0.99, review=0.0)
        decision = fv.verify_embedding(
            fv.perturb_embedding(self.enrolled, 0.5, "review"),
            self.centroid,
            thresholds=thresholds,
        )
        self.assertEqual(decision.decision, "review")

    def test_templates_can_raise_the_score(self):
        other = fv.l2_normalize([0.0, 1.0])
        template = fv.l2_normalize([1.0, 0.0])
        decision = fv.verify_embedding([1.0, 0.0], other, templates=[template])
        self.assertEqual(decision.decision, "accept")


class AuditChainTests(unittest.TestCase):
    def test_chain_verifies_and_detects_tampering(self):
        chain = fv.AuditChain()
        chain.append({"event": "login", "outcome": "accept"})
        chain.append({"event": "photo_viewed", "actor": "compliance"})
        self.assertTrue(chain.verify())

        tampered = list(chain.events)
        tampered[0] = fv.AuditEvent(
            index=tampered[0].index,
            prev_hash=tampered[0].prev_hash,
            event_hash=tampered[0].event_hash,
            payload=tampered[0].payload.replace("accept", "deny"),
        )
        chain._events = tampered
        self.assertFalse(chain.verify())

    def test_deterministic_payload_is_order_independent(self):
        left = fv.canonical_payload({"b": 2, "a": 1})
        right = fv.canonical_payload({"a": 1, "b": 2})
        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
