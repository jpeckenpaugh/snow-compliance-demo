#!/usr/bin/env python3
"""Reference policy and routing for the bounded support agent.

Implements the deterministic parts of ``docs/SUPPORT_AGENT_INTEGRATION.md``:
a situation catalog, a keyword router (a stand-in for the production
classifier), a tool allowlist, human-review gates, PII redaction, and a
redacted audit event.

This module does not call an LLM, retrieve documents, or execute tools. The
production design uses the same policy boundaries with a model-generated
situation and reply, and a separate tool gateway that re-checks every call.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

CONFIDENCE_THRESHOLD = 0.55
AGENT_RELEASE = "support-agent-reference@1"

DENIED_TOOLS = frozenset(
    {
        "read_other_user",
        "view_raw_photo",
        "get_embedding",
        "get_centroid",
        "change_role",
        "unlock_account",
        "approve_access",
        "delete_audit",
        "set_threshold",
        "disable_liveness",
        "run_sql",
        "http_passthrough",
    }
)

HUMAN_APPROVAL_TOOLS = frozenset(
    {
        "request_accommodation",
        "request_consent_withdrawal",
        "request_photo_access",
    }
)


@dataclass(frozen=True)
class Situation:
    code: str
    title: str
    keywords: Tuple[str, ...]
    allowed_tools: Tuple[str, ...]
    actions: Tuple[str, ...] = ()
    human_only: bool = False
    queue: str = "SUPPORT_TIER_1"
    article_ids: Tuple[str, ...] = ()
    response: str = ""


SITUATIONS: Tuple[Situation, ...] = (
    Situation(
        code="SUSPECTED_FRAUD",
        title="Suspected account compromise",
        keywords=(
            "someone else",
            "someone is using",
            "not me",
            "account compromised",
            "account hacked",
            "stolen account",
            "impersonating me",
        ),
        allowed_tools=("search_support_kb", "escalate_to_human"),
        actions=("escalate_to_human",),
        human_only=True,
        queue="SECURITY_INCIDENT",
        article_ids=("KB-SECURITY-001",),
        response=(
            "This may be an account-security incident. I am escalating it now; "
            "do not share passwords or codes in this chat."
        ),
    ),
    Situation(
        code="BREAK_GLASS",
        title="Emergency / break-glass access",
        keywords=(
            "break glass",
            "breakglass",
            "emergency access",
            "urgent access now",
            "bypass verification",
            "skip verification",
        ),
        allowed_tools=("search_support_kb", "create_support_ticket", "escalate_to_human"),
        actions=("create_support_ticket", "escalate_to_human"),
        human_only=True,
        queue="SECURITY_INCIDENT",
        article_ids=("KB-BREAKGLASS-001",),
        response=(
            "Break-glass access requires two named approvers and is never granted in chat. "
            "I can open an urgent security ticket for that review."
        ),
    ),
    Situation(
        code="CONSENT_WITHDRAWAL",
        title="Consent withdrawal / biometric deletion",
        keywords=(
            "withdraw consent",
            "withdraw my consent",
            "delete my face",
            "delete my biometric",
            "delete my data",
            "erase my data",
            "remove my biometric",
        ),
        allowed_tools=("search_support_kb", "request_consent_withdrawal"),
        actions=("request_consent_withdrawal",),
        human_only=True,
        queue="PRIVACY",
        article_ids=("KB-PRIVACY-002",),
        response=(
            "A privacy specialist must confirm the scope and any legal-hold exception. "
            "I can open that request and record what you want removed."
        ),
    ),
    Situation(
        code="PHOTO_ACCESS",
        title="Raw photo access request",
        keywords=(
            "see the photo",
            "access my photo",
            "raw photo",
            "login photo",
            "photo from my login",
            "copy of my photo",
        ),
        allowed_tools=("search_support_kb", "request_photo_access"),
        actions=("request_photo_access",),
        human_only=True,
        queue="COMPLIANCE_REVIEW",
        article_ids=("KB-PRIVACY-003",),
        response=(
            "Raw-photo access goes through a compliance review with a recorded reason. "
            "I can open that request; I cannot release or display the image in chat."
        ),
    ),
    Situation(
        code="APPEAL",
        title="Appeal a verification decision",
        keywords=(
            "appeal",
            "dispute the denial",
            "contest the decision",
            "review the denial",
            "wrongly denied",
        ),
        allowed_tools=("get_my_login_attempts", "search_support_kb", "create_support_ticket"),
        actions=("create_support_ticket",),
        human_only=True,
        queue="COMPLIANCE_REVIEW",
        article_ids=("KB-APPEAL-001",),
        response=(
            "A reviewer must examine the decision and the audit record. "
            "I can open an appeal case and include the reason you provide."
        ),
    ),
    Situation(
        code="ACCOMMODATION",
        title="Accommodation / alternative authentication",
        keywords=(
            "accommodation",
            "cannot use a camera",
            "can't use a camera",
            "alternative authentication",
            "disability",
            "religious",
            "medical reason",
        ),
        allowed_tools=("search_support_kb", "request_accommodation"),
        actions=("request_accommodation",),
        human_only=True,
        queue="HR_COMPLIANCE",
        article_ids=("KB-ACCOMMODATION-001",),
        response=(
            "An equivalent verification path is available without using a camera. "
            "A human will handle the accommodation request and any supporting details."
        ),
    ),
    Situation(
        code="ACCOUNT_LOCKOUT",
        title="Account lockout",
        keywords=(
            "locked out",
            "account locked",
            "too many attempts",
            "locked my account",
            "cannot sign in after retries",
        ),
        allowed_tools=("get_my_login_attempts", "search_support_kb", "create_support_ticket"),
        actions=("create_support_ticket",),
        queue="SUPPORT_TIER_1",
        article_ids=("KB-LOCKOUT-001",),
        response=(
            "Lockouts are cleared by a support agent after an identity check. "
            "I can open the unlock ticket; I cannot unlock the account myself."
        ),
    ),
    Situation(
        code="ASSISTED_VERIFICATION",
        title="Assisted verification",
        keywords=(
            "assisted verification",
            "manual verification",
            "verify me manually",
            "talk to a person",
            "human verification",
            "video call verification",
        ),
        allowed_tools=(
            "get_my_login_attempts",
            "search_support_kb",
            "request_assisted_verification",
        ),
        actions=("request_assisted_verification",),
        queue="IDENTITY_VERIFICATION",
        article_ids=("KB-ASSISTED-001",),
        response=(
            "A verification specialist can review your case with an approved alternative "
            "procedure. I can open that request now."
        ),
    ),
    Situation(
        code="AUDIT_RECORD",
        title="Own verification history",
        keywords=(
            "audit record",
            "verification history",
            "my login history",
            "my attempts",
            "access history",
            "who viewed my photo",
        ),
        allowed_tools=("get_my_audit_summary", "get_my_login_attempts", "search_support_kb"),
        queue="SUPPORT_TIER_1",
        article_ids=("KB-AUDIT-001",),
        response=(
            "I can show your own redacted verification summary. "
            "Raw photos, embeddings, and score details are not exposed in chat."
        ),
    ),
    Situation(
        code="STEP_UP",
        title="Fresh step-up verification",
        keywords=(
            "step up",
            "step-up",
            "verify again",
            "asked me to verify",
            "high matter",
            "step up verification",
        ),
        allowed_tools=("get_my_login_attempts", "search_support_kb", "start_reverification"),
        actions=("start_reverification",),
        queue="SUPPORT_TIER_1",
        article_ids=("KB-STEPUP-001",),
        response=(
            "High-confidentiality actions require a fresh verification. "
            "I can send a new challenge to your authenticated session."
        ),
    ),
    Situation(
        code="ENROLLMENT",
        title="Face enrollment help",
        keywords=(
            "enroll",
            "enrollment",
            "register my face",
            "set up my face",
            "first time using face",
            "face setup",
        ),
        allowed_tools=(
            "get_my_enrollment_status",
            "search_support_kb",
            "request_assisted_verification",
        ),
        actions=("request_assisted_verification",),
        queue="SUPPORT_TIER_1",
        article_ids=("KB-ENROLL-001",),
        response=(
            "Enrollment needs good lighting, one face in frame, and a few seconds of "
            "movement for the liveness challenge. I can check your status or open an "
            "assisted-enrollment request."
        ),
    ),
    Situation(
        code="CAMERA_DEVICE",
        title="Camera or device troubleshooting",
        keywords=(
            "camera",
            "webcam",
            "black screen",
            "permission",
            "blurry",
            "virtual camera",
            "camera blocked",
            "camera not working",
        ),
        allowed_tools=("get_my_enrollment_status", "search_support_kb", "create_support_ticket"),
        actions=("create_support_ticket",),
        queue="SUPPORT_TIER_1",
        article_ids=("KB-CAMERA-001",),
        response=(
            "Check the browser camera permission, close other apps using the camera, "
            "and avoid virtual-camera filters. If it still fails, I can open a device ticket."
        ),
    ),
    Situation(
        code="VERIFICATION_FAILURE",
        title="Verification or liveness failure",
        keywords=(
            "liveness",
            "cannot verify",
            "can't verify",
            "could not verify",
            "verification failed",
            "failed verification",
            "keeps failing",
            "retry",
        ),
        allowed_tools=(
            "get_my_login_attempts",
            "search_support_kb",
            "request_assisted_verification",
            "start_reverification",
        ),
        actions=("start_reverification", "request_assisted_verification"),
        queue="SUPPORT_TIER_1",
        article_ids=("KB-VERIFY-001",),
        response=(
            "Most failures are lighting, motion, or a stale challenge. I can check your "
            "recent reason codes and send a fresh challenge; repeated liveness failures "
            "can be reviewed by a specialist."
        ),
    ),
    Situation(
        code="POLICY_FAQ",
        title="Policy and privacy questions",
        keywords=(
            "how long",
            "retention",
            "who can see",
            "privacy",
            "keep my photo",
            "photo storage",
            "what data",
        ),
        allowed_tools=("search_support_kb",),
        queue="SUPPORT_TIER_1",
        article_ids=("KB-PRIVACY-001", "KB-RETENTION-001"),
        response=(
            "I can answer from the approved privacy and retention policy. "
            "If the policy does not cover your case, I will route it to a human."
        ),
    ),
    Situation(
        code="UNKNOWN",
        title="Out of scope",
        keywords=(),
        allowed_tools=("search_support_kb", "escalate_to_human"),
        actions=("escalate_to_human",),
        human_only=True,
        queue="SUPPORT_TIER_1",
        response=(
            "That request is outside what I can handle here. "
            "I am handing it to a support agent with the context you provided."
        ),
    ),
)


@dataclass(frozen=True)
class SupportUser:
    employee_id: str
    snowflake_user: str
    authenticated: bool
    roles: Tuple[str, ...] = ()

    def has_any_role(self, roles: Iterable[str]) -> bool:
        return bool(set(self.roles).intersection(roles))


@dataclass(frozen=True)
class IntentMatch:
    code: str
    confidence: float
    matched_keywords: Tuple[str, ...]
    ambiguous: bool = False


@dataclass(frozen=True)
class SupportReply:
    reply: str
    situation_code: str
    confidence: float
    citations: Tuple[str, ...]
    proposed_actions: Tuple[str, ...]
    handoff: bool
    handoff_queue: Optional[str]
    reason_code: str


@dataclass(frozen=True)
class ToolAuthorization:
    allowed: bool
    requires_human_approval: bool
    reason_code: str


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def redact_pii(text: str) -> str:
    """Remove common direct identifiers before storage or model input."""
    redacted = re.sub(
        r"\b(?:sk|pk|ghp|xox[baprs])[-_][A-Za-z0-9_\-]{12,}\b",
        "[REDACTED_SECRET]",
        text,
    )
    redacted = re.sub(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        "[REDACTED_EMAIL]",
        redacted,
    )
    redacted = re.sub(
        r"(?<!\d)(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?!\d)",
        "[REDACTED_PHONE]",
        redacted,
    )
    redacted = re.sub(r"(?<!\d)\d{9,}(?!\d)", "[REDACTED_ID]", redacted)
    return redacted


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SupportAgent:
    """Deterministic reference for routing, policy, and audit.

    ``classify`` is intentionally simple. The production classifier may be an
    LLM, but its output is accepted only if it names a catalog code and passes
    the same policy checks implemented here.
    """

    def __init__(
        self,
        situations: Sequence[Situation] = SITUATIONS,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> None:
        if not situations:
            raise ValueError("at least one situation is required")
        codes = [situation.code for situation in situations]
        if len(codes) != len(set(codes)):
            raise ValueError("situation codes must be unique")
        self.situations = tuple(situations)
        self.by_code = {situation.code: situation for situation in situations}
        self.confidence_threshold = confidence_threshold

    def classify(self, message: str) -> IntentMatch:
        normalized = _normalize(message)
        scored = []
        for index, situation in enumerate(self.situations):
            if not situation.keywords:
                continue
            matched = tuple(
                keyword for keyword in situation.keywords if _normalize(keyword) in normalized
            )
            if matched:
                scored.append((len(matched), -index, situation.code, matched))
        if not scored:
            return IntentMatch("UNKNOWN", 0.0, ())

        scored.sort(reverse=True)
        best_score, _, best_code, best_matches = scored[0]
        ambiguous = len(scored) > 1 and scored[1][0] == best_score and scored[1][2] != best_code
        confidence = min(0.95, 0.45 + 0.16 * best_score)
        return IntentMatch(best_code, confidence, best_matches, ambiguous)

    def handle(
        self,
        user: SupportUser,
        message: str,
        conversation_id: str = "conv-reference",
    ) -> SupportReply:
        if not user.authenticated:
            return SupportReply(
                "Please sign in to the portal first so I can check your own status.",
                "AUTH_REQUIRED",
                0.0,
                (),
                (),
                True,
                "SUPPORT_TIER_1",
                "AUTH_REQUIRED",
            )

        intent = self.classify(message)
        if intent.ambiguous:
            return self._handoff(
                "I am not sure which workflow you need. I am routing this to a human "
                "so you do not get the wrong instructions.",
                intent,
                "AMBIGUOUS_INTENT",
            )
        if intent.code == "UNKNOWN":
            return self._handoff(
                self.by_code["UNKNOWN"].response,
                intent,
                "UNKNOWN_INTENT",
            )
        if intent.confidence < self.confidence_threshold:
            return self._handoff(
                self.by_code["UNKNOWN"].response,
                intent,
                "LOW_CONFIDENCE",
            )

        situation = self.by_code[intent.code]
        if situation.human_only:
            return SupportReply(
                situation.response,
                situation.code,
                intent.confidence,
                situation.article_ids,
                situation.actions,
                True,
                situation.queue,
                "HUMAN_REVIEW_REQUIRED",
            )
        return SupportReply(
            situation.response,
            situation.code,
            intent.confidence,
            situation.article_ids,
            situation.actions,
            False,
            None,
            "ANSWERED",
        )

    def _handoff(
        self,
        reply: str,
        intent: IntentMatch,
        reason_code: str,
    ) -> SupportReply:
        situation = self.by_code["UNKNOWN"]
        return SupportReply(
            reply,
            intent.code if intent.code in self.by_code else "UNKNOWN",
            intent.confidence,
            situation.article_ids,
            situation.actions,
            True,
            situation.queue,
            reason_code,
        )

    def authorize_tool(
        self,
        user: SupportUser,
        tool_name: str,
        situation_code: str,
    ) -> ToolAuthorization:
        if not user.authenticated:
            return ToolAuthorization(False, False, "AUTH_REQUIRED")
        if tool_name in DENIED_TOOLS:
            return ToolAuthorization(False, False, "DENIED_TOOL")
        situation = self.by_code.get(situation_code)
        if situation is None:
            return ToolAuthorization(False, False, "UNKNOWN_SITUATION")
        if tool_name not in situation.allowed_tools:
            return ToolAuthorization(False, False, "TOOL_NOT_ALLOWED_FOR_SITUATION")
        requires_human = tool_name in HUMAN_APPROVAL_TOOLS
        return ToolAuthorization(True, requires_human, "HUMAN_APPROVAL" if requires_human else "ALLOWED")

    def audit_event(
        self,
        user: SupportUser,
        message: str,
        reply: SupportReply,
        conversation_id: str = "conv-reference",
    ) -> Dict[str, object]:
        redacted_message = redact_pii(message)
        return {
            "release": AGENT_RELEASE,
            "conversation_id": conversation_id,
            "user_hash": _sha256(user.snowflake_user),
            "situation_code": reply.situation_code,
            "confidence": round(reply.confidence, 4),
            "handoff": reply.handoff,
            "handoff_queue": reply.handoff_queue,
            "reason_code": reply.reason_code,
            "citations": list(reply.citations),
            "proposed_actions": list(reply.proposed_actions),
            "message_sha256": _sha256(redacted_message),
            "reply_sha256": _sha256(reply.reply),
        }
