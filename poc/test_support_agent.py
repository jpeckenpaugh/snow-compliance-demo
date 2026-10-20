#!/usr/bin/env python3
"""Tests for the bounded support-agent reference policy.

Run: python3 -m unittest poc/test_support_agent.py -v
"""
import json
import unittest

from poc import support_agent as sa


def user(authenticated=True, roles=()):
    return sa.SupportUser(
        employee_id="emp-1042",
        snowflake_user="alice",
        authenticated=authenticated,
        roles=tuple(roles),
    )


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.agent = sa.SupportAgent()

    def test_codes_are_unique(self):
        codes = [situation.code for situation in sa.SITUATIONS]
        self.assertEqual(len(codes), len(set(codes)))

    def test_catalog_covers_the_requested_situations(self):
        expected = {
            "ENROLLMENT",
            "CAMERA_DEVICE",
            "VERIFICATION_FAILURE",
            "ACCOUNT_LOCKOUT",
            "ASSISTED_VERIFICATION",
            "ACCOMMODATION",
            "CONSENT_WITHDRAWAL",
            "AUDIT_RECORD",
            "APPEAL",
            "STEP_UP",
            "SUSPECTED_FRAUD",
            "PHOTO_ACCESS",
            "BREAK_GLASS",
            "POLICY_FAQ",
            "UNKNOWN",
        }
        self.assertTrue(expected.issubset({s.code for s in sa.SITUATIONS}))

    def test_high_risk_situations_are_human_only(self):
        for code in (
            "CONSENT_WITHDRAWAL",
            "PHOTO_ACCESS",
            "APPEAL",
            "ACCOMMODATION",
            "SUSPECTED_FRAUD",
            "BREAK_GLASS",
        ):
            self.assertTrue(self.agent.by_code[code].human_only, code)


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.agent = sa.SupportAgent()

    def test_representative_messages_route_to_the_expected_situation(self):
        samples = {
            "My camera is blocked": "CAMERA_DEVICE",
            "How do I enroll my face?": "ENROLLMENT",
            "It keeps failing liveness": "VERIFICATION_FAILURE",
            "I am locked out after too many attempts": "ACCOUNT_LOCKOUT",
            "I need assisted verification": "ASSISTED_VERIFICATION",
            "I need an accommodation": "ACCOMMODATION",
            "I want to withdraw my consent": "CONSENT_WITHDRAWAL",
            "I need my audit record": "AUDIT_RECORD",
            "I want to appeal the denial": "APPEAL",
            "Why is it asking me to verify again for a high matter?": "STEP_UP",
            "Someone is using my account": "SUSPECTED_FRAUD",
            "Can I see the photo from my login?": "PHOTO_ACCESS",
            "I need break glass access": "BREAK_GLASS",
            "How long do you keep my photo?": "POLICY_FAQ",
        }
        for message, expected in samples.items():
            with self.subTest(message=message):
                match = self.agent.classify(message)
                self.assertEqual(match.code, expected)
                self.assertFalse(match.ambiguous)

    def test_unmatched_message_is_unknown(self):
        match = self.agent.classify("hello there")
        self.assertEqual(match.code, "UNKNOWN")
        self.assertEqual(match.confidence, 0.0)

    def test_equal_top_scores_are_ambiguous(self):
        first = sa.Situation("A", "A", ("alpha",), ("search_support_kb",))
        second = sa.Situation("B", "B", ("beta",), ("search_support_kb",))
        agent = sa.SupportAgent([first, second])
        match = agent.classify("alpha beta")
        self.assertTrue(match.ambiguous)


