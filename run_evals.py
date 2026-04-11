"""Simple eval harness for Curunir. Sends prompts from simple_evals.md one at a
time, shows real-time output, and saves results to a timestamped file.

Usage:
    python run_evals.py [--host localhost] [--port 8765]
    python run_evals.py --resume results/eval-20260406-141719-openai_gemma-4-E4B-it.json --from 14
"""

import argparse
import asyncio
import json
import platform
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import websockets

DEFAULT_EVALS_FILE = Path(__file__).parent / "simple_evals.md"
RESULTS_DIR = Path(__file__).parent / "results"


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
        for match in re.finditer(
            r"```(?:max_loops=(\d+))?\n(.*?)\n```", body, re.DOTALL
        ):
            max_loops = int(match.group(1)) if match.group(1) else None
            prompts.append({
                "category": category,
                "prompt": match.group(2).strip(),
                "max_loops": max_loops,
            })
    return prompts


def collect_system_info() -> dict:
    """Collect hardware info from the machine running this script."""
    info: dict = {"os": f"{platform.system()} {platform.release()}"}
    system = platform.system()

    def _run(cmd: list[str]) -> str:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()

    try:
        if system == "Linux":
            for line in _run(["lscpu"]).splitlines():
                k, _, v = line.partition(":")
                v = v.strip()
                match k.strip():
                    case "Model name": info["cpu"] = v
                    case "Core(s) per socket": info["cores"] = v
                    case "Thread(s) per core": info["threads_per_core"] = v
                    case "Socket(s)": info["sockets"] = v
            for line in _run(["free", "-h"]).splitlines():
                if line.startswith("Mem:"):
                    info["ram"] = line.split()[1]
            try:
                info["gpu"] = _run([
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader",
                ])
            except FileNotFoundError:
                info["gpu"] = "none detected"

        elif system == "Darwin":
            info["cpu"] = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
            info["cores"] = _run(["sysctl", "-n", "hw.perflevel0.physicalcpu"])
            mem_bytes = int(_run(["sysctl", "-n", "hw.memsize"]))
            info["ram"] = f"{mem_bytes // (1024**3)}GB"
            try:
                for line in _run(["system_profiler", "SPDisplaysDataType"]).splitlines():
                    if "Chipset Model:" in line:
                        info["gpu"] = line.split(":", 1)[1].strip()
                        break
            except Exception:
                pass
    except Exception:
        pass
    return info


def query_inference_server(url: str) -> dict:
    """Query a llama.cpp-compatible server for build and model metadata."""
    info: dict = {}
    props_url = f"{url.rstrip('/')}/props"
    try:
        req = urllib.request.Request(props_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())

        if "build_info" in data:
            bi = data["build_info"]
            info["build_number"] = bi.get("build_number")
            info["build_commit"] = bi.get("commit")
        dgs = data.get("default_generation_settings") or {}
        if dgs.get("model"):
            info["model_path"] = dgs["model"]
        if dgs.get("n_ctx"):
            info["n_ctx"] = dgs["n_ctx"]

        # Parse quantization from model filename
        model_path = info.get("model_path", "")
        if model_path:
            fname = model_path.rsplit("/", 1)[-1]
            for q in [
                "Q8_0", "Q6_K", "Q5_K_M", "Q5_K_S", "Q4_K_M", "Q4_K_S",
                "Q4_0", "Q3_K_M", "Q3_K_S", "Q2_K", "IQ4_XS", "IQ3_M",
                "BF16", "F16", "F32",
            ]:
                if q in fname:
                    info["quantization"] = q
                    break
    except Exception as e:
        info["error"] = str(e)
    return info


def build_metadata(
    inference_url: str | None = None,
    inference_cmd: str | None = None,
    hardware: str | None = None,
) -> dict:
    """Collect all available metadata about the inference environment.

    When *inference_url* is set, inference is assumed to be remote and local
    system info is suppressed (it would describe the wrong machine).  Use
    *hardware* to record the remote machine's specs instead.
    """
    meta: dict = {}
    if inference_url:
        meta["server"] = query_inference_server(inference_url)
        if hardware:
            meta["hardware"] = hardware
    else:
        meta["system"] = collect_system_info()
    if inference_cmd:
        meta["inference_cmd"] = inference_cmd
    return meta


