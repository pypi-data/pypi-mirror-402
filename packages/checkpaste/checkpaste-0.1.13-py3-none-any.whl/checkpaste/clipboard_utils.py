import sys
import os
import io
import time
import subprocess
import shutil
from typing import List, Optional, Tuple, Any

# Platform flags
IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Platform specific imports
if IS_WIN:
    try:
        import win32clipboard
        import win32con
        from PIL import Image, ImageGrab
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False
    try:
        from PIL import Image, ImageGrab
    except ImportError:
        pass

def get_clipboard_content() -> Tuple[str, Any]:
    """
    Returns (type, content)
    type: "text", "image", "files", or None
    """
    
    # --- LINUX ---
    if IS_LINUX:
        return _get_linux_clipboard()

    # --- MACOS ---
    if IS_MAC:
        return _get_mac_clipboard()

    # --- WINDOWS ---
    if IS_WIN and HAS_WIN32:
        return _get_windows_clipboard()
    
    # Fallback to text (pyperclip is cross-platform for text)
    try:
        import pyperclip
        text = pyperclip.paste()
        if text:
            return "text", text
    except:
        pass
    
    return None, None

def set_clipboard_files(paths: List[str]):
    """
    Puts a list of file paths onto the clipboard.
    """
    if IS_WIN:
        _set_windows_files(paths)
    elif IS_LINUX:
        _set_linux_files(paths)
    elif IS_MAC:
        _set_mac_files(paths)

def set_clipboard_image(image_data: bytes):
    """
    Puts PNG bytes onto the clipboard as an Image.
    """
    if IS_WIN:
        _set_windows_image(image_data)
    elif IS_LINUX:
        _set_linux_image(image_data)
    elif IS_MAC:
        _set_mac_image(image_data)


# ---------------- INTERNAL PLATFORM IMPLEMENTATIONS ----------------

def _get_windows_clipboard():
    try:
        win32clipboard.OpenClipboard()
        
        # 1. Check for Files (CF_HDROP)
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
            files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
            win32clipboard.CloseClipboard()
            if files:
                return "files", files
            return None, None

        win32clipboard.CloseClipboard()
        
        # 2. Check for Images (Pillow)
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
             b = io.BytesIO()
             # Optimize: Convert to RGB if needed, or keep original
             img.save(b, format="PNG")
             return "image", b.getvalue()
        elif isinstance(img, list):
            return "files", img
        
        # 3. Text
        import pyperclip
        text = pyperclip.paste()
        if text:
            return "text", text

    except Exception as e:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        print(f"Win Clipboard Error: {e}")
    return None, None

def _set_windows_files(paths: List[str]):
    if not HAS_WIN32: return
    try:
        import struct
        valid_paths = [os.path.abspath(p) for p in paths if os.path.exists(p)]
        if not valid_paths: return
        
        # DWORD(I), LONG(l), LONG(l), BOOL(i), BOOL(i)
        dropfiles_header = struct.pack("Iiiii", 20, 0, 0, 0, 1)
        files_data = ("\0".join(valid_paths) + "\0\0").encode("utf-16-le")
        data = dropfiles_header + files_data
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
        win32clipboard.CloseClipboard()
    except Exception as e:
        print(f"Win Set Files Error: {e}")

def _set_windows_image(image_data: bytes):
    if not HAS_WIN32: return
    try:
        img = Image.open(io.BytesIO(image_data))
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:] # DIB
        output.close()
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        win32clipboard.CloseClipboard()
    except Exception as e:
        print(f"Win Set Image Error: {e}")

# --- LINUX UTIL (xclip) ---
def _check_xclip():
    return shutil.which('xclip') is not None

