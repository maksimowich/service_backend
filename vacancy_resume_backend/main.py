import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.docstore.document import Document
from vacancy_resume_backend.parser import generate_json_from_text, get_text, RESUME_JSON_TEMPLATE, VACANCY_JSON_TEMPLATE
from vacancy_resume_backend.config import CONNECTION_STRING, COLLECTION_NAME, OPENAI_API_KEY, STORAGE_PATH
from vacancy_resume_backend.response import zipfiles
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
    if file.filename.endswith('.pdf'):
        file_content = get_text(file.file._file)
        try:
            file_content = generate_json_from_text(
                file_content,
                RESUME_JSON_TEMPLATE,
                OPENAI_API_KEY,
                doc_type='резюме')
        except:
            pass
    else:
        file_content = file.file.read().decode("utf-8")

    print(file_content)

    if file:
        path = STORAGE_PATH + str(len(os.listdir(STORAGE_PATH))) + '.pdf'
        doc = Document(page_content=file_content, metadata={
            'path': path})
        STORE.add_documents([doc])[0]
        with open(path, 'wb') as doc_file:
            doc_file.write(file.file._file.getvalue())
        return {"message": "File uploaded and saved successfully"}
    else:
        return {"message": "No file uploaded"}

@app.post("/upload_vacancy/")
async def upload_vacancy(file: UploadFile):
    if file.filename.endswith('.pdf'):
        file_content = get_text(file.file._file)
        try:
            file_content = generate_json_from_text(
                file_content,
                VACANCY_JSON_TEMPLATE,
                OPENAI_API_KEY,
                doc_type='вакансия')
        except:
            pass
    else:
        file_content = file.file.read().decode("utf-8")

    print(file_content)

    if file:
        path = STORAGE_PATH + str(len(os.listdir(STORAGE_PATH))) + '.pdf'
        doc = Document(page_content=file_content, metadata={
            'path': path})
        STORE.add_documents([doc])[0]
        with open(path, 'wb') as doc_file:
            doc_file.write(file.file._file.getvalue())
        return {"message": "File uploaded and saved successfully"}
    else:
        return {"message": "No file uploaded"}

@app.get("/score_resume/")
async def resumes_with_score(file: UploadFile):
    if file.filename.endswith('.pdf'):
        file_content = get_text(file.file._file)
        try:
            file_content = generate_json_from_text(
                file_content,
                VACANCY_JSON_TEMPLATE,
                OPENAI_API_KEY,
                doc_type='вакансия')
        except:
            pass
    else:
        file_content = file.file.read().decode("utf-8")

    paths = []
    docs_with_score = STORE.similarity_search_with_score(file_content, 10)
    for doc, score in docs_with_score:
        print("-" * 80)
        print("Score: ", score)
        print(doc.page_content)
        print("-" * 80)

        paths.append(doc.metadata['path'])

    return zipfiles(paths)

@app.get("/score_vacancy/")
async def vacancies_with_score(file: UploadFile):
    if file.filename.endswith('.pdf'):
        file_content = get_text(file.file._file)
        try:
            file_content = generate_json_from_text(
                file_content,
                RESUME_JSON_TEMPLATE,
                OPENAI_API_KEY,
                doc_type='резюме')
        except:
            pass
    else:
        file_content = file.file.read().decode("utf-8")

    print(file_content)

    paths = []
    docs_with_score = STORE.similarity_search_with_score(file_content, 10)
    for doc, score in docs_with_score:
        print("-" * 80)
        print("Score: ", score)
        print(doc.page_content)
        print("-" * 80)

        paths.append(doc.metadata['path'])

    return zipfiles(paths)


def main():
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5000)
