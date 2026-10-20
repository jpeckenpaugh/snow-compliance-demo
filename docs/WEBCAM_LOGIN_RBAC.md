# Webcam Photo Verification at Login — Design & Implementation Guide

Status: **proposal for board review (2026-10-20)** · Owner: CEO office · Applies to:
`SNOW_COMPLIANCE_DEMO` · Companion artifacts: [`sql/identity/01_identity_verification.sql`](../sql/identity/01_identity_verification.sql),
[`poc/face_verification.py`](../poc/face_verification.py) · Follow-up:
[`SUPPORT_AGENT_INTEGRATION.md`](SUPPORT_AGENT_INTEGRATION.md) specifies the bounded
customer-support agent that fields the predictable login/verification requests.

> **Read this first.** This document describes a proposed capability. Nothing in the
> current POC captures a webcam, stores a face image, or performs recognition. Facial
> biometrics are sensitive personal information and, in several jurisdictions, a
> regulated biometric identifier. Do not enable this feature for real people until
> legal review, a data-protection impact assessment, written consent, and a signed
> vendor/data-processing agreement are complete. This is not legal advice.

## 1. What the board asked for

> "Add a feature to login that users must provide a photo with their webcam. Photos
> should be saved for auditing purposes, have info on generating embeddings,
> maintaining centroid. This should be AI / ML integration for compliance and RBAC."

The request bundles five capabilities that should be delivered as one governed
authentication flow, not five unrelated additions:

1. **Capture** — the browser asks for a webcam photo at sign-in.
2. **Verify** — the photo is compared to the signed-in employee's enrolled face.
3. **Retain** — the photo and decision are stored for audit.
4. **Learn** — a face embedding and per-user centroid are generated and maintained.
5. **Authorize** — the verification result raises an *authentication assurance level*
   that controls which roles and matters the session can reach.

## 2. Recommendation

**Add webcam verification as a step-up authenticator after password + MFA, never as
the only factor.** Use **1:1 verification** against the employee's own enrolled
template. Do **not** build 1:N face search, surveillance, emotion detection, or
demographic inference.

| Decision | Recommendation | Why |
| --- | --- | --- |
| Factor role | Step-up after password + MFA (AAL2/AAL3) | A face is not a secret; a photo can be replayed. It is an additional signal, not a password replacement. |
| Matching mode | 1:1 against the enrolled employee | 1:N identification creates far larger privacy, bias, and false-match exposure. |
| Enrollment | 3–5 consented, liveness-checked frames; store template + centroid | One frame gives no variance estimate and makes thresholds uncalibrated. |
| Raw photo retention | Encrypted, access-restricted, short retention (default 90 days) with legal-hold override | Audit needs evidence, not indefinite biometric archives. |
| Embedding retention | Life of employment + configured audit tail; deleted on separation/erasure | Embeddings are still biometric data even though they are not images. |
| Thresholds | Start conservative; calibrate on a consented pilot; review per model version | Published numbers from other deployments do not transfer. |
| Rollout | Legal/DPIA → sandbox → 20-person pilot → privileged roles → all staff | Fail safely and measure FAR/FRR before scaling. |
| Fallback | Explicit assisted-verification path, never a silent downgrade | Outages and accommodations must not become an auth bypass. |

## 3. Why this belongs in this demo

The repository already demonstrates the same governance pattern in a different
domain: **one enforcement point, a mapping table, and an append-only audit trail.**

| Existing demo concept | Webcam-login equivalent |
| --- | --- |
| `matter_authorization` mapping | `IDENTITY.role_assurance_policy` + session assurance level |
| Row access policy on `matter_id` | Assurance-gated roles; row access on identity tables |
| Masking policy on client PII | Masking of photo URIs and embeddings |
| `poc/access.py` enforcement point | `IDENTITY` verification service; one decision function |
| `audit_log` + Snowflake history | `login_attempt`, `verification_event`, `photo_audit`, hash chain |
| `GOV` evidence queries | Audit views over identity events and Snowflake `ACCESS_HISTORY` |

The important architectural rule is unchanged: **the application never decides
authorization by itself.** It produces a signed verification result; Snowflake
enforces the data boundary through roles and policies.

## 4. Scope, policy, and non-goals

### In scope

