# Eval Results: openrouter/minimax/minimax-m2.7

- **Version:** 004dd18
- **Model:** openrouter/minimax/minimax-m2.7
- **Timestamp:** 2026-04-09T05:00:32.057564+00:00

---

## Tool Use Accuracy

### 1. Find all Python files under src/tools/ that contain the word "async" and tell me how many there are.

**Max tool calls:** 5

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 4519 |
| Completion tokens | 158 |
| Total tokens | 4677 |
| Completion tok/s | 29.3 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 5.39 |
| Wall time (s) | 5.4 |

**Tool Calls:**
- `Grep pattern='async'`

**Response:**

**2 Python files** under `src/tools/` contain the word "async":

1. `src/tools/dispatcher.py`
2. `src/tools/delegate.py`

---

### 2. Read the file context/identity.md and summarize it in one sentence.

**Max tool calls:** 3

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 4750 |
| Completion tokens | 121 |
| Total tokens | 4871 |
| Completion tok/s | 11.6 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 10.44 |
| Wall time (s) | 10.44 |

**Tool Calls:**
- `Read context/identity.md`

**Response:**

This file defines my identity as **curunir**, a proactive assistant characterized by professionalism, directness, and problem-solving initiative, with capabilities including filesystem interaction, command execution, persistent memory, and scheduled task automation.

---

### 3. What is the current working directory? List all top-level folders.

**Max tool calls:** 3

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 5107 |
| Completion tokens | 189 |
| Total tokens | 5296 |
| Completion tok/s | 16.6 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 11.36 |
| Wall time (s) | 11.36 |

**Tool Calls:**
- `Bash pwd && ls -la`

**Response:**

**Current working directory:** `/app`

**Top-level folders:**

| Folder | Description |
|--------|-------------|
| `.claude` | Claude configuration directory |
| `.pytest_cache` | Pytest cache |
| `context` | Context/memory files |
| `docs` | Documentation |
| `eval` | Evaluation directory |
| `journal` | Journal files |
| `secrets` | Secrets management |
| `skills` | Skills directory |
| `src` | Source code |
| `workspace` | Workspace directory |

---

## Multi-Step Planning

### 4. I want to add a new tool called "summarize" that takes a file path and returns a summary. Walk me through every file I'd need to change and in what order, but don't make any changes.

**Max tool calls:** 15

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 73610 |
| Completion tokens | 1617 |
| Total tokens | 75227 |
| Completion tok/s | 40.3 |
| Iterations | 7 |
| LLM calls | 7 |
| LLM time (s) | 40.11 |
| Wall time (s) | 40.13 |

**Tool Calls:**
- `Glob **/*`
- `Read src/tools/dispatcher.py`
- `Read src/tools/schemas.py`
- `Read src/tools/__init__.py`
- `Read CLAUDE.md`
- `Read src/tools/README.md`
- `Read src/tools/fs_tools.py`
- `Glob tests/**/*.py`
- `Glob tests/*`
- `Read src/agent/system_prompt.py`

**Response:**

Here's the complete walkthrough of every file you need to change, in order:

---

## Files to Change (in order)

### 1. `src/tools/schemas.py`
**Purpose:** Define the tool's JSON schema so the LLM knows the interface.

**What to add:** A new dict entry in `_SCHEMAS` (or `_OPT_IN_SCHEMAS` if you want it opt-in only):
```python
{
    "type": "function",
    "function": {
        "name": "summarize",
        "description": "Summarize a file...",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "..."},
            },
            "required": ["file_path"],
        },
    },
},
```
Then add it to the `for _s in _SCHEMAS: _register(_s)` loop at the bottom.

---

### 2. `src/tools/summarize.py` (new file)
**Purpose:** The executor function that does the actual work.

**What to add:** A new file with a function like:
```python
from src.config import AgentConfig

def exec_summarize(args: dict, config: AgentConfig) -> str:
    """Summarize the contents of a file."""
    # read file, call LLM or use heuristics, return summary string
```

Signatures for existing tools follow the pattern `def exec_<toolname>(args: dict, config: AgentConfig) -> str`. You can put it in `fs_tools.py` alongside `read`/`edit`, but keeping it separate (like `web_fetch.py`) is cleaner if it has distinct dependencies (e.g., an LLM call).

---

### 3. `src/tools/dispatcher.py`
**Purpose:** Route the tool name to your executor function at runtime.

**What to add:** Import and register in `_SYNC_EXECUTORS` (since it sounds like a blocking I/O task, not async):
```python
from src.tools.summarize import exec_summarize
# ...
_SYNC_EXECUTORS = {
    # ... existing entries ...
    "summarize": exec_summarize,
}
```
If you make it async, you'd use `_get_native_async_executor()` instead.

---

### 4. `src/tools/README.md`
**Purpose:** Documentation for developers adding new tools.

