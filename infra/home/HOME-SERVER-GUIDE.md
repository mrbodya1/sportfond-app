# Sportfond: домашний сервер и доступ

Сведено 15 ноября 2026 года. Только Sportfond; PACE и SKPROBEG сюда не входят.
Без паролей, API-ключей, токенов VPN и кодов удалённого доступа.

## Рабочая схема

Портал sportfondhm.ru, приложение app.sportfondhm.ru и карта map.sportfondhm.ru — отдельные GitHub Pages сайты.
Домашний сервер обслуживает api.sportfondhm.ru. Публичный IPv4 → роутер → Windows/Docker → Caddy HTTPS → Python API.
Cloudflare Tunnel для текущего публичного API не нужен. Старый контейнер probe-tunnel существует исторически и не является основным маршрутом.

## Адреса и порты

- Последний проверенный публичный IPv4:188.19.201.153 (15.11.2026). A-запись api.sportfondhm.ru указывает сюда.
- Старый94.50.96.146 больше не использовать. Адрес менялся после перезагрузки; постоянство адреса у провайдера отдельно не подтверждено.
- Роутер192.168.1.1, Rotek RX33412.
- Windows-сервер192.168.1.2, адаптер «Беспроводная сеть 2» (USB Wi-Fi). Старый192.168.1.7 не использовать.
- На роутере TCP80→192.168.1.2:80 и TCP443→192.168.1.2:443. Временный18080 после диагностики удалён.
- Правило Windows Firewall «Sportfond API TCP 80 443», входящее разрешающее, включено при проверке15.11.
- Docker/Caddy слушает80/443. Локальный Python API127.0.0.1:18767→контейнер8080.18767 наружу не открывать.
- Вручную настраивать portproxy для80/443 не нужно: используются порты Docker Desktop.
- Существующий Tailscale100.111.164.116 и старое SSH-сопоставление2222 не относятся к публикации API; их не удалять ради сайта.

## HTTPS и запуск контейнеров

Конфигурация: compose.yaml и Caddyfile рядом с этим документом. Compose project sportfond-public-api.
Контейнеры: sportfond-public-api-api-1, sportfond-public-api-https-1, sportfond-public-api-backup-1.
Caddy получает сертификат для api.sportfondhm.ru, сертификаты хранятся в постоянных Docker volumes.
API имеет restart unless-stopped и healthcheck. Docker Desktop настроен на автозапуск; надёжность полного восстановления после перезагрузки ещё требует контрольного теста: раньше контейнеры иногда не стартовали до готовности WSL bind mounts.
Не удалять volumes Caddy и каталог runtime при обновлении.

## VPN и удалённый доступ

Paper VPN в полном туннеле мешал входящему доступу. Рабочий клиент — v2rayN:
D:/Programs/v2rayN/v2rayN-windows-64/v2rayN.exe
Локальный mixed proxy127.0.0.1:10808, не открыт в LAN.
Последняя подтверждённая пользователем рабочая настройка: TUN включён, v2rayN запущен с повышенными правами, профиль маршрутизации «Sportfond — выборочный VPN»; Paper VPN выключен.
Запись «TUN off» в начале NETWORK-STATE.md описывает промежуточный этап, не итог.

Порядок правил: локальная сеть/Tailscale→direct; нужные процессы/домены→proxy; последнее общее правило TCP/UDP→direct.
Локальные исключения:127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10.
Через proxy настраивались Codex.exe,codex-code-mode-host.exe,remoting_host.exe,remoting_desktop.exe,Telegram.exe и домены OpenAI/ChatGPT.
Для Chrome Remote Desktop дополнительно:instantmessaging-pa.googleapis.com,remotedesktop-pa.googleapis.com,remotedesktop.google.com и замеченный relay74.125.247.128/32. Relay может измениться; это исторически помогший адрес, не универсальная гарантия.
Google Remote Desktop, Telegram, GPT и публичный сайт пользователь подтвердил работающими вместе.
Windows11 Home не предоставляет стандартный RDP-сервер. Не устанавливать RDP-патчи и не отключать антивирус.

Задание планировщика Sportfond-v2rayN: при входе пользователя, задержка30сек, с повышенными правами, интерактивно. Скрипт Set-V2rayStartup.ps1 рядом. Реальная проверка после следующего входа/перезагрузки отдельно не зафиксирована.
API получает HTTPS_PROXY=http://host.docker.internal:10808 для исходящих HTTPS; NO_PROXY исключает локальные адреса/сервисы. Системный VPN не отключать автоматически: можно потерять удалённую связь.

## Проверка при сбое