- Enrollment and re-enrollment of consenting employees.
- Webcam capture with liveness/anti-spoof checks and image-quality gates.
- 1:1 face verification with a confidence score and explicit reason codes.
- Encrypted photo retention with retention dates, legal hold, and access logging.
- Embedding generation, per-user centroid maintenance, drift monitoring, and model
  versioning.
- Mapping verification strength to RBAC roles and high-confidentiality matters.
- Audit evidence suitable for compliance review and incident investigation.

### Explicit non-goals

- Identifying an unknown person from a crowd or a photo gallery (1:N).
- Continuous camera monitoring, keystroke surveillance, or productivity scoring.
- Inferring emotion, health, age, gender, race, ethnicity, or religion.
- Training a face model on employee images without separate, explicit consent.
- Replacing MFA, password managers, or Snowflake's own authentication for
  administrative accounts.
- Using the raw photo as the authorization token. The token is the signed
  verification result; the photo is evidence.

## 5. Policy decisions the board must make

These are product and legal decisions, not engineering defaults. Record them in the
decision log before build.

| # | Decision | Options | Recommended default |
| --- | --- | --- | --- |
| P1 | Who must verify? | All staff / privileged roles only / opt-in | Privileged roles first (`COMPLIANCE_ADMIN`, `AUDITOR`, attorneys handling High matters) |
| P2 | Is participation voluntary? | Mandatory / voluntary with alternative | Voluntary where required by law; always provide an equivalent assisted path |
| P3 | Raw photo retention | 30 / 90 / 365 days / indefinite | 90 days, legal-hold override, automatic deletion job |
| P4 | Embedding retention | Session / employment / employment + 3 years | Employment + configured audit tail, then delete |
| P5 | Verification target | 1:1 self / 1:N employee directory | 1:1 only |
| P6 | Vendor | Self-hosted model / cloud biometric API | Decide after DPIA; self-hosted keeps images inside our boundary |
| P7 | Failure policy | Fail open / fail closed / assisted | Fail closed for privileged roles; assisted verification with two-person approval |
| P8 | Threshold policy | Single global / per-role strictness | Global floor + stricter step-up for High matters |
| P9 | Audit visibility | Compliance only / auditors / managers | Compliance + auditor; managers see outcome only, never embeddings or photos |
| P10 | Works council / union review | Required / not required | Confirm per jurisdiction before pilot |

## 6. User experience

### 6.1 Enrollment (once, then annually or on model upgrade)

1. User signs in with password + MFA and opens **Enroll face**.
2. Consent screen explains purpose, retention, who can view photos, the voluntary
   alternative, and how to withdraw. Record consent version and timestamp.
3. Browser requests camera permission; the page shows a live preview and a randomly
   selected challenge ("turn your head slightly left", "blink twice").
4. Capture 3–5 frames. Reject frames that fail quality or liveness and explain why.
5. Server generates embeddings, computes the centroid and intra-user distance
   distribution, and stores the template and centroid versions.
6. Show a confirmation with the enrollment date and a "re-enroll / withdraw" link.

### 6.2 Daily sign-in

1. Password + MFA succeed → short-lived pre-auth session (`AAL1`).
2. If the account or target role requires webcam verification, show the camera step.
3. Browser captures a fresh frame after a challenge. Include a nonce from the server
   and, where supported, device-attestation evidence.
4. Server runs quality → liveness → embedding → 1:1 comparison.
5. On accept, issue a session token carrying `verification_id`, `assurance_level`,
   `model_id`, `centroid_version`, and `verified_at`.
6. On review/deny, show a neutral message and the retry/assisted path. Do not reveal
   similarity scores or whether another person's face was involved.

### 6.3 Step-up for sensitive actions

Opening a High-confidentiality matter or entering the compliance console may require
a **fresh** verification (for example, within the last 5 minutes). Implement this as a
second verification event with its own audit record, not as a reused daily-login
result.

### 6.4 Failure paths

| Condition | User-visible result | Server action |
| --- | --- | --- |
| No camera / permission denied | "Camera unavailable" | Offer assisted verification; do not downgrade silently |
| Poor lighting / blur / multiple faces | Retry with guidance | Log quality failure without storing the rejected frame by default |
| Liveness fail | Retry once | Log spoof signal; rate-limit; escalate after repeated failures |
| Similarity in review band | "We could not verify you automatically" | Queue assisted review; do not accept |
| Similarity below threshold | Deny | Log reason; allow retry policy; lock after N attempts |
| Model/service outage | "Verification temporarily unavailable" | Fail closed for privileged roles; incident ticket |
| Suspected deepfake / virtual camera | Deny | Security alert, preserve evidence if policy allows |

