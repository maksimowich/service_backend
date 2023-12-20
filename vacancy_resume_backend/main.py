import os
from fastapi import FastAPI, UploadFile  # , File
# from fastapi.responses import FileResponse
# from pathlib import Path
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.docstore.document import Document
from vacancy_resume_backend.parser import get_pdf_file_content
from vacancy_resume_backend.config import CONNECTION_STRING, COLLECTION_NAME, OPENAI_API_KEY, STORAGE_PATH, RESUME, \
    VACANCY
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
    response = await  _process_file(file, doc_type=RESUME)
    return response


@app.post("/upload_vacancy/")
async def upload_vacancy(file: UploadFile):
    response = await _process_file(file, doc_type=VACANCY)
    return response


@app.get("/score_resume/")
async def resumes_with_score(file: UploadFile):
    response = await _process_file(file, doc_type=VACANCY, process='scoring')
    return response


@app.get("/score_vacancy/")
async def vacancies_with_score(file: UploadFile):
    response = await _process_file(file, doc_type=RESUME, process='scoring')
    return response


async def _process_file(file: UploadFile, doc_type=RESUME, process='uploading'):
    if not file:
        return {"message": "No file uploaded"}

    file_bytes = await file.read()

    if file.filename.endswith('.pdf'):
        file_content = get_pdf_file_content(file, doc_type)
    else:
        file_content = file_bytes.decode("utf-8")

    print(file_content)

    if process == 'uploading':
        path = STORAGE_PATH + str(len(os.listdir(STORAGE_PATH))) + '.pdf'
        doc = Document(page_content=file_content, metadata={'path': path})
        STORE.add_documents([doc])
        with open(path, 'wb') as doc_file:
            doc_file.write(file_bytes)
        return {"message": "File uploaded and saved successfully"}
    elif process == 'scoring':
        paths = []
        docs_with_score = STORE.similarity_search_with_score(file_content, 10)
        for doc, score in docs_with_score:
            print("-" * 80)
            print("Score: ", score)
            print(doc.page_content)
            print("-" * 80)
            paths.append(doc.metadata['path'])
        file_response = zipfiles(paths)
        return file_response


def main():
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5000)
