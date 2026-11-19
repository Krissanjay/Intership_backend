
import PyPDF2
from docx import Document
import os


def extract_text_from_pdf(file_path):
    text = ""

    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        print("PDF pages:", len(reader.pages))

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            print(
                f"Page {page_number} extracted characters:",
                len(page_text)
            )

            text += page_text + "\n"

    return text.strip()


def extract_text_from_docx(file_path):
    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text.strip()


def extract_resume_text(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    elif extension == ".docx":
        return extract_text_from_docx(file_path)

    else:
        raise ValueError("Only PDF and DOCX files are supported")