## 7. Architecture

```text
Browser (getUserMedia, WASM liveness)
        |
        |  TLS, short-lived nonce, image bytes
        v
Auth / verification service  ---- signed event ---->  SIEM
        |        |
        |        +--> Face pipeline (detect -> align -> quality -> liveness -> embed)
        |                     |
        |                     +--> model version / threshold config
        |
        +--> Object storage (encrypted photos, Object Lock, 90-day lifecycle)
        |
        +--> Snowflake IDENTITY schema (templates, centroids, attempts, audit)
        |
        +--> IdP / token service (assurance claims -> Snowflake role)
```

### Components

| Component | Responsibility | Trust boundary |
| --- | --- | --- |
| Browser capture page | Camera permission, challenge UI, still capture | Untrusted client |
| Verification API | Nonce validation, rate limiting, orchestration, audit write | Trusted application |
| Face pipeline | Detection, alignment, quality, liveness, embedding, comparison | Trusted processing |
| Photo store | Encrypted object storage with lifecycle and Object Lock | Restricted access |
| Snowflake `IDENTITY` | Templates, centroids, verification metadata, audit | Governed data plane |
| IdP / token service | Short-lived session tokens with assurance claims | Identity control plane |
| SIEM | Real-time alerts for spoofing, drift, mass failures | Security operations |

### Deployment note

The face model is not a Snowflake-native function. Run it in a container service or
vendor API, then write only the resulting vector and metadata to Snowflake. If the
model runs outside Snowflake, encrypt vectors in transit and restrict the service
principal to `INSERT` on the `IDENTITY` tables it owns. Snowflake Cortex text
embeddings are **not** a face-embedding substitute.

## 8. Data model

The full DDL is in [`sql/identity/01_identity_verification.sql`](../sql/identity/01_identity_verification.sql).
The model separates **identity**, **biometric template**, **verification evidence**,
and **audit chain** so each can have its own retention and access policy.

| Table | Grain | Key fields | Notes |
| --- | --- | --- | --- |
| `employee_identity` | employee | `employee_id`, `status`, `consent_version`, `enrolled_at`, `model_id` | One active identity per employee |
| `consent_record` | consent event | `employee_id`, `consent_version`, `signed_at`, `method`, `withdrawn_at` | Append-only; withdrawal triggers deletion workflow |
| `face_template` | enrollment frame | `template_id`, `employee_id`, `model_id`, `embedding VECTOR(FLOAT,512)`, `quality_score`, `liveness_score`, `is_active` | Never expose raw vector to the app |
| `face_centroid` | employee + model | `employee_id`, `model_id`, `centroid VECTOR(FLOAT,512)`, `sample_count`, `intra_p50`, `intra_p95`, `version` | One current row per employee/model |
| `centroid_history` | centroid version | prior centroid, reason, actor, metrics | Enables rollback and drift review |
| `login_attempt` | attempt | `attempt_id`, `employee_id`, `outcome`, `similarity`, `threshold`, `liveness_score`, `quality_score`, `reason_code`, `photo_id`, `request_id`, `ip`, `user_agent` | Store decision, not just success |
| `photo_audit` | stored photo | `photo_id`, `stage_uri`, `sha256`, `captured_at`, `retention_until`, `legal_hold`, `deleted_at`, `key_id` | URI masked; deletion is a workflow, not a `DELETE` |
| `verification_event` | audit event | `event_id`, `prev_hash`, `event_hash`, `payload` | Append-only hash chain for tamper evidence |
| `photo_access_log` | view event | `photo_id`, `viewer`, `reason`, `approved_by`, `viewed_at` | Every human view of a raw photo |
| `role_assurance_policy` | role | `role_name`, `required_assurance`, `step_up_for_level` | Drives RBAC mapping |
| `model_registry` | model version | `model_id`, `pipeline_version`, `thresholds`, `activated_at`, `retired_at` | Pin versions; never mix silently |

### Why vectors and images are separate

- **Vectors** are small, queryable, and useful for monitoring drift. They live in
  Snowflake with masking and strict grants.
- **Images** are large, hard to delete from backups, and the highest-risk artifact.
  They live in encrypted object storage with lifecycle rules, Object Lock, and
  pre-signed access mediated by the verification service.
- **Audit events** are immutable and contain hashes and decision metadata, not
  embeddings or image bytes.

