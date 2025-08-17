from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Optional
import httpx
import re
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://aipipe.org/openrouter/v1"
OPENAI_MODEL = "openai/gpt-3.5-turbo"

app = FastAPI(title="TDS Data Analyst Agent")

@app.post("/api/")
async def analyze(
    questions_file: UploadFile = File(...),
    files: Optional[List[UploadFile]] = File(None)
):
    # Read questions.txt content
    questions_text = (await questions_file.read()).decode("utf-8")

    # List filenames of uploaded files
    filenames = [f.filename for f in (files or [])]

    # Prepare prompt
    prompt = f"""
You are a helpful Data Analyst Agent.

Task:
{questions_text}

If the task requires a plot, generate it using matplotlib and include the plot as a base64 encoded data URI string like "data:image/png;base64,...".

Respond only in JSON format (array or object as appropriate).
"""

    # Call LLM API
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful data analyst."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
        )

    if response.status_code != 200:
        return JSONResponse(
            status_code=500,
            content={"error": f"LLM API error {response.status_code}: {response.text}"},
        )

    answer_text = response.json()["choices"][0]["message"]["content"]

    # Extract references (URLs)
    references = re.findall(r"http[s]?://\S+", answer_text)

    # Extract first base64 image URI if any
    base64_match = re.search(r"(data:image\/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+)", answer_text)
    chart_base64 = base64_match.group(1) if base64_match else None

    return {
        "answer": answer_text,
        "references": references,
        "chart_base64": chart_base64,
        "other_files_received": filenames,
    }

@app.get("/")
async def root():
    return {"message": "TDS Data Analyst Agent API is running!"}