class HandleTests(unittest.TestCase):
    def setUp(self):
        self.agent = sa.SupportAgent()

    def test_unauthenticated_user_is_handed_off(self):
        reply = self.agent.handle(user(authenticated=False), "My camera is blocked")
        self.assertTrue(reply.handoff)
        self.assertEqual(reply.reason_code, "AUTH_REQUIRED")

    def test_unknown_intent_is_handed_off(self):
        reply = self.agent.handle(user(), "hello there")
        self.assertTrue(reply.handoff)
        self.assertEqual(reply.reason_code, "UNKNOWN_INTENT")
        self.assertEqual(reply.handoff_queue, "SUPPORT_TIER_1")

    def test_low_confidence_is_handed_off(self):
        agent = sa.SupportAgent(confidence_threshold=0.99)
        reply = agent.handle(user(), "My camera is blocked")
        self.assertTrue(reply.handoff)
        self.assertEqual(reply.reason_code, "LOW_CONFIDENCE")

    def test_simple_situation_is_answered_with_citation(self):
        reply = self.agent.handle(user(), "My camera is blocked")
        self.assertFalse(reply.handoff)
        self.assertEqual(reply.situation_code, "CAMERA_DEVICE")
        self.assertIn("KB-CAMERA-001", reply.citations)
        self.assertIn("create_support_ticket", reply.proposed_actions)

    def test_high_risk_situation_requires_human(self):
        reply = self.agent.handle(user(), "I want to withdraw my consent")
        self.assertTrue(reply.handoff)
        self.assertEqual(reply.reason_code, "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(reply.handoff_queue, "PRIVACY")
        self.assertIn("request_consent_withdrawal", reply.proposed_actions)

    def test_fraud_escalates_immediately(self):
        reply = self.agent.handle(user(), "Someone is using my account")
        self.assertTrue(reply.handoff)
        self.assertEqual(reply.handoff_queue, "SECURITY_INCIDENT")

    def test_policy_answer_is_grounded(self):
        reply = self.agent.handle(user(), "How long do you keep my photo?")
        self.assertFalse(reply.handoff)
        self.assertTrue(reply.citations)
        self.assertIn("KB-RETENTION-001", reply.citations)


class ToolPolicyTests(unittest.TestCase):
    def setUp(self):
        self.agent = sa.SupportAgent()

    def test_self_read_tool_is_allowed(self):
        decision = self.agent.authorize_tool(user(), "get_my_enrollment_status", "ENROLLMENT")
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_human_approval)

    def test_cross_user_and_biometric_tools_are_always_denied(self):
        for tool in ("read_other_user", "view_raw_photo", "get_embedding", "change_role"):
            with self.subTest(tool=tool):
                decision = self.agent.authorize_tool(user(), tool, "AUDIT_RECORD")
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.reason_code, "DENIED_TOOL")

    def test_tool_not_in_situation_is_denied(self):
        decision = self.agent.authorize_tool(user(), "request_photo_access", "ENROLLMENT")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "TOOL_NOT_ALLOWED_FOR_SITUATION")

    def test_high_risk_tool_requires_human_approval(self):
        for tool, situation in (
            ("request_photo_access", "PHOTO_ACCESS"),
            ("request_consent_withdrawal", "CONSENT_WITHDRAWAL"),
            ("request_accommodation", "ACCOMMODATION"),
        ):
            with self.subTest(tool=tool):
                decision = self.agent.authorize_tool(user(), tool, situation)
                self.assertTrue(decision.allowed)
                self.assertTrue(decision.requires_human_approval)

    def test_unauthenticated_tool_call_is_denied(self):
        decision = self.agent.authorize_tool(
            user(authenticated=False), "get_my_enrollment_status", "ENROLLMENT"
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "AUTH_REQUIRED")


class RedactionTests(unittest.TestCase):
    def test_email_phone_and_long_identifier_are_redacted(self):
        text = "Email alice@example.com, call 555-123-4567, id 123456789."
        redacted = sa.redact_pii(text)
        self.assertNotIn("alice@example.com", redacted)
        self.assertNotIn("555-123-4567", redacted)
        self.assertNotIn("123456789", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)
        self.assertIn("[REDACTED_PHONE]", redacted)
        self.assertIn("[REDACTED_ID]", redacted)

    def test_secret_like_token_is_redacted(self):
        redacted = sa.redact_pii("token ghp_abcdefghijklmnopqrstuvwxyz")
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.agent = sa.SupportAgent()

    def test_audit_event_hashes_text_and_omits_identifiers(self):
        message = "My email is alice@example.com and my camera is blocked"
        reply = self.agent.handle(user(), message, conversation_id="conv-7")
        event = self.agent.audit_event(user(), message, reply, conversation_id="conv-7")
        serialized = json.dumps(event)
        self.assertNotIn("alice@example.com", serialized)
        self.assertNotIn(message, serialized)
        self.assertEqual(event["conversation_id"], "conv-7")
        self.assertEqual(event["situation_code"], "CAMERA_DEVICE")
        self.assertEqual(len(event["message_sha256"]), 64)
        self.assertEqual(len(event["user_hash"]), 64)

    def test_audit_event_records_handoff_reason(self):
        message = "I need break glass access"
        reply = self.agent.handle(user(), message)
        event = self.agent.audit_event(user(), message, reply)
        self.assertTrue(event["handoff"])
        self.assertEqual(event["handoff_queue"], "SECURITY_INCIDENT")
        self.assertEqual(event["reason_code"], "HUMAN_REVIEW_REQUIRED")


class RoleTests(unittest.TestCase):
    def test_has_any_role(self):
        self.assertTrue(user(roles=("SUPPORT_HUMAN",)).has_any_role({"SUPPORT_HUMAN"}))
        self.assertFalse(user(roles=("EMPLOYEE",)).has_any_role({"SUPPORT_HUMAN"}))


if __name__ == "__main__":
    unittest.main()
