"""Inspect one supplied clean case with real NeMo logs, without rewriting reports."""
import argparse
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CLEAN_SET_PATH
from src.experiment_support import read_json
from src.phase_c_guard import setup_nemo_rails


async def inspect(case_id):
    row = next(r for r in read_json(CLEAN_SET_PATH) if r["id"] == case_id)
    rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": row["input"]}],
        options={"rails": ["input"], "log": {"activated_rails": True, "llm_calls": True}},
    )
    return result.model_dump_json(indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--input-id", type=int, required=True)
    parser.add_argument("--output", type=Path, help="Save the genuine NeMo trace for this fixture.")
    args = parser.parse_args()
    if not args.live:
        parser.error("Pass --live to inspect one clean control using the provider API.")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    trace = asyncio.run(inspect(args.input_id))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(trace + "\n", encoding="utf-8")
        print(f"Saved NeMo trace: {args.output}")
    else:
        print(trace)
