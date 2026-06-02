import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str


@app.get("/")
async def root():
    return {"message": "Backend running"}


@app.post("/chat")
async def chat(data: ChatRequest):

    def generate():
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": data.prompt
                    }
                ],
                stream=True
            )

            for chunk in completion:
                try:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    if delta is None:
                        continue

                    content = delta.content

                    if content is not None:
                        yield content

                except Exception:
                    continue

        except Exception as e:
            yield f"\nERROR: {str(e)}"

    # BUG FIX: return StreamingResponse here, in chat(), not inside generate()
    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )
