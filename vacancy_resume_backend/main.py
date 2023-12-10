import os

from fastapi import FastAPI, UploadFile, File
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.docstore.document import Document
from vacancy_resume_backend.parser import generate_json_from_file, RESUME_JSON_TEMPLATE, VACANCY_JSON_TEMPLATE
from vacancy_resume_backend.config import CONNECTION_STRING, COLLECTION_NAME, OPENAI_API_KEY, HOST, PORT
app = FastAPI()

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

embeddings = OpenAIEmbeddings()
STORE = PGVector(
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    embedding_function=embeddings,
)

@app.post("/upload_resume/")
async def upload_resume(file: UploadFile):
    print(1)
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
    uvicorn.run(app, host='0.0.0.0', port=30000)
