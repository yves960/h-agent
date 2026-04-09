# h-agent Full Experience Flow

This document defines a complete product experience for `h-agent` as a Harness Engineering system.

It has two layers:

1. Automated verification for offline-safe capabilities
2. Manual acceptance for interactive, networked, or system-level capabilities

The goal is not just to check that commands exist, but to verify that the system behaves coherently across:

- bootstrap
- control plane
- state and persistence
- extension surfaces
- local knowledge/RAG
- scheduling
- agent/team orchestration
- online LLM execution
- daemon and web surfaces

## How To Run

Automated verification:

```bash
.venv/bin/python scripts/verify_full_experience.py
```

The script uses an isolated temporary `HOME` and `H_AGENT_HOME`, so it does not mutate your real local state.

## Phase 1: Bootstrap

Goal: prove that a fresh environment can discover and diagnose the product.

Commands:

```bash
python -m h_agent --help
python -m h_agent doctor
python -m h_agent config --show
```

Expected:

- root help shows all top-level commands
- `doctor` renders a readable diagnostic report
- `config --show` works even with minimal config

## Phase 2: Control Plane Discovery

Goal: verify every top-level and nested control surface is discoverable.

Automated scope:

- top-level help for:
  `start`, `status`, `stop`, `autostart`, `team`, `agent`, `logs`, `session`, `rag`, `run`, `chat`, `config`, `memory`, `plugin`, `skill`, `template`, `model`, `init`, `doctor`, `web`, `cron`, `heartbeat`
- nested help for:
  `autostart status`
  `session list/create/history/delete/search/rename/tag/group/cleanup`
  `rag index/search/stats`
  `memory list/add/get/delete/search/dump`
  `plugin list/info/enable/disable/install/uninstall`
  `skill list/info/enable/disable/install/uninstall/run`
  `template list/show/apply/create/delete`
  `model list/switch/info/add`
  `cron list/add/remove/enable/disable/exec/log`
  `heartbeat start/stop/status/run`

Expected:

- every advertised surface returns structured help
- no parser crashes
- no import-time warnings

## Phase 3: Session Lifecycle

Goal: verify that session state is visible, persistent, and manageable.

Automated scope:

```bash
h-agent session create --name smoke
h-agent session list
h-agent session rename <id> smoke-renamed
h-agent session tag add <id> demo
h-agent session tag get <id>
h-agent session group set <id> acceptance
h-agent session group sessions acceptance
h-agent session search smoke
h-agent session history <id>
h-agent session delete <id>
h-agent session cleanup
```

Expected:

- a created session is immediately visible in `session list`
- rename/tag/group updates are queryable through the control plane
- delete removes the session cleanly

## Phase 4: Memory Lifecycle

Goal: verify long-term memory acts like a stable product surface.

Automated scope:

```bash
h-agent memory add fact smoke-key smoke-value --tags demo
h-agent memory get smoke-key
h-agent memory search smoke-key
h-agent memory list
h-agent memory dump
h-agent memory delete fact smoke-key
```

Expected:

- memory add/get/search/list/dump are coherent
- deletion removes the record

## Phase 5: Local Knowledge / RAG

Goal: verify indexing and search on a small local codebase.

Automated scope:

```bash
h-agent rag index --directory <temp-project>
h-agent rag search smoke_function --directory <temp-project>
h-agent rag stats --directory <temp-project>
```

Expected:

- indexing completes without requiring ChromaDB
- symbol search returns local matches
- stats report indexed files and symbols

## Phase 6: Templates, Models, Plugins, Skills

Goal: verify the extension/control surfaces work even in a clean environment.

Automated scope:

- `template list`
- `template create/show/delete`
- `model list`
- `plugin list`
- `skill list --all`
- `skill info office`

Expected:

- empty states are readable
- create/show/delete flows work for templates
- unavailable skills are reported explicitly rather than silently failing

## Phase 7: Agent And Team Surfaces

Goal: verify orchestration surfaces can be initialized locally.

Automated scope:

```bash
h-agent agent list
h-agent agent init smoke-agent --role coder --description "smoke agent"
h-agent agent show smoke-agent
h-agent agent sessions smoke-agent
h-agent team list
h-agent team status
```

Expected:

- agent profile creation succeeds in isolated state
- team surfaces are readable even before active collaboration

Manual scope:

```bash
h-agent team init
h-agent team talk planner "Analyze how to implement login"
```

Expected:

- team init creates default agents
- team talk reaches a real handler and returns a response

## Phase 8: Scheduling

Goal: verify cron and heartbeat control surfaces.

Automated scope:

```bash
h-agent cron list
h-agent cron add "*/5 * * * *" "echo smoke" --name smoke-job
h-agent cron disable <job_id>
h-agent cron enable <job_id>
h-agent cron log --job <job_id>
h-agent cron remove <job_id>
h-agent heartbeat status
h-agent heartbeat run
```

Expected:

- cron job state is visible and mutable
- heartbeat status and one-shot execution are readable

Manual scope:

```bash
h-agent heartbeat start --interval 60
h-agent heartbeat status
h-agent heartbeat stop
```

Expected:

- background heartbeat starts and stops cleanly

## Phase 9: Online LLM Execution

Goal: verify the real harness path against a reachable provider.

Manual prerequisites:

- valid `OPENAI_API_KEY`
- valid `OPENAI_BASE_URL`
- valid `MODEL_ID`
- outbound network connectivity

Commands:

```bash
h-agent run "Explain the current directory in one sentence"
h-agent chat
```

Expected:

- `run` produces a model answer or a well-classified error
- `chat` opens a REPL, preserves history, and allows `/history` and `/clear`

Failure-path acceptance:

- invalid key -> authentication-specific error
- invalid base URL / blocked network -> connection-specific error
- invalid model -> model-not-found style error

## Phase 10: Daemon And Web

Goal: verify long-running surfaces.

Manual scope:

```bash
h-agent start
h-agent status
h-agent logs --tail 50
h-agent stop
h-agent web --port 8080 --no-browser
```

Expected:

- daemon starts, reports status, writes logs, and stops cleanly
- web server binds successfully and serves the UI

## Phase 11: Install Flows

Goal: verify extension installation flows that require network or package managers.

Manual scope:

```bash
h-agent plugin install <url>
h-agent plugin uninstall <name>
h-agent skill install <name>
h-agent skill uninstall <name>
```

Expected:

- installs are explicit about the source
- uninstall paths clean up state fully
- failures report URL/package/permission context clearly

## Acceptance Standard

The system is considered fully acceptable when:

1. `scripts/verify_full_experience.py` passes end-to-end
2. all manual phases complete with expected outcomes
3. failure paths produce actionable diagnostics
4. state is isolated and predictable in fresh environments
5. no capability is discoverable only in code but missing from the public CLI
