---
layout: default
title: "GLM-5.1: A Step Backward from GLM-5 Turbo"
---

*This article is part of the [Agentic Eval Series](./), where we run different models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. The only variable is the model. Claude Sonnet 4.6 is the baseline. This is a qualitative smoke test — single-run, no repeated trials — useful for spotting capability gaps, not for definitive model rankings.*

# GLM-5.1: A Step Backward from GLM-5 Turbo

Zhipu AI's GLM-5 Turbo went [23/24 against Sonnet 4.6](article-draft-glm5turbo-sonnet46-20260408) — a statistical tie, with codebase-grounded analysis that matched Sonnet's depth. GLM-5.1, the newer model from the same family, should be at least as good. Right?

GLM-5.1 completed 17 of 24 prompts. Seven failures. The quality is there when it works — but it doesn't work often enough.

## The Setup

| | GLM-5.1 | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | OpenRouter (cloud) | Anthropic (cloud) |
| **Provider** | Zhipu AI | Anthropic |
| **Cost** | Paid (OpenRouter) | Paid (Anthropic) |
| **Privacy** | Data sent to OpenRouter/Zhipu | Data sent to Anthropic |

Same harness, same tools, same system prompt.

Full results: [GLM-5.1](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260408-223000-openrouter_z-ai_glm-5_1.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### GLM-5.1 completed 17 of 24 prompts. Sonnet completed 23.

Seven failures across three distinct failure modes: budget exhaustion from over-reading, path hallucination, and an API error. On prompts where GLM-5.1 reaches the right files, the analysis is solid — sometimes sharper than Sonnet's. But it gets there less than three quarters of the time.

### Where They're Equal (13 prompts)

**Basic tool use (1–3):** Both grepped for "async" and found 2 files. Both read `identity.md` and summarized it. Both listed the working directory. GLM-5.1 added context about what each async usage does — a nice touch. Equal.

**Attach skills (5):** Both found deep-research and email-send. GLM-5.1 was especially clear here — explicitly stated "Only deep-research uses the attach tool" and that email-send's `--attach` is a CLI flag, not the Curunir tool. The sharpest version of this answer in the series.

**Memory — about me (7):** GLM-5.1 used 7 tool calls across 5 iterations, searching memory files including archived conversations. Thorough, accurate profile. Sonnet used 2 tool calls. Both correct.

**Projects (8):** Both read `projects.md` and returned detailed project lists. GLM-5.1 included open tasks and roadmap items. Equal.

**Identity (10):** Both found and read `context/identity.md`. Both answered correctly from the right source.

**Skills list (11):** Both listed 11 skills from the manifest, zero tool calls.

**Haiku (12):** Both wrote one.

**Deep-research deps (14):** Both loaded the skill. GLM-5.1 included a detailed topic-to-skill mapping table — more thorough than most models.

**Reddit skill (15):** Both loaded and explained the two-step pipeline.

**Failed import (17):** Both handled the ModuleNotFoundError cleanly.

**No-match pattern (18):** Both identified the sentinel test case.

**Delegate comparison (20):** Neither read code. Both gave strong comparisons. GLM-5.1 had a standout line: "Use delegate when the *journey* doesn't matter, only the *destination*."

**Scheduled tasks (23):** Both checked the scheduler, found nothing.

### Where Sonnet Is Better (3 prompts)

**People (9):** Both completed. GLM-5.1 used 9 tool calls across 6 iterations — thorough, found Marc, family, and Thariq, noted the empty `people/` directory as a gap. Sonnet used 5 tool calls and was more concise. Both succeeded, Sonnet was cleaner.

**Model config (22):** GLM-5.1 found `anthropic/claude-sonnet-4-20250514` — the hardcoded default in `src/config.py`. Sonnet found the actual runtime `MODEL` env var. GLM-5.1 answered a different question: what's the default vs. what's currently running. Sonnet's answer was more operationally correct.

**Context overflow (19):** Sonnet failed its usual way — 8/8 tool calls, no response. GLM-5.1 used 3 tool calls and answered about the delegate tool and persistent memory. Correct in spirit, though less code-grounded than GLM-5 Turbo's answer on the same prompt. GLM-5.1 wins this one by default.

### Where GLM-5.1 Failed (7 prompts)

Three distinct failure modes:

**Budget exhaustion from over-reading (prompts 4, 6, 24):**

GLM-5.1 has a habit of reading aggressively — starting with memory files, doing broad filesystem discovery, reading tangential files — before getting to the actual task. This burns through the tool budget.

- **Prompt 4 (summarize tool, 15-call limit):** Read 15 files including `CLAUDE.md` and `system_prompt.py` alongside the relevant tool files. Found everything it needed. Never synthesized an answer.
- **Prompt 6 (code trace, 20-call limit):** Started with `context/memory/README.md` and `projects.md` — irrelevant to a code trace question. Tried `find / -name "*.py"`. Eventually read all the right files (ws.py, router.py, agent.py, dispatcher.py, llm.py, run.py) but hit the budget at 20/20 with no response.
- **Prompt 24 (test count, 8-call limit):** The usual: 8 glob patterns, no response.

The pattern: GLM-5.1 reads the right files but also reads too many wrong files first. On prompts with tight budgets, this is fatal. GLM-5 Turbo didn't have this problem — it was more focused in its tool usage.

**Path hallucination (prompts 16, 21):**

Like [Kimi K2.5](article-draft-kimik25-sonnet46-20260408), GLM-5.1 sometimes guesses file paths from training data instead of using the working directory.

- **Prompt 16 (missing file, 3-call limit):** Tried `/Users/curunir/src/nonexistent/fake_module.py` — a fabricated absolute path. Then `pwd`, then glob. Budget exhausted.
- **Prompt 21 (design decisions, 10-call limit):** Tried `/home/user/src/agent/agent.py`, `/home/user/src/tools/dispatcher.py`, `/home/user/src/skills.py` — all wrong. Then globbed to find the right paths, read all three files — but hit 10/10. The files were successfully read, the analysis never produced.

This is the Kimi failure mode, but less severe — GLM-5.1 recovers and finds the right paths, it just wastes budget doing so. GLM-5 Turbo never exhibited this.

**API error (prompt 13):**

Loaded web-search, hit Brave, then returned "Sorry, I encountered an error processing your message." A crash, not a reasoning failure.

### Where Both Failed

**Test count (24):** GLM-5.1 exhausted its budget. Sonnet answered 0 (wrong). The real answer is 202. Six models in, zero correct answers.

## Comparison

| | GLM-5.1 | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 17/24 | 23/24 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Pass | Pass |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Mixed (prompt 16) | Pass |
| **Code tracing** | Fail (budget) | Strong |
| **Multi-step planning** | Fail (budget) | Strong |
| **Instruction precision** | Strong | Strong |
| **Self-directed exploration** | Weak (over-reads) | Strong |
| **Efficiency** | Weak (too many calls) | Mixed |
| **Knows when to stop** | No | No (prompt 19) |

## Comparison with GLM-5 Turbo

This is the more revealing comparison. Same model family, different results:

| | GLM-5 Turbo | GLM-5.1 |
|---|:-:|:-:|
| **Prompts completed** | 23/24 | 17/24 |
| **Code tracing** | Strong | Fail (budget) |
| **Multi-step planning** | Strong | Fail (budget) |
| **Path hallucination** | None | 2 prompts |
| **Over-reading** | Minimal | Frequent |
| **Efficiency** | Strong | Weak |

GLM-5 Turbo was focused: it picked the right files, read them, and answered. GLM-5.1 starts with memory files on nearly every prompt, does broad filesystem discovery, and reads tangentially related files. On easy prompts with generous budgets, this doesn't matter. On hard prompts with tight budgets, it's the difference between 23/24 and 17/24.

## What I Take Away

**Newer doesn't mean better for agentic tool use.** GLM-5.1 is presumably the successor to GLM-5 Turbo within the same model family. On agentic tasks, it's meaningfully worse — 17/24 vs 23/24. The regression isn't in reasoning quality (when GLM-5.1 reads the right files, its analysis is strong) but in tool-use discipline: which files to read, when to stop reading, and how to budget limited tool calls.

**Over-reading is a distinct failure mode from over-investigation.** Sonnet's prompt 19 failure is about searching for a source it can cite. GLM-5.1's failures are about reading everything it can find before starting to think. Different behavior, same outcome: budget exhausted, no response. GLM-5 Turbo avoided both patterns.

**Path hallucination isn't limited to one model family.** [Kimi K2.5](article-draft-kimik25-sonnet46-20260408) had it on 8 prompts. GLM-5.1 has it on 2. The severity varies, but the pattern — guessing paths from training data instead of using `pwd`/`ls` — appears across model families. GLM-5 Turbo didn't exhibit it at all.

**The quality floor is high when GLM-5.1 succeeds.** The attach skill analysis was the sharpest in the series. The delegate comparison had a memorable insight. The memory retrieval was thorough. This isn't a weak model — it's a capable model with poor tool-use budgeting. For workflows with generous tool budgets or explicit file paths, GLM-5.1 would perform well. For the constrained, self-directed tasks in this eval, it doesn't.

**Model selection for agentic use requires its own eval.** Benchmark scores, parameter counts, and model generation numbers don't predict agentic performance. GLM-5 Turbo is better at driving an agent than GLM-5.1, despite being the older model. The only way to know is to test with actual agentic tasks.

---

*Tested on Curunir. GLM-5.1 at harness commit `e63cf72`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 8, 2026.*
