import os
from typing import List

PDF_SUPPORT_AVAILABLE = False
try:
    import pdfplumber
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    PDF_SUPPORT_AVAILABLE = True
except ImportError:
    pdfplumber = None
    RecursiveCharacterTextSplitter = None


class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if not PDF_SUPPORT_AVAILABLE:
            raise ImportError("pdfplumber and langchain-text-splitters are required for PDF processing")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        text = ""
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def chunk_text(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)

    def process_pdf(self, pdf_path: str) -> List[dict]:
        text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(text)
        return [
            {"content": chunk, "source": os.path.basename(pdf_path), "index": i}
            for i, chunk in enumerate(chunks)
        ]

    def process_pdf_bytes(self, pdf_bytes: bytes, source_name: str = "document") -> List[dict]:
        text = self.extract_text_from_bytes(pdf_bytes)
        chunks = self.chunk_text(text)
        return [
            {"content": chunk, "source": source_name, "index": i}
            for i, chunk in enumerate(chunks)
        ]