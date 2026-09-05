# Family Chore Management Tool — MVP Scope

## 1. Target Users & Problem

### Target
- Families living together (parents + children).

### Core Problems
- Fairness
- Accountability
- Organization

## 2. Chore Assignment & Claiming

- Family members choose/claim chores themselves.
- Anyone can claim any available chore.
- The app warns when claiming would make workload unfair.
- Claims happen immediately.
- Another family member can challenge/request reassignment.
- Chores can be claimed anytime, even before their scheduled period.
- Chores can be unclaimed anytime.
- When unclaimed, the chore becomes immediately available to others and the household is notified.
- No limit on how many times someone can claim the same chore consecutively.
- No chore swapping.
- All chores are visible to the household; no private/personal chores.
- Members cannot mark chores as “Not applicable.”

## 3. Unclaimed & Missed Chores

- If an important chore is unclaimed:
  - Parent gets a notification.
  - Family can vote/decide who takes it.
- If a chore is missed:
  - Mark it overdue and notify the member.
  - Escalate to a parent.
- Unclaimed chores do not affect fairness.
- Overdue chores do not affect fairness.
- Unclaimed chores do not become more urgent as the due date approaches.
- No upcoming-chore reminders.

## 4. Chore Scheduling

### Recurrence
MVP supports only:
- Daily
- Weekly
- Monthly

No custom intervals or specific-day recurrence beyond these basic frequencies.

### Due Dates
A chore can have:
- A due date with optional time, OR
- A flexible window such as “anytime today.”

No separate time-of-day scheduling system.

### Pausing
Members can pause:
- An individual chore, or
- All of their chores.

A pause can be:
- For a defined date range, or
- Indefinite.

When paused:
- The affected chores immediately become available for others to claim.

When the pause ends:
- The original member chooses whether to resume the chore.

## 5. Chore Properties

Each chore can include:
- Name/description
- Category
- Difficulty
- Estimated minutes
- Priority: Low / Medium / High
- Recurrence
- Due date/window
- Optional checklist/subtasks
- Optional before/after photos
- Optional dependencies where order matters
- Point value

### Categories
- Default categories
- Custom categories

Categories are organized around tasks/areas such as:
- Kitchen
- Bathroom
- Laundry
- etc.

Chores do NOT require a room/location field.

### Difficulty & Time
- Both difficulty and estimated minutes are tracked.
- The app suggests an initial estimate.
- The app learns actual completion time over time.
- Members can manually adjust the estimate.

### Priority
- Low / Medium / High.
- Priority affects visibility/notifications only.
- Priority does not affect fairness.

## 6. Chore Creation, Editing & Permissions

- Permissions are custom.
- Permissions control who can create, suggest, approve, edit, etc.
- Anyone with edit permission can edit any chore.
- Anyone with edit permission can permanently delete a chore.
- Chore deletion permanently removes all associated history and statistics.
- No separate admin dashboard; everyone uses the same dashboard with permissions controlling actions.

### Templates
The MVP includes:
- A template library
- Fully custom chores

Templates are organized by rooms/tasks.

## 7. Collaborative Chores

- A chore normally has one person responsible.
- The creator can enable multiple people for a chore.
- Collaborative chores split workload based on actual contribution.
- Contributors manually enter the minutes they spent.
- No timer is required.
- Partial completion is not supported: a chore is either Done or Not Done.

## 8. Completion Verification

Completion verification combines:
- Optional photo proof
- Optional parent confirmation

## 9. Fairness System

Fairness is based on **workload**, not simple chore count.

### Fairness Calculation
- Uses weekly chore minutes.
- Adjusts workload based on each person's availability.
- Age/ability is not used in fairness calculations.
- Only completed chores count.
- Overdue chores do not reduce fairness.
- Unclaimed chores do not affect fairness.
- The person who actually completes a chore receives the workload credit, even if someone else originally claimed it.

### Availability
Each person can set:
- Available days
- Available hours

Availability is also collected during household setup.

### Fairness Display
Everyone can see:
- A fairness percentage
- Workload comparison with other household members

Fairness is:
- Calculated/displayed weekly
- Based on a rolling 7-day calculation
- Shown with historical trends

The trend display includes:
- Up/down indicator
- Line chart

Fairness trends are visible to everyone.

## 10. My Chores

There is a dedicated **My Chores** view.

It prioritizes:
- Today
- Upcoming
- Overdue

Suggested chores also appear on My Chores.

