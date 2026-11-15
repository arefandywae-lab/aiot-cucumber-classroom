#!/bin/bash
# REST API + dashboard (background)
python -u rest_app.py &

# Telegram bot (background). Exit code 0 = intentionally disabled (no/invalid
# token) -> do not restart; any other code = crash -> restart after 5 s.
(
  while true; do
    python -u telegram_app.py
    [ $? -eq 0 ] && break
    sleep 5
  done
) &

# MQTT collector (foreground; keeps the container alive)
python -u mqtt_app.py
