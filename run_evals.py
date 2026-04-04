"""Simple eval harness for Curunir. Sends prompts from simple_evals.md one at a
time, shows real-time output, and saves results to a timestamped file.

Usage:
    python run_evals.py [--host localhost] [--port 8765]
"""

import argparse
import asyncio
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import websockets

EVALS_FILE = Path(__file__).parent / "simple_evals.md"
RESULTS_DIR = Path(__file__).parent / "eval_results"


def parse_prompts(path: Path) -> list[dict]:
    """Extract prompts and their categories from the evals markdown file."""
    text = path.read_text()
    prompts = []
    current_category = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current_category = line.removeprefix("## ").strip()
        elif line.startswith("```") and current_category:
            # skip, handled below
            pass

    # Regex: find each ## heading, then all ``` blocks under it
    sections = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
    for section in sections:
        lines = section.strip().splitlines()
        category = lines[0].strip()
        body = "\n".join(lines[1:])
        for match in re.finditer(r"```\n(.*?)\n```", body, re.DOTALL):
            prompts.append({"category": category, "prompt": match.group(1).strip()})
    return prompts


def get_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always"], text=True
        ).strip()
    except Exception:
        return "unknown"


async def send_prompt(ws, prompt: str) -> dict:
    """Send a prompt, stream output to terminal, return collected result."""
    # Clear session first
    await ws.send(json.dumps({"content": "", "command": "clear"}))
    # Drain any clear response
    async for raw in ws:
        data = json.loads(raw)
        if data.get("final"):
            break

    await ws.send(json.dumps({"content": prompt, "command": None}))

    tool_calls = []
    content_parts = []

    async for raw in ws:
        data = json.loads(raw)

        for tc in data.get("tool_calls") or []:
            tool_calls.append(tc)
            print(f"  ├─ {tc}")

        text = data.get("content") or ""
        if text:
            content_parts.append(text)
            print(text)

        if data.get("final"):
            break

    return {
        "tool_calls": tool_calls,
        "response": "\n".join(content_parts),
    }


async def run(host: str, port: int) -> None:
    uri = f"ws://{host}:{port}"
    prompts = parse_prompts(EVALS_FILE)
    print(f"Loaded {len(prompts)} eval prompts from {EVALS_FILE.name}")
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        # Read welcome message to get model
        raw = await ws.recv()
        welcome = json.loads(raw)
        model = welcome.get("model", "unknown")
        print(f"Model: {model}\n")

        version = get_version()
        results = {
            "version": version,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": [],
        }

        for i, item in enumerate(prompts, 1):
            header = f"[{i}/{len(prompts)}] {item['category']}"
            print(f"\n{'='*60}")
            print(header)
            print(f"{'='*60}")
            print(f"> {item['prompt']}\n")

            result = await send_prompt(ws, item["prompt"])
            results["results"].append({
                "category": item["category"],
                "prompt": item["prompt"],
                **result,
            })

    # Save results
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_model = re.sub(r"[^\w\-]", "_", model)
    out_path = RESULTS_DIR / f"eval-{ts}-{safe_model}.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Curunir evals")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(run(args.host, args.port))


if __name__ == "__main__":
    main()
