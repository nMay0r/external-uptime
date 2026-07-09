# External Uptime Monitor

Внешний монитор для dementiq.ru — крутится на GitHub Actions,
не зависит от твоего сервера. Если сервер целиком упадёт —
этот воркфлоу всё равно проверит домены и VLESS-ноду снаружи
и пришлёт алерт в Telegram.

## Настройка (один раз)

### 1. Создать приватный репозиторий
На github.com → New repository → например `external-uptime` → **Private** → Create.

### 2. Залить эти файлы
На своей машине (не на сервере с ботом, а откуда угодно, где есть git):

```bash
cd external-uptime
git init
git add .
git commit -m "init external uptime monitor"
git branch -M main
git remote add origin https://github.com/<ТВОЙ_ЮЗЕРНЕЙМ>/external-uptime.git
git push -u origin main
```

### 3. Добавить секреты
В репозитории: Settings → Secrets and variables → Actions → New repository secret:

- `TELEGRAM_BOT_TOKEN` — токен бота (получи новый через @BotFather, старый лучше отозвать — он был в чате открытым текстом)
- `TELEGRAM_CHAT_ID` — `5201016535`

### 4. Проверить
Actions → External Uptime Monitor → Run workflow (запустить вручную первый раз).
Дальше сам будет бегать каждые 5 минут по расписанию.

## Что проверяется
- dementiq.ru, panel.dementiq.ru, vault.dementiq.ru, kuma.dementiq.ru,
  sub.dementiq.ru, wecl1.ru — HTTPS-доступность
- connect.dementiq.ru:443 — TCP-коннект (VLESS-нода)

Список можно менять в `monitor.py`, блок `TARGETS`.

## Важно про расписание
GitHub cron не гарантирует точные 5 минут — при высокой нагрузке
на платформу может быть задержка в несколько минут. Для полностью
критичного мониторинга это стоит иметь в виду, но для алертов
"сервер лежит" — более чем достаточно.