def get_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always"], text=True
        ).strip()
    except Exception:
        return "unknown"


async def send_prompt(ws, prompt: str, max_loops: int | None = None) -> dict:
    """Send a prompt, stream output to terminal, return collected result."""
    # Clear session first
    await ws.send(json.dumps({"content": "", "command": "reset"}))
    # Drain any clear response
    async for raw in ws:
        data = json.loads(raw)
        if data.get("final"):
            break

    await ws.send(json.dumps({"content": prompt, "command": None}))

    tool_calls = []
    content_parts = []
    stats = None
    tool_call_count = 0
    hit_limit = False

    async for raw in ws:
        data = json.loads(raw)

        for tc in data.get("tool_calls") or []:
            tool_calls.append(tc)
            tool_call_count += 1
            print(f"  ├─ {tc}")

        text = data.get("content") or ""
        if text:
            content_parts.append(text)
            print(text)

        if data.get("stats"):
            stats = data["stats"]

        if data.get("final"):
            break

        # Abort if we've exceeded the tool-call budget for this prompt
        if max_loops is not None and tool_call_count >= max_loops:
            hit_limit = True
            print(f"  ⚠ eval limit reached ({tool_call_count}/{max_loops} tool calls) — resetting")
            await ws.send(json.dumps({"content": "", "command": "reset"}))
            # Drain the reset response
            async for reset_raw in ws:
                reset_data = json.loads(reset_raw)
                if reset_data.get("final"):
                    break
            break

    # Print stats summary
    if stats:
        parts = []
        if stats.get("prompt_tokens"):
            parts.append(f"prompt: {stats['prompt_tokens']} tok")
        if stats.get("completion_tokens"):
            parts.append(f"completion: {stats['completion_tokens']} tok")
        if stats.get("completion_tps"):
            parts.append(f"{stats['completion_tps']} tok/s")
        if stats.get("wall_elapsed_sec"):
            parts.append(f"{stats['wall_elapsed_sec']}s")
        if parts:
            print(f"  [{' | '.join(parts)}]")

    response = "\n".join(content_parts)
    if hit_limit and not response.strip():
        response = (
            f"*Model did not produce a response within the tool-call budget "
            f"({tool_call_count}/{max_loops} calls used).*"
        )

    return {
        "tool_calls": tool_calls,
        "response": response,
        "stats": stats,
        "hit_limit": hit_limit,
    }


def save_checkpoint(results: dict, checkpoint_path: Path) -> None:
    """Save current results to a JSON checkpoint file."""
    checkpoint_path.write_text(json.dumps(results, indent=2, default=str))


def load_checkpoint(checkpoint_path: Path) -> dict:
    """Load results from a JSON checkpoint file."""
    return json.loads(checkpoint_path.read_text())


