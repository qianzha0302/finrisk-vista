from dotenv import load_dotenv

load_dotenv()

class Config:
    STORAGE_PATH = "processed_docs"
    VECTORSTORE_PATH = "vectorstores"
    WKHTMLTOPDF_PATH = "/usr/local/bin/wkhtmltopdf"
    TEMPLATE_PATH = "templates"
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150
    DEFAULT_MODEL = "gpt-4o"