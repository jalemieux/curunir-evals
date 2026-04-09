---
layout: default
title: "Agentic Eval Series"
---

# Agentic Eval Series

Can models other than the big cloud APIs actually drive an autonomous agent? Tool calling, multi-step planning, memory retrieval, skill orchestration, error recovery — the basics of an agentic loop. We're running a growing set of models through the same eval harness to find out.

**A note on methodology:** This is a qualitative smoke test, not a rigorous scientific evaluation. Each model is run once through the same 24 prompts — there are no repeated trials, no statistical significance tests, and no controlled ablations. The results are directional: useful for spotting capability gaps and failure modes, not for making definitive claims about model rankings.

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
5. [MiniMax M2.7: Another Cloud Model Goes Toe-to-Toe with Sonnet](article-draft-minimaxm27-sonnet46-20260408) — MiniMax M2.7 vs Sonnet 4.6
6. [GLM-5.1: A Step Backward from GLM-5 Turbo](article-draft-glm51-sonnet46-20260408) — Zhipu AI GLM-5.1 vs Sonnet 4.6

More comparisons coming as we run additional models through the harness.

## Companion Pieces

Follow-ups to the main articles — performance characterization, reruns, and other supporting pieces that don't fit the model-vs-Sonnet format.

- [How Fast Is Gemma 4 26B on a MacBook Pro?](article-draft-26b-perf-20260409) — performance characterization of the 26B local run
- [Gemma 4 26B, Rerun: What Changes on a Newer llama.cpp?](article-draft-26b-rerun-20260409) — same model, new llama.cpp build, reproducibility check

## Source

The [eval prompts](https://github.com/jalemieux/curunir-evals/blob/main/simple_evals.md) and [harness script](https://github.com/jalemieux/curunir-evals/blob/main/run_evals.py) are public.
