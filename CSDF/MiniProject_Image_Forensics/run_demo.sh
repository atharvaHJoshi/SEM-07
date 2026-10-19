#!/usr/bin/env bash
# ----------------------------------------------------------------------
#  Run the Digital Image Forensics mini-project.
#  Uses the first Python interpreter that has Pillow installed.
#
#  Usage:
#      ./run_demo.sh                  # generate samples + run self-test
#      ./run_demo.sh path/to/image    # analyse your own image instead
#
#  If Pillow is missing, a local .venv is created automatically and
#  Pillow is installed into it (needs internet for the first run).
# ----------------------------------------------------------------------
cd "$(dirname "$0")" || exit 1

run_with() {
    local python_bin="$1"
    shift
    if [ $# -gt 0 ]; then
        exec "$python_bin" image_forensics.py "$@"
    else
        exec "$python_bin" image_forensics.py --demo
    fi
}

for candidate in python3 .venv/bin/python ../.venv/bin/python; do
    if command -v "$candidate" >/dev/null 2>&1 && \
       "$candidate" -c "import PIL" >/dev/null 2>&1; then
        echo "Using interpreter: $candidate"
        run_with "$candidate" "$@"
    fi
done

echo "Pillow was not found. Setting up a local virtual environment (.venv)..."
if python3 -m venv .venv >/dev/null 2>&1 && \
   .venv/bin/python -m pip install --quiet --upgrade pip >/dev/null 2>&1 && \
   .venv/bin/python -m pip install --quiet -r requirements.txt; then
    echo "Pillow installed in .venv"
    run_with ".venv/bin/python" "$@"
fi

echo
echo "Automatic setup failed. Install Pillow manually with one of:"
echo "    python3 -m pip install -r requirements.txt"
echo "    python3 -m pip install Pillow"
exit 1
