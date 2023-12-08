from dotenv import load_dotenv
import os

load_dotenv()

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")

print(CONNECTION_STRING)