**What to add:** A row in the "File Layout" table, a brief description in "Individual Tool Details", and note it in the "Default Tools" list. Follow the existing patterns.

---

### 5. `tests/test_tools.py`
**Purpose:** Unit tests for correctness.

**What to add:** Test cases for `exec_summarize()` and/or integration tests with the dispatcher. Follow the existing test patterns (async tests with `pytest-asyncio`, mock LLM where needed).

---

### 6. `CLAUDE.md` (optional but recommended)
**Purpose:** Keep architecture docs current.

**What to add:** `"summarize"` to the **Default tools** line under the Tools section:
```
**Default tools:** glob, grep, read, edit, write, bash, load_skill, web_fetch, delegate, schedule, summarize
```

---

## Summary Table

| Order | File | Change Type |
|-------|------|-------------|
| 1 | `src/tools/schemas.py` | Schema registration |
| 2 | `src/tools/summarize.py` | New executor (new file) |
| 3 | `src/tools/dispatcher.py` | Executor registration |
| 4 | `src/tools/README.md` | Documentation |
| 5 | `tests/test_tools.py` | Tests |
| 6 | `CLAUDE.md` | Architecture docs |

The core wiring is just **3 files**: schema → executor → dispatcher. The rest are docs and tests.

---

### 5. Find every skill that uses the "attach" tool, then for each one tell me what it does and why it needs attach.

**Max tool calls:** 15

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 9952 |
| Completion tokens | 783 |
| Total tokens | 10735 |
| Completion tok/s | 35.8 |
| Iterations | 3 |
| LLM calls | 3 |
| LLM time (s) | 21.89 |
| Wall time (s) | 21.91 |

**Tool Calls:**
- `Glob **/SKILL.md`
- `Grep pattern='attach'`
- `Read skills/email-send/SKILL.md`
- `Read skills/deep-research/SKILL.md`

**Response:**

## Skills Using the `attach` Tool

Only **2 skills** declare and use the `attach` tool:

---

### 1. `deep-research`
| | |
|---|---|
| **Does** | Conducts in-depth research by decomposing a topic into sub-questions, searching multiple sources (web, Reddit, X, LinkedIn, Gemini), synthesizing findings, and delivering a structured report as a PDF. |
| **Why it needs `attach`** | The final delivery is the report as a PDF file. The skill explicitly instructs to run `pandoc` to convert the markdown report to PDF, then attach it with `attach(path="{file}.pdf")`. The attachment is the primary deliverable — the text reply is just a summary. As the skill puts it: *"the report file must be attached, not just written."* |

---

### 2. `email-send`
| | |
|---|---|
| **Does** | Sends emails via the `gog` CLI (Gmail integration), supporting plain text, HTML bodies, multiple recipients, CC/BCC, and file attachments. |
| **Why it needs `attach`** | The `--attach` flag is passed directly to the `gog gmail send` command for each file to include as an email attachment (e.g. `--attach /path/to/report.pdf --attach /path/to/data.csv`). The `attach` tool is the mechanism the skill uses to bind local files into the outgoing email. |

---

**Note:** The remaining 9 skills (`web-search`, `reddit-research`, `xai-search`, `linkedin-research`, `gemini-search`, `playwright`, `git-contribute`, `skill-factory`, `extract-learnings`) do **not** use the `attach` tool at all.

---

### 6. Figure out how an incoming message travels from the WebSocket connection all the way to a tool being executed. Trace the full path through the code, citing files and line numbers.

**Max tool calls:** 20

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 63046 |
| Completion tokens | 2356 |
| Total tokens | 65402 |
| Completion tok/s | 20.5 |
| Iterations | 6 |
| LLM calls | 6 |
| LLM time (s) | 114.98 |
| Wall time (s) | 115.0 |

**Tool Calls:**
- `Glob **/*.py`
- `Read README.md`
- `Read src/channels/ws.py`
- `Read src/channels/router.py`
- `Read src/agent/agent.py`
- `Read src/tools/dispatcher.py`
- `Read src/tools/schemas.py`
- `Read src/tools/__init__.py`
- `Read run.py`
- `Read src/channels/base.py`
- `Read src/tools/fs_tools.py`

**Response:**

Here's the complete end-to-end trace, from a raw WebSocket frame to a tool executing:

---

## Step-by-step path

### 1. WebSocket server accepts a raw JSON frame

**File: `src/channels/ws.py`, lines 53–68**

```python
async for raw in websocket:               # line 54 — raw bytes received
    data = json.loads(raw)                # line 56 — parsed to dict
    msg = IncomingMessage(
        content=data.get("content", ""),  # line 62 — extracted
        channel="cli",
        session_id=SESSION_ID,
        reply_address={},
        command=data.get("command") or None,
    )
    await self.in_queue.put(msg)          # line 68 — enqueued
```

