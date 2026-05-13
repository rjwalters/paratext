#!/usr/bin/env python3
"""Thin wrapper: python scripts/generate_variants.py [--input ...] [--output ...]."""

import typer

from paratext.cli import generate_variants_cmd

if __name__ == "__main__":
    typer.run(generate_variants_cmd)
