#!/usr/bin/env python3
"""
Внешний монитор (запускается в GitHub Actions, НЕ на твоём сервере).
Проверяет домены + VLESS-ноду снаружи. Шлёт алерт в Telegram
только при смене статуса (up -> down или down -> up),
чтобы не спамить каждые 5 минут.
"""
import json
import os
import socket
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
TIMEOUT = 10

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Что проверяем. type=http — просто ждём любой ответ сервера (даже 4xx/5xx
# считается "up", down — только если соединение вообще не установилось).
# type=tcp — просто открываем сокет на host:port.
TARGETS = [
    {"name": "dementiq.ru",       "type": "http", "url": "https://dementiq.ru"},
    {"name": "panel.dementiq.ru", "type": "http", "url": "https://panel.dementiq.ru"},
    {"name": "vault.dementiq.ru", "type": "http", "url": "https://vault.dementiq.ru"},
    {"name": "kuma.dementiq.ru",  "type": "http", "url": "https://kuma.dementiq.ru"},
    {"name": "sub.dementiq.ru",   "type": "http", "url": "https://sub.dementiq.ru"},
    {"name": "wecl1.ru",          "type": "http", "url": "https://wecl1.ru"},
    {"name": "connect.dementiq.ru (VLESS)", "type": "tcp",
     "host": "connect.dementiq.ru", "port": 443},
]


def check_http(url: str) -> bool:
    req = urllib.request.Request(url, method="GET",
                                  headers={"User-Agent": "external-uptime-monitor"})
    try:
        urllib.request.urlopen(req, timeout=TIMEOUT)
        return True
    except urllib.error.HTTPError:
        # сервер ответил (пусть и ошибкой) — значит он жив
        return True
    except Exception:
        return False


def check_tcp(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False


def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_notification": False,
    }).encode()
    req = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=TIMEOUT)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}", file=sys.stderr)


def main():
    prev_state = load_state()
    new_state = dict(prev_state)
    changes = []

    for target in TARGETS:
        name = target["name"]
        if target["type"] == "http":
            is_up = check_http(target["url"])
        else:
            is_up = check_tcp(target["host"], target["port"])

        status = "up" if is_up else "down"
        prev_status = prev_state.get(name)

        new_state[name] = status

        if prev_status is None:
            # первый прогон для этого сервиса — просто фиксируем базу, без алерта
            continue

        if status != prev_status:
            changes.append((name, prev_status, status))

    if changes:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [f"🌐 <b>Внешняя проверка (GitHub)</b> — {now}", ""]
        for name, prev_status, status in changes:
            if status == "down":
                lines.append(f"🔴 <b>{name}</b>: недоступен снаружи!")
            else:
                lines.append(f"🟢 <b>{name}</b>: снова доступен")
        send_telegram("\n".join(lines))
        print("Изменения:", changes)
    else:
        print("Без изменений статусов.")

    save_state(new_state)


if __name__ == "__main__":
    main()
