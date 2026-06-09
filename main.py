"""
Conference Discovery — entry point.

Usage:
    uv run python run_pipeline.py <url>          # Full pipeline CLI (recommended)
    uv run python main.py                        # Short alias for run_pipeline.py

Prerequisites:
    - docker compose up -d
    - conference_agent/.env configured
"""
import sys

from run_pipeline import run_pipeline


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "https://2026.emnlp.org/"
    import asyncio

    asyncio.run(run_pipeline(url))


if __name__ == "__main__":
    main()
