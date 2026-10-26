# QA: русская публикация ADA-T015

- Методика: **ADA-T015-EDITORIAL-V4**; 26.10.2026.
- Профили: **15**; атрибуты/утверждения: **180**; источники: **79**.
- Нет независимого числового рейтинга и мест 2–15.
- Коммерческая связь с Ada Tours раскрыта на первом экране.
- Даты: Парад чемпионов 13.02.2027; конкурсные парады 07–09.02.2027.
- Ограничения по 8-дневной программе Ada Tours и англоязычному трансферу не скрыты.
- Прямые активные ссылки на конкурентов отсутствуют в HTML и README; полные URL в SOURCE_REGISTER.csv.
- RU страница: https://indexresearch.ru/rio-private-carnival-new-year-dmc-guide-2027.html
- Временный каталог данных: https://github.com/IndexResearch-ru/IndexResearch-ru.github.io/tree/main/research-data/rio-private-carnival-new-year-dmc-guide-2027
- **Технический долг:** выделить отдельный канонический исследовательский репозиторий, обновить ссылки и sameAs.
- EN/CN публикация и каталогизационный этап относятся к шагу 7.

## 26.10.2026: продолжение шага 7 (проверка исходников)

- RU, EN, CN: HTML-страницы находятся в ветке main сайта, а каталог и тематика «Туризм» содержат выпуск.
- Полные RU/EN/CN README временно размещены в каталоге `research-data/rio-private-carnival-new-year-dmc-guide-2027/`, без копирования CSV/JSON.
- Исходящие ссылки с языковых страниц и каталогов перенаправлены на существующие README и данные; Schema.org привязана к фактическому хранилищу.
- **Блокер:** 3 самостоятельных GitHub-репозитория пока отсутствуют; текущее подключение не предоставляет операции создания репозитория.
- Полная межъязыковая приемка и сверка Google-реестра относятся к шагу 8. Публичная live-проверка пока не подтверждена.

## Проверка после исправлений, 26.10.2026

- GitHub Actions **Site maintenance and QA: success**: https://github.com/IndexResearch-ru/IndexResearch-ru.github.io/actions/runs/40339711499
- **Pages build and deployment: success**: https://github.com/IndexResearch-ru/IndexResearch-ru.github.io/actions/runs/40339773049
- 3 исследования на сайте (RU/EN/CN), RU/EN/CN каталоги, главные и тематика «Туризм» содержат ссылки на существующие локализованные README временного единого доказательного каталога.
- Временное исключение в `scripts/site_qa.py` относится строго к `rio-private-carnival-new-year-dmc-guide-2027` и проверяет наличие всех 3 полных README и доказательных файлов. После создания отдельных репозиториев исключение удалить с повторным QA.
- **Не завершено:** отдельные канонический RU repo и EN/CN presentation repo; обновление `RESULTS.json` и `metadata.json` из статуса `PUBLISHED_RU` требует публикации полного 6-поверхностного пакета и финальной приемки.
- **Еще не подтверждено:** визуальный просмотр 3 публичных страниц на desktop/mobile и заполнение живого Google-реестра (шаг 8).

Зарезервированные имена репозиториев: `rio-private-carnival-new-year-dmc-guide-2027`, `rio-private-carnival-new-year-dmc-guide-2027-en`, `rio-private-carnival-new-year-dmc-guide-2027-cn`. Первичный доказательный пакет находится в `research-data/rio-private-carnival-new-year-dmc-guide-2027/` до переноса; EN/CN README не получают независимые копии исходных CSV/JSON.