1. Проверить Docker Desktop и три контейнера, healthcheck API.
2. Локально открыть https://api.sportfondhm.ru/api/health: ожидается {"status":"ok"}.
3. С телефона через мобильную сеть, без домашнего Wi-Fi, открыть тот же адрес. Владелец подтвердил15.11, что работает.
4. Если локально публичный адрес не отвечает, это ещё не доказывает внешнюю недоступность:15.11 внешний адрес из Windows давал ошибку TLS, а локальный TLS с тем же hostname и доступ по мобильной сети работали.
5. Диагностическая HTTP-страница http://188.19.201.153/sportfond-connectivity возвращает Sportfond connection OK, если маршрут доступен. Она не является API и не принимает данные.
6. Сверить фактический WAN роутера и A-запись api.sportfondhm.ru. Сверить LAN сервера и адрес назначения проброса.
7. Проверить правило Firewall и маршрутизацию VPN; не отключать защиту и не открывать все порты.

## Файлы, данные и ключи

- D:/Projects/sportfond-app/backend — активный Python API.
- runtime/data/app.sqlite3 — пользователи, тренировки и партнёрские заявки.
- runtime/uploads — изображения тренировок; runtime/backups — локальные SQLite+image snapshots.
- runtime/private/limetime.env — ключ LIMETIME, только сервер, не GitHub.
- Прочие рабочие секреты примонтированы из Linux/private путей, указанных в compose.yaml; значения в документацию не копировать.
- backend/woodtrail.py — только чтение LIMETIME, публичные поля участников, кэш120сек; почта/телефоны/даты рождения не выдаются.
- Партнёрские заявки: partnership_requests в app.sqlite3; презентация и автоматическая рассылка ещё не подключены.
- Резервные копии сейчас на том же домашнем диске. Внешний независимый бэкап ещё не настроен.

## GitHub и публикация

mrbodya1/sportfond: портал в корне, WOOD TRAIL в woodtrail/, исходник портала portal-redesign/; инструкции docs/PORTAL-PUBLISH.md и docs/PARTNERSHIPS.md.
mrbodya1/sportfond-app: приложение и серверный код. Новые интеграции сохранены в feature/partner-enquiries; это важно при восстановлении — один main может не содержать последних серверных изменений.
mrbodya1/sportfond-map: отдельная карта.
Не заменять корень sportfond только сборкой WOOD TRAIL: сохранять портал,CNAME и существующие страницы.
Подробный журнал:NETWORK-STATE.md. При противоречии сначала сверять текущие конфигурации и этот сводный документ, а не старую промежуточную запись.

## 15 ноября 2026 — добавлен отдельный HTTPS PACE

Общий Caddyfile теперь также обслуживает pace-api.sportfondhm.ru: CNAME на api.sportfondhm.ru, reverse_proxy host.docker.internal:8091 к закрытому Windows gateway PACE, затем PocketBase127.0.0.1:8090. Существующая секция Sportfond не изменялась. Caddy validate пройден; SIGUSR1 на2.11.9 применил файл без остановки контейнера (ID/StartedAt сохранены). Сертификат получен автоматически; PACE и Sportfond health200, внешний PACE health200 подтверждён владельцем с мобильной сети. Новых портов или правил firewall не создавалось. Не удалять блок PACE при будущих изменениях общего файла. Подробности: D:/Applications/PACE/Project/docs/direct-https.md. По последующему прямому указанию владельца старый Funnel PACE полностью отключён: serve/funnel status No serve config. PACE использует только новый прямой HTTPS; установленной версии со старым URL потребуется обновление. Tailscale остаётся только отдельным административным каналом. API-контейнер Sportfond и его данные не перезапускались/не менялись.

## Карта: кабинеты и администрирование — 15.11.2026
Map API теперь работает на том же домашнем сервере, namespace /api/map, отдельная cookie и отдельные таблицы map_* в приватной app.sqlite3. Администратор только подтверждённая почта89821575459@ya.ru; код backend/map_service.py.
Локальный frontend:http://127.0.0.1:4178/organizers.html и moderation.html. Локальный Caddy проксирует /api/map на127.0.0.1:18767 через host.docker.internal; прямой статический файловый просмотр для входа не подходит.
Карта/кабинеты сохранены в mrbodya1/sportfond-map ветка design/first-draft, сервер — mrbodya1/sportfond-app ветка feature/partner-enquiries. Frontend пока только в черновике, map production не переключался.
Афиши map-<sha256>.<ext> находятся в runtime/uploads; обновлённый backup_data.py резервирует текущие и опубликованные афиши вместе с базой. Подробный процесс/поля/проверки см.docs/ORGANIZERS.md репозитория sportfond-map.


2026-11-15: map preview 4178 uses MapLibre/OpenFreeMap vector styles. API /api/map/tiles/ relays only validated tile/glyph paths with bounded memory cache; map_tiles.py buffers verified gzip byte ranges, font source fixed to maplibre/demotiles. No DNS, ports, router or VPN changes. See sportfond-map/docs/VECTOR-MAP.md.