This is a **sync** iteration over the WebSocket stream — each frame is processed sequentially. On disconnect, a sentinel `command="extract"` message is injected at **lines 75–82** to trigger memory extraction.

---

### 2. `route_outbound` task drains the out-queue

**File: `run.py`, lines 362 (spawned), `src/channels/router.py`, lines 9–15**

```python
# router.py
async def route_outbound(out_queue: asyncio.Queue, channels: dict[str, Channel]):
    while True:
        msg: OutgoingMessage = await out_queue.get()   # line 11 — blocks until something arrives
        channel = channels.get(msg.channel)            # line 12 — routes by channel name
        await channel.send(msg)                        # line 15 — dispatches
```

---

### 3. `agent_worker` pulls from the in-queue and bridges to the agent

**File: `run.py`, lines 165–279**

```python
msg = await in_queue.get()                         # line 173
# ...
content = _build_content(msg)                     # line 208 — wraps message with channel metadata
attachments = []
metadata: dict = {}
handle_task = asyncio.create_task(
    agent.handle(
        content, msg.session_id,                  # line 213 — actual agent entry point
        on_tool_call=on_tool_call, attachments=attachments,
        metadata=metadata, stop_event=stop_event,
    )
)
# ...
await out_queue.put(OutgoingMessage(...))         # lines 271–279 — result enqueued back
```

`agent_worker` is the async loop that dequeues messages from `in_queue`, calls `agent.handle()`, and enqueues the result to `out_queue` for `route_outbound` to ship back.

---

### 4. `Agent.handle()` runs the agent loop

**File: `src/agent/agent.py`, lines 144–308**

```python
history = self.sessions.setdefault(session_id, [])   # line 161 — per-session history
history.append({"role": "user", "content": message})  # line 172 — message appended
tool_schemas = self._get_tool_schemas(session_id)    # line 181 — schemas fetched

for iteration in range(self.config.max_iterations):  # line 207
    response = await call_llm(...)                  # line 217 — LLM called with schemas
```

The loop iterates up to `max_iterations` times. Each iteration:
1. Calls the LLM with system prompt + conversation history + tool schemas (line 217)
2. If `response.tool_calls` is present (line 241), appends the assistant message to history and **executes each tool** (line 262)
3. After all tool results are appended back as `role=tool` messages (line 281), the loop `continue`s to call the LLM again
4. When `response.text` is non-empty and no tool calls remain (line 291), the final response is returned and the loop exits

---

### 5. Tool schemas come from `get_tool_schemas`

**File: `src/tools/schemas.py`, lines 1–25, 293–328**

All schemas are registered at module-import time via `_register()` (line 6). `get_tool_schemas()` (line 17) returns:
- **Default tools** (all non-opt-in registered schemas) when called with `names=None`
- **Skill-unlocked tools** (e.g. `attach`) when `load_skill` adds them to `_session_tools` in the agent (agent.py lines 272–277)

---

### 6. `execute_tool_call()` dispatches to the right executor

**File: `src/tools/dispatcher.py`, lines 40–68**

```python
async def execute_tool_call(name, args, config, ...):
    async_executor = _get_native_async_executor(key)  # line 50 — checks async first (delegate)
    if async_executor:
        return await async_executor(args, config, ...)  # line 52

    sync_executor = _SYNC_EXECUTORS.get(key)           # line 55 — checks sync map
    if sync_executor:
        result = await asyncio.to_thread(sync_executor, args, config)  # line 61
        # schedule tool triggers context sync
        if key == "schedule" and context_sync and ...:
            await context_sync.notify_write(...)       # lines 64–66
        return result

    return f"Unknown tool: {name}"
```

**Sync tools** (wrapped in `asyncio.to_thread` to avoid blocking the event loop): `glob`, `grep`, `read`, `edit`, `write`, `bash`, `load_skill`, `web_fetch`, `attach`, `schedule`

**Native async tools** (awaited directly): `delegate`

---

### 7. The concrete executor runs (example: `read`)

**File: `src/tools/fs_tools.py`, lines 156–185**

```python
def exec_read(args: dict, config: AgentConfig) -> str:
    path = Path(args["file_path"])
    if not path.exists():
        return f"Error: File not found: {path}"

    suffix = path.suffix.lower()
    reader = _BINARY_READERS.get(suffix)          # line 164 — PDF, DOCX, XLSX, CSV
    if reader:
        return reader(path)                      # line 166

    if suffix in _IMAGE_EXTENSIONS:
        return f"This is an image file..."

    lines = path.read_text().splitlines()        # line 171 — text path
    numbered = [f"{i}\t{line}" for i, line in ...]
    return "\n".join(numbered)                    # line 183
```

---

## Visual summary