### Chore Suggestions
- The app suggests available chores to members with lower workloads.
- It does not automatically assign them.
- Suggested chores cannot be declined.
- They remain available until claimed.

## 11. Family Dashboard

The family overview shows:
- All of today's chores
- Each person's workload/fairness
- Overdue chores
- Unclaimed chores
- Upcoming chores

Users can:
- Filter
- Sort
- Switch views by person/date/status

The household also has full search across:
- Chores
- People
- Categories
- Activity/history

There is no family-wide activity feed.

## 12. Notifications

Notifications are intentionally minimal.

The MVP sends notifications for:
- Overdue chores
- Unclaimed chores
- Important unclaimed chore escalation

No upcoming chore reminders.

## 13. Points System

Points are purely for fun/status and do **not** affect fairness.

### Point Factors
Points can be based on:
- Completion
- Difficulty/time
- On-time completion
- Helping others

The chore creator can set the point value for each chore.

### Completion Rules
- Points are awarded only when a chore is fully completed.
- Partial completion does not receive points.
- If a completed chore is later marked invalid/incomplete, its points are removed.
- Points never expire.

## 14. Badges

- Badges are milestone-based only.
- No complex badge categories.
- Examples: 10, 50, 100 chores.
- Badges are awarded automatically.
- Badges are visible to everyone in the household.

## 15. Leaderboard

- Family members are ranked by points.
- Leaderboard is always visible.
- Points and leaderboard positions cannot be hidden.
- Points do not affect fairness.

## 16. Statistics

The chosen stats focus is:
- Points
- Streaks

### Streaks
Streaks measure consistency based on each chore's own schedule.

## 17. Comments & Checklists

### Comments
- Comments are allowed on individual chores.
- No family-wide chat.

### Checklists
- Optional subtasks/checklists can be attached to chores depending on the chore.

## 18. Chore History & Audit

- Full history records who changed what and when.
- Recurring chore history focuses on completion trends/statistics rather than listing every past occurrence individually.
- If a chore is permanently deleted, its history and statistics are also permanently deleted.

## 19. Household Membership

### Accounts
- Each account can belong to multiple households.
- Only one household can be active at a time.

### Joining
- Everyone creates their own account.
- Members join a household using a code.
- Invitations can be sent by email or through a join code/link.

### Login
- Passwordless authentication.
- Email one-time code (OTP).

### Profile
- Minimal profile: name only.

### Leaving
When a member leaves:
- Their active chores immediately become available for others.
- Their completed chore history is removed completely.
- Their points/badges/leaderboard history remains visible.
- Everyone in the household is notified.
- They can be re-added later.

### Rejoining
When a returning member rejoins:
- Their previous account/history/points are restored.
- Their old active chores are automatically restored.

### Removal
- Members can leave themselves.
- A parent/admin cannot remove another member in the MVP.

## 20. Family Setup & Roles

- Custom roles/permissions.
- No fixed parent/child role system.
- Availability is collected during setup.
- No dedicated family settings page in the MVP.
- No family-wide goals.

## 21. Household Expenses

- Not included.
- The MVP is focused on chores only.

## 22. Platforms & Connectivity

### Platform
- Start with web.
- Mobile app may be added later.

### Offline
- Offline support is not part of the MVP.
- Internet connection is required.

## 23. Onboarding

- No onboarding walkthrough.
- Users should be able to figure out the product without a guided tutorial.

## 24. Explicitly Out of Scope for MVP

- Household expense tracking
- Family-wide chat
- Family goals
- Offline mode
- Mobile apps
- Upcoming chore reminders
- Custom recurrence intervals
- Specific time-of-day scheduling
- Private chores
- Chore swapping
- “Not applicable” status
- Separate admin dashboard
- Dedicated family settings page
- Complex badge categories
- Partial completion
- Automatic chore assignment
- Age/ability-based fairness
- Family-wide activity feed
- Custom urgency escalation for unclaimed chores

## 25. Core Product Principle

The product should make household chores feel **fair, visible, accountable, and lightweight**.

The central loop is:

1. Create or select a chore.
2. Members claim available chores.
3. The system estimates and tracks workload.
4. Members complete chores.
5. Completion can optionally be supported by photos/confirmation.
6. Completed work contributes to weekly fairness.
7. Points, badges, and streaks provide fun/status.
8. Unclaimed or overdue chores generate targeted alerts.
9. Members can pause or leave, with chores becoming available for redistribution.
10. The family can see workload and fairness without needing a separate admin experience.
