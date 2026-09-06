# Backlog — Family Chore Management Tool

Companion to [plan.md](plan.md) and [architecture.md](architecture.md). Each
task is scoped to one session and assumes only those two docs as context —
no task depends on reading any other task in this file.

## 1. Project skeleton with a passing test
Goal: A running Django project with one green test, so every later task starts from a known-good baseline.
Description: Create the Django project (`config/`) and the three apps (`accounts/`, `households/`, `chores/`) per architecture.md, wire up `pytest`/`pytest-django` and `ruff`, and add `docker-compose.yml` with `web` + `db` (Postgres) services. Add a single trivial test (e.g. a health-check view returning 200) and confirm `pytest` passes both locally and via `docker compose run web pytest`.

## 2. Household and Membership models
Goal: Persist households and who belongs to them.
Description: Implement the `Household` model (`name`, `join_code`, `created_at`) and `Membership` model (`household`, `user`, `role` choice of `PARENT`/`MEMBER`, `is_active`, `joined_at`, `left_at`, `available_days`, `available_hours`) in `households/`, per architecture.md's data model section. Write migrations and model-level tests (uniqueness of `(household, user)`, default role, etc.) — no views yet.

## 3. Signup, login, logout
Goal: A user can create an account and sign in with a username and password.
Description: Wire up `django.contrib.auth`'s built-in login/logout views in `accounts/` and add one signup view using `UserCreationForm` plus a `display_name` field. No email, no OTP — see architecture.md's Auth section. Include tests for successful signup+login and for rejecting a duplicate username.

## 4. Household creation and join-by-code
Goal: A logged-in user can create a household or join an existing one via a code.
Description: Add a "create household" view that creates a `Household`, generates a `join_code`, and makes the creator a `PARENT` `Membership`. Add a `/join/<code>/` view that creates a `MEMBER` `Membership` for the current user. Add a "rotate join code" action restricted to `PARENT`s. Include tests for join, duplicate join, and rotation revoking the old code.

## 5. Active household selection
Goal: A user who belongs to multiple households can switch which one is "current."
Description: Store the active household id in the session (`request.session["active_household_id"]`) as described in architecture.md, with a view/dropdown to switch between the user's active `Membership` rows. Include a test that a user with two households can switch and that all household-scoped views use the session value.

## 6. Role-based permission predicates
Goal: A single, testable place that answers "can this user do this?"
Description: Create `households/permissions.py` with predicate functions (`can_manage_chores`, `can_approve`, `can_manage_members`) that check `Membership.role`, per the Permissions table in architecture.md. Write unit tests for each predicate covering `PARENT`, `MEMBER`, and a user with no membership in the household.

## 7. Category model and default categories
Goal: Chores can be organized into categories.
Description: Implement the `Category` model (`household`, `name`, `is_default`) in `chores/`, seed a fixed set of default categories (e.g. Kitchen, Bathroom, Laundry) for every new household via the household-creation flow from Task 4, and allow `PARENT`s to add custom categories. Include tests for default-category seeding and custom-category creation permission.

## 8. Chore model and create/edit form
Goal: A `PARENT` can define a chore with all its properties.
Description: Implement the `Chore` model (name, description, category, difficulty, estimated/initial minutes, priority, recurrence, due_kind/due_time, point_value, is_collaborative, created_by) per architecture.md, plus a create/edit form gated by `can_manage_chores`. Include tests for field validation and that a `MEMBER` cannot create or edit a chore.

## 9. Chore deletion (hard delete)
Goal: Deleting a chore removes it and all of its history, permanently.
Description: Add a delete view/action for `Chore`, restricted to `PARENT`s, that relies on cascading foreign keys (occurrences, contributions, point awards, streaks) to remove all related history in one transaction, per the hard-delete rule in architecture.md. Include a test that deleting a chore also removes its `ChoreOccurrence` and `PointAward` rows.