```
WebSocket frame (ws.py:54)
    │
    ▼ json.loads → IncomingMessage (ws.py:56–67)
    │
    ▼ in_queue.put (ws.py:68)
    │
    ▼ agent_worker dequeues (run.py:173)
    │
    ▼ agent.handle(...) (run.py:213 → agent.py:144)
    │       │
    │       ▼ call_llm with tool_schemas (agent.py:217)
    │       │
    │       ▼ response.tool_calls? (agent.py:241)
    │       │       │
    │       │       ▼ for each tool_call:
    │       │       │   execute_tool_call() (agent.py:262 → dispatcher.py:40)
    │       │       │       │
    │       │       │       ▼ sync map lookup (dispatcher.py:55)
    │       │       │       │
    │       │       │       ▼ asyncio.to_thread(exec_read, ...) (dispatcher.py:61)
    │       │       │       │
    │       │       │       ▼ exec_read() (fs_tools.py:156)
    │       │       │
    │       ▼ history.append tool result (agent.py:281)
    │       │
    └─────── loop back to call_llm (agent.py:288) ──────────────────┘
              │
              ▼ no tool_calls + text → return (agent.py:299)
              │
              ▼ out_queue.put (run.py:271)
              │
              ▼ route_outbound (router.py:11,15)
              │
              ▼ WebSocketChannel.send() (ws.py:84,98)
```

The round trips between LLM call and tool execution (steps 4–7 repeated per tool) continue until the model produces a text reply with no tool calls, or `max_iterations` (default 15) is exhausted.

---

## Memory Retrieval

### 7. What do you know about me? Check your memory before answering.

**Max tool calls:** 8

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 17702 |
| Completion tokens | 580 |
| Total tokens | 18282 |
| Completion tok/s | 12.2 |
| Iterations | 4 |
| LLM calls | 4 |
| LLM time (s) | 47.59 |
| Wall time (s) | 47.6 |

**Tool Calls:**
- `Read context/memory/README.md`
- `Glob context/memory/**/*`
- `Read context/memory/preferences.md`
- `Read context/memory/people`
- `Read context/memory/projects.md`
- `Glob context/memory/people/*.md`

**Response:**

Here's what I know about you from my memory:

**You're Marc Chen** (Marcus David Chen), 45, based in San Mateo, CA.

**Day job:** Engineering leader at Salesforce (6 years there, 20+ years total SaaS experience).

**Side venture:** Founder of **BrightPath.AI** (doing AI agents for marketing/SaaS) — your X handle is @marc_chen, company @brightpath_ai. Still figuring out whether it's consulting, product, or both.

**You're building a lot:** curunir (my own framework), gtm-agent (GTM product for builders), code_factory, trading_agent, Vaultnet.tech, and more — you name it. Prolific builder across domains.

**Communication style:** You prefer terse, no-bullshit communication. "Yes", "do it", "critique the critique" — no preamble, no pleasantries. I should match that.

**Content voice:** You hate corporate tone and self-bragging. You want X to feel authentic — curious, understated, engineer-sharing-learnings energy. No "revolutionizing", no humblebrags, no LinkedIn-style thought leadership slop.

**Audience priority:** Investors first, potential customers second, fellow builders third.

**Family:** Wife Elena, kids Kai (8), Mia (9), and Suki.

**You distrust polished AI output:** You routinely ask for meta-critiques ("critique the critique") rather than taking generated advice at face value.

Anything you want to add or correct?

---

### 8. Before answering this: what projects am I currently working on? Look in memory first.

**Max tool calls:** 5

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 10508 |
| Completion tokens | 516 |
| Total tokens | 11024 |
| Completion tok/s | 18.3 |
| Iterations | 3 |
| LLM calls | 3 |
| LLM time (s) | 28.15 |
| Wall time (s) | 28.15 |

**Tool Calls:**
- `Read context/memory/README.md`
- `Glob context/memory/**/*`
- `Read context/memory/projects.md`

**Response:**

Based on your memory, here's a summary of what you're currently working on:

## Active Projects

| Project | What | Status |
|---------|------|--------|
| **curunir** | Your agent framework — asyncio, Docker, skills/memory/scheduling | Operational, evolving toward system-initiated loops, GitHub pipeline, streaming |
| **gtm-agent / LaunchKit** | AI-powered GTM product for technical solopreneurs | Phase 1 built (onboard-ingest skill), Phases 2-5 planned; still figuring out pricing, name, web vs conversational |
| **skill_factory** | Meta-skill that builds skills (spec → TDD → SKILL.md → smoke test) | Operational, actively used |
| **code_factory** | GitHub issues → merged PRs pipeline via Claude CLI | Fully implemented, battle-tested |
| **curunir-context** | Persistent state repo mounted as Docker volume | Active, in daily use |
| **curunir-personas** | Persona-based skill bundles (1 persona so far) | Early stage |
| **trading_agent** | LLM-driven quantitative trading via Coinbase | Public, less recently updated |
| **playbook / playbook_ui** | AI email assistant for Gmail | 19 open issues, active development |
| **conversation_with_ai** | Compare AI model perspectives | Active, updated 2026-03-20 |

