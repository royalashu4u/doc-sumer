import os
import json
import re
from PyPDF2 import PdfReader


def load_env_api_key() -> str:
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "API":
                            return v.strip()
    return os.getenv("API")


def parse_json_safely(content: str) -> dict:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError("Response from model was not in a valid JSON structure.")


def extract_text(pdf_file) -> str:
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to read PDF file: {str(e)}")


def get_ai_summary(text: str, api_key: str = None, language: str = "English") -> dict:
    if not api_key:
        api_key = load_env_api_key()
    if not api_key:
        raise ValueError("API key is required. Set API in .env file.")

    clean_text = re.sub(r'\s+', ' ', text).strip()

    from openai import OpenAI
    client = OpenAI(
        base_url="https://gen.pollinations.ai/v1",
        api_key=api_key
    )

    prompt = f"""You are an expert document analyst.
Analyze the following document and provide a structured JSON response.
Provide the entire analysis in the {language} language. Keep the JSON keys in English, but the values (sentences/bullets) must be in {language}.

The JSON response MUST contain these exact keys:
1. "executive_summary": A paragraph of about 100 words summarizing the main purpose, findings, and conclusion of the document in {language}.
2. "key_insights": An array of 3-5 strings, each representing a key insight or major takeaway in {language}.
3. "action_items": An array of 3-5 strings, each representing a clear, actionable task or next step derived from the document in {language}.
4. "risks_notes": An array of 2-3 strings, each representing a significant risk, warning, or important caveat mentioned or implied in the document in {language}.

Document to analyze:
{clean_text[:6000]}
"""

    try:
        response = client.chat.completions.create(
            model="openai",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a professional document analysis assistant that outputs strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        result_content = response.choices[0].message.content
    except Exception:
        response = client.chat.completions.create(
            model="openai",
            messages=[
                {"role": "system", "content": "You are a professional document analysis assistant that outputs strictly valid JSON. Return ONLY the JSON object, with no other text or explanation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        result_content = response.choices[0].message.content

    return parse_json_safely(result_content)


def query_pdf_data(text: str, user_question: str, history: list = None, api_key: str = None) -> str:
    if not api_key:
        api_key = load_env_api_key()
    if not api_key:
        raise ValueError("API key is required. Set API in .env file.")

    from openai import OpenAI
    client = OpenAI(
        base_url="https://gen.pollinations.ai/v1",
        api_key=api_key
    )

    clean_text = re.sub(r'\s+', ' ', text).strip()
    context = clean_text[:6000]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI Document Assistant. You are given the text of a PDF document. "
                "Answer the user's question accurately based ONLY on the provided document context. "
                "If the answer cannot be found in the document, politely say so. Do not make up facts. "
                "Keep your response concise and structured."
            )
        },
        {
            "role": "system",
            "content": f"DOCUMENT CONTENT:\n{context}"
        }
    ]

    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_question})

    response = client.chat.completions.create(
        model="openai",
        messages=messages,
        temperature=0.5
    )
    return response.choices[0].message.content