async def run(
    host: str,
    port: int,
    evals_file: Path,
    resume_path: Path | None = None,
    start_from: int | None = None,
    inference_url: str | None = None,
    inference_cmd: str | None = None,
    hardware: str | None = None,
) -> None:
    uri = f"ws://{host}:{port}"
    prompts = parse_prompts(evals_file)
    print(f"Loaded {len(prompts)} eval prompts from {evals_file.name}")

    # Resume: load prior results and determine start index
    prior_results = []
    if resume_path:
        checkpoint = load_checkpoint(resume_path)
        prior_results = checkpoint.get("results", [])
        if start_from is None:
            start_from = len(prior_results) + 1
        # Keep only results before the start point
        prior_results = prior_results[: start_from - 1]
        print(f"Resuming from question {start_from} (keeping {len(prior_results)} prior results)")

    start_idx = (start_from or 1) - 1  # 0-based

    if start_idx >= len(prompts):
        print(f"Nothing to run: start_from={start_from} but only {len(prompts)} prompts")
        return

    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        # Read welcome message to get model
        raw = await ws.recv()
        welcome = json.loads(raw)
        model = welcome.get("model", "unknown")
        print(f"Model: {model}\n")

        version = get_version()
        metadata = build_metadata(inference_url, inference_cmd, hardware)
        print(f"System: {json.dumps(metadata.get('system', {}), indent=2)}")
        if metadata.get("server"):
            print(f"Server: {json.dumps(metadata['server'], indent=2)}")

        results = {
            "version": version,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
            "results": list(prior_results),
        }

        # Set up checkpoint path early so we can save incrementally
        RESULTS_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_model = re.sub(r"[^\w\-]", "_", model)
        checkpoint_path = RESULTS_DIR / f"eval-{ts}-{safe_model}.json"

        for i, item in enumerate(prompts, 1):
            if i < (start_from or 1):
                continue

            max_loops = item.get("max_loops")
            loops_label = f" (max_loops={max_loops})" if max_loops else ""
            header = f"[{i}/{len(prompts)}] {item['category']}{loops_label}"
            print(f"\n{'='*60}")
            print(header)
            print(f"{'='*60}")
            print(f"> {item['prompt']}\n")

            result = await send_prompt(ws, item["prompt"], max_loops=max_loops)
            results["results"].append({
                "category": item["category"],
                "prompt": item["prompt"],
                "max_loops": max_loops,
                **result,
            })

            # Save checkpoint after each prompt
            save_checkpoint(results, checkpoint_path)

    # Build markdown output
    md_lines = [
        f"# Eval Results: {model}",
        "",
        f"- **Version:** {version}",
        f"- **Model:** {model}",
        f"- **Timestamp:** {results['timestamp']}",
        "",
    ]

    # Inference setup table from metadata
    if metadata.get("system") or metadata.get("server") or metadata.get("hardware"):
        md_lines.append("## Inference Setup")
        md_lines.append("")
        md_lines.append("| Setting | Value |")
        md_lines.append("|---------|-------|")
        # Local system info (only present when inference is local)
        sys_info = metadata.get("system", {})
        if sys_info.get("cpu"):
            md_lines.append(f"| CPU | {sys_info['cpu']} |")
        if sys_info.get("cores"):
            threads = ""
            if sys_info.get("threads_per_core"):
                total = int(sys_info["cores"]) * int(sys_info.get("threads_per_core", 1))
                threads = f" ({total} threads)"
            md_lines.append(f"| Cores | {sys_info['cores']}{threads} |")
        if sys_info.get("ram"):
            md_lines.append(f"| RAM | {sys_info['ram']} |")
        if sys_info.get("gpu"):
            md_lines.append(f"| GPU | {sys_info['gpu']} |")
        if sys_info.get("os"):
            md_lines.append(f"| OS | {sys_info['os']} |")
        # Manual hardware description (remote inference)
        if metadata.get("hardware"):
            md_lines.append(f"| Hardware | {metadata['hardware']} |")
        srv = metadata.get("server", {})
        if srv.get("build_number"):
            commit = f" (`{srv['build_commit']}`)" if srv.get("build_commit") else ""
            md_lines.append(f"| Inference engine | llama.cpp b{srv['build_number']}{commit} |")
        if srv.get("n_ctx"):
            md_lines.append(f"| Context window | {srv['n_ctx']} |")
        if srv.get("quantization"):
            md_lines.append(f"| Quantization | {srv['quantization']} |")
        if srv.get("model_path"):
            md_lines.append(f"| Model path | `{srv['model_path']}` |")
        if metadata.get("inference_cmd"):
            md_lines.append(f"| Launch command | `{metadata['inference_cmd']}` |")
        md_lines.append("")

    md_lines.extend(["---", ""])
    current_category = ""
    prompt_num = 0
    for entry in results["results"]:
        if entry["category"] != current_category:
            current_category = entry["category"]
            md_lines.append(f"## {current_category}")
            md_lines.append("")
        prompt_num += 1
        md_lines.append(f"### {prompt_num}. {entry['prompt']}")
        md_lines.append("")

        if entry.get("max_loops"):
            status = " — **LIMIT HIT**" if entry.get("hit_limit") else ""
            md_lines.append(f"**Max tool calls:** {entry['max_loops']}{status}")
            md_lines.append("")

        # Stats table
        stats = entry.get("stats")
        if stats:
            md_lines.append("**Stats:**")
            md_lines.append("")
            md_lines.append("| Metric | Value |")
            md_lines.append("|--------|-------|")
            if stats.get("prompt_tokens"):
                md_lines.append(f"| Prompt tokens | {stats['prompt_tokens']} |")
            if stats.get("completion_tokens"):
                md_lines.append(f"| Completion tokens | {stats['completion_tokens']} |")
            if stats.get("total_tokens"):
                md_lines.append(f"| Total tokens | {stats['total_tokens']} |")
            if stats.get("completion_tps"):
                md_lines.append(f"| Completion tok/s | {stats['completion_tps']} |")
            if stats.get("iterations"):
                md_lines.append(f"| Iterations | {stats['iterations']} |")
            if stats.get("llm_calls"):
                md_lines.append(f"| LLM calls | {stats['llm_calls']} |")
            if stats.get("llm_elapsed_sec"):
                md_lines.append(f"| LLM time (s) | {stats['llm_elapsed_sec']} |")
            if stats.get("wall_elapsed_sec"):
                md_lines.append(f"| Wall time (s) | {stats['wall_elapsed_sec']} |")
            # llama.cpp server stats
            server = stats.get("server")
            if server:
                for slot in server.get("slots", []):
                    sid = slot.get("id", "?")
                    if slot.get("n_ctx"):
                        md_lines.append(f"| Slot {sid} n_ctx | {slot['n_ctx']} |")
                    if slot.get("n_past") is not None:
                        md_lines.append(f"| Slot {sid} n_past | {slot['n_past']} |")
                    if slot.get("prompt_tps"):
                        md_lines.append(f"| Slot {sid} prompt tok/s | {slot['prompt_tps']} |")
                    if slot.get("generation_tps"):
                        md_lines.append(f"| Slot {sid} gen tok/s | {slot['generation_tps']} |")
            md_lines.append("")

        if entry["tool_calls"]:
            md_lines.append("**Tool Calls:**")
            for tc in entry["tool_calls"]:
                md_lines.append(f"- `{tc}`")
            md_lines.append("")
        else:
            md_lines.append("**Tool Calls:** *(none)*")
            md_lines.append("")
        md_lines.append("**Response:**")
        md_lines.append("")
        md_lines.append(entry["response"])
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    out_path = RESULTS_DIR / f"eval-{ts}-{safe_model}.md"
    out_path.write_text("\n".join(md_lines))
    print(f"\nResults saved to {out_path}")
    print(f"Checkpoint: {checkpoint_path}  (use with --resume to continue)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Curunir evals")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_EVALS_FILE,
        help="Eval markdown file (default: simple_evals.md)",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Path to a checkpoint .json file from a previous run to resume from",
    )
    parser.add_argument(
        "--from",
        type=int,
        dest="start_from",
        default=None,
        help="Question number to resume from (1-based). Requires --resume.",
    )
    parser.add_argument(
        "--inference-url",
        default=None,
        help="URL of the llama.cpp server (e.g. http://localhost:8080) to query /props for build info",
    )
    parser.add_argument(
        "--inference-cmd",
        default=None,
        help="Record the server launch command (e.g. './llama-server -c 8192 -ngl 0 -m ...')",
    )
    parser.add_argument(
        "--hardware",
        default=None,
        help="Hardware description for remote inference (e.g. 'AMD Ryzen 7 8745HS, 32GB RAM, no discrete GPU')",
    )
    args = parser.parse_args()
    if args.start_from and not args.resume:
        parser.error("--from requires --resume to specify which run to continue")
    asyncio.run(run(
        args.host, args.port, args.file, args.resume, args.start_from,
        args.inference_url, args.inference_cmd, args.hardware,
    ))


if __name__ == "__main__":
    main()
