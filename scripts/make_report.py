#!/usr/bin/env python3
"""Alias of analyze_runs.py — generate the Markdown report from existing JSONL runs."""

import typer

from textual_intuition.cli import analyze_cmd

if __name__ == "__main__":
    typer.run(analyze_cmd)