## 10. ChoreTemplate library
Goal: New chores can be created from a starter template instead of from scratch.
Description: Implement `ChoreTemplate` (name, category, default difficulty/minutes/points) in `chores/`, seed a small library organized by room/task, and add a "create from template" flow that pre-fills the Task 8 chore form. Include a test that creating a chore from a template copies the template's defaults and can still be edited before saving.

## 11. ChoreDependency and ChecklistItem
Goal: A chore can require another chore first, and can carry an optional checklist.
Description: Implement `ChoreDependency` (self-referential `chore` → `depends_on`) and `ChecklistItem` (`chore`, `label`, `position`) models with basic CRUD in the chore edit form from Task 8. Include a test preventing a chore from depending on itself and one confirming checklist items are ordered by `position`.

## 12. ChoreOccurrence model and on-demand generation
Goal: Recurring chores produce a claimable instance for the current period, generated lazily.
Description: Implement `ChoreOccurrence` (chore, period_start, due_at, window_label, status, claimed_by, claimed_at, completed_by, completed_at) and the `ensure_occurrences_exist(household)` function described in architecture.md, using `get_or_create` on `(chore, period_start)` so it's safe to call on every page load. Include tests for DAILY/WEEKLY/MONTHLY period boundaries and for idempotency (calling it twice creates no duplicate rows).

## 13. Claim and unclaim service
Goal: Any active member can claim or release an available chore occurrence.
Description: Implement the claim/unclaim service function in `chores/occurrences.py` that is the sole writer of `ChoreOccurrence.status`/`claimed_by`/`claimed_at`, allowing claims at any time (even before the period starts) and unclaiming with no cooldown. Include tests for claim, unclaim, and re-claim by the same or a different member.

## 14. Overdue detection inline
Goal: Occurrences past their due time are flagged without a background job.
Description: Extend `ensure_occurrences_exist` (from Task 12) to flip any `CLAIMED`/`AVAILABLE` occurrence whose `due_at` has passed to `OVERDUE`, matching the on-demand pattern in architecture.md. Include a test that an occurrence with a past `due_at` is `OVERDUE` after the function runs, and unaffected before its due time.

## 15. Pause a chore or all of a member's chores
Goal: A member can pause specific chores or everything, for a date range or indefinitely.
Description: Implement the `Pause` model (membership, chore nullable, start_date, end_date nullable, ended_at) and the logic that unclaims every currently-`CLAIMED` occurrence covered by a new pause, reusing the unclaim path from Task 13. Include tests for a date-ranged pause, an indefinite pause, and pausing "all chores" (chore=null) releasing every claim.

## 16. Pause resume prompt
Goal: When a pause ends, the original member decides whether to resume — nothing happens automatically.
Description: Add a view that lists a member's ended pauses needing a decision and a "resume" action that has no automatic effect beyond letting the member re-claim through the normal claim flow from Task 13. Include a test confirming an ended pause does not auto-reclaim any occurrence.

## 17. Leave and rejoin a household
Goal: A member can leave a household, and later rejoin without losing points/badges/streaks.
Description: Implement a "leave" action that sets `Membership.is_active=False`/`left_at`, releases the member's active claims (reusing Task 13's unclaim path), deletes their completed-occurrence history, but preserves `PointAward`/`MemberBadge`/`Streak` rows, plus a "rejoin" action via the same join code that flips `is_active=True` again. Include tests for each preserved/deleted data category.

