import os
import requests
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from notion_client import Client as NotionClient
from googleapiclient.discovery import build
from google.oauth2 import service_account
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

# --- Slack ---
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# --- Ollama ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

# --- Google Docs ---
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH", "credentials.json")

def read_google_doc(doc_id, creds_path):
    try:
        SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        service = build("docs", "v1", credentials=creds)
        doc = service.documents().get(documentId=doc_id).execute()
        content = []
        for el in doc.get("body", {}).get("content", []):
            if "paragraph" in el:
                for elem in el["paragraph"]["elements"]:
                    if "textRun" in elem:
                        content.append(elem["textRun"]["content"])
        return "\n".join(content)
    except Exception as e:
        print("⚠️ Google Docs недоступен:", e)
        return ""

# --- Notion ---
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

def read_notion_page(page_id, notion_token):
    try:
        notion = NotionClient(auth=notion_token)
        blocks = notion.blocks.children.list(page_id)
        content = []
        for block in blocks["results"]:
            if block["type"] == "paragraph":
                for text in block["paragraph"]["text"]:
                    content.append(text["plain_text"])
        return "\n".join(content)
    except Exception as e:
        print("⚠️ Notion недоступен:", e)
        return ""

# --- Ollama ---
def chat_local(prompt, model=MODEL):
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False}
    )
    data = response.json()
    return data.get("response", "").strip()

# --- Векторное хранилище ---
def build_vector_store(texts):
    client = chromadb.Client()
    embedder = embedding_functions.DefaultEmbeddingFunction()
    collection = client.create_collection(name="docs", embedding_function=embedder)
    for i, chunk in enumerate(texts):
        if chunk.strip():
            collection.add(documents=[chunk], ids=[str(i)])
    return collection

def search_context(collection, query, top_k=3):
    results = collection.query(query_texts=[query], n_results=top_k)
    if not results["documents"]:
        return []
    return results["documents"]

# --- Агент ---
def agent(user_message, collection):
    contexts = search_context(collection, user_message, top_k=3)
    if not contexts:
        return "⚠️ В документации нет подходящего ответа.", []

    joined_context = "\n---\n".join(["\n".join(c) for c in contexts])

    prompt = f"""
Ты ассистент, который отвечает строго на основе документации.
Вот найденные куски документации:

{joined_context}

Вопрос пользователя: {user_message}

Требование:
- Используй только приведённые куски.
- Если ответа нет в них, скажи: '⚠️ В документации нет информации по этому запросу.'
- Не придумывай ничего нового.
Ответ ассистента:
"""
    answer = chat_local(prompt)
    return answer, contexts

# --- Slack Bot ---
app = App(token=SLACK_BOT_TOKEN)

@app.event("app_mention")
def handle_mention(body, say):
    user_text = body["event"]["text"]
    print("📩 Получено упоминание:", user_text)

    answer, contexts = agent(user_text, collection)

    if contexts:
        context_text = "\n---\n".join(["\n".join(c) for c in contexts])
        say(f"📄 Найденные куски документации:\n```{context_text}```\n\n🤖 Ответ:\n{answer}")
    else:
        say(answer)

    print("🤖 Ответ:", answer)

if __name__ == "__main__":
    google_text = read_google_doc(GOOGLE_DOC_ID, GOOGLE_CREDS_PATH)
    notion_text = read_notion_page(NOTION_PAGE_ID, NOTION_TOKEN)

    print("✅ Google Docs загружен:", len(google_text.split()), "слов")
    print("✅ Notion загружен:", len(notion_text.split()), "слов")

    all_texts = (google_text + "\n" + notion_text).split("\n")
    collection = build_vector_store(all_texts)

    print("🤖 Slack‑бот запущен!")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()