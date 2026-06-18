# EduCore LMS v1.2 — Premium Production Technical Specification

**Document type:** Engineering + Product Technical Specification
**Version:** 1.2 (supersedes v1.0 MVP)
**Status:** Design / Pre-implementation
**Owner roles:** CTO · Product Architect · Senior Full-Stack Eng · EdTech Strategist · QA Lead · Security Architect
**Date:** 2026-06-18

---

## Table of Contents

1. [Product Vision](#1-product-vision)
2. [User Roles and Permissions](#2-user-roles-and-permissions)
3. [Role-Based User Journeys](#3-role-based-user-journeys)
4. [Feature Scope for v1.2](#4-feature-scope-for-v12)
5. [Out of Scope for v1.2](#5-out-of-scope-for-v12)
6. [Future-Ready Architecture](#6-future-ready-architecture)
7. [Backend Domain Architecture](#7-backend-domain-architecture)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Telegram Bot Architecture](#9-telegram-bot-architecture)
10. [Database Entity Design](#10-database-entity-design)
11. [API Design Principles](#11-api-design-principles)
12. [Authentication and Authorization Design](#12-authentication-and-authorization-design)
13. [Caching and Performance Strategy](#13-caching-and-performance-strategy)
14. [Security and Audit Strategy](#14-security-and-audit-strategy)
15. [Analytics Strategy](#15-analytics-strategy)
16. [Risk Assessment and Mitigation Plan](#16-risk-assessment-and-mitigation-plan)
17. [QA / Test Plan](#17-qa--test-plan)
18. [Acceptance Criteria](#18-acceptance-criteria)
19. [90-Day Implementation Roadmap](#19-90-day-implementation-roadmap)
20. [Premium UX Guidelines for Desktop and Mobile](#20-premium-ux-guidelines-for-desktop-and-mobile)

---

## How to read this document

This spec is written to be directly actionable by an engineering team. It assumes the existing v1.0 stack (FastAPI · React · PostgreSQL · JWT · RBAC · Telegram bot) and describes a **refactor + expansion**, not a rewrite. Where v1.0 already has a working module, the spec marks it **[evolve]**; new modules are marked **[new]**.

The guiding principle throughout: **the backend is the single source of truth for authorization and data scope. The frontend never decides who can see what — it only renders what the backend is willing to return.** Every painful problem in the v1.0 audit traces back to violating that principle.

---

## 1. Product Vision

### 1.1 One-line vision

EduCore v1.2 is a premium, role-separated operating system for learning centers — combining a sales-and-operations CRM for administrators with genuine learning experiences for students, teaching tools for instructors, and progress visibility for parents, unified across responsive web and Telegram, and architected so AI, Face ID attendance, and native mobile apps can be added without a rewrite.

### 1.2 The problem we are solving

Learning centers today juggle spreadsheets, paper attendance, manual payment chasing, and disconnected chat groups. v1.0 proved the data model works but exposed three classes of failure that block monetization as a premium product:

- **Trust failures** — data leaks between roles and sessions destroy the one thing a paid B2B tool must guarantee: that a parent sees only their child, a teacher sees only their groups, and a student never sees admin finances.
- **Value failures** — the LMS is too thin to make students or parents *want* to log in. Without roadmaps, tests, and growth analytics, the product is a glorified attendance sheet.
- **Operational failures** — admins can record data but cannot *run a business*: no sales pipeline, no debt control, no retention signals.

v1.2 attacks these in priority order.

### 1.3 Vision pillars

1. **Four products, one platform.** Admin, Teacher, Student, and Parent are not "views" of one UI — they are four distinct experiences sharing one secure backend. Each role sees only its own mental model.
2. **Security and isolation are features, not chores.** Tenant + role + ownership scoping is enforced at the data layer, audited, and testable.
3. **Learning that earns return visits.** Roadmaps, tests, weak-topic detection, badges, and growth trends give students and parents a reason to open the app weekly.
4. **A CRM that runs the business.** Leads → trials → enrollment → retention → debt control, with the numbers an owner checks every morning.
5. **Fast and calm.** Sub-second role dashboards, paginated tables, background-processed analytics, and clear loading/empty/error/forbidden states. Premium feels *quiet and instant*.
6. **Future-ready by construction.** AI, Face ID, native apps, multi-branch SaaS, and payment gateways are anticipated as clean extension points, not retrofits.

### 1.4 Target users and buyer

- **Buyer / champion:** learning-center owner or operations manager (the Admin). They pay the subscription and judge ROI by revenue captured, debt reduced, and churn avoided.
- **Daily power users:** teachers (must save time, not add work) and admins/managers.
- **Engagement users:** students and parents (must perceive value to justify the center's subscription and reduce churn).

### 1.5 Success metrics (product-level)

| Metric | v1.0 baseline | v1.2 target |
|---|---|---|
| Cross-role data leak incidents | Known issues | **Zero** (hard gate) |
| Teacher daily active usage | Low | ≥ 80% of teachers mark attendance in-app daily |
| Student weekly active usage | ~None | ≥ 50% open app or bot weekly |
| Parent monthly active usage | ~None | ≥ 60% view child progress monthly |
| Debt collection cycle | Manual | Automated reminders; measurable debt-day reduction |
| Role dashboard load (p95) | Unmeasured | < 1.5s on mid-tier mobile |
| Lead → enrollment conversion visibility | None | Full funnel analytics |

---

## 2. User Roles and Permissions

### 2.1 Role catalog

| Role | Scope | Primary purpose | v1.2 status |
|---|---|---|---|
| **Super Admin** | Platform (all orgs) | SaaS operator; provisions organizations, global settings, billing of the SaaS itself | **Foundation only** (role exists, guarded; full tooling deferred) |
| **Admin** (Org Owner) | One organization, all branches | Full operational + financial control of their center | Active |
| **Manager** | One or more branches | Operations subset of Admin — no destructive/org-config powers | Active |
| **Teacher** | Assigned groups/students | Teaching operations: lessons, attendance, tests, student analytics | Active |
| **Student** | Self only | Learning experience | Active |
| **Parent** | Linked children only | Monitoring experience | Active |

> **Design rule:** roles are *coarse* (the six above). Fine-grained differences (e.g., a teacher granted a second group) are handled by **scope grants**, not by inventing new roles.

### 2.2 Three-layer authorization model

Every request is authorized by the conjunction of three checks. **All three must pass.**

1. **Tenant scope** — `organization_id` (and where relevant `branch_id`) on the JWT must match the resource's org/branch. Cross-tenant access is impossible by construction (every scoped table carries `organization_id`).
2. **Role permission** — does this role hold the permission for this action? (e.g., `payment:write`, `test:create`, `student:read`).
3. **Ownership / relationship scope** — even with the permission, can this *specific* actor touch this *specific* row? (Teacher → only assigned groups; Parent → only linked children; Student → only self.)

```
authorized = same_tenant(actor, resource)
           AND role_has_permission(actor.role, action)
           AND ownership_scope_allows(actor, resource)
```

### 2.3 Permission matrix (representative, not exhaustive)

Legend: **F** = full (CRUD within scope) · **R** = read within scope · **own** = own/linked records only · **—** = no access · **(b)** = background/automated only.

| Capability | Super Admin | Admin | Manager | Teacher | Student | Parent |
|---|---|---|---|---|---|---|
| Manage organizations / branches | F | branch R/limited | R | — | — | — |
| Manage users & roles | F | F (org) | partial | — | — | — |
| Leads & sales pipeline | R | F | F | — | — | — |
| Student CRM records | R | F | F | R (assigned) | own | own (child) |
| Teacher records | R | F | R | own profile | — | R (their teachers, limited) |
| Groups & schedules | R | F | F | R/own | R (enrolled) | R (child's) |
| Courses & roadmap definitions | R | F | F | R, propose | R (enrolled) | R (child's) |
| Attendance — mark | — | F | F | F (own groups) | — | — |
| Attendance — view | R | F | F | own groups | own | own (child) |
| Tests — create/assign | — | F | F | F (own groups) | — | — |
| Tests — take | — | — | — | — | F (assigned) | — |
| Test results — view | R | F | F | own groups | own | own (child) |
| Payments & invoices — manage | R | F | F | — | — | — |
| Payments — view | R | F | F | — | own | own (child) |
| Financial reports / revenue | R | F | F (branch) | — | — | — |
| Analytics — org-wide | R | F | F (branch) | — | — | — |
| Analytics — student/group | R | F | F | own groups | own | own (child) |
| Notifications — broadcast | F | F | F | own groups | — | — |
| Audit log — view | F | F (org) | limited | — | — | — |
| Settings — org config | R | F | partial | — | — | — |
| Telegram linking | self | self | self | self | self | self |

> **Manager vs Admin:** Manager is Admin minus org configuration, minus user-role assignment beyond their branch, minus destructive deletes, minus cross-branch financial consolidation. Encoded as a permission set, enforced server-side.

### 2.4 Scope grant mechanism

A `scope_grant` record can extend a user's default ownership scope (e.g., grant a teacher read access to another group, or a manager to a second branch). Grants are explicit, time-boundable, audited, and never widen the *role's* permission set — only the *rows* in scope. This avoids role proliferation while keeping least-privilege auditable.

---

## 3. Role-Based User Journeys

Each journey below is the "happy path" plus the critical guard states (forbidden, empty, error) that v1.0 lacked.

### 3.1 Admin / Manager — "Run the center this morning"

1. **Login** → MFA-optional → lands on **Admin Dashboard** scoped to their org (and selected branch).
2. Sees the morning KPIs: today's revenue, MTD revenue, outstanding debt, active students, new leads, conversion rate, attendance rate, at-risk students, teacher workload, group performance, payment-reminder queue.
3. **Triage debt:** clicks "Outstanding debt" → filtered, paginated invoice list → bulk-selects overdue → "Send reminder" (queues Telegram + notification jobs) → action audited.
4. **Work the pipeline:** opens Sales board → drags a lead from *Trial* to *Enrolled* → conversion modal creates a Student from the lead, links parent, assigns group → audited.
5. **Spot risk:** "At-risk students" widget → drills into a student whose attendance + test trend dropped → assigns follow-up.
6. **Report:** exports a filtered payment/attendance report to CSV.

Guard states: a Manager attempting org-config sees a **forbidden** panel with explanation, not a blank page; an empty pipeline column shows an onboarding hint; a failed report shows a retryable error.

### 3.2 Teacher — "Teach today's groups"

1. **Login** → **Teacher Dashboard**: today's groups, attendance to mark, tests to review, low-performing students, group progress, lesson materials, quick test creation.
2. **Mark attendance:** taps today's group → roster loads → "Mark all present" → toggles 2 absences with reason → save (single request, optimistic UI) → audited.
3. **Assign a test:** opens Tests → picks from question bank or quick-creates 5 MCQs → assigns to group with deadline → students + parents notified via background job.
4. **Review & coach:** results dashboard auto-grades objective questions → flags weak topics across the group → teacher leaves a note on a struggling student (visible to that student + their parent only).
5. Teacher **cannot** see revenue, other teachers' groups, or any student outside assignment — those routes return forbidden and the nav never renders them.

### 3.3 Student — "Learn and track my growth"

1. **Login** → **Student Dashboard**: today's lessons, assigned tests, learning roadmap, progress %, weak topics, latest result, attendance summary, achievement badges.
2. **Follow the roadmap:** sees course as a sequence of milestones with completion + test checkpoints; current milestone highlighted; next action obvious.
3. **Take an assigned test:** timer (if set) → submit → objective portion auto-graded instantly → result + which topics to revisit.
4. **See growth:** personal analytics trend (scores over time, attendance, milestone completion), badges earned.
5. **Check logistics:** payment status (own only), attendance history, notifications.
6. Student sees **no other student**, no teacher admin data, no finances beyond their own balance.

### 3.4 Parent — "Is my child okay?"

1. **Login** (or open Telegram) → **Parent Dashboard** with a child switcher (if multiple linked children).
2. **Child overview:** attendance, latest test results, progress trend, payment/debt status, teacher notes, alerts.
3. **Act on debt:** sees outstanding balance + due date + "how to pay" instructions; receives reminders via web + Telegram.
4. **Stay informed:** alerts for absences, low scores, upcoming tests, and teacher feedback.
5. Parent sees **only linked children** — never other children, never the teacher's full roster, never org finances.

### 3.5 Cross-cutting journey — logout / role switch (the v1.0 bug class)

On logout: tokens revoked server-side; **entire client query cache, persisted store, and in-memory state cleared**; redirect to login. On a *different* user logging in on the same device: a fresh cache namespace keyed by `userId+role` guarantees zero carryover. This is a first-class, tested journey — see §13.4 and §17.

---

## 4. Feature Scope for v1.2

Scope is organized by domain. Each item is tagged **[new]** or **[evolve]** relative to v1.0.

### 4.1 Admin CRM
- Lead management with statuses: `new → contacted → trial → enrolled / lost` **[new]**
- Lead source tracking and per-source conversion analytics **[new]**
- Lead → Student conversion (carries history, links parent, assigns group) **[new]**
- Student profile with full history (groups, attendance, payments, tests, roadmap, notes) **[evolve]**
- Teacher profile (assignments, schedule, workload, performance) **[evolve]**
- Group profile (roster, schedule, progress, performance) **[evolve]**
- Payment & debt tracking with statuses **[evolve]**
- Parent linking (one parent ↔ many children; one child ↔ many guardians) **[new]**
- Reports with filters + CSV import/export **[new]**

### 4.2 Sales
- Sales pipeline board (Kanban by status) **[new]**
- Source tracking **[new]**
- Conversion analytics (funnel, by source, by period) **[new]**
- Follow-up reminders (scheduled, assigned) **[new]**
- Trial lesson tracking (scheduled, attended, outcome) **[new]**

### 4.3 Students
- Personal dashboard **[new]**
- Profile, groups, schedule **[evolve]**
- Attendance history (own) **[evolve]**
- Payments (own) **[evolve]**
- Assigned tests + attempts + results **[new]**
- Progress %, weak topics, growth analytics **[new]**
- Learning roadmap + achievement milestones/badges **[new]**
- Parent links **[new]**

### 4.4 Teachers
- Teacher workspace dashboard **[new]**
- Profile, assigned groups, schedule **[evolve]**
- Lesson control (mark lesson taught, attach materials) **[new]**
- Attendance marking (fast, bulk, late/absent + reason) **[evolve]**
- Test creation (question bank, MCQ, optional open) **[new]**
- Test assignment to group/student **[new]**
- Result review + weak-topic analytics + weak-student identification **[new]**
- Student/group progress analytics **[new]**
- Lesson materials management **[new]**

### 4.5 Tests
- Question bank (reusable, tagged by topic/difficulty) **[new]**
- Multiple-choice (auto-graded); open/manual questions optional (teacher-graded) **[new]**
- Test assignment to group or individual, with open/close windows **[new]**
- Test attempt tracking (start, submit, time spent, one-attempt or N-attempts) **[new]**
- Auto grading for objective questions **[new]**
- Results dashboard (per student, per group, per question) **[new]**
- Weak-topic analytics (aggregate by topic tag) **[new]**

### 4.6 Learning Roadmap
- Course roadmap definition (ordered milestones) **[new]**
- Milestones with lesson completion + test checkpoints **[new]**
- Achievement status / badges **[new]**
- Student-facing progress view **[new]**

### 4.7 Attendance
- Fast marking UI; bulk "mark all present" **[evolve]**
- Late / absent / present / excused statuses + comment/reason **[evolve]**
- Teacher-based attendance tied to lesson sessions **[evolve]**
- **Abstraction layer** so a future Face ID provider can post attendance through the same domain service **[new]**

### 4.8 Payments
- Monthly invoice generation **[evolve]**
- Paid / partial / unpaid / overdue statuses **[evolve]**
- Debt tracking + aging **[new]**
- Receipts **[new]**
- Reminders (web + Telegram, scheduled jobs) **[new]**
- Parent notification on due/overdue **[new]**
- **Payment-gateway-ready abstraction** (provider interface, no live gateway in v1.2) **[new]**

### 4.9 Telegram Bot
- Secure phone-based account linking **[evolve]**
- Role-based menus (student / parent / teacher / admin) **[new]**
- Student: schedule, tests, results, attendance, payments
- Parent: child progress, attendance, debt, alerts
- Teacher: today's groups, attendance reminders, test notifications
- Admin: key alerts, debt summary, attendance issues
- Internal bot API secured by service token + per-user linkage **[evolve]**

### 4.10 Analytics
- Student growth analytics **[new]**
- Group performance **[new]**
- Teacher performance **[new]**
- Attendance trend **[new]**
- Payment/debt trend **[new]**
- Sales funnel **[new]**
- At-risk student detection foundation (rule-based scoring; AI-ready) **[new]**

### 4.11 Platform / cross-cutting
- Strict role-based routing + nav per role **[new]**
- Cache isolation by user+role; full logout purge **[new]**
- Audit log for all sensitive actions **[new]**
- Background job runner (reminders, reports, analytics, notifications) **[new]**
- Responsive desktop + mobile layouts (not shrunk desktop) **[evolve]**
- API versioning `/api/v1` **[evolve]**
- Organization/branch tenancy foundation on every scoped table **[new]**
- File/media storage abstraction (local dev → S3/MinIO prod) **[new]**

---

## 5. Out of Scope for v1.2

Explicitly **not** built in v1.2 (but architected for — see §6). Deferring these is what keeps v1.2 shippable and premium rather than broad and shallow.

| Deferred capability | Why deferred | Kept ready by |
|---|---|---|
| Live AI tutor / AI quiz generation / AI recommendations | Needs stable data + content first | Clean topic-tagged data model, service interfaces, event log |
| Face ID attendance (actual biometrics) | Hardware + privacy + vendor selection | Attendance ingestion abstraction (§4.7) |
| Native iOS / Android apps | Web + bot cover v1.2 reach | Pure JSON REST API, no server-rendered coupling |
| Web/native push notifications | Telegram + in-app cover v1.2 | Notification domain with pluggable channels |
| Live payment gateway integration | Region/provider selection pending | Payment provider interface (§4.8) |
| Full multi-branch SaaS billing / Super Admin console | One org per deployment suffices now | `organization_id`/`branch_id` on all tables; Super Admin role guarded |
| Certificates, video lessons, parent-teacher chat | Value-add, not core pain | File storage abstraction; messaging-ready notification core |
| Advanced BI / custom report builder | Fixed reports cover v1.2 | Analytics aggregation tables + event stream |

**Scope discipline rule:** a feature enters v1.2 only if it serves one of the nine prioritized pains (§ Important). Everything else is logged to the v1.3+ backlog.

---

## 6. Future-Ready Architecture

### 6.1 High-level topology

```
                    ┌─────────────────────────────────────────────┐
                    │                Clients                       │
                    │  Web SPA (React/Next) · Telegram Bot ·        │
                    │  (future) iOS · Android · Face ID device      │
                    └───────────────┬─────────────────────────────┘
                                    │ HTTPS / JSON (REST, /api/v1)
                    ┌───────────────▼─────────────────────────────┐
                    │            API Gateway / Edge                │
                    │  TLS · CORS · rate limit · request ID ·      │
                    │  auth middleware (JWT verify, tenant inject) │
                    └───────────────┬─────────────────────────────┘
                                    │
        ┌───────────────────────────▼───────────────────────────────┐
        │              FastAPI Application (modular monolith)        │
        │  ┌────────────────────────────────────────────────────┐  │
        │  │  Domain modules (independent packages, §7)          │  │
        │  │  auth · users · org · crm · students · teachers ·   │  │
        │  │  groups · courses · lessons · tests · attempts ·    │  │
        │  │  attendance · payments · notifications · telegram · │  │
        │  │  analytics · audit · settings · files               │  │
        │  └────────────────────────────────────────────────────┘  │
        │  Cross-cutting: authz engine · tenant context · event bus │
        └───┬────────────┬───────────────┬──────────────┬──────────┘
            │            │               │              │
     ┌──────▼───┐  ┌─────▼─────┐  ┌──────▼──────┐ ┌─────▼──────┐
     │PostgreSQL│  │   Redis   │  │ Worker pool │ │  Object    │
     │ (source  │  │ cache +   │  │ (Celery/RQ/ │ │  storage   │
     │ of truth)│  │ job queue │  │  ARQ jobs)  │ │ local→S3   │
     └──────────┘  └───────────┘  └─────────────┘ └────────────┘
```

### 6.2 Architectural style decision

**Modular monolith, not microservices (yet).** A single deployable FastAPI app with strictly separated domain packages. Rationale: one learning-center deployment does not warrant the operational cost of microservices, but clean domain boundaries + an internal event bus mean any domain can be extracted into a service later without rewriting callers. Domains communicate through **service interfaces and domain events**, never by reaching into each other's tables.

### 6.3 Future-readiness as explicit seams

Each deferred capability (§5) maps to a concrete extension seam present in v1.2:

| Future capability | Seam built in v1.2 |
|---|---|
| AI tutor / quiz gen / recommendations | `analytics` event stream + topic-tagged questions + `AIProvider` interface stub; all student interactions emit events |
| Face ID attendance | `AttendanceSource` interface — manual marking is one implementation; a device webhook is another, both call `AttendanceService.record()` |
| Native mobile apps | 100% of features behind versioned JSON REST; no HTML coupling; auth via bearer tokens usable by any client |
| Push notifications | `NotificationChannel` interface (in-app, Telegram in v1.2; web-push/APNs/FCM later) |
| Payment gateways | `PaymentProvider` interface (manual/cash in v1.2; Stripe/Click/Payme later) |
| Multi-branch SaaS | `organization_id` + `branch_id` on every scoped row from day one; Super Admin role reserved |
| Video / files / certificates | `files` domain with storage abstraction (local→S3/MinIO) |

### 6.4 Environments & configuration

- **Environments:** `local` → `staging` → `production`, identical code, env-driven config (12-factor). Secrets via environment / secret manager, never in code.
- **Storage:** local filesystem in dev; S3/MinIO in staging/prod behind the same `Storage` interface.
- **Background jobs:** Redis-backed worker (ARQ or Celery). All notifications, reminders, report generation, CSV import/export, and analytics rollups run as jobs — never inline in request handlers.
- **API versioning:** all routes under `/api/v1`. A future `/api/v2` can coexist; v1 contracts are frozen once shipped.
- **Observability built in from day one:** structured JSON logs with request IDs, health/readiness endpoints, metrics (request latency, job queue depth, DB pool), and error tracking (Sentry-compatible). Lack of observability was a named technical risk.

### 6.5 Data backup & migration strategy

- **Migrations:** Alembic, forward-only in production, reviewed in PRs, run automatically on deploy with a gate. Every schema change ships with a migration; no manual SQL in prod.
- **Backups:** automated daily PostgreSQL snapshots + point-in-time WAL archiving; documented restore runbook tested quarterly.
- **Object storage:** versioned bucket + lifecycle policy.
- **Zero-downtime principle:** additive migrations first (add column/table), backfill via job, then switch reads/writes, then remove old columns in a later release.

---

## 7. Backend Domain Architecture

### 7.1 Module layout

Each domain is an independent Python package with a consistent internal structure. Domains never import another domain's `models` or `repository` directly — only its public `service`.

```
app/
  core/                # cross-cutting, no business logic
    config.py          # settings (env-driven)
    security.py        # hashing, token issue/verify
    authz.py           # permission + scope engine (§12)
    tenant.py          # request-scoped org/branch context
    events.py          # in-process event bus (→ queue later)
    db.py              # session, base model (org_id, timestamps, soft-delete)
    pagination.py      # cursor/offset helpers
    errors.py          # typed errors → consistent API envelope
  domains/
    auth/              # login, refresh rotation, revocation, invites
    users/             # user + role + scope_grant
    org/               # organization, branch (tenancy)
    crm/               # leads, pipeline, sources, follow-ups, trials
    students/          # student profile + enrollment + parent link
    parents/           # guardian records + child links
    teachers/          # teacher profile + assignments
    groups/            # group, group_membership, schedule
    courses/           # course, roadmap, milestone definitions
    lessons/           # lesson sessions, materials
    tests/             # test, question bank, assignment
    attempts/          # test attempts, answers, grading
    attendance/        # attendance records + AttendanceSource interface
    payments/          # invoices, payments, debt, PaymentProvider interface
    notifications/     # notification core + NotificationChannel interface
    telegram/          # bot handlers, linking, internal API
    analytics/         # aggregation jobs + read models
    audit/             # audit log writer + query
    settings/          # org/user settings
    files/             # media + Storage interface
  api/
    v1/                # routers per domain, thin — call services only
  workers/             # job definitions, schedules
  main.py
```

### 7.2 Layering within a domain

```
router (api/v1/<domain>.py)     ← HTTP only: parse, call service, serialize
   │  depends on: authz guard, tenant context, pydantic schemas
service (<domain>/service.py)   ← business rules, transactions, emits events
   │  depends on: repository, other domains' services, event bus
repository (<domain>/repo.py)   ← DB queries only; tenant filter applied here
   │  depends on: models, db session
models (<domain>/models.py)     ← SQLAlchemy ORM, inherits TenantScopedBase
```

**Rules:**
- Routers contain **no business logic** and **no raw queries**.
- The repository layer **always** applies `organization_id` (and branch where relevant) filters from the tenant context — making cross-tenant leakage a code smell that fails review.
- Services own transactions and emit domain events (`payment.recorded`, `attempt.submitted`, `lead.converted`, `attendance.marked`) consumed by `analytics`, `notifications`, and `audit`.

### 7.3 Domain responsibilities (summary)

| Domain | Owns | Key events emitted |
|---|---|---|
| auth | sessions, tokens, refresh rotation, revocation, invites/temp passwords | `auth.login`, `auth.logout`, `auth.token_revoked` |
| users | user identity, role, scope grants | `user.created`, `role.changed`, `scope.granted` |
| org | organizations, branches | `branch.created` |
| crm | leads, pipeline stages, sources, follow-ups, trials | `lead.created`, `lead.stage_changed`, `lead.converted` |
| students | student profiles, enrollments, parent links | `student.enrolled`, `student.parent_linked` |
| parents | guardians, child links | `parent.linked` |
| teachers | teacher profiles, group assignments | `teacher.assigned` |
| groups | groups, memberships, schedules | `group.created`, `member.added` |
| courses | courses, roadmaps, milestones | `roadmap.published`, `milestone.completed` |
| lessons | lesson sessions, materials | `lesson.held`, `material.added` |
| tests | tests, question bank, assignments | `test.assigned` |
| attempts | attempts, answers, grading | `attempt.started`, `attempt.submitted`, `attempt.graded` |
| attendance | attendance records (via AttendanceSource) | `attendance.marked` |
| payments | invoices, payments, debt (via PaymentProvider) | `invoice.issued`, `payment.recorded`, `invoice.overdue` |
| notifications | messages, delivery via channels | `notification.sent` |
| telegram | bot menus, linking, internal API | `telegram.linked` |
| analytics | read models, rollups, at-risk scoring | `analytics.rollup_done` |
| audit | immutable audit trail | — (consumer) |
| settings | org/user config | `settings.updated` |
| files | media, storage | `file.uploaded` |

### 7.4 Event bus & background jobs

v1.2 ships an **in-process event bus** that hands work to the Redis-backed worker. Example flow for `payment.recorded`:

```
PaymentService.record_payment(...)        # in request, in a DB transaction
  └─ commit
  └─ emit event payment.recorded
       ├─ audit consumer        → write audit row (job)
       ├─ analytics consumer    → enqueue debt/revenue rollup (job)
       └─ notifications consumer→ enqueue parent receipt + Telegram (job)
```

Heavy work (rollups, broadcasts, CSV import/export, report PDFs) **never** runs inline. Scheduled jobs: nightly analytics rollups, daily overdue-invoice scan + reminders, follow-up reminder dispatch, at-risk recompute.

---

## 8. Frontend Architecture

### 8.1 Stack decision

**Next.js (App Router) + TypeScript**, React Server Components where they help first paint, client components for interactive dashboards. Rationale over plain React SPA: route-level code splitting per role, better initial load (a named v1.0 weakness), straightforward auth-guarded layouts, and an easy future path to SSR/SEO for public/marketing pages. If the team prefers a pure SPA, the same role-routing and cache-isolation rules apply — the decision that matters is the **per-role route tree + cache namespacing**, not the framework.

### 8.2 Role-based route tree

Each role gets its **own route group and layout**, not a shared shell with conditional menus. This is the structural fix for "same UI for all roles."

```
app/
  (auth)/login, /invite/[token], /forgot, /reset
  (admin)/dashboard, /leads, /students, /teachers, /groups,
          /payments, /attendance, /reports, /settings, /audit
  (teacher)/dashboard, /groups/[id], /attendance, /tests, /results, /materials
  (student)/dashboard, /schedule, /roadmap, /tests, /results, /progress, /payments
  (parent)/dashboard, /child/[id]/...   # attendance, results, progress, payments
  (shared)/notifications, /profile
```

- A **route guard** in each role layout checks the authenticated role; mismatched access redirects to that user's own dashboard (never renders the wrong shell, never flashes forbidden data).
- **Nav is derived from role + permissions** returned by the backend `GET /api/v1/me` (which includes the user's effective permission set). The frontend renders only permitted nav items — but this is **UX convenience, not security**; the backend still enforces every call (§12).

### 8.3 State & data layer

- **Server state:** TanStack Query (React Query). **Every query key is namespaced with `userId` and `role`:** `['payments', { orgId, userId, role, page, filters }]`. This is the core fix for cross-role/session cache leakage.
- **Auth state:** in-memory access token + httpOnly refresh cookie (preferred) or rotating refresh token; access token never in `localStorage`.
- **Client UI state:** lightweight store (Zustand) for ephemeral UI; **no user data persisted to `localStorage`/`sessionStorage`** by default. If any persistence is enabled, the persisted store is namespaced by `userId` and wiped on logout.
- **No data caching across identities:** see §13.4 for the exact logout/login purge contract.

### 8.4 Required UI states (every data view)

Every list/detail/dashboard must implement four states explicitly — their absence was a named UX risk:

1. **Loading** — skeletons, not spinners-on-blank.
2. **Empty** — guidance ("No leads yet — add your first lead"), not a blank table.
3. **Error** — human message + retry, with the request ID for support.
4. **Forbidden** — explicit "You don't have access to this" panel for 403s (should be rare given nav-gating, but always handled).

### 8.5 Responsive strategy

Mobile is a **distinct layout**, not a shrunk desktop. Desktop uses a persistent sidebar; mobile uses a bottom tab bar (role-specific 4–5 tabs) + a "more" sheet. Tables collapse into card lists on small screens. Forms are single-column, large-tap-target, with sticky primary actions. Breakpoints and full guidelines in §20.

### 8.6 Performance practices

Route-level code splitting per role; lazy-load heavy widgets (charts) below the fold; virtualized long lists; debounced server-side search; optimistic updates for attendance; prefetch the dashboard's primary query on login. Targets in §13.

---

## 9. Telegram Bot Architecture

### 9.1 Position in the system

The bot is a **first-class client**, not a side script. It talks to the backend exclusively through an **internal, authenticated API** — it holds no direct database access and reuses the same domain services and authorization engine as the web app.

```
Telegram → Bot service (webhook) → Internal API (service token + linked user)
                                  → same authz engine (role + tenant + ownership)
                                  → domain services
```

### 9.2 Secure account linking

The v1.0 risk of "insecure Telegram linking" is closed by a **one-time, server-issued linking code**:

1. User (in web app) requests "Connect Telegram" → backend issues a short-lived, single-use code bound to their `user_id` + `organization_id`.
2. User sends the code (or taps a deep link `t.me/<bot>?start=<code>`) to the bot.
3. Bot calls internal API to redeem the code → backend verifies, binds `telegram_chat_id` ↔ `user_id`, marks code used, audits `telegram.linked`.
4. Phone number, if collected, is verified against the user record, not trusted blindly.

A `telegram_chat_id` maps to exactly one user; every bot request resolves to that user and inherits their full role/tenant/ownership scope. **The bot can never see more than the linked user could see in the web app.**

### 9.3 Role-based menus

The bot fetches the linked user's role and renders the matching menu:

- **Student:** Schedule · Assigned tests · Results · Attendance · Payments
- **Parent:** Child progress · Attendance · Debt · Alerts (child switcher if multiple)
- **Teacher:** Today's groups · Attendance reminders · Test notifications
- **Admin:** Key alerts · Debt summary · Attendance issues

Read-only and notification flows are prioritized in v1.2; sensitive writes (recording payments, taking graded tests) stay in the web app to keep the bot surface small and safe.

### 9.4 Security & infrastructure

- **Internal bot API token** (service credential) authenticates the bot service to the backend; rotated, stored as a secret.
- **Webhook secret** validates that updates genuinely come from Telegram.
- **Rate limiting** per `chat_id` to prevent abuse.
- **No secrets in messages;** linking codes are single-use and short-lived.
- All bot-initiated reads/writes pass the same authz engine and are audited where sensitive.
- Outbound notifications (reminders, alerts) are dispatched by the **notifications domain** via the Telegram `NotificationChannel`, queued as background jobs — the bot service does not own business logic.

---

## 10. Database Entity Design

PostgreSQL. All identifiers are UUIDv7 (sortable) primary keys. **Every business table inherits a common base.**

### 10.1 Base columns (every scoped table)

```sql
id              uuid        PRIMARY KEY DEFAULT uuid_generate_v7(),
organization_id uuid        NOT NULL REFERENCES organizations(id),
branch_id       uuid        NULL REFERENCES branches(id),   -- null = org-wide
created_at      timestamptz NOT NULL DEFAULT now(),
updated_at      timestamptz NOT NULL DEFAULT now(),
created_by      uuid        NULL REFERENCES users(id),
deleted_at      timestamptz NULL                            -- soft delete
```

> **Tenant invariant:** `organization_id` is non-null on every scoped row and is *always* part of repository query filters. A composite index leads with `organization_id` (and `branch_id` where queried) on virtually every table. Soft-deleted rows (`deleted_at IS NOT NULL`) are filtered by default.

### 10.2 Identity & tenancy

```sql
-- organizations
organizations(id, name, slug UNIQUE, plan, status, settings jsonb, timestamps)

-- branches  (multi-branch foundation)
branches(id, organization_id, name, address, phone, status, timestamps)
  INDEX (organization_id)

-- users  (one identity; role is coarse, scope via grants)
users(
  id, organization_id, branch_id NULL,
  role text NOT NULL CHECK (role IN
    ('super_admin','admin','manager','teacher','student','parent')),
  full_name, phone, email NULL,
  password_hash NULL,            -- null until invite redeemed
  status text NOT NULL,          -- invited|active|suspended|disabled
  must_change_password bool DEFAULT false,
  last_login_at timestamptz NULL,
  telegram_chat_id bigint NULL UNIQUE,
  timestamps, deleted_at
)
  UNIQUE (organization_id, phone)
  UNIQUE (organization_id, email) WHERE email IS NOT NULL
  INDEX (organization_id, role)

-- scope_grant  (extends ownership scope without new roles)
scope_grants(
  id, organization_id, user_id,
  resource_type text,            -- 'group' | 'branch' | 'student' ...
  resource_id uuid,
  access text,                   -- 'read' | 'write'
  granted_by uuid, expires_at timestamptz NULL, timestamps
)
  INDEX (organization_id, user_id, resource_type)

-- refresh_tokens  (rotation + revocation)
refresh_tokens(
  id, user_id, token_hash UNIQUE, family_id uuid,
  issued_at, expires_at, revoked_at NULL, replaced_by uuid NULL,
  user_agent, ip
)
  INDEX (user_id), INDEX (family_id)

-- invites / temporary access
invites(id, organization_id, user_id, token_hash UNIQUE, expires_at,
        accepted_at NULL, created_by, timestamps)
```

### 10.3 CRM & sales

```sql
lead_sources(id, organization_id, name, active bool)

leads(
  id, organization_id, branch_id,
  full_name, phone, email NULL,
  source_id REFERENCES lead_sources(id),
  status text CHECK (status IN ('new','contacted','trial','enrolled','lost')),
  assigned_to uuid REFERENCES users(id) NULL,   -- sales owner
  lost_reason text NULL,
  converted_student_id uuid NULL,
  notes text, timestamps, deleted_at
)
  INDEX (organization_id, status),
  INDEX (organization_id, assigned_to),
  INDEX (organization_id, source_id)

lead_activities(id, organization_id, lead_id, type, note, occurred_at, created_by)
  INDEX (organization_id, lead_id)

trials(id, organization_id, lead_id, group_id NULL, scheduled_at,
       attended bool NULL, outcome text NULL, timestamps)
  INDEX (organization_id, scheduled_at)

follow_ups(id, organization_id, lead_id NULL, student_id NULL,
           due_at, assigned_to, status, note, timestamps)
  INDEX (organization_id, assigned_to, status, due_at)
```

### 10.4 People: students, parents, teachers

```sql
students(
  id, organization_id, branch_id,
  user_id REFERENCES users(id) UNIQUE,   -- their login identity
  code text,                              -- human-friendly student no.
  status text,                            -- active|paused|graduated|dropped
  enrolled_at date, source_lead_id uuid NULL,
  timestamps, deleted_at
)
  INDEX (organization_id, status)

teachers(
  id, organization_id, branch_id, user_id UNIQUE,
  specialization text, hourly_rate numeric NULL, status text, timestamps
)
  INDEX (organization_id, status)

parents(id, organization_id, user_id UNIQUE, timestamps)

-- guardian ↔ child  (many-to-many; the parent-isolation backbone)
parent_links(
  id, organization_id, parent_id REFERENCES parents(id),
  student_id REFERENCES students(id),
  relation text,                          -- mother|father|guardian
  is_primary bool DEFAULT false,
  UNIQUE (parent_id, student_id), timestamps
)
  INDEX (organization_id, parent_id),
  INDEX (organization_id, student_id)
```

### 10.5 Groups, courses, roadmap, lessons

```sql
courses(id, organization_id, name, description, level, status, timestamps)

groups(
  id, organization_id, branch_id, course_id,
  name, teacher_id REFERENCES teachers(id) NULL,
  capacity int, status text,              -- active|archived
  start_date date, timestamps
)
  INDEX (organization_id, teacher_id),
  INDEX (organization_id, course_id, status)

group_members(
  id, organization_id, group_id, student_id,
  joined_at, left_at NULL, status text,
  UNIQUE (group_id, student_id) WHERE left_at IS NULL
)
  INDEX (organization_id, group_id),
  INDEX (organization_id, student_id)

group_schedule(
  id, organization_id, group_id,
  weekday int, start_time time, end_time time, room text
)
  INDEX (organization_id, group_id)

-- roadmap = ordered milestones for a course
roadmap_milestones(
  id, organization_id, course_id, order_index int,
  title, description, type text,          -- lesson|checkpoint|achievement
  test_id uuid NULL,                      -- checkpoint test, if any
  timestamps
)
  INDEX (organization_id, course_id, order_index)

student_milestone_progress(
  id, organization_id, student_id, milestone_id,
  status text,                            -- locked|in_progress|completed
  completed_at timestamptz NULL, score numeric NULL,
  UNIQUE (student_id, milestone_id)
)
  INDEX (organization_id, student_id)

achievements(id, organization_id, code, title, description, icon)
student_achievements(id, organization_id, student_id, achievement_id,
  earned_at, UNIQUE (student_id, achievement_id))
  INDEX (organization_id, student_id)

-- lessons = actual held sessions
lesson_sessions(
  id, organization_id, group_id, scheduled_at, held_at timestamptz NULL,
  topic text, status text,                -- planned|held|cancelled
  taught_by uuid REFERENCES teachers(id), timestamps
)
  INDEX (organization_id, group_id, scheduled_at)

lesson_materials(id, organization_id, group_id NULL, lesson_id NULL,
  course_id NULL, title, file_id REFERENCES files(id) NULL, url NULL, timestamps)
  INDEX (organization_id, group_id)
```

### 10.6 Tests, questions, attempts

```sql
questions(                                 -- reusable bank
  id, organization_id, course_id NULL,
  topic_tag text,                          -- drives weak-topic analytics
  difficulty int,                          -- 1..5
  type text CHECK (type IN ('mcq','multi','open')),
  prompt text, explanation text NULL,
  created_by, timestamps, deleted_at
)
  INDEX (organization_id, topic_tag),
  INDEX (organization_id, course_id)

question_options(id, organization_id, question_id, label, is_correct bool, order_index)
  INDEX (organization_id, question_id)

tests(
  id, organization_id, course_id NULL, title, description,
  duration_minutes int NULL, max_attempts int DEFAULT 1,
  shuffle bool, created_by, status text, timestamps
)
  INDEX (organization_id, course_id)

test_questions(id, organization_id, test_id, question_id, order_index, points numeric)
  INDEX (organization_id, test_id)

test_assignments(
  id, organization_id, test_id,
  group_id uuid NULL, student_id uuid NULL,   -- one or the other
  opens_at timestamptz, closes_at timestamptz, assigned_by, timestamps
)
  INDEX (organization_id, group_id),
  INDEX (organization_id, student_id)

attempts(
  id, organization_id, test_id, assignment_id, student_id,
  started_at, submitted_at NULL,
  status text,                              -- in_progress|submitted|graded
  auto_score numeric NULL, manual_score numeric NULL, total_score numeric NULL,
  max_score numeric, timestamps
)
  INDEX (organization_id, student_id),
  INDEX (organization_id, test_id),
  INDEX (organization_id, assignment_id)

attempt_answers(
  id, organization_id, attempt_id, question_id,
  selected_option_ids uuid[] NULL, open_text text NULL,
  is_correct bool NULL, awarded_points numeric NULL, graded_by uuid NULL
)
  INDEX (organization_id, attempt_id)
```

### 10.7 Attendance

```sql
attendance(
  id, organization_id, lesson_id REFERENCES lesson_sessions(id),
  student_id, group_id,
  status text CHECK (status IN ('present','absent','late','excused')),
  reason text NULL,
  source text DEFAULT 'manual',            -- manual|faceid|import (future-ready)
  marked_by uuid NULL, marked_at timestamptz,
  UNIQUE (lesson_id, student_id)
)
  INDEX (organization_id, group_id, marked_at),
  INDEX (organization_id, student_id, marked_at)
```

### 10.8 Payments & debt

```sql
invoices(
  id, organization_id, branch_id, student_id,
  period_month date,                       -- billing month
  amount numeric, discount numeric DEFAULT 0,
  due_date date,
  status text CHECK (status IN ('unpaid','partial','paid','overdue','void')),
  paid_total numeric DEFAULT 0, timestamps, deleted_at
)
  INDEX (organization_id, status, due_date),
  INDEX (organization_id, student_id)

payments(
  id, organization_id, invoice_id, student_id,
  amount numeric, method text,             -- cash|card|transfer (provider-ready)
  provider text DEFAULT 'manual', provider_ref text NULL,
  received_by uuid, received_at timestamptz, receipt_no text, timestamps
)
  INDEX (organization_id, invoice_id),
  INDEX (organization_id, received_at)
```

### 10.9 Notifications, telegram, audit, files, settings

```sql
notifications(
  id, organization_id, user_id, type, title, body,
  channel text,                            -- in_app|telegram (push later)
  payload jsonb, read_at timestamptz NULL, sent_at timestamptz NULL,
  status text, timestamps
)
  INDEX (organization_id, user_id, read_at)

telegram_link_codes(id, organization_id, user_id, code_hash UNIQUE,
  expires_at, used_at NULL, timestamps)

audit_logs(
  id, organization_id, actor_user_id, actor_role,
  action text,                             -- e.g. payment.recorded
  entity_type text, entity_id uuid,
  before jsonb NULL, after jsonb NULL,
  ip text, user_agent text, request_id text, created_at timestamptz
)
  INDEX (organization_id, entity_type, entity_id),
  INDEX (organization_id, actor_user_id, created_at),
  INDEX (organization_id, action, created_at)

files(id, organization_id, owner_user_id, kind, storage_key, url NULL,
  content_type, size_bytes, timestamps)

settings(id, organization_id, scope text, scope_id uuid NULL, key, value jsonb,
  UNIQUE (organization_id, scope, scope_id, key))

-- analytics read models (populated by jobs, never written in request path)
analytics_daily(organization_id, branch_id NULL, date,
  metric text, dimension jsonb, value numeric,
  PRIMARY KEY (organization_id, date, metric, dimension))

student_risk_scores(organization_id, student_id, score numeric, factors jsonb,
  computed_at, PRIMARY KEY (organization_id, student_id))
```

### 10.10 ER overview (textual)

```
organization 1─* branch
organization 1─* user ─1 (student | teacher | parent profile)
parent *─* student        (via parent_links)
teacher 1─* group ─* group_member *─1 student
course 1─* group ; course 1─* roadmap_milestone
group 1─* lesson_session 1─* attendance *─1 student
course/test 1─* question (bank) ; test *─* question (via test_questions)
test 1─* test_assignment ─→ group|student
test_assignment 1─* attempt 1─* attempt_answer
student 1─* invoice 1─* payment
user 1─* notification ; user 1─1 telegram link
* ─→ audit_logs (cross-cutting) ; * ─→ analytics read models
```

### 10.11 Indexing principles

- Lead every multi-tenant index with `organization_id`.
- Add covering indexes for the exact filters each list screen uses (status + date, teacher + group, student + period).
- Foreign keys are indexed (Postgres does not auto-index FK columns).
- Time-series tables (`attendance`, `payments`, `audit_logs`, `analytics_daily`) consider monthly partitioning by `created_at`/`date` when volume grows.
- Full-text/`trigram` (`pg_trgm`) index on searchable name fields (students, leads) for fast type-ahead.

---

## 11. API Design Principles

### 11.1 Conventions

- **Base path & versioning:** all endpoints under `/api/v1`. Contracts frozen once shipped; breaking changes go to `/api/v2`.
- **Resource-oriented REST + JSON.** Nouns, plural, nested only one level: `/api/v1/groups/{id}/attendance`.
- **Consistent envelope.** Success: `{ "data": ..., "meta": {...} }`. Error: `{ "error": { "code", "message", "details", "request_id" } }`. Stable machine `code`s (e.g. `forbidden_scope`, `validation_error`, `invoice_already_paid`).
- **Pagination:** cursor-based for large/append-heavy lists (attendance, audit), offset+limit acceptable for small admin tables; always return `meta.next_cursor` / `meta.total`.
- **Filtering & sorting:** explicit allow-listed query params per endpoint (`?status=overdue&due_before=...&sort=-due_date`); never pass raw user input into queries.
- **Idempotency:** mutating endpoints that can be retried (payments, bulk attendance, conversions) accept an `Idempotency-Key` header.
- **Request IDs:** every request/response carries `X-Request-ID`, logged and surfaced in error envelopes for support.

### 11.2 The `/me` contract (drives the frontend)

`GET /api/v1/me` returns identity, role, tenant, **effective permission set**, and linked entities (children for a parent, groups for a teacher). The frontend builds nav and feature flags from this — but it is convenience only; the backend re-checks every call.

### 11.3 Representative endpoints

```
# Auth
POST   /api/v1/auth/login            {phone|email, password} → access+refresh
POST   /api/v1/auth/refresh          rotates refresh, returns new pair
POST   /api/v1/auth/logout           revokes refresh family
POST   /api/v1/auth/invite/accept    {token, new_password}
GET    /api/v1/me

# CRM / Sales
GET    /api/v1/leads?status=&source=&assigned_to=&cursor=
POST   /api/v1/leads
PATCH  /api/v1/leads/{id}            (stage change → emits lead.stage_changed)
POST   /api/v1/leads/{id}/convert    → creates student (+parent link, +group)
GET    /api/v1/sales/funnel?from=&to=

# Students / Parents / Teachers
GET    /api/v1/students?status=&group_id=&q=&cursor=
GET    /api/v1/students/{id}          (admin/teacher-in-scope/self/parent-of)
GET    /api/v1/parents/{id}/children
GET    /api/v1/teachers/{id}/groups

# Groups / Lessons / Roadmap
GET    /api/v1/groups/{id}
GET    /api/v1/groups/{id}/schedule
GET    /api/v1/courses/{id}/roadmap
GET    /api/v1/students/{id}/roadmap-progress

# Tests
POST   /api/v1/tests
POST   /api/v1/tests/{id}/questions
POST   /api/v1/tests/{id}/assign       {group_id|student_id, opens_at, closes_at}
GET    /api/v1/students/{id}/assigned-tests
POST   /api/v1/attempts                 {assignment_id} → start
POST   /api/v1/attempts/{id}/submit     → auto-grade objective, queue manual
GET    /api/v1/tests/{id}/results       (teacher/admin, group-scoped)
GET    /api/v1/analytics/weak-topics?group_id=

# Attendance
GET    /api/v1/lessons/{id}/attendance
POST   /api/v1/lessons/{id}/attendance/bulk   [{student_id,status,reason}]
                                              (Idempotency-Key supported)

# Payments
GET    /api/v1/invoices?status=overdue&cursor=
POST   /api/v1/invoices/generate        {period_month}  (admin; queued)
POST   /api/v1/payments                 {invoice_id, amount, method}
POST   /api/v1/invoices/{id}/remind     (queues notification)

# Notifications / Telegram / Audit
GET    /api/v1/notifications?unread=true
POST   /api/v1/telegram/link-code
GET    /api/v1/audit?entity_type=&entity_id=&actor=&from=&to=
```

### 11.4 Mobile & multi-client readiness

The API is the contract for web, bot, and future native apps: no server-rendered HTML coupling, bearer-token auth usable by any client, all media via signed URLs from the storage abstraction, and responses sized for mobile (no over-fetching; expandable resources via explicit `?include=`).

---

## 12. Authentication and Authorization Design

### 12.1 Authentication

- **Password hashing:** Argon2id (or bcrypt cost ≥ 12). No plaintext, ever.
- **No hidden default passwords.** New users are created in `invited` status with no usable password. They receive an **invite link** (single-use, expiring token) or an admin-issued **temporary password** with `must_change_password = true`, forcing a reset on first login.
- **JWT access tokens:** short-lived (10–15 min), signed (RS256 preferred for future multi-service verification), carrying `sub`, `org_id`, `branch_id`, `role`, `token_version`.
- **Refresh tokens:** long-lived, **rotated on every use**, stored hashed, grouped by `family_id`. Using a rotated (already-replaced) token revokes the entire family — detecting theft/replay.
- **Revocation:** logout revokes the refresh family; `token_version` on the user lets an admin force-logout-all (e.g., on suspected compromise) by bumping the version, invalidating outstanding access tokens at verify time.
- **MFA-ready:** optional TOTP for admin/manager accounts (hook present; enforcement configurable).

### 12.2 Authorization engine (the three-layer model in code)

A single `authz` module enforces §2.2 on every request. Routers declare requirements declaratively:

```python
@router.get("/students/{student_id}")
@require(permission="student:read", scope=StudentScope)
async def get_student(student_id: UUID, ctx: AuthContext = Depends(auth_context)):
    return StudentService.get(ctx, student_id)   # service re-applies tenant filter
```

- **`auth_context`** dependency verifies the JWT, loads the user, and builds an immutable `AuthContext { user_id, org_id, branch_id, role, permissions, scope_grants }`. It also sets the **request-scoped tenant context** used by every repository.
- **`@require(permission=...)`** checks the role's permission set (layer 2).
- **`scope=...`** runs the ownership check (layer 3): `StudentScope` resolves whether this actor may touch this student — admin/manager (in org), teacher (student in an assigned group), the student themselves, or a linked parent; anyone else → `403 forbidden_scope`.
- **Tenant (layer 1)** is enforced in the repository: every query filters `organization_id = ctx.org_id`. Even a logic bug in a scope check cannot cross tenants.

### 12.3 Ownership scope resolvers (examples)

| Resource | Allowed actors |
|---|---|
| Student record | admin/manager (org); teacher if student ∈ assigned/granted group; the student; linked parents |
| Group | admin/manager; assigned teacher; granted teacher; enrolled students (read); their parents (read) |
| Invoice/Payment | admin/manager (write+read); the student (read own); linked parent (read) |
| Attempt | the student (own); teacher of the assignment's group; admin/manager |
| Audit log | admin (org); manager (limited) |

### 12.4 Defense in depth: backend vs frontend

The frontend hides unavailable actions for UX, but **authorization is never delegated to the client.** Each of the following is independently true: nav hides what you can't do; the API returns 403 if you call it anyway; the repository returns nothing outside your tenant. A penetration test that calls every endpoint with each role's token is part of acceptance (§17, §18).

### 12.5 Closing the v1.0 leak vectors

| v1.0 vector | v1.2 control |
|---|---|
| Teacher sees admin finance | `payment:*` not in teacher permission set; finance routes 403 for teacher |
| Student sees other students | `StudentScope` restricts to self; list endpoints filter to scope |
| Parent sees non-children | `parent_links` is the only path; scope resolver enforces it |
| Cross-tenant access | `organization_id` filter in every repository query |
| Privilege via crafted requests | server-side `@require` + scope on every endpoint, tested with role-matrix suite |

---

## 13. Caching and Performance Strategy

### 13.1 Performance targets

| Surface | Target (p95) |
|---|---|
| Login → role dashboard interactive | < 1.5 s on mid-tier mobile, < 1 s desktop |
| Paginated table page (50 rows) | < 400 ms server response |
| Attendance bulk save (30 students) | < 300 ms server response |
| Test auto-grade on submit | < 500 ms |
| Heavy report / analytics | async job; UI returns immediately, notifies on ready |

### 13.2 Database performance

- **No N+1:** list endpoints use explicit joins / `selectinload`; a query-count assertion in tests guards hot endpoints.
- **Indexes** per §10.11 for every filter/sort/report path.
- **Pagination everywhere** — no unbounded list endpoints.
- **Read models** for analytics (`analytics_daily`, `student_risk_scores`) so dashboards read precomputed rows, not live aggregates.
- Connection pooling tuned; slow-query logging on in all envs.

### 13.3 Redis caching (safe, scoped only)

Cache **only** data that is safe and user-scoped, with keys that embed identity:

```
cache key = v1:{org_id}:{role}:{user_id}:{resource}:{params_hash}
```

- Cache: `/me` payload, role dashboard aggregates (short TTL), reference data (courses, lead sources).
- **Never cache** cross-user lists under a shared key; never cache anything not already scoped by the authz layer.
- Invalidate on the relevant domain event (e.g., `payment.recorded` busts that org's revenue/debt dashboard cache).

### 13.4 Frontend cache isolation & logout purge (the core v1.0 fix)

This is a hard, tested contract:

1. **Namespaced keys.** Every React Query key includes `userId` and `role`. Two identities can never read the same cache entry.
2. **No sensitive persistence.** User data is not written to `localStorage`/`sessionStorage` by default; access token lives in memory only.
3. **Logout purge.** On logout the client: calls `POST /auth/logout` (server revokes refresh family) → `queryClient.clear()` → resets all in-memory stores → clears any namespaced persisted storage → hard-navigates to `/login`. No stale data can survive into the next session.
4. **Identity-change guard.** On app boot / token refresh, if the resolved `userId` differs from the last known one, the client clears all caches before rendering. This catches same-device user switches.
5. **Verified.** An automated E2E test logs in as user A, logs out, logs in as user B, and asserts zero A-data is reachable in cache or UI (§17).

### 13.5 Background jobs (keep requests fast)

Reminders, invoice generation, broadcasts, CSV import/export, report rendering, analytics rollups, and at-risk recompute all run on the Redis worker. Request handlers enqueue and return; results surface via notifications. Scheduled cadence: nightly rollups, daily overdue scan, periodic follow-up dispatch.

---

## 14. Security and Audit Strategy

### 14.1 Controls checklist (all required for v1.2)

- JWT access + refresh **rotation** + **family revocation** (§12.1).
- Argon2id/bcrypt password hashing; no default/hidden passwords; invite or temp-password flow.
- **Rate limiting** at the edge (per IP) and per-account on auth endpoints; per-`chat_id` on the bot.
- **Secure CORS:** explicit allow-list of origins per environment; credentials handling deliberate; no wildcard with credentials.
- **Input validation** via Pydantic schemas on every endpoint; allow-listed query params; output schemas to avoid leaking fields.
- **Transport:** TLS everywhere; HSTS; secure + httpOnly + SameSite cookies for refresh.
- **Secrets** via environment/secret manager; rotated; never in repo (enforced by secret-scanning in CI).
- **Strong error handling:** typed errors, no stack traces or internal details to clients, request IDs for correlation.
- **Authorization** enforced server-side on every endpoint, independent of UI (§12.4).
- **Cache isolation** by user+role; full logout purge (§13.4).
- **File uploads:** content-type + size validation, virus-scan hook, signed URLs, no public buckets.
- **Dependency & container scanning** in CI; least-privilege DB credentials.

### 14.2 Audit strategy

Every sensitive action writes an **immutable `audit_logs` row** (append-only; no updates/deletes) capturing actor, role, action, entity, before/after JSON, IP, user-agent, request ID, timestamp. Audited actions include at minimum:

- All auth events (login, logout, failed login, token revoke, password/role change).
- Every payment and invoice change (issue, pay, partial, void, discount).
- Every attendance create/modify.
- Every test/score change and manual grade.
- Lead conversion, student status change, parent link change.
- Scope grants, user creation/suspension, settings changes, Telegram linking.

Audit is written by an event consumer (off the request path where possible) so it cannot be skipped by a code path that forgets to log. Admins query audit by entity, actor, action, and time range (§11.3). Retention policy configurable; logs are part of the backup set.

### 14.3 Privacy & data protection

- Minimal PII; phone/email scoped per org; soft-delete + purge policy.
- Parent/student data access strictly via relationship scopes.
- Face ID (future) treated as biometric data: explicit consent, separate storage, never in the main user table — the abstraction keeps it isolated when added.

---

## 15. Analytics Strategy

### 15.1 Principle

Analytics are **precomputed read models** populated by background jobs from the domain event stream, never live aggregations in the request path. Dashboards read fast rows from `analytics_daily` and `student_risk_scores`. This keeps dashboards sub-second and creates the clean event/feature foundation AI will later consume.

### 15.2 Metric catalog

| Audience | Metric | Source / computation |
|---|---|---|
| Admin | Today's & MTD revenue | sum(payments) by day/month |
| Admin | Outstanding debt + aging | invoices where status in (unpaid,partial,overdue) bucketed by days overdue |
| Admin | Active students | students status=active |
| Admin | New leads / conversion rate | leads by status; enrolled ÷ (enrolled+lost) by period & source |
| Admin | Attendance rate | present ÷ total attendance records, by group/org |
| Admin | At-risk students | risk score (§15.3) above threshold |
| Admin | Teacher workload | active groups × scheduled hours per teacher |
| Admin | Group performance | avg test score + attendance + milestone completion per group |
| Teacher | Group progress | milestone completion + avg scores for own groups |
| Teacher | Low-performing students | students below score/attendance threshold in own groups |
| Teacher | Weak topics | wrong-answer rate aggregated by `question.topic_tag` |
| Student | Progress % | completed milestones ÷ total in course roadmap |
| Student | Growth trend | scores over time, attendance trend, milestones earned |
| Student | Weak topics | own wrong-answer rate by topic |
| Parent | Child progress trend | same as student, scoped to linked child |
| Parent | Payment/debt status | child's invoices |

### 15.3 At-risk student detection (rule-based, AI-ready)

A nightly job computes a `student_risk_scores.score` from weighted, explainable factors stored in `factors` JSON:

- Declining test-score trend (recent vs prior window)
- Attendance drop / consecutive absences
- Stalled roadmap progress (no milestone in N weeks)
- Overdue payments (engagement/retention signal)
- Low recent app/bot activity

The score is **explainable** (factors are visible to admins) and the weights are config-driven. Because the inputs are already a clean feature set keyed per student, swapping the rule engine for an ML model later requires no schema change — only a new `RiskScorer` implementation.

### 15.4 Funnel & cohort analytics

Sales funnel (new → contacted → trial → enrolled, with drop-off and by-source conversion) and retention cohorts (enrollment month vs active months) are computed from `leads`, `lead_activities`, and `students`. Exposed to admin as fixed reports + CSV export in v1.2; a custom report builder is deferred (§5).

---

## 16. Risk Assessment and Mitigation Plan

Each risk: likelihood/impact, and the concrete v1.2 mitigation (with the spec section that implements it).

### 16.1 Security risks

| Risk | L/I | Mitigation |
|---|---|---|
| Data leakage between roles | H/H | Three-layer authz on every endpoint; role-matrix pen-test in acceptance (§12, §17, §18) |
| Cache leakage after logout/login | H/H | Namespaced query keys + full logout purge + identity-change guard + E2E test (§13.4) |
| Weak permission checks | M/H | Declarative `@require` + scope resolvers; default-deny; tested per role (§12.2) |
| Student/parent seeing others' data | H/H | `StudentScope` / `parent_links` resolvers; list endpoints scoped (§12.3) |
| Teacher seeing admin finance | H/H | Finance permissions absent from teacher set; routes 403 (§12.5) |
| Insecure Telegram linking | M/H | Single-use, short-lived, server-issued link codes; webhook secret; per-chat scope (§9.2) |
| Missing audit logs | M/H | Event-driven append-only audit on all sensitive actions (§14.2) |
| Token theft / replay | M/H | Refresh rotation + family revocation + token_version force-logout (§12.1) |

### 16.2 Business risks

| Risk | L/I | Mitigation |
|---|---|---|
| Product too broad/unfocused | H/H | Strict scope discipline; nine prioritized pains; explicit out-of-scope (§4, §5) |
| LMS too basic to sell premium | H/H | Roadmap + tests + weak-topic + growth analytics + badges ship in v1.2 (§4.3–4.6) |
| CRM lacks sales/debt workflow | H/H | Pipeline, conversion, debt aging, automated reminders (§4.1–4.2, §4.8) |
| Teachers don't use it daily | M/H | Fast bulk attendance, quick test creation, mobile-first teacher workspace (§3.2, §20) |
| Students have no reason to return | M/H | Roadmap, badges, instant results, growth trend, bot reminders (§3.3, §9.3) |
| Parents see too little value | M/H | Child dashboard, alerts, debt visibility via web + Telegram (§3.4, §9.3) |
| Support cost > subscription | M/M | Clear empty/error/forbidden states, self-service flows, onboarding hints (§8.4, §20) |

### 16.3 Technical risks

| Risk | L/I | Mitigation |
|---|---|---|
| Poor mobile layout | H/M | Distinct mobile layouts, bottom-tab nav, card tables (§8.5, §20) |
| Slow tables/reports | M/H | Pagination, indexes, read models, async reports (§13) |
| N+1 queries | M/M | Eager loading + query-count test guards on hot paths (§13.2) |
| No background jobs | M/H | Redis worker for all heavy/async work from day one (§6.4, §13.5) |
| No branch/tenant foundation | H/H | `organization_id`/`branch_id` on every scoped table (§10.1) |
| No observability | M/H | Structured logs, request IDs, metrics, error tracking from day one (§6.4) |
| No migration strategy | M/H | Alembic forward-only, additive-first, reviewed (§6.5) |
| No backup/restore | M/H | Daily snapshots + WAL + tested restore runbook (§6.5) |

### 16.4 UX risks

| Risk | L/I | Mitigation |
|---|---|---|
| Same UI for all roles | H/H | Four separate route trees + layouts, not conditional menus (§8.2) |
| Irrelevant menu items per role | M/M | Nav derived from `/me` permission set (§8.2, §11.2) |
| Generic error messages | M/M | Typed errors + human messages + request ID (§8.4, §11.1) |
| Confusing forms | M/M | Single-column, validated, sticky actions, inline help (§20) |
| No forbidden/empty states | M/M | Four mandatory UI states on every view (§8.4) |
| Poor mobile navigation | M/H | Role-specific bottom tabs + more sheet (§20) |

### 16.5 Top risk register (watch-list)

1. Cross-role/session data leakage — **gating**, zero tolerance.
2. Scope creep diluting premium quality — enforced by scope discipline.
3. Teacher non-adoption — measured weekly; UX iterated.
4. Mobile performance on low-end devices — budgeted and tested.

---

## 17. QA / Test Plan

### 17.1 Test pyramid

- **Unit tests** — domain services, authz scope resolvers, grading logic, risk scoring, validators. Highest count.
- **Integration tests** — repository + DB (tenant filter correctness), event consumers, job execution.
- **API/contract tests** — every endpoint, every role, success + forbidden + validation paths.
- **E2E tests** (Playwright) — the four role journeys (§3) end-to-end on desktop + mobile viewports.
- **Non-functional** — load, security, accessibility.

### 17.2 Security & isolation test suite (non-negotiable, gating)

| Test | Asserts |
|---|---|
| **Role-matrix sweep** | Every endpoint called with each role's token returns the spec-correct allow/deny. Generated from the §2.3 matrix. |
| **Cross-tenant probe** | User from org A cannot read/write any org B resource (all domains). |
| **Ownership scope** | Teacher denied non-assigned student; parent denied non-linked child; student denied other students. |
| **Logout/login cache** | Login A → logout → login B → assert zero A-data in cache/UI/network (the v1.0 bug, automated). |
| **Token lifecycle** | Rotation works; reused refresh revokes family; revoked access rejected; force-logout-all works. |
| **No-default-password** | New user cannot log in until invite/temp flow completed; temp password forces change. |
| **Rate limit** | Auth + bot endpoints throttle as configured. |
| **Audit completeness** | Every sensitive action produces an audit row with before/after. |

### 17.3 Functional coverage by domain

Each domain ships with tests for happy path, validation failures, scope denial, and event emission. Specific must-cover cases: lead→student conversion integrity; bulk attendance idempotency; test auto-grading correctness (incl. multi-select & partial credit); invoice status transitions (unpaid→partial→paid→overdue→void); roadmap milestone unlock logic; weak-topic aggregation correctness.

### 17.4 Performance & load

- p95 latency assertions on hot endpoints (§13.1) in CI against a seeded dataset (e.g., 1 org, 20 groups, 1,000 students, 50k attendance rows).
- Query-count guards (no N+1) on list/dashboard endpoints.
- Load test: concurrent attendance marking + dashboard reads at peak class-change time.

### 17.5 Mobile, accessibility, compatibility

- E2E across desktop + mobile viewports; manual smoke on real low/mid-tier Android.
- WCAG AA: contrast, focus order, tap-target size, screen-reader labels on key flows.
- Telegram bot: linking, role menus, and notification delivery tested in a staging bot.

### 17.6 CI gates & process

- PRs blocked unless: lint + type-check pass, unit/integration/contract green, **security/isolation suite green**, migration present for schema changes, no secret-scan hits.
- Staging deploy runs full E2E + load smoke before production promotion.
- Quarterly: restore-from-backup drill; dependency/container scan review.

---

## 18. Acceptance Criteria

v1.2 is acceptable **only if all of the following pass.** Each maps to verifiable tests (§17).

### 18.1 Role separation & isolation (gating)

1. Admin, Teacher, Student, and Parent each have a **separate route tree, layout, and dashboard** — verified by E2E per role.
2. **No user can see data from another role, another tenant, or a previous session** — role-matrix sweep, cross-tenant probe, ownership tests, and the logout/login cache test all pass with zero leaks.
3. Nav per role shows only permitted items; every unauthorized API call returns 403 regardless of UI.

### 18.2 Student experience

4. Student app provides schedule, learning roadmap, assigned tests, results, attendance, payment status, notifications, and personal growth analytics — all scoped to self.
5. Objective tests auto-grade on submit; weak topics surface to the student.

### 18.3 Teacher workspace

6. Teacher can mark attendance (bulk), create and assign tests, review results, see weak topics, and identify low-performing students — only within assigned/granted groups.

### 18.4 Parent portal

7. Parent sees child progress, results, attendance, and payment/debt status for **linked children only**, on web and via Telegram.

### 18.5 Admin CRM

8. Admin CRM supports leads/sales pipeline with conversion, student/teacher/group management, payments with debt tracking + reminders, attendance monitoring, and filterable reports with CSV import/export.

### 18.6 Platform & non-functional

9. Telegram bot supports the core role-based workflows with secure linking.
10. Web app is responsive and genuinely usable on desktop and mobile (distinct mobile layout, not shrunk desktop).
11. Backend is demonstrably ready for AI, Face ID attendance, and native mobile apps (documented seams: clean JSON REST, attendance/notification/payment provider interfaces, event stream, tenancy columns).
12. Performance targets (§13.1) met at p95 on the seeded dataset.
13. Every sensitive action is audited; auth uses rotating refresh tokens with revocation; no default passwords exist.
14. Migrations, backups, observability, and background jobs are in place and exercised.

### 18.7 Definition of Done (per feature)

A feature is done when: backend endpoint(s) authorized + validated + audited; repository tenant-scoped; unit/integration/contract tests green incl. scope-denial; frontend implements loading/empty/error/forbidden; mobile layout verified; events emitted and consumed; docs/changelog updated.

---

## 19. 90-Day Implementation Roadmap

Three phases, each ~30 days. Priority order follows the nine stated pains. Each phase ends shippable.

### Phase 0 — Pre-flight (Days 1–5, overlaps Phase 1)
- Lock this spec; set up environments, CI, observability, Alembic, Redis worker, secret management.
- Define the **authz engine + tenant context + base model** scaffolding (the foundation everything else depends on).

### Phase 1 — Foundation, security & isolation (Days 1–30) — *pains #1, #2, #9*
**Goal: the trust layer is bulletproof before features land.**
- Tenancy columns + base model on all tables; org/branch entities.
- Auth: invite/temp-password flow, Argon2id, JWT access + refresh rotation + revocation, `/me`.
- Authorization engine: permission matrix, scope resolvers, default-deny; role-matrix + cross-tenant test suite **green and gating**.
- Frontend: four role route trees + layouts, nav from `/me`, **cache isolation + logout purge** with passing E2E.
- Audit log core + event bus + first consumers.
- Four mandatory UI states baked into the component library.
- **Exit:** isolation/security acceptance criteria (18.1) pass. Nothing else proceeds until they do.

### Phase 2 — Operations & learning core (Days 31–60) — *pains #3, #4, #5*
**Goal: the product becomes valuable to run a business and to learn.**
- Admin CRM: leads, pipeline board, sources, conversion, follow-ups, trials, conversion analytics.
- Students/Teachers/Groups/Courses CRUD with scoped lists + search (indexed).
- Payments: invoices, statuses, debt aging, payments, receipts; overdue scan + reminder jobs.
- Attendance: fast bulk marking via `AttendanceSource` abstraction; admin monitoring.
- Tests: question bank, MCQ, assignment, attempts, auto-grading, results dashboard, weak-topic analytics.
- Learning roadmap: milestones, progress, checkpoints, badges; student progress view.
- Analytics read models + nightly rollups; admin/teacher/student dashboards reading precomputed data.
- **Exit:** acceptance criteria 4–8, 12 pass.

### Phase 3 — Engagement, polish & future-proofing (Days 61–90) — *pains #6, #7, #8 + readiness*
**Goal: premium feel, mobile, bot, and documented future seams.**
- Parent portal: child dashboard, alerts, scoped views.
- Telegram bot: secure linking, role menus, notification delivery for all four roles.
- Mobile-first responsive pass: bottom-tab nav, card tables, form ergonomics; performance budget enforced.
- At-risk scoring job + admin/teacher surfacing.
- Reports + CSV import/export; notification center.
- Future-readiness: finalize and document provider interfaces (payment, notification, attendance, AI stub), event stream, Super Admin guard.
- Full regression: load, security, accessibility, restore drill.
- **Exit:** all acceptance criteria (§18) pass; production promotion.

### Milestone summary

| Day | Milestone |
|---|---|
| 30 | Secure, isolated multi-role shell live; isolation suite gating |
| 60 | CRM + payments + tests + roadmap + attendance + analytics usable |
| 90 | Parent portal + bot + mobile polish + future seams; v1.2 GA |

*Sequencing rule:* security/isolation (Phase 1) is a hard gate. Within Phase 2, deliver vertical slices (one domain end-to-end: API + tests + UI + states) rather than horizontal layers, so each domain is shippable and demoable.

---

## 20. Premium UX Guidelines for Desktop and Mobile

### 20.1 Premium feel = calm, fast, obvious

Premium is not ornamentation; it is the absence of friction. Every screen answers "what is the one thing I should do now?" instantly. Quiet visual design, instant feedback, no dead-ends.

### 20.2 Design system foundation

- **Tokens:** a single source for color, spacing (4px base), radius, elevation, typography. Light + dark themes.
- **Type scale:** clear hierarchy; generous line-height; one display, body, caption family.
- **Color:** restrained neutral base + one brand accent + semantic colors (success/warning/danger/info). Role accent tints help orient (subtle, accessible-contrast).
- **Components:** shared library with built-in loading/empty/error/forbidden states (§8.4), accessible by default (focus rings, ARIA, AA contrast, ≥44px tap targets).

### 20.3 Layout: desktop vs mobile (distinct, not scaled)

| Aspect | Desktop | Mobile |
|---|---|---|
| Primary nav | Persistent left sidebar (role-specific) | Bottom tab bar, 4–5 role tabs + "More" sheet |
| Data tables | Full tables, sortable columns, inline actions | Card list per row; key fields only; tap → detail |
| Forms | Multi-column where sensible | Single column, large inputs, sticky primary action |
| Density | Comfortable, multi-panel dashboards | One focus per screen; progressive disclosure |
| Actions | Toolbar + row actions | FAB / sticky bottom action bar |

Breakpoints: mobile < 640px, tablet 640–1024px, desktop > 1024px. Mobile is designed first for the teacher (attendance) and student (roadmap/tests) flows — the daily-use cases.

### 20.4 Role-specific dashboards (information hierarchy)

- **Admin:** money first (today/MTD revenue, debt), then operations (active students, attendance rate, at-risk), then growth (leads, conversion), then teacher workload/group performance; quick actions + payment-reminder queue prominent.
- **Teacher:** today's groups and "attendance to mark" at the very top (the daily job), then tests to review, low-performing students, group progress, quick test creation, materials.
- **Student:** today's lessons + next roadmap step first, then assigned tests, progress % and weak topics, latest result, attendance summary, badges.
- **Parent:** child overview card (with switcher), then alerts, attendance, latest results, progress trend, payment status, teacher notes.

### 20.5 Interaction & feedback

- **Optimistic UI** for attendance and toggles; reconcile on server response.
- **Skeleton loaders**, never blank screens; perceived performance matters as much as real.
- **Inline validation** with helpful messages, not error walls on submit.
- **Empty states teach** ("No tests assigned yet — your teacher will add them here").
- **Forbidden states explain** rather than dead-end; offer a route back to the user's own dashboard.
- **Confirmation** for destructive/financial actions; **undo** where feasible.
- **Toasts** carry request IDs on error for support.

### 20.6 Navigation clarity

- Each role sees only its relevant menu (derived from `/me`); no aspirational/irrelevant items.
- Breadcrumbs on desktop deep pages; back affordance on mobile detail screens.
- Global search scoped to what the role may see (students/groups for admin/teacher; own content for student/parent).

### 20.7 Performance as UX

Honor §13.1 budgets: prefetch the dashboard's primary query at login, lazy-load charts, virtualize long lists, debounce search, and keep first interaction under 1.5s on mid-tier mobile. A premium app *feels instant* — the perception is part of the design.

### 20.8 Accessibility & inclusivity

WCAG AA minimum: keyboard navigable, screen-reader labels on key flows, sufficient contrast, motion-reduction respect, and localization-ready strings (the user base is multilingual; no hard-coded text).

---

## Appendix A — Traceability: pains → solutions

| # | Painful problem (priority) | Primary sections |
|---|---|---|
| 1 | Role-based architecture & UI | §2, §3, §8.2, §12, §20.4 |
| 2 | Cache/data leakage prevention | §13.4, §12.5, §17.2 |
| 3 | Admin CRM for sales & operations | §4.1–4.2, §4.8, §10.3, §10.8 |
| 4 | Student roadmap, tests, progress analytics | §4.3–4.6, §10.5–10.6, §15 |
| 5 | Teacher test/lesson control | §3.2, §4.4, §10.6, §10.7 |
| 6 | Parent progress visibility | §3.4, §4.9, §9.3 |
| 7 | Mobile-first responsive redesign | §8.5, §20.3 |
| 8 | Telegram bot role workflows | §9 |
| 9 | Audit logs & future-ready backend | §6.3, §14.2, §7.4 |

## Appendix B — Key architectural decisions (ADR summary)

1. **Modular monolith over microservices** — domain isolation now, extraction later (§6.2).
2. **Backend-enforced 3-layer authz; frontend hiding is UX only** (§12.4).
3. **Tenancy columns on every table from day one** — multi-branch without rewrite (§10.1).
4. **Precomputed analytics read models** — fast dashboards, AI-ready features (§15.1).
5. **Provider interfaces for payment/notification/attendance/AI** — future capabilities as implementations, not rewrites (§6.3).
6. **Cache keys namespaced by identity + full logout purge** — closes the v1.0 leak class (§13.4).

*End of specification.*
