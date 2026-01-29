from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="checkpaste Server")

# In-memory storage for the clipboard
clipboard_content = {"text": ""}

class ClipboardItem(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "checkpaste server is running"}

@app.get("/clipboard")
def get_clipboard():
    return clipboard_content

@app.post("/clipboard")
def set_clipboard(item: ClipboardItem):
    clipboard_content["text"] = item.text
    return {"message": "Clipboard updated", "content": item.text}

@app.post("/file")
async def upload_file(file: UploadFile = File(...)):
    # Save uploaded file to the current directory (or a downloads folder)
    # For MVP, saving to current working directory of the server
    try:
        file_location = f"{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        return {"info": f"file '{file.filename}' saved at '{file_location}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