## Exploratory
- **BrightPath Ventures** — still figuring out if it's consulting, product, or both
- **Vaultnet.tech** — local-first AI platform (separate from BrightPath)

**Note:** The projects.md was last updated 2026-03-22, so it's reasonably fresh. Would you like me to research anything specific about these projects, or do you have a new question to tackle?

---

### 9. Who are the people you remember? Check context/memory/ for any information about contacts or collaborators.

**Max tool calls:** 10 — **LIMIT HIT**

**Tool Calls:**
- `Read context/memory/README.md`
- `Glob context/memory/**/*`
- `Glob context/memory/people/**/*`
- `Read context/memory/preferences.md`
- `Read context/memory/projects.md`
- `Bash ls -la context/memory/people/`
- `Read context/memory/tasks.md`
- `Bash ls -la context/memory/archives/conversations/`
- `Read context/memory/archives/conversations/2026-04-08-agentic-role-assessment-blocker.md`
- `Read context/memory/archives/conversations/2026-04-08-interaction-failure.md`

**Response:**

*Model did not produce a response within the tool-call budget (10/10 calls used).*

---

## Instruction Following

### 10. What is your name and what are you? Answer only from your identity file, don't make anything up.

**Max tool calls:** 8

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 7869 |
| Completion tokens | 227 |
| Total tokens | 8096 |
| Completion tok/s | 14.4 |
| Iterations | 3 |
| LLM calls | 3 |
| LLM time (s) | 15.82 |
| Wall time (s) | 15.83 |

**Tool Calls:**
- `Glob **/*identity*`
- `Read context/memory/README.md`
- `Read context/identity.md`

**Response:**

My name is **curunir**, and I am a proactive assistant with many useful skills and tools.

---

### 11. List all skills you have available. Only list what's in your skill manifest, nothing else.

**Max tool calls:** 2

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 2212 |
| Completion tokens | 312 |
| Total tokens | 2524 |
| Completion tok/s | 19.3 |
| Iterations | 1 |
| LLM calls | 1 |
| LLM time (s) | 16.21 |
| Wall time (s) | 16.21 |

**Tool Calls:** *(none)*

**Response:**

Based on my skill manifest:

| Skill | Description |
|-------|-------------|
| deep-research | In-depth topic research and comprehensive analysis reports |
| email-send | Send emails via gog CLI |
| extract-learnings | Process meeting/incident notes to extract durable knowledge |
| gemini-search | Web search and YouTube summarization via Gemini API |
| git-contribute | Autonomous bug fix and feature implementation for GitHub repos |
| linkedin-research | LinkedIn profile, company, and job posting research |
| playwright | Web scraping, browser navigation, and UI interaction |
| reddit-research | Reddit discussions, reviews, and community sentiment analysis |
| skill-factory | Create and build new skills |
| web-search | Brave Search API for web queries |
| xai-search | Web search and X/Twitter search via xAI/Grok |

---

### 12. I want you to write a haiku about the ocean. Do not use any tools — just respond directly.

**Max tool calls:** 1

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 2199 |
| Completion tokens | 80 |
| Total tokens | 2279 |
| Completion tok/s | 13.6 |
| Iterations | 1 |
| LLM calls | 1 |
| LLM time (s) | 5.9 |
| Wall time (s) | 5.9 |

**Tool Calls:** *(none)*

**Response:**

Tidal waves crash and rise,
salt wind whispers ancient songs—
moon pulls the blue heart.

---

## Skill Orchestration

### 13. Load the web-search skill and search for "asyncio best practices 2025". Summarize the top results.

**Max tool calls:** 12

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 30263 |
| Completion tokens | 1014 |
| Total tokens | 31277 |
| Completion tok/s | 18.7 |
| Iterations | 5 |
| LLM calls | 5 |
| LLM time (s) | 54.12 |
| Wall time (s) | 55.81 |

**Tool Calls:**
- `LoadSkill web-search`
- `Bash curl -s "https://api.search.brave.com/res/v1/web/search?q...`
- `WebFetch https://shanechang.com/p/python-asyncio-best-practices-pitfalls/`
- `WebFetch https://discuss.python.org/t/asyncio-best-practices/12576`
- `WebFetch https://levelup.gitconnected.com/mastering-pythons-asyncio-the-unspoken-secrets-of-writing-high-performance-code-3d7483518894?gi=06d0175b96f6`
- `WebFetch https://betterstack.com/community/guides/scaling-python/python-async-programming/`
- `WebFetch https://docs.python.org/3/library/asyncio-dev.html`

