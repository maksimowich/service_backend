import enum
import os
from enum import Enum
import json

from fastapi import FastAPI, UploadFile
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.docstore.document import Document
from vacancy_resume_backend.parser import get_pdf_file_content, DocType
from vacancy_resume_backend.config import CONNECTION_STRING, COLLECTION_NAME, OPENAI_API_KEY, STORAGE_PATH, RESUMES_STORAGE_PATH, BOT_VACANCY_STORAGE_PATH
from vacancy_resume_backend.response import zipfiles
from email_alert import send_email

from fastapi import FastAPI
from starlette.responses import RedirectResponse
from yarl import URL
import requests
from time import sleep
import io
from bs4 import BeautifulSoup
from fastapi import Request
from starlette.responses import Response
from starlette.status import HTTP_200_OK

class Process(Enum):
    UPLOADING = 'uploading'
    SCORING = 'scoring'


app = FastAPI()

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

embeddings = OpenAIEmbeddings()
STORE = PGVector(
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    embedding_function=embeddings,
)


# @app.post("/upload_resume/")
# async def upload_resume(file: UploadFile):
#     response = await _process_file(file, doc_type=DocType.RESUME, process=Process.UPLOADING)
#     return response

@app.post("/upload_vacancy/")
async def upload_vacancy(file: UploadFile):
    try:
        response = await _process_file(file, doc_type=DocType.VACANCY, process=Process.UPLOADING)
    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
#        send_email("Backend Error", error_message)
    return response

@app.post("/upload_vacancy_bot/")
async def upload_vacancy_bot(request: Request):
    a = await request.json()

    html_string = a['forms'][0]['answer']
    soup = BeautifulSoup(html_string, 'html.parser')
    link = soup.a['href']

    response = requests.get(link)
    file_bytes = io.BytesIO(response.content)

    path = BOT_VACANCY_STORAGE_PATH + str(len(os.listdir(BOT_VACANCY_STORAGE_PATH))) + '.pdf'
    with open(path, 'wb') as doc_file:
        doc_file.write(file_bytes.getvalue())
    return {"message": "Vacancy from bot saved successfully"}
    

# @app.get("/score_resume/")
# async def resumes_with_score(file: UploadFile):
#     paths, scores = await _process_file(file, doc_type=DocType.VACANCY, process=Process.SCORING)
#     return zipfiles(paths)

# @app.get("/score_vacancy/")
# async def vacancies_with_score(file: UploadFile):
#     paths, scores = await _process_file(file, doc_type=DocType.RESUME, process=Process.SCORING)
#     return zipfiles(paths)


@app.post('/score_vacancy_bot/')
async def vacancies_with_score(request: Request):
    a = await request.json()

    html_string = a['forms'][0]['answer']
    soup = BeautifulSoup(html_string, 'html.parser')
    link = soup.a['href']

    response = requests.get(link)
    file_content = io.BytesIO(response.content)

    # Создание экземпляра UploadFile для передачи в FastAPI
    upload_file = UploadFile(file=file_content, filename="resume.pdf")

    try:
        paths, scores = await _process_file(upload_file, doc_type=DocType.RESUME, process=Process.SCORING)

        # Отправка файла пользователю в телеграм
        bot_token = '5535503367:AAG6YVSW04UFwe8aeNVbJAGbzuxZFQOnFRY'

        bot_chatID = a['user']['id']
    #     bot_chatID = 1137971119
        for i in range(len(paths)):
            doc_file_path = paths[i]
            similarity_percentage = round((1 - scores[i]) * 100, 2)

            if doc_file_path.endswith('.pdf'):
                send_URL = f'https://api.telegram.org/bot{bot_token}/sendDocument'

                with open(doc_file_path, 'rb') as doc_file:
                    doc_file_content = doc_file.read()

                requests.post(
                send_URL,
                files={'document': doc_file_content},
                params={'chat_id': bot_chatID, 'caption': f'score: {similarity_percentage}%'}
                )

            elif doc_file_path.endswith('.json'):
                # send_URL = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                with open(doc_file_path, 'r') as doc_file:
                    json_string = doc_file.read()

                vacancy_dict = json.loads(json_string)
                vacancy_url = vacancy_dict['alternate_url']
                
                text_message = f'{vacancy_url}\nscore: {similarity_percentage}%'
                TOKEN_API = "grizgcx4yibbeAAoicAz5NVgeRWh2Z5a"
                METHOD = "tg.sendMessage"
                chat_id = bot_chatID

                send_URL = f'https://api.puzzlebot.top/?token={TOKEN_API}&method={METHOD}&chat_id={chat_id}&text={text_message}'
                #requests.post(
                #send_URL,
                #params={'chat_id': bot_chatID, 'text': f'{vacancy_url}\nscore: {similarity_percentage}%'}
                #)
                requests.post(url=send_URL)


            print("Vacancies has been sent")
                                            
    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        send_email("Backend Error", error_message)
    return


async def _process_file(file: UploadFile, doc_type: DocType, process: Process):
    if not file:
        return {"message": "No file uploaded"}

    file_bytes = await file.read()

    if doc_type == DocType.VACANCY:
        if file.filename.endswith('.pdf'):
            file_content = get_pdf_file_content(file, doc_type)
            path = STORAGE_PATH + str(len(os.listdir(STORAGE_PATH))) + '.pdf'
        elif file.filename.endswith('.json'):
            file_content = file_bytes.decode("utf-8")
            path = STORAGE_PATH + str(len(os.listdir(STORAGE_PATH))) + '.json'
        else:
            raise TypeError('Unsupported file type')
    else:
        if file.filename.endswith('.pdf'):
            file_content = get_pdf_file_content(file, doc_type)
            path = RESUMES_STORAGE_PATH + str(len(os.listdir(RESUMES_STORAGE_PATH))) + '.pdf'
        else:
            raise TypeError('Unsupported file type')

    if process == Process.UPLOADING:
        doc = Document(page_content=file_content, metadata={'path': path})
        STORE.add_documents([doc])
        with open(path, 'wb') as doc_file:
            doc_file.write(file_bytes)
        return {"message": "File uploaded and saved successfully"}

    elif process == Process.SCORING:
        paths = []
        scores = []
        docs_with_score = STORE.similarity_search_with_score(file_content, 5)
        for doc, score in docs_with_score:
            paths.append(doc.metadata['path'])
            scores.append(score)
        with open(path, 'wb') as doc_file:
            doc_file.write(file_bytes)
        return paths, scores
    else:
        raise NameError(f'Unknown process: {process}')


def main():
    import uvicorn
    uvicorn.run(app, host='188.44.41.125', port=30000)
