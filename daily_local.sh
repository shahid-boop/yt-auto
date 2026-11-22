#!/data/data/com.termux/files/usr/bin/bash
# Roz 06:30 (phone time) video banata hai — UPLOAD nahi karta.
# Aap bas out/ folder se video utha kar YouTube par upload kar dein.
#
# Abhi video banane ke liye:   ./daily_local.sh --now
# Roz auto chalane ke liye:    nohup ./daily_local.sh >/dev/null 2>&1 &
cd "$(dirname "$0")" || exit 1
mkdir -p logs out

command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock

run_once() {
  echo "===== $(date) =====" >> logs/daily.log
  python3 -m src.pipeline "$@" >> logs/daily.log 2>&1
  echo "DONE $(date)" >> logs/daily.log
}

if [ "$1" = "--now" ]; then
  shift
  run_once "$@"
  echo "Video ban gaya: $(ls -t out/*.mp4 2>/dev/null | head -1)"
  exit 0
fi

while true; do
  now=$(date +%s)
  target=$(date -d "today 06:30" +%s 2>/dev/null || echo 0)
  [ "$target" -le "$now" ] && target=$((target + 86400))
  sleep $((target - now))
  run_once
done
