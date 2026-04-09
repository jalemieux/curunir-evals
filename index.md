---
layout: default
title: Curunir Evals
---

# Curunir Evals

Can different models actually drive an autonomous agent? We're running a growing set of models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. The only variable is the model. Claude Sonnet 4.6 is the baseline.

## Articles

1. [Can a Local 26B Model Drive an Agentic Framework?](reviews/article-draft-26b-sonnet46-20260407) — Gemma 4 26B vs Sonnet 4.6
2. [How Far Down Can You Go? E4B vs Sonnet 4.6](reviews/article-draft-e4b-sonnet46-20260407) — Gemma 4 E4B vs Sonnet 4.6
3. [GLM-5 Turbo vs Sonnet 4.6: A Statistical Tie](reviews/article-draft-glm5turbo-sonnet46-20260408) — Zhipu AI GLM-5 Turbo vs Sonnet 4.6
4. [Kimi K2.5: When Path Hallucination Kills Agentic Tool Use](reviews/article-draft-kimik25-sonnet46-20260408) — Moonshot AI Kimi K2.5 vs Sonnet 4.6

[Full series index](reviews/)

## Source

- [Eval prompts](https://github.com/jalemieux/curunir-evals/blob/main/simple_evals.md)
- [Harness script](https://github.com/jalemieux/curunir-evals/blob/main/run_evals.py)
