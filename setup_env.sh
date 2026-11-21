#!/bin/bash
# Secrets file banayein aur edit karein
cd "$(dirname "$0")" || exit 1
mkdir -p secrets
if [ ! -f secrets/.env ]; then
  cp .env.example secrets/.env
  echo "secrets/.env ban gaya. Ab values bharein:"
fi
nano secrets/.env
