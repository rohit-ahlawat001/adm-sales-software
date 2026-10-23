import json
import tempfile
from pathlib import Path

import whisper
from fastapi import FastAPI, File, Form, UploadFile
# from fastapi.responses import JSONResponse
from pydantic import BaseModel, field

from app.rag import ask_question

app = FastAPI()
whisper_model = whisper.load_model("base")

class chatRequest(BaseModel):
    question: str
    history: list[dict] = field(default_factory=list)

@app.post("/chat")
async def chat(request: chatRequest):
    response = ask_question(request.question, request.history)
    return {"response": response}

@app.post("/voice")
async def voice(
      file: UploadFile = File(...),
      history: str = Form("[]"),
  ):
      history_messages = json.loads(history)

      with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
          audio_file.write(await file.read())
          audio_path = Path(audio_file.name)

      try:
          result = whisper_model.transcribe(str(audio_path))
          question = result["text"].strip()
          answer = ask_question(question, history_messages)
          return {"question": question, "answer": answer}
      finally:
          audio_path.unlink(missing_ok=True)