import fitz
import os
from markitdown import MarkItDown
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("LLM_ENDPOINT")
)
md = MarkItDown(llm_client=client, llm_model=os.getenv("MODEL"))

doc = fitz.open("data/landing/legal/luat116-2025_an_ninh_mang.pdf")
print("Total pages:", len(doc))

# Take just the first page to test
page = doc[0]
pix = page.get_pixmap()
pix.save("test_page_0.png")

result = md.convert("test_page_0.png")
print("--- Extracted ---")
print(result.text_content)
