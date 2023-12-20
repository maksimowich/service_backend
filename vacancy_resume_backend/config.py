from dotenv import load_dotenv
import os

load_dotenv()

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
STORAGE_PATH = os.environ.get("STORAGE_PATH")
RESUME = 'резюме'
VACANCY = 'вакансия'
