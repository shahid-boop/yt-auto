#!/bin/bash
# Termux me roz 06:30 (local time) video banayega aur upload karega.
# chalane ke liye: nohup ./termux_daily.sh >/dev/null 2>&1 &
cd "$(dirname "$0")" || exit 1
mkdir -p logs
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock

while true; do
  now=$(date +%s)
  target=$(date -d "today 06:30" +%s 2>/dev/null || echo 0)
  [ "$target" -le "$now" ] && target=$((target + 86400))
  sleep $((target - now))

  echo "===== $(date) =====" >> logs/daily.log
  python3 -m src.pipeline --upload >> logs/daily.log 2>&1
done