## 9. Generating embeddings

### 9.1 Model choice

Use a modern face-recognition embedding model that produces an **L2-normalized
512-dimensional vector**, such as an ArcFace/InsightFace-family model, or a vendor
verification API that returns a comparable similarity score. Record the exact model
and preprocessing versions. A model upgrade is a **new template generation**, not a
silent in-place change.

| Option | Pros | Cons | Fit |
| --- | --- | --- | --- |
| Self-hosted ArcFace/InsightFace | Images stay in our boundary; low per-check cost; full control | GPU/CPU ops, model supply-chain review, bias evaluation | Recommended for a firm with its own infrastructure |
| Cloud biometric API | Managed quality/liveness; less ML ops | Images leave boundary; vendor DPA, retention, and regional issues | Consider only after DPIA |
| Generic image embeddings | Easy | Not trained for identity; unacceptable FAR/FRR | Do not use |

### 9.2 Pipeline

1. **Decode** the captured image; reject malformed or oversized files.
2. **Detect** faces. Require exactly one face above the minimum pixel size.
3. **Align** using five landmarks to the model's canonical crop (commonly 112×112).
4. **Quality gate**: brightness, contrast, blur/Laplacian variance, pose yaw/pitch,
   occlusion, and inter-eye distance. Reject before embedding.
5. **Liveness**: passive anti-spoof score plus the server's challenge response. A
   still photo or replayed video must not pass.
6. **Embed**: normalized `float32[512]`.
7. **Compare** with cosine similarity against the active centroid and templates.
8. **Decide** and write the attempt, photo metadata, and audit event atomically where
   possible; if not atomic, reconcile with a request ID.

### 9.3 Quality and liveness gates (starting values)

| Signal | Minimum | Action on failure |
| --- | --- | --- |
| Face count | exactly 1 | Ask user to remove other people / reframe |
| Face width | ≥ 160 px | Ask user to move closer |
| Brightness | 0.25–0.85 (normalized) | Ask for better lighting |
| Blur (Laplacian variance) | model-specific floor | Ask user to hold still |
| Yaw / pitch | ≤ 20° / ≤ 15° | Ask user to face the camera |
| Passive liveness | ≥ 0.80 | Retry once, then deny and alert |
| Active challenge | exact match | Retry with a fresh nonce |

These are starting points. Calibrate against the chosen model, camera population, and
lighting conditions; record the calibration set and results in the model registry.

## 10. Maintaining the centroid

### 10.1 Definition

For one employee and one model version, the centroid is the L2-normalized mean of the
accepted enrollment embeddings. It is a compact representation of "this person under
this model," not a universal identity.

```text
c_0 = normalize(mean(e_1 ... e_n))          # enrollment
d_i = 1 - cosine(e_i, c_0)                 # intra-user distance
p50, p95 = percentiles(d_i)
suggested_threshold = clamp(1 - p95 - margin, floor, ceiling)
```

### 10.2 Update policy

Use a **bounded exponential moving average**, not an unbounded average that older
photos dominate forever.

```text
alpha_eff = max(alpha_min, 1 / (sample_count + 1))
c_new = normalize((1 - alpha_eff) * c_old + alpha_eff * e_accepted)
```

Starting values: `alpha_min = 0.05`, one update per successful login maximum, at most
three updates per day. Only update when **all** of the following are true:

- decision is `accept`, not `review`;
- similarity exceeds the accept threshold **plus** a safety margin;
- liveness and quality scores exceed their thresholds;
- the sample is not an outlier relative to the current centroid;
- no legal hold or account investigation is active.

### 10.3 Poisoning and drift guards

| Risk | Guard |
| --- | --- |
| One bad accepted frame pulls the centroid | Outlier gate: reject updates with distance above the user's p99 + margin |
| Repeated spoof attempts gradually shift the template | Require liveness; cap updates/day; alert on repeated spoof signals |
| Model drift or camera change | Cohort monitoring; per-user drift alert; compare centroid version to new samples |
| Insider or attacker with account access re-enrolls | Re-enrollment requires MFA + manager/compliance approval + cooling-off period |
| Silent model upgrade | New `model_id`; recompute centroids from active templates; old vectors retained for audit, not matching |
| Centroid corruption | Version history; rollback to prior version; checksum; two-person review for forced updates |

### 10.4 When to recompute rather than update

Recompute from the last N accepted templates when:

