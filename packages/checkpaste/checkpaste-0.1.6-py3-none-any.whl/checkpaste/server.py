from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import shutil

app = FastAPI(title="checkpaste Server")
# ... (existing code) ...

@app.post("/file")
async def upload_file(file: UploadFile = File(...)):
    # ... (existing upload code) ...
    try:
        file_location = f"{file.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"info": f"file '{file.filename}' saved at '{file_location}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{filename}")
def download_file(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/files")
def list_files():
    # Simple listing of files in current directory (excluding hidden/system files if possible)
    files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.startswith('.')]
    return {"files": files}
