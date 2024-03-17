from dotenv import load_dotenv
import os

load_dotenv()

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
STORAGE_PATH = os.environ.get("STORAGE_PATH")
RESUMES_STORAGE_PATH = os.environ.get("RESUMES_STORAGE_PATH")
BOT_VACANCY_STORAGE_PATH = os.environ.get("BOT_VACANCY_STORAGE_PATH")