- the model version changes;
- the user re-enrolls;
- more than 30% of the active templates are older than the retention window;
- drift alerts persist after two consecutive updates;
- a compliance investigation requires a clean baseline.

### 10.5 Metrics to monitor

- Per-user and cohort similarity distributions.
- False accept rate (FAR), false reject rate (FRR), and equal error rate (EER) on the
  consented pilot.
- Failure reason mix (quality vs liveness vs match).
- Centroid drift magnitude and update frequency.
- Score distribution by camera type, lighting, and accessibility needs. Investigate
  disparities; do not use demographic attributes to adjust scores.

## 11. Verification decision

Use **cosine similarity** (or the model vendor's calibrated score) and three bands.
The numbers below are illustrative starting points for an ArcFace-family model; they
must be calibrated and approved before use.

| Band | Similarity | Outcome | User experience |
| --- | --- | --- | --- |
| Accept | ≥ 0.68 | `accept` | Sign in with required assurance |
| Review | 0.58–0.679 | `review` | Assisted verification; never auto-accept |
| Deny | < 0.58 | `deny` | Neutral failure, retry policy, security log |

Additional rules:

- **Liveness or quality failure overrides the similarity score.** A high score on a
  spoof is still a deny.
- **Multiple frames**: capture 3 frames and require at least 2 acceptable matches; use
  the median similarity for the decision to reduce single-frame noise.
- **Score secrecy**: return only the decision and a generic reason code to the
  browser. Detailed scores belong in the audit record.
- **Rate limits**: per account, per IP, and per device. Exponential backoff after
  repeated failures; alert on distributed attempts.
- **No enumeration**: do not reveal whether an account exists, whether enrollment is
  complete, or whether a face matched a different template.

## 12. RBAC and session integration

### 12.1 Assurance levels

| Level | Factors | Typical use |
| --- | --- | --- |
| `AAL1` | Password + MFA | Low-risk read-only views |
| `AAL2` | AAL1 + successful webcam 1:1 verification | Attorneys, paralegals, auditors |
| `AAL3` | AAL2 + fresh step-up + device attestation / managed device | Compliance admin, break-glass, High matters |

### 12.2 Role mapping (starting point)

| Snowflake role | Required assurance | Step-up |
| --- | --- | --- |
| `PARALEGAL` | `AAL2` | On High-confidentiality matters |
| `ATTORNEY` | `AAL2` | On High-confidentiality matters |
| `AUDITOR` | `AAL2` | Never gets raw-photo access without break-glass |
| `COMPLIANCE_ADMIN` | `AAL3` | Fresh verification for policy changes |
| `DEMO_ADMIN` | `AAL3` + managed device | Build/administration only |

### 12.3 Snowflake enforcement

Use **external OAuth** or a governed token exchange so the application never holds a
user's Snowflake password. The token service asserts the assurance level; map it to a
distinct Snowflake role or entitlement.

```text
AAL2 verified  -> grant ATTORNEY_AAL2  (inherits ATTORNEY read grants)
AAL3 verified  -> grant COMPLIANCE_ADMIN_AAL3
No verification -> only low-risk AAL1 role; no matter rows
```

Implementation rules:

1. **Do not trust a client-supplied `assurance_level` header.** Read it from the
   signed token or a server-side verification record.
2. **Bind the token to the verification event.** Include `verification_id`,
   `model_id`, `centroid_version`, `verified_at`, and a short expiry.
3. **Re-check freshness for step-up actions** (for example, verification within the
   last 5 minutes).
4. **Use Snowflake row access policies** for matter confidentiality as already
   designed; add an assurance predicate only through roles/entitlements, not through
   unverified session text.
5. **Revoke on separation or incident**: disable the identity, revoke tokens, delete
   or tombstone templates per retention policy.
6. **Break-glass**: time-bound, two-person approval, explicit reason, full audit, and
   a post-incident review. Break-glass is not a silent fallback.

### 12.4 Access to biometric data

| Role | Own metadata | Own photo | Any raw photo | Embeddings | Audit events |
| --- | --- | --- | --- | --- | --- |
| Employee | Read | Request/download own, time-limited | No | No | Own outcomes |
| Manager | Read outcome | No | No | No | Team outcomes only |
| `AUDITOR` | Read | No | Break-glass only | Masked / aggregate | Read |
| `COMPLIANCE_ADMIN` | Read | Yes, with reason | Yes, with reason | Read | Read |
| Application service | Insert/update own records | Write via scoped credential | No human access | Write | Append |
| `ACCOUNTADMIN` | Emergency only | Emergency only | Emergency only | Emergency only | Emergency only |

Every human view of a raw photo writes a `photo_access_log` row with a reason and,
for break-glass, an approver.

## 13. Audit, retention, and deletion

### 13.1 What to record

For every attempt:

- `attempt_id`, `request_id`, `employee_id` (or a pseudonymous key), timestamp in UTC.
- Outcome and reason code; similarity, threshold, liveness, and quality scores.
- Model ID, pipeline version, centroid version, threshold version.
- Photo ID, SHA-256 hash, storage URI (masked), encryption key ID.
- IP address, user agent, device-attestation result, ASN/geo if policy allows.
- Session ID and the resulting assurance level.

For every photo view or deletion: who, when, why, approval, and ticket reference.

### 13.2 Integrity

- Append-only tables; revoke `UPDATE`/`DELETE` from application roles.
- Hash-chain each `verification_event` (`event_hash = SHA256(prev_hash || canonical_payload)`).
- Periodically anchor the chain head in an immutable store (Object Lock or a signed
  export) and verify it in CI or a scheduled job.
- Store photos with Object Lock / WORM where available; lifecycle deletion must be
  blocked while `legal_hold = TRUE`.
- Use Snowflake `ACCESS_HISTORY` and `QUERY_HISTORY` as independent evidence that
  identity tables were accessed by authorized roles.

### 13.3 Retention schedule (defaults, subject to legal review)

| Artifact | Default retention | Trigger for earlier deletion |
| --- | --- | --- |
| Raw login photo | 90 days | Consent withdrawal, erasure request, successful appeal |
| Enrollment photos | Life of employment + 90 days | Separation + audit tail, withdrawal |
| Face template / embedding | Life of employment + configured audit tail | Separation, withdrawal, model retirement |
| Login attempt metadata | 2 years | Investigation hold |
| Audit hash chain | 7 years | Legal requirement |
| Photo access log | 7 years | Legal requirement |
| Model registry | Life of system + 3 years | None |

### 13.4 Deletion and legal hold

1. Deletion requests enter a workflow, not a direct `DELETE`.
2. Check `legal_hold` and open investigations; if held, suspend deletion and notify
   the requester.
3. Delete the object from the photo store; mark `photo_audit.deleted_at`; retain the
   hash and audit row to prove deletion.
4. Delete or irreversibly anonymize embeddings and centroids; keep aggregate metrics.
5. Run a verification job and record the result. Backups follow the same schedule;
   document the maximum backup lag.

## 14. Compliance and privacy

This is a high-risk feature. The following are **requirements**, not suggestions.

| Area | Requirement |
| --- | --- |
| Legal basis / consent | Written, informed consent where required (for example, Illinois BIPA, Texas CUBI, Washington). Provide a genuine alternative and no retaliation. |
| Notice | Explain purpose, data categories, retention, recipients, and rights before the first capture. |
| DPIA / risk assessment | Complete before pilot; update on model, vendor, or retention changes. |
| Data minimization | Capture only what is needed; do not store rejected frames by default; do not collect emotion or demographic data. |
| Purpose limitation | Authentication and audit only; no performance monitoring or marketing. |
| Vendor management | DPA, subprocessor list, security attestations, deletion terms, breach notification, cross-border transfer mechanism. |
| Access control | Least privilege, two-person access for raw photos, break-glass with audit. |
| Security | TLS 1.3, encryption at rest with customer-managed keys, key rotation, secret management, vulnerability scanning, signed model artifacts. |
| Bias and accessibility | Evaluate error rates across lighting, camera, age, and accessibility needs; provide assisted verification; never use protected attributes to adjust scores. |
| AI governance | Model card, intended use, evaluation results, human oversight, change control, incident response. Check EU AI Act and local workplace-biometric rules with counsel. |
| Data subject rights | Access, correction, deletion, withdrawal, and appeal process with a service-level target. |
| Incident response | Spoofing, data breach, model compromise, and mass false-reject playbooks; regulatory notification timeline. |
| Employment law | Confirm voluntariness, works council/union consultation, and non-retaliation with counsel. |

> **Jurisdictional note.** Biometric-privacy statutes differ materially. Some require
> written release and a retention schedule; some restrict employer collection; some
> require a private right of action notice. Do not treat this table as a legal opinion.

## 15. Threat model and controls

| Threat | Example | Controls |
| --- | --- | --- |
| Presentation attack | Printed photo, phone screen, mask | Passive liveness, active challenge, depth/IR where available, replay nonce |
| Deepfake / virtual camera | Injected video stream | Device attestation, virtual-camera detection, challenge freshness, anomaly alerts |
| Replay of a prior capture | Reusing an old image | Server nonce, short expiry, bind to session, reject reused image hash |
| Stolen password / session | Attacker has credentials | MFA + webcam step-up, impossible-travel alerts, session binding, fresh step-up for sensitive actions |
| Insider photo access | Employee browses audit photos | Masked URIs, scoped service credential, two-person approval, `photo_access_log` |
| Embedding inversion | Reconstructing a face from a vector | Treat vectors as biometric; encrypt, mask, restrict; no external sharing |
| Centroid poisoning | Repeated accepted spoofs shift template | Liveness, outlier gate, update caps, drift alerts, re-enrollment approval |
| Model supply chain | Malicious model weights | Pin hashes, signed artifacts, isolated inference, dependency review |
| Denial of service | Camera or model outage | Queue, timeouts, status page, fail-closed for privileged roles, assisted path |
| Fallback abuse | Attacker triggers manual path | Two-person approval, reason codes, rate limits, audit review |
| Data exfiltration | Bulk export of templates | Least privilege, query monitoring, egress controls, no `SELECT *` grants |
| Race condition | Two enrollments overwrite each other | Optimistic concurrency on `version`; transaction; idempotency key |

## 16. API contracts

All endpoints require TLS and return `request_id`. Errors use stable codes and do not
leak match details.

### `POST /v1/enrollment/start`

```json
{ "consent_version": "2026-10-20", "device": { "attestation": "..." } }
```

Returns `enrollment_id`, `challenge` (type, nonce, expires_at), and capture guidance.

### `POST /v1/enrollment/capture`

```json
{ "enrollment_id": "...", "challenge_nonce": "...", "image": "<base64 or multipart>" }
```

Returns `accepted`, `quality`, `liveness`, and `frames_remaining`. Rejected frames are
not retained by default.

### `POST /v1/enrollment/complete`

Returns `template_id`, `centroid_version`, `model_id`, `enrolled_at`, and the suggested
next re-enrollment date. Requires at least three accepted frames.

### `POST /v1/login/verify`

```json
{
  "preauth_token": "...",
  "challenge_nonce": "...",
  "image": "<base64 or multipart>",
  "device": { "attestation": "..." }
}
```

Returns:

```json
{
  "decision": "accept",
  "assurance_level": "AAL2",
  "verification_id": "...",
  "expires_at": "2026-10-20T09:35:00Z",
  "reason_code": "MATCH"
}
```

`review` and `deny` return no similarity score. Include `retry_after_seconds` and a
support reference.

### `POST /v1/admin/photos/{photo_id}/access`

Requires `COMPLIANCE_ADMIN` or break-glass; body includes `reason`, `ticket`,
`approver_id`. Returns a short-lived pre-signed URL and writes `photo_access_log`.

## 17. Reference implementation

[`poc/face_verification.py`](../poc/face_verification.py) is a dependency-free
reference for the deterministic parts of the design:

- L2 normalization and cosine similarity.
- Centroid construction and intra-user percentile statistics.
- Bounded EMA centroid updates with poisoning guards and update caps.
- Quality and liveness gates.
- Three-band accept/review/deny decisions.
- A hash-chained audit event helper.
- A deterministic `HashingEmbedder` for tests only.

It deliberately does **not** include a real face model, camera capture, storage, or
network calls. Replace `HashingEmbedder` with the chosen model's inference call and
keep the same decision and audit interfaces. Run the tests with:

```bash
python3 -m unittest poc/test_face_verification.py -v
```

Mapping to production:

| Reference symbol | Production equivalent |
| --- | --- |
| `l2_normalize`, `cosine_similarity` | Model output normalization / vendor score |
| `build_centroid`, `intra_user_stats` | Enrollment service writing `face_centroid` |
| `plan_centroid_update` | Post-login updater with the guard table in §10.3 |
| `quality_gate`, `liveness_gate` | Face pipeline quality/liveness stage |
| `verify_embedding` | Verification decision service |
| `AuditChain` | `verification_event` append + hash anchor |
| `HashingEmbedder` | ArcFace/InsightFace or vendor inference |

## 18. Rollout plan

| Phase | Work | Exit criteria |
| --- | --- | --- |
| 0 — Legal & design | DPIA, consent text, retention schedule, vendor selection, works council review, threat model | Signed approvals; no real captures yet |
| 1 — Sandbox | Synthetic/pilot-consented data; model evaluation; threshold calibration; DDL applied | FAR/FRR targets met; audit chain verified; deletion tested |
| 2 — Pilot | 20 consenting employees; both camera types; accessibility testing; assisted path | ≥ 99% completion for consenting users with support; no unaddressed bias signal |
| 3 — Privileged roles | `COMPLIANCE_ADMIN`, `AUDITOR`, High-matter attorneys; step-up for sensitive actions | RBAC matrix passes; break-glass drill passes |
| 4 — General rollout | All required staff; training; support runbook; quarterly access review | Operational SLOs met; incident playbook exercised |
| 5 — Continuous | Model/drift monitoring, threshold review, retention jobs, audits | Quarterly report to the board |

### Suggested SLOs

| Metric | Target |
| --- | --- |
| Verification latency (p95) | < 2.5 s excluding user challenge |
| Availability (privileged login path) | 99.9% monthly |
| False accept rate | Below the approved risk appetite (calibrate; never guess) |
| False reject rate | Below the approved support threshold |
| Audit event write success | 100% of decisions; alert on any gap |
| Photo deletion job | 100% before retention deadline; alert on failures |

### Rollback

1. Disable the webcam requirement for the affected role cohort.
2. Keep audit records and templates; do **not** delete evidence during an incident.
3. Revert to the prior model/threshold version using `model_registry`.
4. Notify affected users and support; document the rollback reason and duration.
5. Re-enable only after the root cause and a fresh DPIA review, if scope changed.

## 19. Cost sketch

| Item | Assumption | Order of magnitude |
| --- | --- | --- |
| Face inference | 1 CPU/GPU service, low volume | $50–$300/month self-hosted; vendor per-check pricing otherwise |
| Photo storage | 500 employees × ~200 KB × 90 days | < $5/month at object-storage rates |
| Snowflake | Vectors and audit rows are tiny; X-Small warehouse | Existing demo footprint; likely < $20/month incremental |
| Engineering | Capture UI, service, model integration, DDL, audit, tests | 4–6 weeks for a production-grade pilot |
| Legal/DPIA | External counsel and vendor review | Budget separately; do not skip |

## 20. Open decisions for the board

1. Is participation mandatory, voluntary, or role-based? What is the approved
   alternative for employees who decline or cannot use a camera?
2. Self-hosted model or vendor API? If vendor, which regions and retention terms?
3. What is the approved raw-photo retention period, and who can approve legal hold?
4. Which roles require `AAL2` vs `AAL3`, and which matters require fresh step-up?
5. What are the FAR/FRR risk-appetite targets, and who signs off on calibration?
6. Should re-enrollment require manager approval, compliance approval, or both?
7. What is the break-glass procedure and who are the two approvers?
8. Which jurisdictions are in the pilot, and what additional notice/consent is needed?

## 21. Acceptance checklist

- [ ] Legal review, DPIA, consent text, and retention schedule approved.
- [ ] Vendor DPA and security review complete (if applicable).
- [ ] DDL applied and `IDENTITY` schema grants reviewed.
- [ ] Real model integrated behind the reference interface; model hash pinned.
- [ ] Enrollment captures ≥ 3 frames with quality and liveness gates.
- [ ] Verification returns accept/review/deny with reason codes and no score leakage.
- [ ] Centroid update guards, caps, versioning, and rollback tested.
- [ ] RBAC mapping and step-up enforced server-side; client claims ignored.
- [ ] Raw photos encrypted, access-logged, retention-scheduled, and deletable.
- [ ] Audit hash chain verified; deletion and legal-hold workflows tested.
- [ ] FAR/FRR and accessibility results reviewed; assisted path exercised.
- [ ] Incident, break-glass, and rollback drills completed.
- [ ] Board approval recorded before enabling for real employees.

---

**Framing for this repository.** This design belongs to the same fictional,
board-review staging environment as the rest of the demo. Do not use real employee
photos or real client data here. If the board approves a pilot, run it in a separate,
production-governed Snowflake account with real consent records and legal review.
