# BrandFound GEO-специалисты: общий корпус для 2 исследований, 30.10.2026

**110 из 110 ответов · 10 вопросов · 11 интерфейсов · 74 распознанных человека.** Все интерфейсы включены.

Этот набор используется в 2 отдельных исследованиях: [BMR](../../research/geo-experts-bmr-russia-2026/) и [FRS](../../research/geo-experts-first-recommendation-russia-2026/). Это **не 2 независимые выборки**, а 2 метрики одной панели.

## Открытые источники
- [observations.jsonl](observations.jsonl): полный текст каждого ответа, кроме редактирования контактных данных;
- [prompts.json](prompts.json): точные варианты 10 запросов для 11 интерфейсов;
- [entity_dictionary.csv](entity_dictionary.csv): имена и детерминированные шаблоны для BMR;
- [first_recommendation_labels.csv](first_recommendation_labels.csv): кодировка FRS по 110 ответам, объяснение и фрагмент текста;
- [LABELING_PROTOCOL.md](LABELING_PROTOCOL.md): как определить первую рекомендацию;
- [DATA_PROVENANCE.md](DATA_PROVENANCE.md): откуда ответы и чем различаются запросы;
- [contact_redactions.csv](contact_redactions.csv): учет замен контактной информации;
- [manifest.json](manifest.json): контроль комплекта;
- [reproduce.py](reproduce.py): автоматический пересчет 2 метрик.

```bash
python3 research-data/geo-experts-2026-10-30/reproduce.py
```

**Статус: DRAFT.** Кодировка FRS требует независимой проверки, исследование связано с участником Алексеем Яковлевым через основателей IndexResearch. Оно не является организационно независимым источником и не оценивает реальную квалификацию людей.