**Response:**

## Summary: asyncio Best Practices (2025)

### Core Entry Points & Initialization
- **Use `asyncio.run()`** as the main entry point — it properly sets up and tears down the event loop and handles cleanup on exceptions
- **Enable debug mode** during development via `PYTHONASYNCIODEBUG`, `python -X dev`, or `asyncio.run(main(), debug=True)` — catches thread-safety violations, slow callbacks, and missing awaits

### Concurrency & Task Management
- **Use `asyncio.create_task()`** to schedule coroutines concurrently, and `asyncio.gather()` to wait for multiple tasks
- **Always await coroutines** — calling `coro()` without await emits `RuntimeWarning` (coroutine never awaited)
- **Retrieve exceptions from tasks** — unhandled exceptions in detached tasks are silently lost; always `.result()` or `.exception()` on tasks
- **Use `asyncio.Semaphore`** to limit concurrency and prevent resource exhaustion

### Blocking Code
- **Never call CPU-bound or blocking code directly** in async functions — it blocks the entire event loop
- Use `loop.run_in_executor()` with `ThreadPoolExecutor` or `ProcessPoolExecutor` for blocking operations

### Resource Management
- **Use async context managers** (`async with`) for proper cleanup (e.g., `aiohttp.ClientSession`)
- **Close async generators explicitly** with `contextlib.aclosing()` to ensure cleanup runs in expected context
- **Create async generators only after the event loop is running** — otherwise the event loop can't manage them properly
- **Avoid concurrent iteration/closure** of the same async generator

### Cancellation
- **Handle `asyncio.CancelledError`** gracefully in tasks — clean up resources and re-raise so callers know the task was cancelled

### Common Gotchas
| Mistake | Fix |
|---------|-----|
| Using `time.sleep()` instead of `asyncio.sleep()` | `asyncio.sleep()` yields control back to the event loop |
| Forgetting to `await` | The coroutine runs but silently fails |
| Long-running loops without yielding | Break work into smaller chunks; use `asyncio.sleep(0)` to yield |
| Mixing sync and async libraries without executor | Use `run_in_executor()` for sync I/O |

### Testing
- Ensure each test runs with a clean event loop state
- Use `pytest-asyncio` for proper async test support

These practices align with Python's official documentation and community consensus from early 2025.

---

### 14. Load the deep-research skill and tell me what sub-skills it depends on before running anything.

**Max tool calls:** 5

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 6362 |
| Completion tokens | 331 |
| Total tokens | 6693 |
| Completion tok/s | 36.6 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 9.04 |
| Wall time (s) | 9.04 |

**Tool Calls:**
- `LoadSkill deep-research`

**Response:**

Here's what **deep-research** depends on:

## Always Required
| Skill | Role |
|-------|------|
| **`web-search`** | Backbone for every research task — authoritative articles, news, reference |

## Conditional (pick 2-3 based on topic)

| Skill | When to Use |
|-------|-------------|
| **`reddit-research`** | Consumer products, app/tool reviews, developer sentiment, complaints |
| **`xai-search`** | Breaking news, trending events, real-time X/Twitter reactions |
| **`gemini-search`** | Google's index (thin Brave results), YouTube video summarization |
| **`linkedin-research`** | Company/startup analysis, founder/exec backgrounds, job postings, hiring signals |

---

**To run deep-research, you need:**
1. **`web-search`** (always) — load this first
2. Then load 1-3 additional skills based on your topic (consumer product → Reddit; company → LinkedIn + Gemini; breaking news → X; etc.)

Would you like to proceed with a research task, or do you want me to load any of these dependencies for you first?

---

### 15. Which skill would you use to research a topic on Reddit? Load it and explain what it does.

**Max tool calls:** 5

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 6175 |
| Completion tokens | 353 |
| Total tokens | 6528 |
| Completion tok/s | 63.7 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 5.54 |
| Wall time (s) | 5.54 |

**Tool Calls:**
- `LoadSkill reddit-research`

**Response:**

## Reddit Research Skill

This skill is designed for **product and market research** — specifically to find what real users are saying about a product, competitor, pain point, or topic on Reddit.

### How it works (2-step pipeline)

**Step 1 — Discovery**
Uses Brave Search (with `site:reddit.com`) to find Reddit posts matching your query. This bypasses the fact that Reddit blocks headless browsers at the network level.

**Step 2 — Extraction**
Fetches the full post and comments via Reddit's public `.json` API. No authentication needed — it's a public API. The output includes title, author, scores, post body, and comments — all parsed cleanly with `jq`.

### Key requirements
- `BRAVE_API_KEY` environment variable
- `curl` and `jq` utilities

### Why not Playwright?
Reddit detects and rejects automated browser traffic *before* any content loads. This skill avoids the issue entirely by using search + JSON API — no browser involved.

