from io import StringIO
import requests

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from openai import OpenAI


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
        "amount": null,
        "currency": null
    },
    "education_level": "",
    "education": [
        {
            "year": null,
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
            "end": null,
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
        "to": null,
        "from": null,
        "currency": "",
        "gross": null
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


def generate_json_from_text(text, json_template, openai_api_key, doc_type='резюме'):
    client = OpenAI(api_key=openai_api_key)

    sys_prompt = f"Преобразуй текст {doc_type} в JSON.\nJSON шаблон: {json_template}"
    prompt = f"{doc_type}: {text}"

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        stream=True,
    )

    result = ''
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            result += chunk.choices[0].delta.content

    return result


def generate_json_from_file(pdf_file, json_template, openai_api_key, doc_type='резюме'):
    text = get_text(pdf_file)
    json = generate_json_from_text(text, json_template, openai_api_key, doc_type)
    return json