from io import StringIO
import requests
from fastapi import UploadFile

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from vacancy_resume_backend.config import OPENAI_API_KEY, RESUME, VACANCY

RESUME_JSON_TEMPLATE = """{
    "birth_date": "",
    "gender": "",
    "area": "",
    "title": "",
    "specialization": [
        {
            "name": "",
            "profarea_name": ""
        }
    ],
    "salary": {
        "amount": "",
        "currency": ""
    },
    "education_level": "",
    "education": [
        {
            "year": "",
            "name": "",
            "organization": ""
        }
    ],
    "language": [
        {
            "name": "",
            "level": ""
        }
    ],
    "experience": [
        {
            "company": "",
            "start": "",
            "end": "",
            "position": "",
            "description": ""
        }
    ],
    "skill_set": [
        ""
    ],
    "skills": "",
    "additional_info": ""
}"""

VACANCY_JSON_TEMPLATE = """{
    "id": "",
    "department": {
        "id": "",
        "name": ""
    },
    "salary": {
        "to": "",
        "from": "",
        "currency": "",
        "gross": ""
    },
    "name": "",
    "area": {
        "id": "",
        "name": ""
    },
    "working_days": [
        {
            "id": "",
            "name": ""
        }
    ],
    "working_time_intervals": [
        {
            "id": "",
            "name": ""
        }
    ],
    "working_time_modes": [
        {
            "id": "",
            "name": ""
        }
    ],
    "experience": {
      "id": "",
      "name": ""
    },
    "employment": {
      "id": "",
      "name": ""
    },
    "description": "",
    "key_skills": [
        {"name":""}
    ]
}"""


def is_header_footer(text):
    keys = ['Приглашен на вакансию:', 'Резюме обновлено', 'Resume updated']
    for key in keys:
        if key in text:
            return True
    return False


def get_text(pdf_file):
    output_string = StringIO()
    parser = PDFParser(pdf_file)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)

    raw_text = output_string.getvalue()
    lines = [line for line in raw_text.splitlines() if not is_header_footer(line)]

    return '\n'.join(lines)


def generate_json_from_text(text, json_template, openai_api_key, doc_type=RESUME):
    # client = OpenAI(api_key=openai_api_key)
    api_endpoint = "https://api.openai.com/v1/chat/completions"

    sys_prompt = f"Преобразуй текст {doc_type} в JSON.\nJSON шаблон: {json_template}"
    prompt = f"{doc_type}: {text}"

    # stream = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": sys_prompt},
    #         {"role": "user", "content": prompt}
    #     ],
    #     stream=True,
    # )

    headers = {"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048  # Adjust as needed
    }

    # result = ''
    # for chunk in stream:
    #     if chunk.choices[0].delta.content is not None:
    #         result += chunk.choices[0].delta.content
    #
    # return result

    response = requests.post(api_endpoint, headers=headers, json=data)

    # Check for a successful response
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        raise Exception


def generate_json_from_file(pdf_file, json_template, openai_api_key, doc_type='резюме'):
    text = get_text(pdf_file)
    json = generate_json_from_text(text, json_template, openai_api_key, doc_type)
    return json


def get_pdf_file_content(file: UploadFile, doc_type=RESUME):
    file_content = get_text(file.file)

    if doc_type == RESUME:
        template = RESUME_JSON_TEMPLATE
    elif doc_type == VACANCY:
        template = VACANCY_JSON_TEMPLATE
    else:
        raise NameError(f'Unknown doc_type: {doc_type}')

    try:
        file_content = generate_json_from_text(
            file_content,
            template,
            OPENAI_API_KEY,
            doc_type)
    except Exception as exc:
        print(f'exc: {type(exc)}')

    return file_content
