import fitz 
import re

def extract_text_from_pdf(file_bytes : bytes) -> str:
    """
    Takes the raw bytes of a PDF file and returns the extracted, cleaned text.
    """

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        extract_text = ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            extract_text += page.get_text()

        cleaned_text = re.sub(r'\s+',' ',extract_text).strip()

        if len(cleaned_text) > 120000:
            cleaned_text = cleaned_text[:120000]

        return cleaned_text
    
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""
    