# ForgeMCP

**An MCP-native GitHub automation platform with a LangGraph-powered, planner-driven conversational agent, Postgres-backed memory, human-in-the-loop approval for destructive actions, and a full FastMCP tool server exposing the GitHub REST API.**

---

## Table of Contents

- [Project Overview](#project-overview)
- [Why This Was Built This Way](#why-this-was-built-this-way)
- [Features](#features)
- [Architecture](#architecture)
- [Agent Workflow Graph](#agent-workflow-graph)
- [Folder Structure](#folder-structure)
- [Technologies Used](#technologies-used)
- [Available Tools](#available-tools)
- [Prompt System](#prompt-system)
- [LangGraph Nodes](#langgraph-nodes)
- [Human In The Loop](#human-in-the-loop)
- [Memory: Short-Term vs. Long-Term](#memory-short-term-vs-long-term)
- [Advantages](#advantages)
- [Drawbacks / Current Limitations](#drawbacks--current-limitations)
- [Future Improvements](#future-improvements)
- [Use Cases](#use-cases)
- [Installation](#installation)
- [Quick Start (CLI)](#quick-start-cli)
- [Running the Streamlit UI](#running-the-streamlit-ui)
- [Example Commands](#example-commands)
- [Project Review](#project-review)
- [Conclusion](#conclusion)

---

## Project Overview

**ForgeMCP** is a two-layer system that lets a language model operate GitHub on a user's behalf through natural language, with a safety gate in front of anything destructive and a planner in front of everything else.

It is built from two cooperating parts:

1. **An MCP (Model Context Protocol) server** (`MCP/`) — a [FastMCP](https://github.com/jlowin/fastmcp)-based server that wraps the GitHub REST API as ~34 individually-typed, individually-documented tools (list repos, get a README, create a branch, merge a PR, delete a repository, etc.), authenticated with a bearer token and deployable as a standalone HTTP service (currently on Render).
2. **A LangGraph agent** (`Agent/`) — a conversational agent built on [LangGraph](https://github.com/langchain-ai/langgraph) that connects to the MCP server as a tool client (via `langchain-mcp-adapters`' `MultiServerMCPClient`), **breaks the user's request into an ordered plan of subtasks**, classifies each subtask's intent, selects a tool, classifies the *safety* of that tool call, pauses for human approval when the action is destructive, executes the tool, tracks task completion, and finally summarizes the whole run into one natural-language answer.

**Why it exists:** talking to GitHub today means either using the `gh` CLI, clicking through the web UI, or hand-writing REST calls. ForgeMCP's goal is to make GitHub operable conversationally — "create a repo called `hello`, add a README, and push it" — as a single multi-step request the agent plans and executes on its own, while keeping a human explicitly in the loop before anything irreversible happens (deleting a repo, merging a PR, deleting a file). The MCP layer is also decoupled from the agent: because it is a standard MCP server, any MCP-compatible client (Claude Desktop, another LangGraph app, a different LLM entirely) can drive the same GitHub tools without touching the agent code at all.

**Problems it solves:**
- Wrapping the (large, inconsistent) GitHub REST API behind a small, uniform, typed tool interface.
- Letting a user issue one compound instruction ("create repo, add file, push") and having the agent decompose and execute it as an ordered sequence, instead of forcing one tool call per message.
- Giving an LLM agent access to that interface without also giving it unsupervised write/delete power.
- Separating "can this model call GitHub" (MCP server + bearer auth) from "should this specific action run right now" (LangGraph safety classifier + interrupt-based approval).
- Persisting conversation state in Postgres so a session — including a pending approval — survives a process restart or a page refresh in the UI.

---

## Why This Was Built This Way

- **MCP as the tool boundary, not a Python function call.** Exposing GitHub as an MCP server (rather than binding tool functions directly inside the LangGraph process) means the tool layer is a *protocol*, not an implementation detail. Any MCP-aware client can reuse the exact same 34 tools without importing any of this repo's agent code — this was a deliberate bet on reusability over convenience.
- **A planner node instead of one-shot tool calling.** Early iterations routed every user message straight into a single tool-call LLM invocation, which works for "list my repos" but breaks down for compound requests like "create a repo, add a README, then push my local folder." Adding `planner_node` at the top of the graph turns that single request into an ordered list of `TaskPlan` subtasks, and the rest of the graph loops over them one at a time via `update_task_node` — so multi-step GitHub workflows are handled natively instead of requiring the user to issue one instruction per turn.
- **HITL as a graph-level `interrupt()`, not a prompt instruction.** Telling the model "always ask before deleting" is a suggestion the model can ignore under the right phrasing. Implementing approval as a LangGraph `interrupt()` means the graph *cannot* proceed past a destructive tool call without an external `Command(resume=...)` — it's a structural guarantee, not a hope.
- **Postgres checkpointing instead of in-memory state.** Both the CLI (`SERVER.py`) and the Streamlit UI (`app_frontend.py`) now compile the graph with `AsyncPostgresSaver`. This was a direct response to the earlier `InMemorySaver` limitation: a pending HITL approval, or an entire multi-turn thread, used to vanish on restart. Now it's durable, and `db_utils.py` gives a one-command way to wipe the checkpoint tables during development.
- **Separate safety classification from tool selection.** Rather than trusting the tool-selecting LLM call to also self-police whether an action is dangerous, a second, independent LLM call (`tool_safety_node`) re-examines the chosen tool's name/description purely for destructiveness. Splitting these into two calls means a single prompt injection or reasoning slip in tool selection doesn't automatically bypass the safety gate too.
- **Mistral over a larger frontier model.** `mistral-small-latest` was chosen for cost and latency — this is a conversational, tool-routing agent making several LLM calls per user turn (planner → router → tool-select → safety → response → summary), so a fast, cheap model that's "good enough" at structured output and tool-calling matters more here than raw reasoning depth.

---

## Features

- **~34 GitHub tools** spanning repository reads, commits, releases, branches, forks, contributors, file/repo creation, file/repo deletion, and the full pull-request lifecycle (create, list, get, update, merge, review, request reviewers).
- **Automatic task planning** — `planner_node` decomposes a user request into an ordered list of subtasks *before* anything runs, so compound instructions ("create a repo, add a file, push it") are executed as a sequence rather than requiring one message per step.
- **Per-subtask intent routing** — for each subtask, the agent decides whether it needs a GitHub action at all, or is just a question it can answer directly (e.g. "what is a pull request?").
- **LLM-driven tool selection** — GitHub tools are bound directly to the chat model, which picks the tool and extracts its arguments from the subtask description in a single call.
- **Independent safety classification** — before any selected tool runs, a *second*, dedicated LLM call classifies it as read-only ("safe") or state-changing ("hitl"), based on the tool's name, description, and the subtask.
- **Human-in-the-loop approval** — destructive tool calls pause the graph with LangGraph's `interrupt()` and wait for an explicit approval before continuing, so nothing is deleted, merged, or overwritten without confirmation. The Streamlit UI surfaces this as an Approve / Reject modal dialog.
- **Postgres-backed durable state** — both entrypoints compile the graph with `AsyncPostgresSaver`, so conversation state (including a pending HITL interrupt) survives process restarts and is keyed by `thread_id`.
- **Task-by-task execution log + final summary** — `update_task_node` marks each subtask complete and advances to the next; once every subtask is done, `summary_node` produces one consolidated answer from the full execution log.
- **Bearer-token-authenticated MCP server** — the MCP server uses FastMCP's `StaticTokenVerifier` so it can be safely exposed over the network rather than only run locally over stdio.
- **Guarded network binding** — the server entrypoint (`demo.py`) refuses to bind to a non-loopback host unless an `MCP_AUTH_TOKEN` is set, to stop an accidentally-public, unauthenticated GitHub-mutating server.
- **Local-repo tools alongside API tools** — `clone_repository` and `push_local_to_github` shell out to `git` directly, so the agent can also work with a local working copy, not just the GitHub API surface.
- **Streamlit chat UI with multi-thread history** — `app_frontend.py` reconstructs past chat threads directly from Postgres checkpoints on load, and offers a sidebar New Chat button plus a Reset-DB button for wiping state during development.
- **Context-window balancing** — `balance_context_window()` trims the oldest human/AI turn once the conversation exceeds 20 messages, so long-running threads don't grow the prompt unbounded.

---

## Architecture

ForgeMCP is deliberately split into two independently runnable pieces that only communicate over MCP:

```
┌───────────────────────────── Agent Layer (Agent/) ─────────────────────────────┐
│                                                                                  │
│   User ──▶ SERVER.py (CLI)  or  app_frontend.py (Streamlit)                     │
│                       │                                                         │
│                       ▼                                                         │
│           LangGraph agent (graph.py + nodes.py)                                 │
│           planner → intent → tool-select → safety → [HITL] → execute → summary  │
│                       │                                                         │
│                       ▼                                                         │
│           MultiServerMCPClient (langchain-mcp-adapters)                         │
│                       │                                                         │
└───────────────────────┼──────────────────────────────────────────────────────┘
                         │  Bearer MCP_AUTH_TOKEN over streamable_http
                         ▼
┌───────────────────────────── MCP Server Layer (MCP/) ──────────────────────────┐
│                                                                                  │
│   FastMCP server (server.py) ──▶ ~34 @mcp.tool functions                        │
│                                    (Tools/Read, create, Delete, Pull)            │
│                                       │                                         │
│                                       ▼                                        │
│                          github_client.py (GET/POST/PUT/PATCH/DELETE)          │
│                                       │  Bearer GITHUB_TOKEN                    │
│                                       ▼                                        │
│                                GitHub REST API                                  │
└──────────────────────────────────────────────────────────────────────────────┘

                    Both entrypoints persist graph state to:
                    PostgreSQL  (AsyncPostgresSaver — checkpoints,
                                 checkpoint_blobs, checkpoint_writes)
```

### Key architectural components

**MCP server (`MCP/`)**
- `server.py` defines a single shared `FastMCP("ForgeMCP")` instance, optionally wrapped with `StaticTokenVerifier` auth if `MCP_AUTH_TOKEN` is set.
- Every tool module imports that same `mcp` instance and registers itself with `@mcp.tool`, so all ~34 tools attach to one server regardless of which subpackage they live in.
- `config.py` loads `GITHUB_TOKEN` and `MCP_AUTH_TOKEN` from `.env` and builds the base GitHub `HEADERS` dict.
- `github_client.py` is the single HTTP boundary: `github_get`, `github_post`, `github_put`, `github_patch`, `git_delete`. Every write/delete call routes through `_auth_headers()`, which raises immediately if `GITHUB_TOKEN` is missing, so a misconfigured deployment fails fast rather than sending unauthenticated write requests.
- `helper.py` provides `get_authenticated_username()`, used by nearly every tool as the default `username` when the caller doesn't supply one (i.e. "act on my own account").
- `Tools/` is organized by intent — `Read/`, `create/`, `Delete/`, `Pull/` — each with an `__init__.py` that re-exports every tool in that category, and a top-level `Tools/__init__.py` that re-exports all four categories, so `demo.py` can register the whole tool surface with one `from MCP.Tools import *`.

**LangGraph agent (`Agent/`)**
- `state.py` defines the graph's shared state as a Pydantic model (`State`), the multi-task planning schema (`TaskPlan`, `PlannerOutput`), and two structured-output schemas used by the LLM: `RouterDecision` (tool vs. llm) and `ToolSafetyDecision` (hitl vs. safe).
- `nodes.py` implements every node function plus the routing functions used on conditional edges. Tools are injected at runtime via `set_tools()` once `MultiServerMCPClient.get_tools()` resolves — the module keeps `tools` and `llm_with_tools` as module-level state populated after startup.
- `graph.py` wires the `StateGraph` (11 nodes, planner-first), and `run_graph()` loops on `__interrupt__` in the result to drive the HITL approval prompt for the CLI path.
- `service.py` builds the Mistral chat model (`ChatMistralAI`, `mistral-small-latest`, streaming), the MCP server connection dict consumed by `MultiServerMCPClient`, the Postgres connection string (`get_db_uri()`), and a fresh per-session `thread_id` (`get_config()`).
- `db_utils.py` provides `clear_postgres_data()` — truncates the `checkpoints`, `checkpoint_blobs`, and `checkpoint_writes` tables (used by the Streamlit "Reset-DB" button and available as a standalone script).
- `SERVER.py` is the CLI entrypoint: it builds the MCP client, loads tools, injects them into `nodes`, opens an `AsyncPostgresSaver`, compiles the graph, and runs a `while True` input loop, resolving HITL interrupts via `input()`.
- `Prompts/` holds one file per prompt (planner, router, llm-answer, tool-safety, tool-response, summary) — kept separate from the node logic so prompt text can be iterated on independently of graph wiring.

**Streamlit frontend (`app_frontend.py`, project root)**
- Compiles the same `build_graph()` with `AsyncPostgresSaver`, so the UI and the CLI share identical agent logic and identical persisted state.
- Reconstructs the chat sidebar directly from Postgres checkpoints on load (`load_threads_from_postgres()`), so refreshing the page or restarting the app doesn't lose thread history.
- Surfaces HITL interrupts as a modal `st.dialog` with Approve/Reject buttons instead of a terminal prompt.
- Ships a **Reset-DB** sidebar button that calls `clear_postgres_data()` for a clean local dev slate.

**State management** — the whole conversation turn (question, plan, current subtask, routing decision, selected tool, tool arguments, safety decision, approval flag, tool result, execution log, final answer) lives in one Pydantic `State` object that flows through every node and is checkpointed by thread in Postgres via `AsyncPostgresSaver` — this is the agent's **short-term memory**; see [Memory](#memory-short-term-vs-long-term) below for the distinction from the *planned* long-term memory layer.

---

## Agent Workflow Graph

Markdown-embedded Mermaid diagrams don't always render reliably in every viewer (GitHub, some IDEs, and most local Markdown previewers handle it differently), so the actual compiled LangGraph graph is included below as a static image, generated directly from `graph.py` via `graph.get_graph().draw_mermaid_png()`:

![ForgeMCP LangGraph workflow](./assets/diagrams/grpah_img.png)

### Request lifecycle (in words)

A user message now goes through a **planning stage first**, then loops through the classify → select → safety → [approve] → execute cycle once per subtask, before being summarized:

1. **`planner_node`** — breaks the raw user request into an ordered list of `TaskPlan` subtasks (each with `description`, `status`, `result`). A simple one-action request produces exactly one subtask.
2. **`planner_router`** — if there are subtasks left, continue to `intent_classifier_node`; if the plan is empty/finished, skip straight to `summary_node`.
3. **`intent_classifier_node`** — for the *current* subtask, decide: does this need a tool, or can the LLM answer it directly?
   - → **`llm_answer_node`** (direct answer, streamed) if no tool is needed.
   - → **`normal_tools`** if a tool is needed.
4. **`normal_tools`** — the LLM (bound to all MCP tools) picks a tool and extracts its arguments from the subtask description.
   - → **`tool_safety_node`** if a tool was selected.
   - → end this subtask if no tool call was produced.
5. **`tool_safety_node`** — a dedicated LLM call classifies the selected tool as `hitl` or `safe`.
   - → **`execute_tools`** if safe.
   - → **`dangerous_tools`** if it requires human approval.
6. **`dangerous_tools`** — calls `interrupt()`, pausing the graph and surfacing the tool name/arguments/reason to the human (CLI prompt or Streamlit dialog).
   - → **`execute_tools`** if approved.
   - → end this subtask (cancelled) if rejected.
7. **`execute_tools`** — actually invokes the MCP tool with the extracted arguments.
8. **`tool_response_node`** — turns the raw tool result into a natural-language answer for this subtask.
9. **`update_task_node`** — marks the current subtask `completed`, records its result, and advances `current_task_index`.
10. Loop back to step 2 (`planner_router`) for the next subtask, or fall through to:
11. **`summary_node`** — once every subtask is done, produces one consolidated, final Markdown answer from the full execution log.

---

## Folder Structure

```
ForgeMCP/
├── Agent/                          # LangGraph conversational agent
│   ├── Prompts/                    # One ChatPromptTemplate per prompt
│   │   ├── planner_prompt.py           # decomposes a request into ordered subtasks
│   │   ├── router_prompt.py            # tool vs. llm classification (per subtask)
│   │   ├── llm_answer_node_prompt.py   # direct-answer persona prompt
│   │   ├── tool_safety_node_prompt.py  # hitl vs. safe classification
│   │   ├── tool_response_node_prompt.py# turns tool output into an answer
│   │   └── summary_prompt.py           # consolidates the full run into one answer
│   ├── SERVER.py                   # CLI entrypoint (Postgres checkpointer, HITL resume)
│   ├── db_utils.py                 # clear_postgres_data() — truncates checkpoint tables
│   ├── graph.py                    # StateGraph wiring (planner-first, 11 nodes) + run_graph()
│   ├── nodes.py                    # All node + routing function implementations
│   ├── service.py                  # LLM client, MCP connection, DB URI, per-session config
│   └── state.py                    # Pydantic State, TaskPlan, PlannerOutput, RouterDecision, ToolSafetyDecision
│
├── MCP/                            # FastMCP GitHub tool server
│   ├── Tools/
│   │   ├── Read/                   # 17 read-only tools (repos, commits, PRs metadata, etc.)
│   │   ├── create/                 # 5 create/mutating tools (repo, file, branch, clone, push)
│   │   ├── Delete/                 # 2 destructive tools (delete file, delete repo)
│   │   └── Pull/                   # 10 pull-request lifecycle tools
│   ├── config.py                   # Loads .env, builds GitHub API headers
│   ├── github_client.py            # GET/POST/PUT/PATCH/DELETE wrapper around requests
│   ├── helper.py                   # get_authenticated_username()
│   └── server.py                   # Shared FastMCP instance + auth
│
├── assets/
│   └── diagrams/
│       └── grpah_img.png           # Rendered LangGraph workflow (embedded above)
│
├── app_frontend.py                 # Streamlit chat UI — same graph, Postgres-backed, HITL modal
├── demo.py                         # MCP server process entrypoint (binds host/port, auth guard)
├── hello.py                        # Trivial smoke-test script
├── requirements.txt                # MCP server dependencies
├── requirements_agent.txt          # Agent dependencies (LangGraph/LangChain/Mistral/psycopg/streamlit)
├── Agent.ipynb / agent_copy.ipynb  # Notebook scratchpads the Agent/ package is iterated from
└── .env                            # GITHUB_TOKEN, MCP_AUTH_TOKEN, MISTRAL_API_KEY, DB_URI (not committed)
```

---

## Technologies Used

| Category | Technology | Role in ForgeMCP |
|---|---|---|
| Language | Python 3.11+ | Required — avoids an `interrupt()`/`get_config()` asyncio context bug present on older versions |
| MCP server framework | [FastMCP](https://pypi.org/project/fastmcp/) | Exposes the ~34 GitHub tools as a standard MCP server with auth |
| Agent orchestration | [LangGraph](https://pypi.org/project/langgraph/) (+ `langgraph-checkpoint-postgres`) | Planner-driven multi-node StateGraph; Postgres-backed durable checkpointing |
| LLM framework | [LangChain](https://pypi.org/project/langchain/) | Prompt templates, structured output, message types |
| MCP↔LangChain bridge | `langchain-mcp-adapters` (`MultiServerMCPClient`) | Loads the MCP tool server's tools as native LangChain tools |
| LLM provider | [Mistral AI](https://pypi.org/project/langchain-mistralai/) (`mistral-small-latest`) | Powers every LLM call in the graph — planning, routing, tool-selection, safety, response, summary |
| MCP protocol | `mcp` | Underlying protocol implementation used by both FastMCP and the adapters client |
| Data validation | [Pydantic](https://pypi.org/project/pydantic/) | `State`, `TaskPlan`, `PlannerOutput`, `RouterDecision`, `ToolSafetyDecision` — all structured-output schemas |
| HTTP client | `requests` | Every GitHub REST API call in `github_client.py` |
| GitHub integration | GitHub REST API (`api.github.com`) | The actual surface being wrapped |
| Config | `python-dotenv` | Loads `.env` locally (`GITHUB_TOKEN`, `MCP_AUTH_TOKEN`, `MISTRAL_API_KEY`, `DB_URI`) |
| **Persistence (short-term memory)** | **PostgreSQL** via `psycopg` + `psycopg-pool`, `langgraph-checkpoint-postgres` (`AsyncPostgresSaver`) | Durable, per-thread conversation state — active in both `SERVER.py` and `app_frontend.py` |
| Frontend | [Streamlit](https://streamlit.io/) | `app_frontend.py` — chat UI, thread sidebar, HITL approval modal |
| Notebook tooling | `ipykernel`, `jupyterlab` | `agent_copy.ipynb` used as an iterative scratchpad before migrating code into `Agent/` |
| Deployment | Render (MCP server, `streamable_http` transport) | Hosts the MCP tool server so the agent (local or deployed) can reach it over HTTPS |

---

## Available Tools

All tools are registered via `@mcp.tool` and default `username` to the authenticated GitHub account when omitted.

### Read tools (17) — safe / read-only

| Tool | Purpose | Key Inputs | Output | Class |
|---|---|---|---|---|
| `get_repository` | Repo metadata (stats, visibility, license, URLs) | `repo_name`, `username?` | Dict of repo metadata | Safe |
| `get_repository_code` | Fetch actual file contents from a repo/folder | `repo_name`, `folder_path?`, `branch`, `username?` | List of `{file, size, code}` | Safe |
| `get_readme` | Get decoded README content | `repo_name`, `username?` | `{name, path, url, content}` | Safe |
| `get_langauge` | Language breakdown (bytes per language) | `repo_name`, `username?` | Dict of language → bytes | Safe |
| `get_branches` | List branches + protection status | `repo_name`, `username?` | List of `{branch_name, is_protected}` | Safe |
| `get_commit` | Single commit details | `repo_name`, `sha`, `username?` | Commit detail dict | Safe |
| `list_commits` | List commits (filterable by branch/author) | `repo_name`, `limit`, `page`, `branch?`, `author?` | List of commit summaries | Safe |
| `compare_commits` | Diff two refs (ahead/behind + commit list) | `repo_name`, `base`, `head`, `username?` | `{status, ahead_by, behind_by, commits}` | Safe |
| `list_tags` | List repository tags | `repo_name`, `limit`, `page`, `username?` | Raw GitHub tag list | Safe |
| `list_releases` | List repository releases | `repo_name`, `limit`, `username?` | List of release summaries | Safe |
| `get_latest_release` | Newest published release | `repo_name`, `username?` | Release summary dict | Safe |
| `list_forks` | List forks of a repo | `repo_name`, `limit`, `page`, `username?` | List of fork summaries | Safe |
| `repo_contributors` | List contributors | `repo_name`, `limit`, `username?` | List of `{username, contributions, profile}` | Safe |
| `list_watchers` | List repo watchers/subscribers | `repo_name`, `limit`, `username?` | List of `{username, profile_url}` | Safe |
| `list_repositories` | List public repos owned by a user | `username?` | List of repo summaries | Safe |
| `search_repos` | Global keyword search across GitHub repos | `query`, `limit` | Raw search result items | Safe |
| `get_user_details` | Public GitHub user profile | `username?` | Profile dict | Safe |

### Create tools (5) — mutating

| Tool | Purpose | Key Inputs | Output | Class |
|---|---|---|---|---|
| `create_repository` | Create a new empty remote repo | `repo_name`, `description`, `private`, `auto_init` | `{status, name, full_name, url}` | HITL (expected) |
| `create_file` | Create one file in a repo via the Contents API | `repo_name`, `path`, `content`, `message`, `branch`, `username?` | `{status, file, commit_sha, url}` | HITL (expected) |
| `create_branch` | Create a branch from an existing branch | `repo_name`, `branch_name?`, `source_branch`, `username?` | `{status, branch, commit_sha, github_url}` | HITL (expected) |
| `clone_repository` | `git clone` a repo to local disk | `repo_url`, `destination` | `{status, repository, location}` | Local-only; not a GitHub API mutation |
| `push_local_to_github` | Push a local folder to GitHub (creates repo if needed, `git init`/commit/push) | `local_path`, `repo_name`, `username`, `commit_message`, `branch`, `private` | `{status, repository_created, repository, url}` | HITL (expected) |

### Delete tools (2) — destructive

| Tool | Purpose | Key Inputs | Output | Class |
|---|---|---|---|---|
| `delete_file` | Delete a file from a repo | `repo_name`, `path`, `message`, `branch`, `confirm=True`, `username?` | `{status, file, branch}` | HITL |
| `delete_repository` | Delete an entire repository | `repo_name`, `confirm=True`, `username?` | `{status, repository}` | HITL |

Both delete tools additionally require an explicit `confirm=True` argument at the tool level, on top of the agent's HITL approval — a second, independent guard against accidental deletion.

### Pull Request tools (10)

| Tool | Purpose | Key Inputs | Output | Class |
|---|---|---|---|---|
| `create_pull_request` | Open a PR | `repo_name`, `title`, `head`, `base`, `body`, `draft`, `username?` | PR summary dict | HITL (expected) |
| `get_pull_request` | Fetch full PR detail | `repo_name`, `pull_request_number`, `username?` | Detailed PR dict | Safe |
| `list_pull_requests` | List PRs by state | `repo_name`, `state`, `base?`, `sort`, `direction`, `page`, `per_page` | List of PR summaries | Safe |
| `list_pull_request_commits` | List commits in a PR | `repo_name`, `pull_request_number`, `username?` | List of commit summaries | Safe |
| `list_pull_request_files` | List files changed in a PR (with patch) | `repo_name`, `pull_request_number`, `username?` | `{total_files, files[]}` | Safe |
| `list_pull_request_reviews` | List reviews on a PR | `repo_name`, `pull_request_number`, `username?` | List of review summaries | Safe |
| `update_pull_request` | Update title/body/state/base of a PR | `repo_name`, `pull_request_number`, fields to update | Updated PR summary | HITL (expected) |
| `merge_pull_request` | Merge a PR (`merge`/`squash`/`rebase`) | `repo_name`, `pull_request_number`, `merge_method`, commit title/message | `{merged, message, sha}` | HITL |
| `request_reviewers` | Request reviewers on a PR | `repo_name`, `pull_request_number`, `reviewers[]` | `{requested_reviewers[]}` | HITL (expected) |
| `submit_pull_request_review` | Submit APPROVE/REQUEST_CHANGES/COMMENT | `repo_name`, `pull_request_number`, `event`, `body` | Review summary | HITL (expected) |

> **Important nuance:** "Safe" vs. "HITL" above reflects the *intended* classification per the tool's semantics and the rules in `tool_safety_node_prompt.py`. The actual safe/hitl decision is not hardcoded per tool — it is inferred at runtime by an LLM call reading only the tool's `name` and `description`. See [Drawbacks](#drawbacks--current-limitations) for why this is a risk rather than a guarantee.

---

## Prompt System

ForgeMCP uses six separate prompts, each isolated in its own file under `Agent/Prompts/`, each feeding a distinct node:

| Prompt | Used by | Purpose |
|---|---|---|
| **Planner Prompt** (`planner_prompt.py`) | `planner_node` | Decomposes a (possibly compound) user request into an ordered list of atomic `TaskPlan` subtasks, with dependency ordering and optional verification steps, *before* anything is executed. Explicitly instructed not to answer, act, or select tools — planning only. |
| **Router Prompt** (`router_prompt.py`) | `intent_classifier_node` | Binary classification per subtask: does it require a *tool* (an action) or just an *llm* answer (information)? Given positive/negative examples to anchor the boundary. Exists to avoid burning a full tool-bound LLM call on subtasks that are pure questions. |
| **LLM Answer Prompt** (`llm_answer_node_prompt.py`) | `llm_answer_node` | The assistant's persona/system prompt for the "no tool needed" path — defines it as a GitHub/dev-focused helper, explicitly instructs it not to claim it performed an action it didn't. |
| **Tool Safety Prompt** (`tool_safety_node_prompt.py`) | `tool_safety_node` | Classifies a *specific selected tool call* as `hitl` or `safe`, given the tool's name, description, and the subtask, with explicit rules (create/update/delete/merge → hitl; read/list/search → safe) and worked examples. The sole gate deciding whether human approval is required before execution. |
| **Tool Response Prompt** (`tool_response_node_prompt.py`) | `tool_response_node` | Converts raw tool output (arbitrary JSON/text) into a natural-language answer for the current subtask, explicitly forbidding invented information and instructing it not to name internal tools. |
| **Summary Prompt** (`summary_prompt.py`) | `summary_node` | Once every subtask is complete, consolidates the full plan + execution log into one final, coherent Markdown answer for the user — turns a sequence of internal task results back into a single conversational reply. |

---

## LangGraph Nodes

| Node | Responsibility | Input (from `State`) | Output (state update) | Routes via |
|---|---|---|---|---|
| `planner_node` | Decompose the request into ordered subtasks | `question`, `messages` | `subtasks`, `current_task_index`, `current_task`, `plan_completed` | `planner_router` → `intent_classifier` \| `summary` |
| `intent_classifier_node` | Classify tool vs. llm intent for the current subtask | current subtask, `messages` | `router_decision` | `router` → `tools_required` \| `llm_answer` |
| `llm_answer_node` | Stream a direct answer when no tool is needed | current subtask | `final_answer`, `execution_log`, `messages` | → `update_task_node` (unconditional) |
| `normal_tools` | Bind tools to the LLM, let it pick one tool + extract its arguments | current subtask | `tool_calls`, `tool_arguments`, `tool_name` (or `final_answer` if none selected) | `tool_selection_router` → `safety_check` \| `end` |
| `tool_safety_node` | Classify the selected tool as `hitl` or `safe` | `tool_name`, current subtask | `tool_safety`, `requires_hitl` | `tool_safety_router` → `hitl` \| `normal` |
| `dangerous_tools` | Pause execution and request human approval via `interrupt()` | `tool_name`, `tool_arguments`, `tool_safety.reason` | `approved` (and `final_answer` if rejected) | `approval_routing` → `tool_execute` \| `end` |
| `execute_tools` | Actually invoke the MCP tool with the extracted arguments | `tool_name`, `tool_arguments` | `tool_result` (or `final_answer` on failure) | → `tool_response_node` (unconditional) |
| `tool_response_node` | Turn the raw tool result into a natural-language answer | current subtask, `tool_name`, `tool_result` | `final_answer`, `execution_log`, `messages` | → `update_task_node` (unconditional) |
| `update_task_node` | Mark the current subtask complete, record its result, advance the index | `subtasks`, `current_task_index`, `tool_result`/`final_answer` | `subtasks`, `current_task_index`, `plan_completed` | `planner_router` → `intent_classifier` \| `summary` |
| `summary_node` | Consolidate the full plan + execution log into one final answer | `question`, `subtasks`, `execution_log`, `tool_result` | `final_answer`, `messages` | → `END` (unconditional) |

Routing functions (`planner_router`, `router`, `tool_selection_router`, `tool_safety_router`, `approval_routing`) are plain functions over `State` that return a string key, matched against the edge-mapping dictionaries in `graph.py`.

---

## Human In The Loop

**Why it exists:** the agent can autonomously *select* any of the ~34 tools, including ones that delete repositories or merge pull requests. Tool selection is a single LLM call with no independent verification — so HITL exists as a second, structurally separate checkpoint that cannot be skipped by the LLM changing its mind, because it's implemented as a graph-level `interrupt()`, not a prompt instruction.

**When it triggers:** whenever `tool_safety_node` classifies the selected tool as `"hitl"` — driven by the tool safety prompt's rules (anything that creates, updates, deletes, merges, or otherwise performs an irreversible/destructive action). The `dangerous_tools` node then calls `interrupt()` with the tool name, arguments, and the safety classifier's stated reason, and blocks until `Command(resume=...)` is sent back in with a truthy/falsy decision.

**In the CLI (`SERVER.py`):** the interrupt message is printed, and `input("(y/n): ")` gathers the decision synchronously.

**In the Streamlit UI (`app_frontend.py`):** the interrupt surfaces as a modal `st.dialog` ("⚠ Approval Required") with distinct **Approve** / **Reject** buttons, and `extract_interrupt_message()` pulls a clean, human-readable message out of the raw LangGraph interrupt payload for display.

**Advantages:**
- Nothing destructive executes without an explicit human decision.
- The approval prompt shows the actual tool name and arguments that will run, not just a vague "are you sure?" — the human can catch wrong arguments, not just wrong intent.
- Rejection is a first-class outcome (`approval_routing` routes to the update/summary path with a `final_answer` explaining the action was cancelled), not an exception.
- Because it's implemented via LangGraph's checkpointer + `interrupt()`, and the checkpointer is now Postgres-backed, the paused state genuinely persists **across process restarts**, not just across the resume call — keyed by `thread_id`.

---

## Memory: Short-Term vs. Long-Term

ForgeMCP currently has **short-term memory (STM)** fully implemented, and treats **long-term memory (LTM)** as the single most important planned upgrade.

### Short-term memory — implemented

- Backed by `AsyncPostgresSaver` (`langgraph-checkpoint-postgres`), writing to the `checkpoints`, `checkpoint_blobs`, and `checkpoint_writes` tables.
- Scoped **per thread** (`thread_id`) — every message, every intermediate `State` field (plan, current subtask, tool call, safety decision, approval, result), and every pending interrupt is checkpointed after each graph step.
- Durable across restarts: killing and restarting either `SERVER.py` or `app_frontend.py` does not lose an in-progress conversation or a pending HITL approval.
- `balance_context_window()` trims the oldest human/AI message pair once a thread exceeds 20 messages, so STM cost stays bounded within a single long-running thread.
- `db_utils.clear_postgres_data()` gives a clean-slate reset for development/testing.

This is **memory of the current conversation** — it does not generalize anything across separate threads or separate sessions.

### Long-term memory — the primary planned upgrade

Right now, two separate conversations (two different `thread_id`s) share *nothing*. If a user tells the agent in one thread "I always want new repos private by default," that preference is gone the moment a new thread starts. **Adding a long-term memory layer is the single biggest planned improvement to this project**, and the intended design is:

- **Storage:** `PostgresStore` + `pgvector` (both already used in the author's separate memory-persistent chatbot project, so the pattern is proven) — a vector-indexed table separate from the LangGraph checkpoint tables, storing semantically embedded memory entries rather than raw message history.
- **What gets remembered:** user preferences ("default new repos to private," "always squash-merge," "my primary org is `Darshanshresthaa`"), recurring workflow patterns (e.g. a user who always creates a branch + PR + review-request as one unit), and durable facts about the user's repos/org structure that would otherwise need to be re-stated every session.
- **Write path:** a dedicated node (or a background/async hook) that, at the end of a thread (e.g. inside or after `summary_node`), evaluates whether anything from the completed conversation is worth persisting long-term — distinct from the STM checkpoint, which saves *everything* mechanically.
- **Read path:** at the start of `planner_node` (or a new node just before it), relevant long-term memories are retrieved via vector similarity search against the current request and injected into the planning/routing prompts as extra context — so "create my usual setup" can resolve against a stored preference instead of failing or asking the user to repeat themselves.
- **Why this matters for ForgeMCP specifically:** the planner already tries to interpret compound, personalized requests ("set up the repo the way I like it") — without LTM, it has no way to know what "the way I like it" means beyond what's in the current thread. LTM turns the agent from *stateless-per-thread* into *actually personalized*, which is a meaningfully different product, not just a bigger context window.
- **Design tension to resolve:** what belongs in LTM (durable, cross-session facts) vs. STM (this conversation's blow-by-blow state) needs a clear boundary, or the two systems will duplicate or contradict each other — this is called out explicitly as an open design question, not solved yet.

---

## Advantages

- **Handles compound, multi-step requests natively.** The planner-first architecture is the biggest functional advantage over a single-shot tool-calling agent — "create a repo, add a README, push my folder" is decomposed and executed as an ordered sequence instead of requiring one message per step.
- **Modular architecture** — MCP server and agent are fully decoupled processes communicating only over the MCP protocol; either can be swapped or redeployed independently.
- **Easy to extend on the tool side** — adding a new GitHub tool is: write one function decorated with `@mcp.tool` in the right subfolder, add it to that folder's `__init__.py`. No agent-side code changes required.
- **Genuinely durable state.** Both entrypoints now use `AsyncPostgresSaver` — a pending HITL approval, an in-progress plan, or an entire conversation thread survives a crash or restart, which was explicitly not true in earlier iterations.
- **Good separation of concerns** — prompts, node logic, graph wiring, state schema, and the LLM/service client are each in their own file, rather than one large notebook-style script.
- **Explicit, structured LLM outputs** — `RouterDecision`, `ToolSafetyDecision`, and `PlannerOutput` are Pydantic models used with `with_structured_output`, not string-parsed, so downstream routing logic works against typed fields.
- **Two working front-ends on one shared agent.** The CLI and Streamlit UI both compile the exact same `build_graph()` — there is no logic fork between them, only presentation.
- **Safe-by-default network posture** — `demo.py` actively refuses to bind to a non-loopback interface without an auth token configured, rather than silently running exposed and unauthenticated.
- **Uniform tool error handling** — nearly every tool wraps its GitHub call in `try/except` and re-raises as a `RuntimeError` with context, giving the LLM a legible error message to reason about instead of a raw traceback.
- **MCP compatibility** — because the tool layer is a standard MCP server, it is usable by any MCP client, not just this specific LangGraph agent.

---

## Drawbacks / Current Limitations

- **No long-term memory yet.** This is the most significant functional gap — see [Memory](#memory-short-term-vs-long-term) above. Every thread starts from zero personalization.
- **Tool routing is a single, unverified LLM call.** `normal_tools` calls `llm_with_tools.invoke(...)` once per subtask and trusts `tool_calls[0]` — there is no validation that the extracted arguments are complete, well-typed, or even relevant to the tool's actual signature before they're used in `execute_tools`.
- **No dedicated parameter-extraction stage.** Tool selection and argument extraction happen in the same LLM call. If the model picks the right tool but a wrong or missing argument, there's no intermediate validation node to catch it — the bad arguments flow straight through the safety check into execution.
- **Planner quality is entirely prompt-dependent.** There's no validation that the generated subtask list is actually correct, minimal, or correctly ordered — a poorly decomposed plan (too granular, missing a dependency, wrong order) will execute exactly as planned, wrong.
- **Safety classification is inferred, not declarative.** Whether a tool requires HITL is decided per-call by an LLM reading the tool's `name` and `description` — it is not a static property of the tool itself. A subtly reworded tool docstring, or an ambiguous subtask description, can change the safety classification of the *same* tool between runs.
- **A real bug in the `get_commit` Read tool:** a null-check written as `if username in None:` instead of `if username is None:` will raise a `TypeError` any time the tool is called without an explicit `username`, breaking the "default to authenticated user" convention every other Read tool relies on.
- **No retry/backoff on GitHub API calls.** `github_client.py`'s request wrapper makes a single attempt with a flat timeout; a transient network blip or a GitHub rate-limit response (403/secondary rate limit) is surfaced directly as a `RuntimeError` rather than retried.
- **No rate-limit awareness.** GitHub's rate-limit headers (`X-RateLimit-Remaining`, etc.) are never inspected, so the agent has no way to warn the user or back off before hitting a 403.
- **Inconsistent error handling across tools.** Some tools re-raise `ValueError` as-is; others wrap everything in `RuntimeError`; a few have thinner or copy-pasted error messages.
- **Minimal input validation.** Several Read tools validate `limit`/`page` ranges, but most create/update/delete tools do no argument validation beyond what GitHub itself will reject.
- **No automated test suite.** There are no test files in the repository; correctness currently depends on manual exercising through the notebooks and both UIs.
- **Limited observability/logging.** There is no structured logging, tracing, or metrics anywhere in `MCP/` or `Agent/` — debugging a failed tool call or a misrouted subtask currently means reading stdout or Streamlit's console output.
- **Security considerations:**
  - `GITHUB_TOKEN` is a single, presumably broad-scope PAT shared by all tools — there's no per-tool or per-user scoping, so any HITL-approved action runs with full token privileges.
  - `MCP_AUTH_TOKEN` is a single static bearer token (`StaticTokenVerifier`) shared by all clients — there is no per-client identity, token rotation, or expiry.
  - Secrets currently live in a local `.env` file loaded via `python-dotenv`; there's no secrets-manager integration for the deployed MCP server.
- **Scalability concerns.** `get_repository_code` fetches the full recursive tree and then makes one additional GitHub API call *per file* to decode its content — for a large repository this is both slow and consumes GitHub's rate limit quickly, with no pagination, streaming, or size cap.
- **Prompt dependence.** Planning, routing, and safety correctness rest entirely on prompt wording and few-shot examples rather than any code-level fallback or confidence threshold — there's no path for the graph to say "I'm not sure" and ask a clarifying question mid-plan.

---

## Future Improvements

Ordered roughly by expected impact:

1. **Long-term memory (LTM) via `PostgresStore` + `pgvector`.** The headline improvement — see the [dedicated section above](#memory-short-term-vs-long-term) for the full design. This turns the agent from stateless-per-thread into actually personalized across sessions (remembered preferences, recurring workflows, durable facts about the user's repos/orgs).
2. **Declarative, static tool-safety registry.** Tag each `@mcp.tool` function with a `safety="safe" | "hitl"` decorator argument at definition time, and have `tool_safety_node` read that tag directly (falling back to the LLM classifier only for tools that don't declare one). Removes the current risk of the same tool being classified differently across runs.
3. **A dedicated parameter-extraction/validation node** between tool selection and safety check — re-validate extracted arguments against the actual tool's JSON schema (FastMCP/MCP tools expose one) before anything is classified for safety.
4. **Plan validation/repair.** A lightweight check (or a second LLM pass) on `planner_node`'s output before execution begins — catching obviously malformed, circular, or missing-dependency plans early instead of discovering the problem mid-execution.
5. **Fix the `get_commit` `in None` bug** (should be `is None`) so the tool respects the "default to authenticated user" convention used everywhere else.
6. **Retry logic with backoff** in `github_client.py` for transient network errors and GitHub 403/secondary-rate-limit responses (e.g. `tenacity` or a small manual exponential backoff), rather than surfacing every transient failure as an immediate `RuntimeError`.
7. **Rate-limit-aware requests** — read `X-RateLimit-Remaining`/`X-RateLimit-Reset` from GitHub responses and surface a clear message (or pre-emptively slow down) instead of failing opaquely mid-conversation.
8. **Move credentials out of `.env` into a secrets manager** for the deployed environment, keeping `.env` for local development only.
9. **Better observability** — structured logging (with request IDs / thread IDs) around every node transition and every GitHub API call, plus optionally LangSmith tracing.
10. **Caching for cheap, frequently-repeated reads** — e.g. `get_repository`, `get_readme`, `list_repositories` — with a short TTL, to cut redundant GitHub API calls and rate-limit pressure within a single conversation.
11. **Streaming improvements** — currently only `llm_answer_node` streams; `tool_response_node` and `summary_node` do not, so tool-driven and summarized responses feel less responsive than pure-Q&A ones.
12. **Parallel tool execution where safe** — several Read subtasks (e.g. `get_repository` + `list_commits` + `get_languages` for an "overview" request) are independent and could fan out concurrently instead of the current one-tool-per-subtask model.
13. **A pluggable tool-registry / plugin architecture** — letting new tool categories be dropped into `MCP/Tools/` and auto-discovered rather than requiring a manual `__init__.py` edit at three levels.
14. **Authentication improvements** — replace the single static `MCP_AUTH_TOKEN` with per-client tokens/scopes, and consider scoping `GITHUB_TOKEN` per-organization or per-repo rather than one account-wide PAT.
15. **Automated tests** — unit tests around `github_client.py`'s status-code handling and the LangGraph routing functions would catch regressions like the `get_commit` bug automatically.

---

## Use Cases

- **GitHub automation** — creating repos/branches/files, opening and merging PRs, deleting stale resources, all through natural language instead of `gh` CLI commands.
- **Compound / multi-step GitHub workflows** — "create a repo, add a README, and push my local project" handled as one planned sequence instead of three separate manual instructions.
- **Repository management** — auditing a repo's languages, contributors, releases, tags, and branch protection status in one conversational pass.
- **AI coding assistants** — as the GitHub-facing tool layer behind a broader coding assistant, since `get_repository_code` can pull real file contents for the LLM to reason about.
- **DevOps workflows** — branch creation, PR review requests, and merges as part of a semi-automated release process, gated by human approval.
- **CI/CD support** — querying PR status, changed files, and commit history for pipeline-adjacent tooling.
- **Educational GitHub assistant** — the `llm_answer_node` path already positions this as a "GitHub, software development, and programming" Q&A assistant independent of the tool layer.
- **Enterprise MCP server** — the MCP layer alone, decoupled from this specific agent, could serve as the shared GitHub tool backend for multiple internal AI tools/agents.

---

## Installation

### Prerequisites
- Python 3.11+ (required — avoids an `interrupt()`/`get_config()` asyncio context bug on older versions)
- A GitHub Personal Access Token with `repo` scope
- A Mistral AI API key
- A PostgreSQL database (local or hosted) for the checkpointer

### 1. Clone and set up the environment

```bash
git clone https://github.com/Darshanshresthaa/ForgeMCP.git
cd ForgeMCP

conda create -n langchain_env311 python=3.11
conda activate langchain_env311
```

### 2. Install dependencies

```bash
# MCP server only
pip install -r requirements.txt

# Agent + Streamlit UI (includes MCP server deps + LangGraph/LangChain/Mistral/Postgres/Streamlit)
pip install -r requirements_agent.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
MCP_AUTH_TOKEN=your-mcp-bearer-token
MISTRAL_API_KEY=your-mistral-api-key
DB_URI=postgresql://user:password@host:port/dbname
```

> `.gitignore` already excludes `.env` — never commit real tokens or connection strings.

### 4. Run the MCP server

```bash
python demo.py
```

By default this binds `0.0.0.0:8000` (or `$PORT`/`$MCP_HOST` if set). If `MCP_HOST` resolves to anything other than `127.0.0.1`/`localhost`, `MCP_AUTH_TOKEN` **must** be set or the server refuses to start.

### 5. Point the agent at the server

In `Agent/service.py`, `get_mcp_server()` currently points at a deployed Render URL. For local development, change the `url` to your local server, e.g. `http://127.0.0.1:8000/mcp`.

---

## Quick Start (CLI)

```bash
$ python -m Agent.SERVER

You: what is a pull request?
Assistant: A pull request (PR) is a way to propose changes to a repository...

You: list my repositories
Assistant: Here are your public repositories: ForgeMCP, RagBasic, ...

You: create a repo called sandbox-test, add a README, then delete it
[planner_node breaks this into 3 ordered subtasks]

The assistant wants to run 'delete_repository' with arguments

{'repo_name': 'sandbox-test', 'confirm': True}.
Reason: Deleting a repository is an irreversible, destructive action.
Approve? (y/n)
(y/n): n
Assistant: Action cancelled — not approved by user.
```

---

## Running the Streamlit UI

```bash
streamlit run app_frontend.py
```

- Past threads reload automatically from Postgres on startup.
- **New-Chat** starts a fresh thread; **Reset-DB** wipes all checkpoint data.
- Destructive actions open an **Approval Required** modal with distinct Approve / Reject buttons instead of a terminal prompt.

---

## Example Commands

- "List my repositories"
- "Show me the README for my ForgeMCP repo"
- "What languages does my ForgeMCP repo use?"
- "Get the latest release for repo X"
- "Compare main and dev branches on ForgeMCP"
- "Create a new private repository called sandbox-test"
- "Create a repo called demo, add a README.md with 'hello', and push it" *(exercises the planner across 3 subtasks)*
- "Create a branch called feature/logging from main on ForgeMCP"
- "Open a pull request from feature/logging into main titled 'Add logging'"
- "List open pull requests on ForgeMCP"
- "Merge pull request #12 using squash"
- "Request a review from octocat on pull request #12"
- "Delete the file old_notes.md from ForgeMCP"
- "Delete the repository sandbox-test"
- "Who are the contributors on ForgeMCP?"
- "What is the difference between merge, squash, and rebase?" *(answered directly, no tool)*

---

## Project Review

*A critical, code-grounded assessment — not a marketing summary.*

**Architecture quality.** The two-layer split (MCP tool server / LangGraph agent) is the strongest architectural decision in the project: it's a genuine protocol boundary, not just a folder boundary, so the tool layer is reusable by any MCP client. Within the agent, adding a planner stage in front of the original classify → select → safety-check → [approve] → execute → respond pipeline is a real capability upgrade — it lets the agent handle compound requests instead of one tool call per user message, and the `update_task_node` / `planner_router` loop back is a clean way to iterate subtasks without a second graph. The weak point is still that individual decisions inside each subtask's cycle (tool selection, safety classification) are single unverified LLM calls with no schema or business-rule validation layer between them and execution.

**Code organization.** Strong at the file level — prompts, nodes, graph wiring, and state are cleanly separated, and the `Tools/{Read,create,Delete,Pull}` split by intent is easy to navigate. Weaker at the package level: inconsistent casing (`create` and `Delete` vs. `Read`/`Pull`), a couple of clearly notebook-era filenames that suggest the code hasn't had a full cleanup pass since being extracted from the original notebooks, and `SERVER.py` (Agent) vs. `server.py` (MCP) is a genuinely confusing near-duplicate filename across two packages that both get imported.

**Maintainability.** Reasonable. Because every tool follows the same shape (validate → call `github_client` → shape the return dict → catch and re-raise), a new contributor can read three existing tools and correctly write a fourth without additional documentation. The main maintainability risk is that safety classification lives in prompt text rather than code — a well-intentioned edit to `tool_safety_node_prompt.py`'s wording could silently change which tools require approval, with no test to catch it. The planner's correctness has the same soft dependency on prompt wording.

**Extensibility.** Good on the tool side (add a function, register it, done) and good on the prompt side (each prompt is independently editable). Weaker on the graph side — adding a genuinely new *stage* (e.g. parameter validation, or an LTM lookup before planning) requires touching `graph.py`'s wiring, `nodes.py`'s function set, and `state.py`'s schema simultaneously, which is normal for LangGraph but is a multi-file change for what's conceptually one new step.

**Design patterns.** The project uses a shared-singleton pattern for the FastMCP instance (all tool modules import the same `mcp` from `server.py`), a strategy-like pattern for routing (conditional edges dispatching on a returned string key), dependency injection for tools (`set_tools()` populating module-level state after async startup), and a plan/execute loop pattern for the multi-subtask flow (`planner_router` cycling back through the subtask pipeline until `plan_completed`). These are all appropriate choices for the framework. The module-level global (`tools`, `llm_with_tools` in `nodes.py`) is a pragmatic but slightly fragile choice — it makes the module stateful and order-dependent (the graph must not run before `set_tools()` is called), which both entrypoints currently handle correctly but which isn't enforced anywhere.

**Scalability.** The MCP tool layer scales fine as a stateless HTTP service. The one clear scalability problem is `get_repository_code`, which makes one GitHub API call per file in the (optionally filtered) tree with no concurrency, pagination, or size limit — this will be slow and rate-limit-hungry on any repository of meaningful size. The agent's state model is now Postgres-backed per-thread, which is a real improvement over in-memory state for both durability and (eventually) horizontal scaling.

**Security.** This is the area needing the most work before any production use. A single broad-scope `GITHUB_TOKEN` backs every tool with no per-action scoping; a single static `MCP_AUTH_TOKEN` authenticates every MCP client with no per-client identity or rotation; and whether an action requires human approval is decided by an LLM reading a tool description at runtime rather than a fixed, auditable policy. The delete tools' extra `confirm=True` requirement is a good defense-in-depth touch, but it doesn't fully offset the fact that safety classification itself is soft. The `demo.py` guard against binding to a public interface without auth is a genuinely good, deliberate security decision.

**Performance.** Acceptable for interactive, single-user use. No caching, no connection pooling beyond `requests`' defaults, no retry/backoff, and a flat timeout on every GitHub call — none of this will show up in normal manual testing, but all of it would show up under concurrent load or flaky network conditions.

**Production readiness.** Getting closer, but not yet production-ready, and the project doesn't claim to be. Durable Postgres checkpointing is now real (previously the top gap); the remaining gaps before production use are: a real test suite (currently none), retry/backoff and rate-limit handling on GitHub calls, a hardened auth model (scoped tokens, not one shared PAT/bearer token), moving safety classification from "LLM-inferred per call" to "declared and enforced per tool," and — the biggest remaining capability gap — long-term memory so the agent can actually personalize across sessions rather than starting cold every thread.

---

## Conclusion

ForgeMCP demonstrates a clean split between *capability* (a well-organized, typed MCP server exposing the GitHub API) and *judgment* (a LangGraph agent that plans, decides what to do, and pauses for human approval before doing anything irreversible). The MCP layer is genuinely reusable independent of the agent; the planner turns compound natural-language requests into reliably ordered execution; and the agent's HITL mechanism, now backed by durable Postgres state, is a real structural safeguard rather than a prompt instruction that can be reasoned around. The project is early-stage — it still lacks tests, retry logic, a hardened safety model, and above all long-term memory — but the architectural decisions already made (protocol-level tool exposure, a dedicated planning stage, a dedicated safety-classification node, `interrupt()`-based approval, Postgres-backed checkpointing, isolated prompts) form a solid foundation to build those hardening steps — and LTM in particular — on top of.
