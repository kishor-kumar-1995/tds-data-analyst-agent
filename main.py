from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Optional
import httpx
import re
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("AIPIPE_TOKEN")
OPENAI_BASE_URL = "https://aipipe.org/openrouter/v1"
OPENAI_MODEL = "openai/gpt-3.5-turbo"

app = FastAPI(title="Generic Data Analyst Agent")

def is_valid_base64_image(data_uri):
    if not data_uri.startswith("data:image/png;base64,"):
        return False
    try:
        raw = base64.b64decode(data_uri.split(",")[1])
        return len(raw) < 100_000
    except Exception:
        return False

@app.post("/api/")
async def analyze(
    questions_file: UploadFile = File(...),
    files: Optional[List[UploadFile]] = File(None)
):
    # Read questions.txt content
    questions_text = (await questions_file.read()).decode("utf-8")

    # Read all other files
    file_descriptions = ""
    for f in files or []:
        content = (await f.read()).decode("utf-8", errors="ignore")
        file_descriptions += f"\nFile: {f.filename}\n{content}\n"

    # Prepare prompt
    prompt = f"""
You are a helpful Data Analyst Agent.

Task:
{questions_text}

Here are the uploaded files:
{file_descriptions}

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

    # Extract base64 image if present
    base64_match = re.search(r"(data:image\/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+)", answer_text)
    chart_base64 = base64_match.group(1) if base64_match and is_valid_base64_image(base64_match.group(1)) else None

    return {
        "answer": answer_text,
        "references": re.findall(r"http[s]?://\S+", answer_text),
        "chart_base64": chart_base64,
        "other_files_received": [f.filename for f in (files or [])],
    }

@app.get("/api/")
async def api_get():
    return JSONResponse(
        status_code=405,
        content={"error": "Method Not Allowed. Use POST with files."}
    )

@app.get("/")
async def root():
    return {"message": "Generic Data Analyst Agent API is running!"}