### Common use cases
- Competitive analysis (what do users say about competitor X?)
- Product feedback mining
- Pain point discovery
- Community sentiment analysis

Would you like me to demo it on a specific topic?

---

## Error Recovery

### 16. Read the file src/nonexistent/fake_module.py and tell me what's in it.

**Max tool calls:** 3

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 4712 |
| Completion tokens | 155 |
| Total tokens | 4867 |
| Completion tok/s | 20.6 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 7.52 |
| Wall time (s) | 7.52 |

**Tool Calls:**
- `Read src/nonexistent/fake_module.py`

**Response:**

That file doesn't exist at `src/nonexistent/fake_module.py`. The path `src/nonexistent/` likely doesn't exist in the current project structure.

Would you like me to:
1. Search for similar files in the project?
2. Check what directories/files actually exist under `src/`?
3. Create this file for you?

Let me know what you'd prefer!

---

### 17. Run the bash command `python -c "import nonexistent_module"` and handle whatever happens.

**Max tool calls:** 3

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 4817 |
| Completion tokens | 249 |
| Total tokens | 5066 |
| Completion tok/s | 55.0 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 4.53 |
| Wall time (s) | 4.54 |

**Tool Calls:**
- `Bash python -c "import nonexistent_module"`

**Response:**

Handled. The command executed and Python raised a `ModuleNotFoundError: No module named 'nonexistent_module'` — this is the expected behavior. Python throws this exception whenever you try to import a module that isn't installed or doesn't exist in the Python path.

The process exit code was non-zero (indicating an error), but no special handling was needed — this is standard runtime behavior, not an actual failure in your environment or code.

---

### 18. Search for the pattern "zzz_no_match_zzz" across the entire codebase. What do you conclude?

**Max tool calls:** 3

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 4816 |
| Completion tokens | 361 |
| Total tokens | 5177 |
| Completion tok/s | 24.2 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 14.89 |
| Wall time (s) | 14.9 |

**Tool Calls:**
- `Grep pattern='zzz_no_match_zzz'`

**Response:**

## Search Results

The pattern `zzz_no_match_zzz` was **not found** in the actual codebase. It only appears once, in an **evaluation/documentation file**:

> **`eval/article-draft-e4b.md`**  
> `"...both found `zzz_no_match_zzz` only in eval/documentation files. Sonnet correctly identified it as a test pattern; E4B noted the matches but was less precise about what they meant."`

### Conclusion

The pattern `zzz_no_match_zzz` is a **deliberate test artifact** used in an evaluation/benchmark context (appears to be an LLM evaluation comparing responses from different models). It is **not part of the codebase itself** — it's being discussed *about* in the evaluation documentation, not used as real code, content, or configuration.

In other words: this codebase contains **no matches** for that string, which is itself the expected behavior — it was designed to be a non-matching probe pattern.

---

## Output Quality

### 19. Explain how Curunir's context overflow handling works. Be concise — under 100 words.

**Max tool calls:** 8

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 5156 |
| Completion tokens | 291 |
| Total tokens | 5447 |
| Completion tok/s | 16.1 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 18.11 |
| Wall time (s) | 18.12 |

**Tool Calls:**
- `Read context/memory/README.md`
- `Grep pattern='context.*overflow|overflow|truncat|context.*window'`

**Response:**

**Curunir's context overflow handling:**

The agent loop enforces a **15-iteration cap** and **truncates conversation history at ~600K characters**. When the limit is hit, older messages are dropped to make room for new ones. This prevents the context window from overflowing while preserving recent context. The loop also auto-captures learnings to persistent memory so important information survives beyond the truncated window.

---

### 20. Compare the delegate tool to a simple function call. When would you use one vs the other?

**Max tool calls:** 5

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 2343 |
| Completion tokens | 551 |
| Total tokens | 2894 |
| Completion tok/s | 21.9 |
| Iterations | 1 |
| LLM calls | 1 |
| LLM time (s) | 25.21 |
| Wall time (s) | 25.21 |

**Tool Calls:** *(none)*

**Response:**

## Delegate Tool vs. Simple Function Call

### Simple Function Call (bash, read, write, etc.)

- **Runs inline** — shares your context window
- **Synchronous** — you get the result immediately
- **Lightweight** — good for quick, atomic operations
- **Context persists** — all intermediate work counts toward your context limit

### Delegate Tool

- **Runs in isolation** — creates a sub-agent with a **clean context window**
- **Asynchronous feel** — you get only the final answer; intermediate work is invisible
- **Self-contained** — the sub-agent has access to all tools but its work doesn't fill your context
- **Good for**:
  - Processing large documents (PDFs, large text files)
  - Image analysis
  - Multi-step research tasks
  - Any task that might generate lots of intermediate tokens

