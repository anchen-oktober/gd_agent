from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

def normalize_notion_id(page_id: str) -> str:
    if page_id and "-" not in page_id and len(page_id) == 32:
        return f"{page_id[0:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
    return page_id

def check_notion_access(page_id, token):
    notion = Client(auth=token)
    page_id = normalize_notion_id(page_id)
    try:
        page = notion.pages.retrieve(page_id)
        print("✅ Доступ к странице есть:", page["id"])
    except Exception as e:
        print("❌ Ошибка при доступе к странице:", e)

if __name__ == "__main__":
    check_notion_access(NOTION_PAGE_ID, NOTION_TOKEN)