---
description: Pull the latest changes from the remote repository.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Outline

1. **Check for uncommitted changes**:
   - Run `git status --short`.
   - If there are uncommitted changes, warn the user that they might want to stash or commit them first.

2. **Pull from remote**:
   - Run `git pull origin <branch-name>` (where `<branch-name>` is the current branch).
   - Alternatively, run `git pull` if the upstream is already set.

3. **Handle conflicts**:
   - If there are merge conflicts, inform the user and list the conflicting files.
   - **DO NOT** attempt to resolve conflicts automatically unless instructed.

4. **Summary**:
   - Report whether the pull was successful and what was updated.
