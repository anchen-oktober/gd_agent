import os
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Загружаем ключи
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
claude_key = os.getenv("CLAUDE_API_KEY")

gpt_client = OpenAI(api_key=openai_key) if openai_key else None
claude_client = Anthropic(api_key=claude_key) if claude_key else None

def fetch_google_doc(doc_id: str, creds_path: str) -> dict:
    creds = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=["https://www.googleapis.com/auth/documents.readonly"]
    )
    service = build("docs", "v1", credentials=creds)
    return service.documents().get(documentId=doc_id).execute()

def extract_plain_text(doc: dict) -> str:
    text = ""
    for element in doc.get("body").get("content", []):
        if "paragraph" in element:
            for run in element["paragraph"]["elements"]:
                if "textRun" in run:
                    text += run["textRun"]["content"]
    return text.strip()

def extract_title(doc: dict) -> str:
    # Берём первый параграф как название
    for element in doc.get("body").get("content", []):
        if "paragraph" in element:
            for run in element["paragraph"]["elements"]:
                if "textRun" in run:
                    title = run["textRun"]["content"].strip()
                    if title:
                        return title
    return "Untitled Project"

def extract_characters(doc: dict) -> str:
    bold_words = []
    for element in doc.get("body").get("content", []):
        if "paragraph" in element:
            for run in element["paragraph"]["elements"]:
                if "textRun" in run:
                    style = run["textRun"].get("textStyle", {})
                    text = run["textRun"]["content"].strip()
                    if style.get("bold") and text:
                        bold_words.append(f"**{text}**")
    return ", ".join(set(bold_words)) if bold_words else "Не указаны"

def generate_moodboard(scenario: str) -> str:
    return """
### Постапокалиптический город
![City](i:turn0image1)

### Заброшенное метро
![Metro](i:turn0image62)

### Таинственная башня в тумане
![Tower](i:turn0image91)

### Руины на закате
![Ruins](i:turn0image31)
"""

def generate_future_ideas(scenario: str) -> str:
    prompt = f"""
    На основе игрового сценария предложи идеи для будущего развития проекта:
    - Возможные сюжетные ветки
    - Новые механики
    - Дополнительные локации
    - Потенциальные расширения (DLC, мультиплеер)
    Сценарий: {scenario}
    """
    if gpt_client:
        try:
            response = gpt_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    if claude_client:
        try:
            response = claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception:
            pass
    return """- Ввести систему фракций и альянсов  
- Добавить процедурно генерируемые руины  
- Разработать мультиплеерный режим выживания  
- Подготовить DLC с новыми регионами"""

def generate_weapon_balance(scenario: str) -> str:
    prompt = f"""
    На основе игрового сценария предложи таблицу баланса оружия.
    В таблице должны быть следующие столбцы:
    - Тип оружия
    - Урон (ед.)
    - Скорость атаки (уд/сек)
    - Дальность (м)
    - Прочность (удары)
    - Особенности / Балансировка

    Сценарий: {scenario}

    Выведи результат в формате Markdown-таблицы.
    """
    if gpt_client:
        try:
            response = gpt_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    if claude_client:
        try:
            response = claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception:
            pass
    return """| Тип оружия | Урон | Скорость атаки | Дальность | Прочность | Особенности |
|------------|------|----------------|-----------|-----------|-------------|
| Ближний бой | 25–35 | 1.8 | 2 | 150 | Быстрое, но слабое против брони |
| Огнестрельное | 60–90 | 0.8 | 50 | 80 | Мощное, но редкие патроны |
| Метательное | 40–55 | 1.2 | 20 | 50 | Универсальное, ограниченный запас |
| Энергетическое | 100–120 | 0.6 | 40 | 60 | Уникальные эффекты, редкость |
"""

def generate_progression(scenario: str) -> str:
    prompt = f"""
    На основе игрового сценария предложи прогрессию игры:
    - Начальный этап
    - Средний этап
    - Поздний этап
    - Пост-игра

    Сценарий: {scenario}

    Выведи результат в виде списка.
    """
    if gpt_client:
        try:
            response = gpt_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    if claude_client:
        try:
            response = claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception:
            pass
    return """- Начало: исследование руин и сбор ресурсов  
- Средний этап: доступ к метро, новые враги и крафт  
- Поздний этап: башня как финальная локация с боссами  
- Пост‑игра: новые регионы и режим выживания"""

def scenario_to_gdd(scenario: str, characters: str, title: str) -> str:
    moodboard = generate_moodboard(scenario)
    future_ideas = generate_future_ideas(scenario)
    weapon_balance = generate_weapon_balance(scenario)
    progression = generate_progression(scenario)

    gdd_md = f"""
# Game Design Document

## Название
{title}

## Жанр и платформа
RPG, PC

## Целевая аудитория
Любители RPG сюжетов

## Сюжет
{scenario}

## Персонажи
{characters}

## Локации
(Автоматически извлекаются позже)

## Игровая механика
Исследование, крафт, выживание

## Прогрессия
{progression}

## UI/UX
Минималистичный HUD, инвентарь в виде сетки

## Технические требования
Unreal Engine, ПК

## Moodboard
{moodboard}

## Баланс оружия
{weapon_balance}

## Идеи на будущее
{future_ideas}
"""
    return gdd_md

def save_to_file(content: str, title: str):
    safe_title = title.replace(" ", "_")
    filename = f"{safe_title}_GDD.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ ГДД сохранён в файл: {filename}")

def save_weapon_balance(content: str, title: str):
    filename = f"{title.replace(' ', '_')}_WeaponBalance.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Таблица баланса оружия сохранена в файл: {filename}")


if __name__ == "__main__":
    DOCUMENT_ID = "1XWUApnYqdH9pYAS3AER30DYTndMTGUQgmkWDvexUz00"
    CREDS_PATH = "credentials.json"

    doc = fetch_google_doc(DOCUMENT_ID, CREDS_PATH)
    scenario_text = extract_plain_text(doc)
    characters = extract_characters(doc)

    gdd_markdown = scenario_to_gdd(scenario_text, characters, title=extract_title(doc))
    save_to_file(gdd_markdown, extract_title(doc))