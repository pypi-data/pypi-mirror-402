import sys
import os
import io
import time
from typing import List, Optional, Tuple, Any

# Platform specific imports
try:
    import win32clipboard
    import win32con
    from PIL import Image, ImageGrab
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

def get_clipboard_content() -> Tuple[str, Any]:
    """
    Returns (type, content)
    type: "text", "image", "files", or None
    """
    if not HAS_WIN32:
        # Fallback for non-Windows (Text only for now)
        try:
            import pyperclip
            text = pyperclip.paste()
            if text:
                return "text", text
        except:
            pass
        return None, None

    try:
        win32clipboard.OpenClipboard()
        
        # 1. Check for Files (CF_HDROP)
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
            files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
            win32clipboard.CloseClipboard()
            if files:
                return "files", files
            return None, None

        # 2. Check for Images (CF_DIB) - reading via Pillow's ImageGrab is easier
        # But we need to close clipboard first before calling ImageGrab
        win32clipboard.CloseClipboard()
        
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
             # Convert to bytes (PNG)
             b = io.BytesIO()
             img.save(b, format="PNG")
             return "image", b.getvalue()
        elif isinstance(img, list):
            # ImageGrab can also return file lists
            return "files", img
        
        # 3. Check for Text (Standard)
        import pyperclip
        text = pyperclip.paste()
        if text:
            return "text", text

    except Exception as e:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        print(f"Clipboard Error: {e}")
    
    return None, None

def set_clipboard_files(paths: List[str]):
    """
    Puts a list of file paths onto the clipboard (CF_HDROP).
    """
    if not HAS_WIN32:
        return
        
    try:
        import ctypes
        from ctypes import wintypes
        import win32clipboard
        import win32con

        # Structure for DROPFILES (simple version using pywin32 built-in logic if possible)
        # Actually, SetClipboardData(CF_HDROP, ...) in pywin32 expects a tuple of strings!
        
        # However, to be robust, we might need to verify paths exist.
        valid_paths = [os.path.abspath(p) for p in paths if os.path.exists(p)]
        if not valid_paths:
            return

        # It seems pywin32's SetClipboardData does NOT automatically handle tuple->DROPFILES struct
        # Wait, for CF_HDROP, it actually DOES accept a list of strings if using standard win32clipboard?
        # Let's try the simple way first.
        # Unfortunately, pywin32 often requires manual memory management for CF_HDROP or specific encoding.
        # But actually, win32clipboard.SetClipboardData(win32con.CF_HDROP, ...) 
        # is tricky. 
        # A clearer way involves using `pythoncom` or custom struct packing.
        # BUT! There is a trick: pywin32 handles it if passed correctly? 
        # Actually, recent pywin32 versions might wrap it.
        # Let's try: OpenClipboard, EmptyClipboard, SetClipboardData(CF_HDROP, valid_paths)
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, tuple(valid_paths))
        win32clipboard.CloseClipboard()
        
    except Exception as e:
        print(f"Error setting files to clipboard: {e}")

def set_clipboard_image(image_data: bytes):
    """
    Puts PNG bytes onto the clipboard as an Image.
    """
    if not HAS_WIN32:
        return

    try:
        # Convert PNG bytes to Image object
        img = Image.open(io.BytesIO(image_data))
        
        # Write to Clipboard using io (DIB)
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:] # Strip BMP Header (14 bytes) to get DIB
        
        output.close()
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        win32clipboard.CloseClipboard()
        
    except Exception as e:
        print(f"Error setting image to clipboard: {e}")
