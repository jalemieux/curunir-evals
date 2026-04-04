# Curunir Evals

Simple agentic eval suite for comparing LLM models driving an agentic loop with tool use, memory, skills, and multi-step planning.

## Contents

- [`simple_evals.md`](simple_evals.md) — The 21 eval prompts across 7 categories
- [`run_evals.py`](run_evals.py) — Eval harness (connects over WebSocket, records tool calls + responses)
- [`article-draft.md`](article-draft.md) — Write-up: Can a Local 26B Model Run an Agentic Framework?

## Results (April 3, 2026)

| Model | Result (JSON) | Result (Markdown) |
|-------|---------------|-------------------|
| Gemma 4 26B-A4B-IT (Q8_0, local) | [JSON](eval-20260403-174008-openai_gemma-4-26B-A4B-it.json) | [Markdown](eval-20260403-174008-openai_gemma-4-26B-A4B-it.md) |
| Claude Sonnet 4 (cloud) | [JSON](eval-20260403-175244-anthropic_claude-sonnet-4-20250514.json) | [Markdown](eval-20260403-175244-anthropic_claude-sonnet-4-20250514.md) |
| GLM-5 Turbo (OpenRouter) | [JSON](eval-20260403-174420-openrouter_z-ai_glm-5-turbo.json) | [Markdown](eval-20260403-174420-openrouter_z-ai_glm-5-turbo.md) |

PII has been redacted from all result files.
