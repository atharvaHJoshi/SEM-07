#!/usr/bin/env bash
#
# Regenerate and execute the LP-III DAA and ML notebooks from their jupytext
# sources. Run from anywhere; paths are resolved relative to this script.
#
# Usage:
#   ./run_all.sh          # DAA and ML
#   ./run_all.sh daa      # DAA only
#   ./run_all.sh ml       # ML only
#
# Environment overrides:
#   VENV=/path/to/venv
#   KERNEL_NAME=lp3-venv
#   TIMEOUT=900

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${VENV:-$ROOT/../.venv}"
KERNEL_NAME="${KERNEL_NAME:-lp3-venv}"
TIMEOUT="${TIMEOUT:-900}"

JUPYTEXT="$VENV/bin/jupytext"
JUPYTER="$VENV/bin/jupyter"

if [[ ! -x "$JUPYTEXT" || ! -x "$JUPYTER" ]]; then
    echo "Could not find jupytext/jupyter in: $VENV" >&2
    echo "Create the environment first, or run with VENV=/path/to/venv." >&2
    exit 1
fi

if [[ $# -eq 0 ]]; then
    subjects=(daa ml)
else
    subjects=("$@")
fi

shopt -s nullglob

for subject in "${subjects[@]}"; do
    case "${subject,,}" in
        daa)
            src_dir="$ROOT/_src/DAA"
            nb_dir="$ROOT/DAA"
            run_dir="$ROOT"
            ;;
        ml)
            src_dir="$ROOT/_src/ML"
            nb_dir="$ROOT/ML"
            run_dir="$ROOT/ML"
            ;;
        *)
            echo "Unknown subject: $subject (expected 'daa' or 'ml')" >&2
            exit 2
            ;;
    esac

    sources=("$src_dir"/*.py)
    if [[ ${#sources[@]} -eq 0 ]]; then
        echo "No jupytext sources found in: $src_dir" >&2
        exit 1
    fi

    for src in "${sources[@]}"; do
        name="$(basename "$src" .py)"
        nb_path="$nb_dir/$name.ipynb"

        echo "==> $subject/$name"
        "$JUPYTEXT" --to ipynb "$src" -o "$nb_path"

        (
            cd "$run_dir"
            "$JUPYTER" nbconvert \
                --to notebook \
                --execute \
                --inplace \
                --ExecutePreprocessor.kernel_name="$KERNEL_NAME" \
                --ExecutePreprocessor.timeout="$TIMEOUT" \
                "$nb_path"
        )
    done
done

echo "All requested notebooks were executed successfully."
