#!/usr/bin/env bash
set -e
uv run ruff format --check . || {
    echo "Unformatted files detected - run: uv run ruff format ."
    exit 1
}
