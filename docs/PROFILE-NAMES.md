# Participant name and rating — 2026-11-17

Owner requested mandatory name and surname for personal rating and a way to notify incomplete profiles. No emails were sent; a persistent in-app reminder appears on account, history and rating screens until the profile is completed.

Existing users.name is retained. POST /api/profile accepts first_name and last_name, validates letter-based names (hyphens/apostrophes supported), updates only the authenticated user and records profile_updated in audit. Email/id/admin fields in payload cannot change identity or role. The avatar opens a profile form; fields are separate and required. New registration uses the same validation.

Session exposes user.profile_complete. Rating excludes incomplete names server-side, but total continues to include all approved non-deleted workouts. Completing the profile immediately restores prior approved results to ranking. No workout dates, statuses or distances were modified.

43 Python tests passed. Browser QA used mocked API fixtures: reminder, required surname, validation error, save, disappearance of reminder, return to ranking, retained profile fields and mobile width. Backup before release: snapshot-20261117T014032117180Z. Existing dirty frontend worktree was not overwritten; release uses app-rating-release worktree.
