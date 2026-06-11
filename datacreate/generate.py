#!/usr/bin/env python3
"""
Generate poems via a local Gemma/ollama instance and store them in SQLite.

Usage:
    python generate.py [--start HH:MM] [--end HH:MM] [--weather WEATHER]
                       [--tags TAG [TAG ...]] [--model MODEL] [--dry-run]

Defaults to the example call: 17:00-17:05, rainy weather, tag "rain".
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from database import DB_PATH, init_db, insert_poem
from llm import MODEL, build_prompt, call_llm
from parser import ParseError, parse_llm_response


BATCH_SIZE = 20


def time_range(start: str, end: str) -> list[str]:
    """Return list of "HH:MM" strings from start up to and including end."""
    fmt = "%H:%M"
    t = datetime.strptime(start, fmt)
    finish = datetime.strptime(end, fmt)
    times = []
    while t <= finish:
        times.append(t.strftime(fmt))
        t += timedelta(minutes=1)
    return times


def batched(times: list[str], size: int) -> list[list[str]]:
    return [times[i:i + size] for i in range(0, len(times), size)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate clock poems via ollama and store them.")
    parser.add_argument("--start", default="17:00", metavar="HH:MM",
                        help="First time to generate (default: 17:00)")
    parser.add_argument("--end", default="17:05", metavar="HH:MM",
                        help="Last time to generate (default: 17:05)")
    parser.add_argument("--weather", default="rainy",
                        help="Weather description to include in the prompt (default: rainy)")
    parser.add_argument("--tags", nargs="*", default=None,
                        help="Tags to attach to all generated poems. "
                             "Defaults to a single tag derived from --weather.")
    parser.add_argument("--model", default=MODEL,
                        help=f"Ollama model name (default: {MODEL})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the prompt and parsed output without writing to the database")
    args = parser.parse_args()

    tags: list[str] = args.tags if args.tags is not None else [args.weather.split()[0].lower()]

    all_times = time_range(args.start, args.end)
    if not all_times:
        print(f"Error: --end {args.end!r} is before --start {args.start!r}", file=sys.stderr)
        sys.exit(1)

    batches = batched(all_times, BATCH_SIZE)
    total = len(all_times)
    print(f"Generating {total} poems ({args.start}–{args.end}) in {len(batches)} batch(es) "
          f"of up to {BATCH_SIZE}, weather: {args.weather}")
    print(f"Tags: {tags}  Model: {args.model}")

    if not args.dry_run:
        init_db()

    all_poems = []
    for i, batch in enumerate(batches, 1):
        batch_start, batch_end = batch[0], batch[-1]
        count = len(batch)
        prompt = build_prompt(
            start_time=batch_start,
            end_time=batch_end,
            weather=args.weather,
            count=count,
        )

        print(f"\n[Batch {i}/{len(batches)}] {batch_start}–{batch_end} ({count} poems)")

        if args.dry_run:
            print("--- Prompt ---")
            print(prompt)

        raw = call_llm(prompt, model=args.model)

        if args.dry_run:
            print("--- Raw LLM response ---")
            print(raw)

        try:
            poems = parse_llm_response(raw, expected_times=batch)
        except ParseError as e:
            print(f"\nParse error in batch {i}: {e}", file=sys.stderr)
            print("--- Raw LLM response ---", file=sys.stderr)
            print(raw, file=sys.stderr)
            sys.exit(1)

        if args.dry_run:
            print(f"--- Parsed {len(poems)} poems ---")
            for p in poems:
                print(f"  {p.time_str}: {p.poem}")
        else:
            for p in poems:
                poem_id = insert_poem(p.time_str, p.poem, tags)
                print(f"  Stored [{poem_id}] {p.time_str}: {p.poem[:60]}")

        all_poems.extend(poems)

    if not args.dry_run:
        print(f"\nDone. {len(all_poems)} poems stored in {DB_PATH}")


if __name__ == "__main__":
    main()
