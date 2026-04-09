# Curunir Evals

Qualitative smoke test comparing LLM models driving an agentic loop with tool use, memory, skills, and multi-step planning. Single-run, 24 prompts, same harness — useful for spotting capability gaps, not for definitive rankings.

**Read the articles: [jalemieux.github.io/curunir-evals](https://jalemieux.github.io/curunir-evals/)**

## Articles

1. [Can a Local 26B Model Drive an Agentic Framework?](https://jalemieux.github.io/curunir-evals/reviews/article-draft-26b-sonnet46-20260407) — Gemma 4 26B vs Sonnet 4.6
2. [How Far Down Can You Go? E4B vs Sonnet 4.6](https://jalemieux.github.io/curunir-evals/reviews/article-draft-e4b-sonnet46-20260407) — Gemma 4 E4B vs Sonnet 4.6
3. [GLM-5 Turbo vs Sonnet 4.6: A Statistical Tie](https://jalemieux.github.io/curunir-evals/reviews/article-draft-glm5turbo-sonnet46-20260408) — Zhipu AI GLM-5 Turbo vs Sonnet 4.6
4. [Kimi K2.5: When Path Hallucination Kills Agentic Tool Use](https://jalemieux.github.io/curunir-evals/reviews/article-draft-kimik25-sonnet46-20260408) — Moonshot AI Kimi K2.5 vs Sonnet 4.6
5. [MiniMax M2.7: Another Cloud Model Goes Toe-to-Toe with Sonnet](https://jalemieux.github.io/curunir-evals/reviews/article-draft-minimaxm27-sonnet46-20260408) — MiniMax M2.7 vs Sonnet 4.6
6. [GLM-5.1: A Step Backward from GLM-5 Turbo](https://jalemieux.github.io/curunir-evals/reviews/article-draft-glm51-sonnet46-20260408) — Zhipu AI GLM-5.1 vs Sonnet 4.6

## Source

- [`simple_evals.md`](simple_evals.md) — The 24 eval prompts across 8 categories
- [`run_evals.py`](run_evals.py) — Eval harness (connects over WebSocket, records tool calls + responses)
- [`results/`](results/) — Raw eval results (markdown + JSON)

PII has been redacted from all result files.
