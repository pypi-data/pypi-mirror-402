---
description: Stage all changes, commit with a generated message, and push to create a Pull Request.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input for the commit message if provided.

## Outline

1. **Check for changes**:
   - Run `git status --short` to see what has changed.
   - If no changes are detected, **STOP** and inform the user.

2. **Stage changes**:
   - Run `git add .` to stage all changes in the repository.

3. **Generate commit message**:
   - Analyze the changes, `spec.md`, and `tasks.md`.
   - Create a concise but descriptive commit message following the project's standards (e.g., Conventional Commits).
   - If the user provided input in `$ARGUMENTS`, incorporate it into the message.

4. **Commit changes**:
   - Run `git commit -m "<message>"` with the generated message.

5. **Push and Create PR**:
   - Get the current branch name: `git rev-parse --abbrev-ref HEAD`.
   - Push to remote: `git push -u origin <branch-name>`.
   - Check if the GitHub CLI (`gh`) is installed:
     - **If `gh` is available**:
       - Create a Pull Request: `gh pr create --fill --draft` (or prompt user for options).
       - Provide the PR URL to the user.
     - **If `gh` is NOT available**:
       - Provide the user with the GitHub link to create a PR manually (usually shown in the `git push` output).

6. **Summary**:
   - Final report on what was committed and the PR status.
