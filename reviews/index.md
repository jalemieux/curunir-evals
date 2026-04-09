---
layout: default
title: "Agentic Eval Series"
---

# Agentic Eval Series

Can models other than the big cloud APIs actually drive an autonomous agent? Tool calling, multi-step planning, memory retrieval, skill orchestration, error recovery — the basics of an agentic loop. We're running a growing set of models through the same eval harness to find out.

## What We're Testing

The benchmark is [Curunir](https://github.com/jalemieux/curunir), a Python agentic framework with basic tools (grep, read, write, bash, web fetch), loadable skills, persistent memory, and multiple channels. The model receives tool schemas via JSON function calling, decides which tools to use, executes them, reads results, and loops until it has an answer.

24 prompts across 8 categories:

| Category | What it tests |
|----------|--------------|
| **Tool Use Accuracy** | Pick the right tool, use it correctly |
| **Multi-Step Planning** | Decompose complex requests into tool call sequences |
| **Memory Retrieval** | Find and synthesize info from persistent memory files |
| **Instruction Following** | Respect constraints ("don't use tools", "only answer from this file") |
| **Skill Orchestration** | Load and execute multi-step skills (web search, research) |
| **Error Recovery** | Handle missing files, failed commands, empty results |
| **Output Quality** | Explain architecture, compare tools, identify design decisions |
| **Efficiency** | Solve simple questions without unnecessary tool calls |

Same harness, same prompts, same tools, same system prompt. The only variable is the model. Claude Sonnet 4.6 is the baseline — every other model is compared against it.

## The Articles

Each article compares one model against Sonnet 4.6, prompt by prompt. Where they're equal, where one is better, where they fail.

1. [Can a Local 26B Model Drive an Agentic Framework?](article-draft-26b-sonnet46-20260407) — Gemma 4 26B vs Sonnet 4.6
2. [How Far Down Can You Go? E4B vs Sonnet 4.6](article-draft-e4b-sonnet46-20260407) — Gemma 4 E4B vs Sonnet 4.6
3. [GLM-5 Turbo vs Sonnet 4.6: A Statistical Tie](article-draft-glm5turbo-sonnet46-20260408) — Zhipu AI GLM-5 Turbo vs Sonnet 4.6
4. [Kimi K2.5: When Path Hallucination Kills Agentic Tool Use](article-draft-kimik25-sonnet46-20260408) — Moonshot AI Kimi K2.5 vs Sonnet 4.6

More comparisons coming as we run additional models through the harness.

## Source

The [eval prompts](https://github.com/jalemieux/curunir-evals/blob/main/simple_evals.md) and [harness script](https://github.com/jalemieux/curunir-evals/blob/main/run_evals.py) are public.
