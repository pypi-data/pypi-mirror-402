# Meet Live Info

Python HTTP-клиент для **Live Info Server** из  
**Splash Meet Manager**.

Библиотека предоставляет типизированный и удобный доступ к официальному
HTTP JSON API Meet Manager без UDP, подписок и фоновых серверов.

Подходит для:
- live-табло
- веб-клиентов
- аналитики соревнований
- экспорта результатов
- интеграций с внешними сервисами

---

## Возможности

- Чистый **HTTP-клиент**
- Полная типизация ответов через **pydantic**
- Поддержка всех динамических HTTP эндпоинтов Live Info Server
- Корректная работа с языками (`Accept-Language`, `language=`)
- Простая интеграция в backend и скрипты
- Python **3.11+**

---

## Требования

- Python **>= 3.11**
- Splash Meet Manager с включённым **Live Info Server (HTTP)**

Зависимости:
- `requests`
- `pydantic`

---

## Установка

```bash
pip install meetliveinfo
````

или

```bash
poetry add meetliveinfo
```

---

## Быстрый старт

```python
from meetliveinfo import HTTPClient

client = HTTPClient("http://localhost:3001")

events = client.events()
for event in events:
    print(event.id, event.status)
```

---

## Работа с языком

Язык данных зависит от:

* HTTP-заголовка `Accept-Language`
* или query-параметра `language`

```python
client = HTTPClient(
    "http://localhost:3001",
    language="us"
)
```

* `us` → английские имена
* любой другой язык → локализованные данные

---

## Поддерживаемые HTTP эндпоинты

### Общие данные

* `/globals`
* `/agegroups`
* `/clubs`
* `/athletes`
* `/events`
* `/events/bysession`
* `/events/bystroke`
* `/events/timing`

### Заплывы и результаты

* `/heats/{event}/{heat}`
* `/heats/byid/{heatid}`
* `/heats/ares/{event}/{round}/{heat}`
* `/results/{event}`

### Медали и очки

* `/medals`
* `/medals/{event}`
* `/pointscores`
* `/pointscores/{id}`

### Рекорды

* `/records`
* `/records/{id}`
* `/records/{id}/all`
* `/records/byevent/{event}`

### Подсчёт очков

* `/time2Points`
* `/time2Points/handicap`
* `/time2Points/master`

---

## Коды и справочники

### Gender

* `1` — Men
* `2` — Women
* `3` — Mixed

### Stroke

* `1` — Freestyle
* `2` — Backstroke
* `3` — Breaststroke
* `4` — Fly
* `5` — Medley

### Status

* `1` — Entries
* `2` — Seeded
* `3` — Running
* `4` — Unofficial
* `5` — Official

---

## Архитектура

* Один HTTPClient
* Синхронные запросы
* Без фоновых процессов
* Без UDP
* Без side-effects

Библиотека безопасна для использования в:

* FastAPI
* Django
* Celery
* CLI-скриптах

---

## Статус проекта

* Активная разработка
* API может расширяться до версии `1.0.0`

---

## Лицензия

MIT

---

## Автор

LordCode /  Dybfuo
📧 [9999269010dddd@gmail.com](mailto:9999269010dddd@gmail.com)
