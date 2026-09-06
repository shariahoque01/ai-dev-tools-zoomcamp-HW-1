# Architecture — Family Chore Management Tool

Companion to [plan.md](plan.md). Describes *how* the MVP is built. No code yet.

## Stack

Versions verified 2026-09-05 against PyPI and endoflife.date.

| Concern | Choice | Version |
|---|---|---|
| Language | Python | 3.14 |
| Framework | Django | 6.1 |
| Database | PostgreSQL | 18 |
| DB driver | psycopg | 3.3 |
| App server | gunicorn | 26 |
| Templates / interactivity | Django templates + HTMX (no separate API layer) | 2.0 |
| Styling | Tailwind (CSS-first config) | 4.x |
| Auth | `django.contrib.auth` — username + password. No email, no OTP, no password reset flow | — |
| Household join | Shareable join code / link (rotatable) | — |
| Background jobs | None — see [On-demand occurrence generation](#on-demand-occurrence-generation-no-background-jobs) | — |
| File storage | `django-storages` + S3-compatible bucket (chore proof photos) | 1.14 |
| Image handling | Pillow (resize/strip EXIF on server-side save) | 12.x |
| Sessions / cache | Database-backed sessions, local-memory cache | — |
| Tests / lint | pytest, pytest-django, ruff | latest / 4.14 / 0.16 |
| Deploy | Docker Compose — `web`, `db` | — |

**Postgres is the only infrastructure dependency, and Django is the only
framework.** No Redis, no message broker, no Celery, no DRF, no worker
container, no cron/scheduler container, no mail server. Everything the plan
needs — claiming, fairness, points, notifications, login — is read/write on
request, not a job queue or a third-party service.

This is a deliberate trade against reaching for more infrastructure by
default. For a household-sized MVP (a handful of members, a few dozen
chores), the volume of work per request is trivially small, so **doing it
inline, on the request that needs it, removes an entire class of
infrastructure** (a worker process, a scheduler process, an email
provider, retry/backoff semantics) for a cost of a few extra milliseconds on
the dashboard load. See
[On-demand occurrence generation](#on-demand-occurrence-generation-no-background-jobs)
for exactly how that trade is implemented, and [Auth](#identity-and-household-membership)
for why login needs none of it either.

## Django apps

```
config/          settings, urls
accounts/        User (django.contrib.auth), login/logout/signup views
households/      Household, Membership (role, availability), join links
chores/          Chore, ChoreTemplate, Category, Dependency, Checklist,
                 ChoreOccurrence, Contribution, Pause,
                 fairness calculation, points/badges/streaks, notifications
```

Three apps. `accounts/` is intentionally thin — it exists only to wrap
`django.contrib.auth`'s login/logout views and a one-field signup form, since
there is no OTP, no email, and no custom `User` fields beyond what Django
ships with (plus `display_name`, see below). `chores/` is the large app —
occurrences, fairness, and rewards are all different views onto the same
`ChoreOccurrence` row (who claimed it, who completed it, how many minutes),
so splitting them into separate apps would add import indirection without
adding isolation: nothing in fairness or rewards logic is ever reused outside
a chore context. Internally it's organized by concern —

```
chores/
  models.py          Chore, ChoreTemplate, Category, ChoreDependency, ChecklistItem,
                      ChoreOccurrence, Contribution, Pause,
                      PointAward, Badge, MemberBadge, Streak, Notification, Comment
  occurrences.py      ensure_occurrences_exist(), claim/unclaim/pause/complete services
  fairness.py         calculate_workload(household, member, as_of) — pure function
  rewards.py          point-award + badge + streak logic, called from the completion service
  notifications.py    unclaimed/overdue notification creation, called inline (see below)
  views.py, urls.py   dashboard, My Chores, chore detail/edit, completion form
```

— but there's one app boundary, one migrations history, one place to look.

## Data model

### Identity and household membership

```
User            django.contrib.auth.models.User — username, display_name, password
Household       name, join_code (rotatable token), created_at
Membership      household, user, role {PARENT, MEMBER}, is_active (bool),
                joined_at, left_at (nullable)
                available_days (set), available_hours (range), unique(household, user)
```

**Auth is as simple as Django gets: username and password, nothing else.**
No custom `User` model, no email field, no OTP model, no code-sending, no
password-reset flow, no third-party auth provider. `accounts/` wires up
`django.contrib.auth.urls` (login, logout — built in) plus one signup view
that is a plain `UserCreationForm` with a `display_name` field added. A
forgotten password is fixed by a household `PARENT` or a superuser via
`manage.py changepassword` — acceptable for a small trusted household tool,
and the same trade the reference architecture this borrows from makes
deliberately.

This replaces an earlier, more "modern-feeling" design that used passwordless
email one-time-codes. That required a `OneTimeCode` model, code hashing,
expiry/attempt-count logic, and a working transactional email path just to
answer "who is this." None of that is required by the plan — it asks for
"passwordless authentication," but username+password is simpler to build,
simpler to reason about, and has zero external dependencies (no SMTP/email
API to configure or fail). If passwordless login matters enough later, it's a
single additive auth backend, not a rewrite of this data model.

**Household join is a link, not an invitation record.** Each household
carries a `join_code`; sharing `/join/<code>/` lets any logged-in user become
a `Membership`. The code is rotatable, which revokes every outstanding link
at once. No `Invitation` table, no pending-invite state.

**Permissions are a single `role` field, not a permission matrix.** The
plan's own list of actions — create/edit/delete chores, approve completions,
manage members — splits cleanly along one axis, so `Membership.role`
(`PARENT` / `MEMBER`) captures it with one column and one predicate module.
This does **not** reintroduce the fixed parent/child *family* role system the
plan rejects — `PARENT` here means "has management rights in this
household," and any adult member can be granted it. See
[Permissions](#permissions) for the exact rule table.

**One active household at a time.** Since `User` is now Django's stock model,
"which household's dashboard is shown" is stored on the session
(`request.session["active_household_id"]`) rather than a custom FK column —
one less thing a custom `User` model would need to carry. A user can hold
multiple `Membership` rows but only one is "current" per session.

**Leave / rejoin is a lifecycle on `Membership`, not a delete.** Leaving sets
`is_active=False` and `left_at`; their `ChoreOccurrence.claimed_by` rows are
released (see below) and their completed-occurrence history rows are deleted
(cascade), but `PointAward`, `MemberBadge`, and `Streak` rows are kept —
per the plan, points/badges/leaderboard history survives, chore history does
not. Rejoining flips `is_active=True` again; any claim that was released on
leave is gone (nothing auto-restores a claim into a state where two other
members may have since acted on it), but points/badges/streaks continue from
where they left off since those rows were never touched.

### Chores and templates

```
Category        household, name, is_default (bool)
ChoreTemplate    name, category, default difficulty/minutes/points (organized by room/task)
Chore            household, name, description, category, difficulty,
                 estimated_minutes, initial_estimate, priority {LOW, MEDIUM, HIGH}
                 recurrence {NONE, DAILY, WEEKLY, MONTHLY}
                 due_kind {FIXED_TIME, WINDOW}, due_time (nullable)
                 point_value, is_collaborative (bool)
                 created_by -> User, created_at
ChoreDependency  chore, depends_on -> Chore (self-referential, "must finish first")
ChecklistItem    chore, label, position
```

Deleting a `Chore` is a hard delete. Per the plan, deletion permanently
removes all history and statistics — `ChoreOccurrence`, `Contribution`,
`PointAward`, and `Streak` rows referencing it cascade. No soft-delete flag,
no "archived" state to reason about, and no separate audit log to clean up
after it — see [Audit trail is columns, not a log table](#audit-trail-is-columns-not-a-log-table).

### Occurrences — the recurring-chore engine

A `Chore` is the recipe; a `ChoreOccurrence` is one instance of it to be
claimed and completed.

```
ChoreOccurrence  chore, period_start, due_at (nullable), window_label (nullable)
                 status {AVAILABLE, CLAIMED, DONE, OVERDUE}
                 claimed_by -> Membership (nullable), claimed_at
                 completed_by -> Membership (nullable), completed_at
                 photo_proof (nullable, S3 key via server-side upload), parent_confirmed_by (nullable), parent_confirmed_at
                 unclaimed_notified_at, overdue_notified_at
Contribution     occurrence, member, minutes_spent, entered_at
                 # only used when chore.is_collaborative
Pause            membership, chore (nullable = pauses all of the member's chores)
                 start_date, end_date (nullable = indefinite), created_at, ended_at (nullable)
```

#### On-demand occurrence generation (no background jobs)

There is no daily task walking every `Chore` to create the next
`ChoreOccurrence`. Instead, every view that reads occurrences for a household
(dashboard, My Chores, chore detail) first calls
`chores/occurrences.py:ensure_occurrences_exist(household)`:

```python
def ensure_occurrences_exist(household):
    for chore in household.chores.filter(recurrence__ne=Chore.Recurrence.NONE):
        current_period = period_start_for(chore.recurrence, today())
        ChoreOccurrence.objects.get_or_create(
            chore=chore, period_start=current_period,
            defaults={"status": "AVAILABLE", "due_at": due_at_for(chore, current_period)},
        )
```

`get_or_create` on `(chore, period_start)` makes this idempotent and safe to
call on every request — the common case is "the row already exists," which is
one indexed query per chore, and only creates a row the first time anyone
loads a view after a period rolls over. The same function also flips any
`CLAIMED`/`AVAILABLE` occurrence whose `due_at` has passed to `OVERDUE` and
writes the overdue/unclaimed `Notification` rows inline (see
[Notifications are created inline](#notifications-are-created-inline)),
instead of a separate scheduled scan.

The cost accepted here: fairness/streak numbers and overdue status are only
as fresh as the last time *someone* in the household loaded a page — for an
app with no upcoming-due reminders and no push notifications, that's already
the ceiling on freshness the plan asks for, so a background job would not
make anything more "real-time" than the plan actually needs.

**Claim/unclaim/pause all funnel through one state transition, not a status
field edit.** A service function (`chores/occurrences.py`) is the only
writer of `ChoreOccurrence.status`, `claimed_by`, and `claimed_at`, so the
"notify household on unclaim" and "warn if this claim is unfair" side effects
can't be forgotten by a view that edits the row directly:

- **Claim**: any active member, any time (even before the period starts). Sets
  `status=CLAIMED`, `claimed_by`. Computes the claimant's rolling workload
  first and returns a warning (not a block) if the claim would widen the
  fairness gap.
- **Unclaim**: sets `status=AVAILABLE`, `claimed_by=None`, and writes a
  household-wide `Notification` row in the same transaction. No cooldown —
  the same member can immediately reclaim it.
- **Pause**: creates a `Pause` row; every `ChoreOccurrence` it covers that is
  currently `CLAIMED` by that member is unclaimed (same code path as above).
  When the pause ends (`end_date` reached or explicitly ended), the *member*
  is prompted to re-claim — nothing auto-resumes, because the plan is explicit
  that resuming is the original member's choice, not automatic.
- **Leave**: identical release step as pause, but the `Membership` itself goes
  inactive rather than a `Pause` row being created.

**Completion is either Done or Not Done.** There's no partial-completion
state on `ChoreOccurrence.status` — collaborative chores split *workload
credit* via `Contribution` rows entered manually by each contributor, but the
occurrence itself flips to `DONE` in one write, by whoever marks it complete.
Photo proof and parent confirmation are both optional fields on the same row,
checked independently by the UI, not a separate approval workflow/state
machine. Photo proof is a normal multipart form POST handled by a Django view
— the view calls `.save()` on the uploaded file, Pillow resizes/strips EXIF,
and `django-storages` streams the result to the bucket; there is no
presigned-URL client-side upload step to build or secure.

### Fairness

```
FairnessSnapshot  household, member, as_of_date, rolling_minutes,
                  availability_minutes, fairness_pct
```

**Fairness is computed on read, not maintained by a job.** The core
calculation — rolling 7-day completed minutes per member, adjusted by that
member's availability — is a pure function over `ChoreOccurrence` and
`Contribution` rows (`chores/fairness.py:calculate_workload`), called
whenever the dashboard or My Chores view renders. `FairnessSnapshot` still
exists, but a row is written the first time a given day is viewed by anyone in
the household (also inside `ensure_occurrences_exist`, since both are "make
sure today's data exists" concerns) rather than by a scheduled nightly job —
same on-demand pattern as occurrence generation, so the trend chart has
history without ever needing a process that runs on a clock.

**Credit follows the completer, not the claimant.** `calculate_workload` sums
minutes from `ChoreOccurrence.completed_by` (or `Contribution.member` for
collaborative ones) — `claimed_by` is never part of the sum. Unclaimed and
overdue occurrences are excluded entirely; they affect notifications, never
this number.

### Rewards — points, badges, streaks, leaderboard

```
PointAward    occurrence, member, points, reason {COMPLETION, ON_TIME, DIFFICULTY, HELPING_OTHERS}
              awarded_at, revoked_at (nullable)
Badge         name, milestone_count (10 / 50 / 100 …)
MemberBadge   member, badge, awarded_at
Streak        member, chore, current_streak, longest_streak, last_period_completed
```

Points are awarded synchronously, in the same request/transaction that marks
an occurrence `DONE` (`chores/rewards.py`, called directly from the
completion view — never at claim time, and never for partial work). If an
occurrence is later invalidated, the same completion-adjacent code path sets
`revoked_at` rather than deleting the row — the plan says points are removed
on invalidation but never expire otherwise, so a soft revoke keeps an honest
record without resurrecting "expired" language anywhere.

Badges are milestone-only and awarded automatically: the same completion
call recomputes the member's lifetime completed-chore count and creates a
`MemberBadge` the first time a threshold is crossed. No badge categories, no
manual awarding, no separate job scanning for "who just crossed 50."

Streaks are per `(member, chore)`, evaluated against that specific chore's own
recurrence — a DAILY chore's streak breaks on a missed day, a WEEKLY chore's
streak breaks on a missed week. Updated inline by the same completion call and
by `ensure_occurrences_exist`'s overdue check (a streak breaks the moment an
occurrence is flipped to `OVERDUE`, which happens the next time anyone loads a
page — see [On-demand occurrence generation](#on-demand-occurrence-generation-no-background-jobs)).

### Comments, checklists, notifications

```
Comment              chore, author, text, created_at
ChecklistCompletion  occurrence, checklist_item, done_by, done_at
Notification         household, member (nullable = household-wide),
                     kind {OVERDUE, UNCLAIMED, IMPORTANT_UNCLAIMED_ESCALATION},
                     occurrence, created_at, read_at
```

#### Notifications are created inline

There's no separate notifier process. `Notification` rows are written at the
two moments the plan cares about, both already inside a request:

- **Unclaim**: written by the unclaim service function, in the same
  transaction as the status change.
- **Overdue / important-unclaimed escalation**: written by
  `ensure_occurrences_exist` the moment it flips an occurrence's status,
  which happens on the next page load after the due time passes — not the
  instant it passes, which matches the plan's "no upcoming reminders, no
  custom urgency escalation" stance: nothing here is time-precise by design.

Rendering unread notifications is a normal query (`Notification.objects
.filter(household=household, read_at__isnull=True)`) on every authenticated
page load via a small HTMX-polled partial, not a push channel.

### Audit trail is columns, not a log table

There is no dedicated audit app, model, or signal handlers. For this MVP's
actual audit needs — who claimed, who completed, who confirmed — that
information already lives as plain columns on `ChoreOccurrence`:
`claimed_by`/`claimed_at`, `completed_by`/`completed_at`,
`parent_confirmed_by`/`parent_confirmed_at`. Full chore history in the plan is
explicitly "completion trends/statistics, not a list of every past
occurrence," so those columns plus the `PointAward`/`Streak` rows already
answer every audit question the UI asks. This also makes the hard-delete rule
simpler: deleting a chore cascades to those same rows — there is no separate
log table to remember to also purge.

## Permissions

All authorization lives in `households/permissions.py` as plain predicate
functions (`can_manage_chores(user, household)`, `can_approve(user,
occurrence)`, `can_manage_members(user, household)`), reading
`Membership.role` — not Django's group/permission machinery, and not a
DRF permission class (there is no DRF).

| Action | Rule |
|---|---|
| Claim / unclaim any available chore | Any active member (`PARENT` or `MEMBER`) |
| Create / edit / delete a chore | `role=PARENT` |
| Approve (parent-confirm) a completion | `role=PARENT` |
| Manage members (grant/revoke `PARENT` role) | `role=PARENT` |
| See another member's workload, points, badges | Everyone, always (no private chores) |
| Remove another member | Nobody — members can only leave themselves (MVP) |

Any member can be promoted to `PARENT` by an existing `PARENT` — this is a
household-management role, not literally "the parent," so a household of
housemates can make everyone a `PARENT` if they want flat permissions.

## Deployment

`docker compose up`, two services:

| Service | Command | Notes |
|---|---|---|
| `db` | postgres:18 | named volume for data |
| `web` | gunicorn | serves Django + HTMX templates; handles login and photo upload inline, no separate worker |

There is no `worker` container and no `scheduler` container — every piece of
work that might otherwise be a background task (occurrence generation,
overdue scan, fairness snapshot, notification creation) now runs inline on
the request that needs it, per the sections above. There is also no mail
server to configure, since auth is username/password. Photo proof uploads are
a normal multipart POST to `web`, which streams the resized image straight to
the S3-compatible bucket via `django-storages`; there's no scratch volume to
share between processes because there's only one process.

Config is environment variables: `DATABASE_URL`, `AWS_*` / bucket
credentials, `SECRET_KEY`, `ALLOWED_HOSTS`, `DEBUG`. Nothing email-related —
this app sends no email.

## Open questions for you

1. **Does an unfair-claim warning ever block the claim, or only warn?** The
   plan says "the app warns," assumed non-blocking — confirm a member can
   claim past the warning.
2. **What counts as an "important" chore for the unclaimed-escalation
   notification?** Assumed `priority=HIGH`, but confirm whether it's a
   separate flag instead.
3. **Username+password vs. the plan's "passwordless authentication" line:**
   this doc trades the plan's stated preference for the simplest possible
   build. Confirm that's acceptable for the MVP, versus keeping a
   passwordless flow (email OTP or a magic link) at the cost of the email
   infrastructure this design otherwise avoids entirely.
4. **A forgotten password needs another `PARENT` or a superuser** (via
   `manage.py changepassword`) — there is no self-serve reset without email.
   Confirm that's an acceptable trade for a small household tool.
5. **Streak breaks: does an unclaimed (never assigned) occurrence break a
   streak the same way a claimed-then-missed one does?** The plan says
   unclaimed doesn't affect fairness, but streaks aren't fairness — confirm
   the same exemption applies.
6. **Photo proof storage on chore deletion:** the plan says deleting a chore
   removes all history — confirm this includes deleting the actual photo
   objects from the bucket, not just the DB rows referencing them.
7. **Collaborative chore point split:** points are per-occurrence; assumed
   split proportionally by each contributor's entered minutes, same as
   fairness credit — confirm, versus a flat award to each contributor.
8. **On-demand freshness:** since occurrence rollover, overdue flags, and
   fairness snapshots now only update when *someone* loads a page, is it
   acceptable for a household that opens the app once a day (or less) to see
   stale-until-viewed data, versus the guaranteed-daily freshness a
   background job would give? Confirm this trade is acceptable for the MVP.