## 18. Mark an occurrence complete
Goal: A member can mark a chore occurrence as Done, with no partial-completion state.
Description: Add a completion view that sets `ChoreOccurrence.status=DONE`, `completed_by`, `completed_at` in one transaction — completion is binary, per architecture.md. Include tests that only `AVAILABLE`/`CLAIMED` occurrences can be completed and that completion is idempotent (completing twice doesn't double-write).

## 19. Photo proof upload
Goal: A completion can optionally include a photo as proof.
Description: Add an optional image field to the completion form from Task 18, handled as a normal multipart POST; on save, resize and strip EXIF with Pillow before streaming to the S3-compatible bucket via `django-storages`. Include a test that an uploaded image is resized to the configured max dimension and that completion without a photo still works.

## 20. Parent confirmation of a completion
Goal: A `PARENT` can confirm (or leave unconfirmed) a completed chore.
Description: Add a confirmation action restricted to `can_approve` (Task 6) that sets `parent_confirmed_by`/`parent_confirmed_at` on an already-`DONE` `ChoreOccurrence`, independent of whether a photo was attached. Include tests that a `MEMBER` cannot confirm and that confirmation fields stay null until acted on.

## 21. Collaborative chores and manual contributions
Goal: Multiple people can split credit for one chore by entering minutes spent.
Description: Implement the `Contribution` model (occurrence, member, minutes_spent, entered_at) and a form — shown only when `chore.is_collaborative` — for each contributor to manually enter their minutes after the occurrence is completed. Include a test that a non-collaborative chore's completion form has no contribution entry.

## 22. Fairness calculation service
Goal: Compute each member's rolling 7-day workload, adjusted by availability.
Description: Implement `calculate_workload(household, member, as_of)` in `chores/fairness.py` as a pure function summing minutes from `ChoreOccurrence.completed_by` and `Contribution.member` (never `claimed_by`), excluding unclaimed/overdue occurrences, adjusted by the member's `available_hours`. Include tests with a fixed set of occurrences verifying the exact expected percentage/minutes output.

## 23. Unfair-claim warning
Goal: Claiming a chore warns (but does not block) a member whose workload would become more unequal.
Description: Call `calculate_workload` (Task 22) from the claim service (Task 13) before committing a claim, and surface a non-blocking warning message in the UI when the claim would widen the fairness gap beyond a defined threshold. Include a test that the claim still succeeds after the warning is shown.

## 24. Fairness snapshot and trend chart
Goal: The household can see a fairness percentage and its trend over time, not just today's number.
Description: Implement `FairnessSnapshot` (household, member, as_of_date, rolling_minutes, availability_minutes, fairness_pct), written the first time a given day is viewed (inside `ensure_occurrences_exist`, per architecture.md), plus a dashboard component showing an up/down indicator and a line chart from recent snapshots. Include a test that viewing the dashboard twice in one day writes only one snapshot row per member.

## 25. Points on completion
Goal: Completing a chore awards points based on the chore's point value and completion circumstances.
Description: Implement `PointAward` (occurrence, member, points, reason, awarded_at, revoked_at) and call it from the completion flow (Task 18) with reasons `COMPLETION`/`ON_TIME`/`DIFFICULTY`/`HELPING_OTHERS`. Include tests that an on-time completion awards more than a late one and that no points are awarded for an incomplete occurrence.

## 26. Point revocation on invalidation
Goal: If a completed chore is later marked invalid, its points are removed without deleting history.
Description: Add an "invalidate completion" action (restricted to `can_approve`) that sets `PointAward.revoked_at` and excludes revoked awards from all point totals/leaderboard queries, per architecture.md's soft-revoke rule. Include a test that a revoked award no longer contributes to a member's point total but the row still exists.

## 27. Badges for milestones
Goal: A member automatically earns a badge at 10/50/100 completed chores.
Description: Implement `Badge` (name, milestone_count) and `MemberBadge` (member, badge, awarded_at), and extend the completion flow (Task 18) to recompute the member's lifetime completed-chore count and award the first newly-crossed milestone badge. Include tests for crossing exactly one milestone in a single completion and for not re-awarding an already-earned badge.

## 28. Streaks per chore
Goal: Track each member's consecutive on-schedule completions of a specific chore.
Description: Implement `Streak` (member, chore, current_streak, longest_streak, last_period_completed), incrementing on on-time completion and resetting to zero when `ensure_occurrences_exist` (Task 14) flips an occurrence to `OVERDUE`, evaluated against that chore's own recurrence. Include tests for a DAILY chore's streak surviving one completion and breaking after one missed day.

## 29. Leaderboard
Goal: Household members are ranked by (non-revoked) points, always visible.
Description: Add a leaderboard view summing each member's non-revoked `PointAward` points for the active household, sorted descending, with no ability to hide a member's position. Include a test that a revoked award (Task 26) does not count toward leaderboard rank.

## 30. Notifications for unclaimed and overdue chores
Goal: The household is notified when an important chore goes unclaimed or a chore becomes overdue.
Description: Implement `Notification` (household, member nullable, kind, occurrence, created_at, read_at), writing a row from the unclaim service (Task 13) and from `ensure_occurrences_exist`'s overdue/unclaimed-escalation check (Task 14), per architecture.md's three notification kinds only (no upcoming-due reminders). Include tests that each trigger creates exactly one notification and that a low-priority unclaimed chore does not trigger the escalation kind.

## 31. Notifications display
Goal: Members can see and dismiss their unread notifications.
Description: Add an HTMX-polled partial that queries unread `Notification` rows for the active household/user and a "mark read" action setting `read_at`. Include a test that marking one notification read does not affect others' unread state.

## 32. Comments on a chore
Goal: Members can leave comments on an individual chore.
Description: Implement the `Comment` model (chore, author, text, created_at) and a simple add/list view on the chore detail page — no family-wide chat, per architecture.md. Include a test that comments are ordered by creation time and scoped to the correct chore.

## 33. Family dashboard view
Goal: One page shows today's chores, workload/fairness per person, overdue, and unclaimed chores.
Description: Build the dashboard view combining `ensure_occurrences_exist` (Task 12/14), `calculate_workload` (Task 22), and simple filters/sorting by person/date/status, per architecture.md's Family Dashboard section. Include a test that overdue and unclaimed sections only show occurrences in those respective statuses.

## 34. My Chores view
Goal: A member sees their own today/upcoming/overdue chores plus suggestions.
Description: Build the My Chores view filtering occurrences by `claimed_by=current membership`, grouped into Today/Upcoming/Overdue sections, plus a "suggested chores" section of available occurrences visible to members with lower workload (per `calculate_workload`). Include a test that a suggested chore appears for a below-average-workload member and not for an above-average one.

## 35. Household-wide search
Goal: Members can search across chores, people, categories, and activity/history.
Description: Add a search view/endpoint that queries `Chore`, `Membership` (by display name), `Category`, and recent `ChoreOccurrence` completions within the active household, returning a combined result list. Include a test that results are scoped to the active household and don't leak another household's data.

## 36. Suggested-chores logic
Goal: The app suggests (never auto-assigns) available chores to members with lower workload.
Description: Implement the suggestion query used by Task 34 as its own testable function in `chores/fairness.py` (or alongside it) that ranks available occurrences for a given member based on their relative workload, explicitly not writing any assignment/claim. Include a test that running the suggestion function never mutates `ChoreOccurrence` state.

## 37. Availability collection during setup
Goal: Each member's available days/hours are captured when they join a household.
Description: Add available-days/available-hours fields to the join flow (Task 4) and an edit view for a member to update their own availability afterward, feeding directly into `Membership.available_days`/`available_hours` used by `calculate_workload` (Task 22). Include a test that updating availability changes a subsequent fairness calculation for that member.

## 38. Production deployment configuration
Goal: The app runs in a two-service (`web`, `db`) Docker Compose setup suitable for a first deploy.
Description: Finalize `docker-compose.yml`/Dockerfile for `web` (gunicorn) and `db` (postgres:18), environment-variable-driven settings (`DATABASE_URL`, `AWS_*`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DEBUG`) per architecture.md, and a health-check endpoint. Include a smoke test (or documented manual check) that `docker compose up` serves the login page and connects to the database.
