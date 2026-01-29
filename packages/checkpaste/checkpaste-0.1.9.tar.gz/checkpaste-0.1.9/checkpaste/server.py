from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
import shutil
import time
from typing import Optional

# Global state
app_state = {
    "password": None,
    "zeroconf": None,
    "service_info": None
}

app = FastAPI(title="checkpaste Server")

# In-memory storage for the clipboard
clipboard_content = {
    "text": "",
    "timestamp": 0.0
}

class ClipboardItem(BaseModel):
    text: str

# Middleware for Authentication
@app.middleware("http")
async def check_auth(request: Request, call_next):
    if app_state["password"]:
        # Skip auth for root endpoint (health check) or public file serving if desired?
        # For now, protect everything except root.
        if request.url.path != "/" and request.method != "OPTIONS":
            auth_header = request.headers.get("X-Checkpaste-Auth")
            if auth_header != app_state["password"]:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    # Read configuration from Environment Variables (passed from CLI)
    password = os.getenv("CHECKPASTE_PASSWORD")
    name = os.getenv("CHECKPASTE_NAME")
    public = os.getenv("CHECKPASTE_PUBLIC")
    
    if password:
        app_state["password"] = password
    
    # Register Zeroconf service if a name is provided
    if name:
        import asyncio
        from checkpaste.discovery import register_service
        
        port = int(os.getenv("CHECKPASTE_PORT", 8000))
        
        # Zeroconf registration can block the event loop, so run it in a thread
        loop = asyncio.get_event_loop()
        zeroconf_instance, info = await loop.run_in_executor(None, register_service, name, port)
        
        app_state["zeroconf"] = zeroconf_instance
        app_state["service_info"] = info

@app.on_event("shutdown")
def shutdown_event():
    if app_state["zeroconf"]:
        app_state["zeroconf"].unregister_service(app_state["service_info"])
        app_state["zeroconf"].close()

@app.get("/")
def read_root():
    return {"message": "checkpaste server is running"}

@app.get("/clipboard")
def get_clipboard():
    return clipboard_content

@app.post("/clipboard")
def set_clipboard(item: ClipboardItem):
    clipboard_content["text"] = item.text
    clipboard_content["timestamp"] = time.time()
    return {"message": "Clipboard updated", "content": item.text, "timestamp": clipboard_content["timestamp"]}

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