### When to Use Each

| Scenario | Use |
|----------|-----|
| Quick file read, write, or command | Function call |
| Need result immediately in current flow | Function call |
| Processing a large PDF or long document | **Delegate** |
| Multi-step research with many steps | **Delegate** |
| Task might token-bomb your context | **Delegate** |
| Sub-task should be independent/self-contained | **Delegate** |
| Simple arithmetic, string manipulation | Function call |

### Mental Model

Think of **delegate** as spinning up a temporary assistant who works behind a curtain — you hand them a task, they do all the work out of your sight, and report back only with the answer. Use it when the task is complex enough that its intermediate steps would bloat your context or when you want clean separation of concerns.

---

### 21. Read src/agent/agent.py, src/tools/dispatcher.py, and src/skills.py. What is the most important design decision in each file? Justify briefly.

**Max tool calls:** 10

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 9408 |
| Completion tokens | 564 |
| Total tokens | 9972 |
| Completion tok/s | 20.0 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 28.19 |
| Wall time (s) | 28.19 |

**Tool Calls:**
- `Read src/agent/agent.py`
- `Read src/tools/dispatcher.py`
- `Read src/skills.py`

**Response:**

Here's my breakdown:

---

### `src/agent/agent.py`
**Design decision: Hybrid sync/async tool loop with iteration cap and context overflow recovery**

The agent runs in a `for` loop over `max_iterations`, awaiting the LLM and then dispatching tool calls sequentially within the same coroutine. The key insight is that tools are executed **one at a time, awaiting each before the next LLM call** — not batched. This is a deliberate trade-off: it keeps the loop simple and the history stateful, but it means a long tool chain blocks the entire event loop. The context overflow recovery (trimming history by half on `ContextWindowExceededError`) and the per-session char-limit trimming (`_trim_history`) are both defensive measures layered on top of this single-threaded loop design.

---

### `src/tools/dispatcher.py`
**Design decision: Separate sync vs. async executor dispatch via `asyncio.to_thread`**

The dispatcher splits tools into two buckets: synchronous I/O-bound tools (filesystem, web fetch, bash) run in a thread via `asyncio.to_thread()`, while native async tools (e.g. `delegate`) are awaited directly. The rationale is sound — `to_thread` offloads blocking calls without needing an explicit `run_in_executor` setup — but it means every sync tool call still creates a new thread each time it's invoked. There's no thread pool reuse, which could be a bottleneck under heavy tool call volume.

---

### `src/skills.py`
**Design decision: Skills are discovered at runtime from `SKILL.md` files via frontmatter scanning**

Rather than registering skills as code, the system scans a directory for `*/SKILL.md` files, parses their YAML frontmatter, and dynamically builds a markdown table for the system prompt. `load_skill` then reads the full file content at runtime. This is a classic **plugin-on-disk** pattern: zero coupling between the agent core and any specific skill. The trade-off is that every skill invocation does a filesystem read, and the frontmatter parsing is naive (no real YAML parser, just line-splitting).

---

## Efficiency

### 22. What model am I configured to use? Find the answer with as few tool calls as possible.

**Max tool calls:** 8

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 9882 |
| Completion tokens | 492 |
| Total tokens | 10374 |
| Completion tok/s | 27.1 |
| Iterations | 4 |
| LLM calls | 4 |
| LLM time (s) | 18.16 |
| Wall time (s) | 18.17 |

**Tool Calls:**
- `Bash echo "Model: $MODEL_NAME" && cat ~/.config/curunir/config...`
- `Read /app/pyproject.toml`
- `Bash env | grep -i model`

**Response:**

You're configured to use **`openrouter/minimax/minimax-m2.2`** (via the `MODEL` environment variable).

---

### 23. Does this project have any scheduled tasks? Check and report.

**Max tool calls:** 3

**Stats:**

| Metric | Value |
|--------|-------|
| Prompt tokens | 4713 |
| Completion tokens | 123 |
| Total tokens | 4836 |
| Completion tok/s | 15.9 |
| Iterations | 2 |
| LLM calls | 2 |
| LLM time (s) | 7.73 |
| Wall time (s) | 7.73 |

**Tool Calls:**
- `Schedule list`

**Response:**

No, this project has **no scheduled tasks** configured. The task scheduler is currently empty.

---

### 24. How many tests does this project have? Just give me the number.

**Max tool calls:** 8 — **LIMIT HIT**

**Tool Calls:**
- `Glob **/*test*`
- `Glob **/*spec*`
- `Glob **/tests/**/*.py`
- `Glob **/test*`
- `Glob **/*_test.py`
- `Glob **/test_*.py`
- `Glob **/*.test.js`
- `Glob **/*Test.java`

**Response:**

*Model did not produce a response within the tool-call budget (8/8 calls used).*

---
