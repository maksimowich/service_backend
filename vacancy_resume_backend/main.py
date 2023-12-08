from fastapi import FastAPI, UploadFile, File
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.docstore.document import Document
import os
from vacancy_resume_backend.parser import generate_json_from_file, RESUME_JSON_TEMPLATE, VACANCY_JSON_TEMPLATE
import sys

app = FastAPI()

CONNECTION_STRING = "postgresql+psycopg2://syash:2004@localhost:5432/resumes"
COLLECTION_NAME = "search_vacancy"
os.environ["OPENAI_API_KEY"] = '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'
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

embeddings = OpenAIEmbeddings()
STORE = PGVector(
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    embedding_function=embeddings,
)

@app.post("/upload_resume/")
async def upload_resume(file: UploadFile):
    if file.filename.endswith('.pdf'):
        file_content = generate_json_from_file(file.file._file, RESUME_JSON_TEMPLATE, OPENAI_API_KEY, doc_type='резюме')
    else:
        file_content = file.file.read().decode("utf-8")

    print(file_content)

    if file:
        STORE.add_documents([Document(page_content=file_content)])
        return {"message": "File uploaded and saved successfully"}
    else:
        return {"message": "No file uploaded"}

@app.post("/upload_vacancy/")
async def upload_vacancy(file: UploadFile):
    if file.filename.endswith('.pdf'):
        file_content = generate_json_from_file(file.file._file, VACANCY_JSON_TEMPLATE, OPENAI_API_KEY, doc_type='вакансия')
    else:
        file_content = file.file.read().decode("utf-8")

    print(file_content)

    if file:
        print('uuid = ', STORE.add_documents([Document(page_content=file_content)]))
        return {"message": "File uploaded and saved successfully"}
    else:
        return {"message": "No file uploaded"}

@app.get("/score_resume/")
async def resumes_with_score(file: UploadFile):
    if file.filename.endswith('.pdf'):
        file_content = generate_json_from_file(file.file._file, VACANCY_JSON_TEMPLATE, OPENAI_API_KEY, doc_type='вакансия')
    else:
        file_content = file.file.read().decode("utf-8")

    print(file_content)

    docs_with_score = STORE.similarity_search_with_score(file_content, 10)
    for doc, score in docs_with_score:
        print("-" * 80)
        print("Score: ", score)
        print(doc.page_content)
        print("-" * 80)

    return [(score, doc.page_content) for doc, score in docs_with_score]

@app.get("/score_vacancy/")
async def vacancies_with_score(file: UploadFile):
    with open('/home/sasha/PycharmProjects/data/docs/Шубочкин.pdf', 'wb') as file_to_save:
        file_to_save.write(file.file._file.getvalue())

    if file.filename.endswith('.pdf'):
        file_content = generate_json_from_file(file.file._file, RESUME_JSON_TEMPLATE, OPENAI_API_KEY, doc_type='резюме')
    else:
        file_content = file.file.read().decode("utf-8")

    print(file_content)

    docs_with_score = STORE.similarity_search_with_score(file_content, 10)
    for doc, score in docs_with_score:
        print("-" * 80)
        print("Score: ", score)
        print(doc.page_content)
        print("-" * 80)

    return [(score, doc.page_content) for doc, score in docs_with_score]


def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
