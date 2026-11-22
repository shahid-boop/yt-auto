#!/data/data/com.termux/files/usr/bin/bash
# Abhi ek video bana kar upload karega (test ke liye)
cd "$(dirname "$0")" || exit 1
python3 -m src.pipeline --upload "$@"