def _get_linux_clipboard():
    if not _check_xclip():
        # Fallback to just text if xclip missing
        try:
            import pyperclip
            return "text", pyperclip.paste()
        except: return None, None

    try:
        # Check targets
        out = subprocess.check_output(['xclip', '-selection', 'clipboard', '-t', 'TARGETS', '-o'], stderr=subprocess.DEVNULL)
        targets = out.decode('utf-8', errors='ignore')
        
        # Priority: Files > Image > Text
        
        if 'text/uri-list' in targets:
            out = subprocess.check_output(['xclip', '-selection', 'clipboard', '-t', 'text/uri-list', '-o'], stderr=subprocess.DEVNULL)
            uris = out.decode('utf-8').strip().splitlines()
            paths = []
            for uri in uris:
                if uri.startswith('file://'):
                    # Decode URL (%20 etc)
                    from urllib.parse import unquote
                    path = unquote(uri[7:]).strip()
                    if os.path.exists(path):
                        paths.append(path)
            if paths:
                return "files", paths

        if 'image/png' in targets or 'image/jpeg' in targets:
            # Prefer PNG
            fmt = 'image/png' if 'image/png' in targets else 'image/jpeg'
            data = subprocess.check_output(['xclip', '-selection', 'clipboard', '-t', fmt, '-o'], stderr=subprocess.DEVNULL)
            if data:
                return "image", data

        # Text
        import pyperclip
        text = pyperclip.paste()
        if text: return "text", text

    except Exception:
        pass
    return None, None

def _set_linux_files(paths: List[str]):
    if not _check_xclip(): return
    try:
        from urllib.parse import quote
        uris = []
        for p in paths:
            # Need absolute path
            abs_p = os.path.abspath(p)
            uris.append(f"file://{quote(abs_p)}")
        
        data = "\r\n".join(uris).encode('utf-8')
        p = subprocess.Popen(['xclip', '-selection', 'clipboard', '-t', 'text/uri-list', '-i'], stdin=subprocess.PIPE)
        p.communicate(input=data)
    except Exception as e:
        print(f"Linux Set Files Error: {e}")

def _set_linux_image(image_data: bytes):
    if not _check_xclip(): return
    try:
        p = subprocess.Popen(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i'], stdin=subprocess.PIPE)
        p.communicate(input=image_data)
    except Exception as e:
        print(f"Linux Set Image Error: {e}")

# --- MAC UTIL (osascript) ---
def _get_mac_clipboard():
    try:
        # 1. Use Pillow for Image (easiest)
        # Note: Pillow on Mac uses pbpaste or specialized C calls.
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
             b = io.BytesIO()
             try:
                 img.save(b, format="PNG")
             except:
                 # Sometimes grabclipboard returns a path or something else?
                 pass
             return "image", b.getvalue()
        elif isinstance(img, list):
            # Pillow might handle files on Mac too?
            return "files", img
        
        # 2. Check for Files via AppleScript if Pillow checks failed
        # 'clipboard info' might reveal class
        # But simpler: try to get list of files
        # osascript -e 'get class of (the clipboard)' -> list?
        # Let's rely on Pillow for Mac (it supports files/images well).
        
        # 3. Text
        import pyperclip
        text = pyperclip.paste()
        if text: return "text", text
        
    except Exception as e:
        print(f"Mac Clipboard Error: {e}")
    return None, None

def _set_mac_files(paths: List[str]):
    # AppleScript: set the clipboard to {POSIX file "a", POSIX file "b"}
    try:
        posix_files = ', '.join([f'POSIX file "{os.path.abspath(p)}"' for p in paths])
        script = f'set the clipboard to {{{posix_files}}}'
        subprocess.run(['osascript', '-e', script])
    except Exception as e:
        print(f"Mac Set Files Error: {e}")

def _set_mac_image(image_data: bytes):
    # This is tricky with AppleScript directly from bytes.
    # Approach: Save to temp file -> set clipboard to POSIX file -> convert to image in swift/obj-c?
    # Or 'set the clipboard to (read (POSIX file "/tmp/image.png") as TIFF picture)'
    try:
        import tempfile
        # Write to temp png
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tf.write(image_data)
            tf.flush()
            tmp_path = tf.name
        
        script = f'set the clipboard to (read (POSIX file "{tmp_path}") as «class PNGf»)'
        subprocess.run(['osascript', '-e', script])
        
        # Cleanup? If we delete immediately, clipboard might lose it? 
        # Actually 'read' reads it into memory.
        time.sleep(0.1)
        os.unlink(tmp_path)
    except Exception as e:
        print(f"Mac Set Image Error: {e}")
