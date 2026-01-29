---
description: Push the current branch to the remote repository.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Outline

1. **Get current branch**:
   - Run `git rev-parse --abbrev-ref HEAD` to determine the current branch name.

2. **Push to remote**:
   - Run `git push -u origin <branch-name>`.

3. **Status Report**:
   - Confirm if the push was successful or report any errors (e.g., merge conflicts, permission issues).
