SPRINT_MD_TEMPLATE = """# OneCoder Sprint Management Guide


This guide defines the standardized workflow for managing sprints using the `onecoder` CLI. All AI agents and developers must follow these patterns to ensure governance compliance and traceability.

## Standard Sprint Workflow

Follow this cycle for every sprint to maintain rigorous governance:

### Phase 1: Initialization
Start a new sprint context. This creates the `.sprint/<id>` directory.
```bash
onecoder sprint init "sprint-name"
```

### Phase 2: The Task Loop (Repeat for each task)
**CRITICAL**: You must be in an active task to write code.
1.  **Start Task**: `onecoder sprint start "Implement Feature X"`
2.  **Code & Commit**: Implementation loop.
    *   Pass `preflight` checks.
    *   `onecoder sprint commit -m "feat: wip" --files "..."`
3.  **Finish Task**: `onecoder sprint finish` (Marks task done)

### Phase 3: Verification
Before closing, ensure the project is clean and policy-compliant.
1.  **Preflight**: `onecoder sprint preflight` (Must be passing)
2.  **Verify**: `onecoder sprint verify` (Zero-Debt check)

### Phase 4: Closure
1.  **Plan**: `onecoder sprint close "sprint-id" --plan` (Dry run)
2.  **Apply**: `onecoder sprint close "sprint-id" --apply --pr` (Finalize & PR)


## Core Commands

### 1. Initialize a Sprint
Creates a new sprint directory under `.sprint/` with the required artifacts.
```bash
onecoder sprint init "sprint-name"
```
*Note: Requires authentication (`onecoder login`) and automatically syncs project context.*


### 2. Status & Backlog
Check the state of all sprints or view a consolidated backlog.
```bash
onecoder sprint status
onecoder sprint backlog
```

### 2b. Readiness & Traceability
Ensure the sprint is ready to start or visualize the implementation of requirements.
```bash
onecoder sprint preflight  # Validate readiness score (min 75)
onecoder sprint trace      # Visualize SPEC traceability
```

### 3. Usage & Feedback
Provide feedback or request features. Use `--include-usage` to attach recent CLI telemetry.
```bash
onecoder feedback --feature-request --include-usage "Description of request"
```

### 4. Task Management
**MANDATORY**: An agent must always start a task before coding and committing.
```bash
onecoder sprint start "[Task ID or Title]"
onecoder sprint finish
```
*Note: You must finish the current task before starting another.*

## Best Practices: Quality & Governance Checks

The `onecoder` CLI provides several tools to ensure code quality and governance compliance. Use them at different stages of your workflow:

### 1. `onecoder sprint preflight` (The "Self-Check")
**When to use:** Frequently, before you consider your task "done".
**What it does:**
- fast (~seconds)
- Checks sprint structure (Tasks, README, TODO)
- Scans for secrets and banned files (e.g., `.env`)
- Verifies basic git governance (clean state)
**Goal:** Ensure you aren't missing administrative or security basics.

### 2. `onecoder sprint verify` (The "Tech Debt Check")
**When to use:** Before closing a sprint or merging a PR.
**What it does:**
- Runs component-specific linters, type checkers, and tests.
- Enforces the **Zero-Debt Policy** (no errors, no warnings allowed).
**Goal:** Ensure the code is technically sound and meets the project's strict quality standards.

### 3. `onecoder feedback`
**When to use:** ANY time you encounter friction, a bug, or have an idea.
**What it does:** Captures your context and sends it to the core team.
**Tip:** Use `onecoder issue create --from-telemetry` if a command just crashed.

### 5. Committing Changes
**CRITICAL**: Always use `onecoder sprint commit` instead of `git commit`. It enforces governance trailers.
The command automatically stages modified files, but using the `--files` (or `-f`) flag is recommended for explicit atomic commits.
```bash
onecoder sprint commit --files "path/to/file1,path/to/file2" -m "feat: description" --status done
```
*Note: Trailers like `Sprint-Id`, `Task-Id`, and `Status` are automatically handled or prompted. This command performs pre-flight checks (Git Config, Sprint Existence, Spec Validity) and triggers a sync on success.*


### 6. Project Intelligence & Sync
```bash
onecoder knowledge  # View platform-wide aggregated knowledge
onecoder sync       # Sync local specs, governance, and learnings to API
onecoder alignment  # Check semantic roadmap alignment and detect drift
onecoder ci         # Run local CI/CD workflows using 'act'
```

### 7. Governance & Traceability
```bash
onecoder sprint audit      # Run Procedural Integrity audit
onecoder sprint verify     # Run Zero-Debt (TSC/Lint) verification
onecoder sprint trace      # Visualize SPEC-to-Code traceability
onecoder sprint preflight  # Validate sprint readiness score (min 75)
```

## Spec Tracking Workflow

To maintain strict traceability (SPEC-GOV-005), every implementation commit should ideally be linked to a Specification ID.

### 1. Identify Specification IDs
Find valid IDs by searching for `SPEC-` markers in:
- `SPECIFICATION.md` (e.g., `SPEC-CLI-001`)
- `governance.yaml` (e.g., `SPEC-GOV-008`)

### 2. Link Specs during Commit
Use the `--spec-id` (or `-s`) flag when committing:
```bash
onecoder sprint commit -f "src/auth.py" -m "feat: implement OAuth" -s SPEC-CLI-001.1 --status done
```
*Note: Multiple IDs can be comma-separated: `-s SPEC-CLI-001.1,SPEC-GOV-005`.*

### 3. Visualize Implementation Coverage
Run `sprint trace` to see the mapping of specifications to commits and sprints:
```bash
onecoder sprint trace
```
This command helps identify "spec-less" features and unimplemented requirements.

### 8. Closing a Sprint
Validates completion criteria (clean tree, finished tasks) and archives the sprint.
```bash
onecoder sprint close "sprint-id" --apply --pr
```

### 9. Delegated GTM Ops (Internal)
Delegate market research or lead gen tasks to GTM Workers.
```bash
# Requires ONE_CODER_DEV=true
onecoder delegate "Find 50 leads" --type gtm
```

## Troubleshooting & Common Failure Modes

### 1. "Zero-Debt verification has not been run"
Run `onecoder sprint verify` first. If it fails, fix the reported errors/lint issues.

### 2. "No such file or directory" during Verify
The `parentComponent` in `sprint.json` must be a valid relative path from the project root (e.g., `onecoder-core/engines/onecoder-api`).

### 3. Regex Mismatch on Sprint-Id
Sprint IDs must follow the `\d{3}-[a-z0-9.-]+` pattern. If your branch name doesn't match, explicitly provide the ID via `--sprint-id`.

### 4. Implementation Integrity Violation (SPEC-GOV-008.2)
###  - **Philosophy**: We explicitly combat Procedural Integrity violations (formerly "BAKE-IT")—where tasks are marked done without implementation or using fake IDs.
You cannot mark a task as `done` if no implementation files have been staged, unless the message includes `docs`, `chore`, or `governance`.

### 5. Submodule Integrity Trap
Submodule URLs must use relative paths (`../repo`) to correctly resolve in CI runners. If a commit link is broken, ensure the submodule's internal commits are pushed to its own `origin` before pushing the parent repo.

## Fail-Fast & Reliability (v0.0.5+)
The CLI now enforces strict pre-checks:
1.  **Auth**: `init` requires login.
2.  **Git Config**: `init` warns, `commit` fails if `user.name` is missing.
3.  **Context**: `commit` fails if the sprint directory is missing.
4.  **Sync**: `init`, `start`, `commit` automatically sync to the platform API.


## Governance Rules (Procedural Integrity)

1. **Atomic Commits**: Every commit must belong to a sprint and have the correct trailers.
2. **Clean Tree**: Do not leave uncommitted changes. Use `sprint commit --files` to stage changes.
3. **Traceability**: Sprints must link back to specification IDs where applicable (`--spec-id SPEC-XXX-001`).
4. **No Side-Effects**: Use `onecoder sprint verify` to check for technical debt or governance violations.
5. **Usage Telemetry**: All CLI interactions are logged for self-improvement analysis.

## Directory Structure
```
.sprint/
  └── XXX-sprint-id/
      ├── README.md         # Goal & Summary
      ├── TODO.md           # Progress checklist
      ├── RETRO.md          # Lessons learned
      ├── walkthrough.md    # Evidence of work (media/logs)
      ├── media/            # Mandatory visual assets
      └── sprint.json       # Machine-readable metadata
```

> [!IMPORTANT]
> When acting as an agent, always check `SPRINT.md` to ensure you are using the correct command patterns for the current project phase.
"""
