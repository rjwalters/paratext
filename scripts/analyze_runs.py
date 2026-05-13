#!/usr/bin/env python3
"""Thin wrapper: python scripts/analyze_runs.py [--explicit ...] [--implicit ...]."""

import typer

from paratext.cli import analyze_cmd

if __name__ == "__main__":
    typer.run(analyze_cmd)
