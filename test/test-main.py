import json  # <-- ADD THIS - it's missing!
import subprocess
import tempfile
import threading
import tkinter as tk
import tkinter.messagebox as messagebox
import webbrowser as wb
from queue import Queue
import customtkinter as ctk
import requests
from PIL import Image, ImageEnhance, ImageGrab, ImageTk
import  sys
import time

time = time(10)

screenshot = ImageGrab.grab()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class bigimagebox:
    def __init__(self, boxa):
        self.boxa = boxa
        self.boxa.attributes("-fullscreen", True)

        screen_width = self.boxa.winfo_screenwidth()
        screen_height = self.boxa.winfo_screenheight()

        self.canvas = tk.Canvas(
            self.boxa,
            width=screen_width,
            height=screen_height,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.focus_set()

        try:
            image = screenshot.resize((screen_width, screen_height), Image.LANCZOS)
            enhancer = ImageEnhance.Brightness(image)
            dimmed_image = enhancer.enhance(0.5)
            self.photo = ImageTk.PhotoImage(dimmed_image)

            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        except Exception as e:
            print(f"Error displaying image: {e}")
            messagebox.showerror("Image Error", f"Error processing image:\n{e}")
            self.canvas.configure(bg="black")

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.canvas.bind("<Escape>", lambda e: self.boxa.destroy())

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="red",
            width=2,
        )

    def on_move_press(self, event):
        curX, curY = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y

        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)

        if right - left < 5 or bottom - top < 5:
            messagebox.showwarning(
                "Selection Too Small", "Please draw a larger selection area."
            )
            return

        try:
            cropped = screenshot.crop((left, top, right, bottom))

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                cropped.save(tmp.name)
                self.tempfile_path = tmp.name

            self.boxa.destroy()

        except Exception as e:
            print(f"Cropping failed: {e}")
            messagebox.showerror(
                "Cropping Error", f"Failed to crop image:\n{e}"
            )


class bluat:
    def __init__(self, root, img_path):
        self.root = root
        self.img_path = img_path

        self.root.geometry("700x700")
        self.root.title("ScreenSearch")
        self.root.configure(fg_color="#1e1e2e")

        # ===== GRID LAYOUT =====
        self.root.grid_rowconfigure(1, weight=1)  # main area expands
        self.root.grid_columnconfigure(0, weight=1)

        # ===== TOOLBAR =====
        self.toolbar = ctk.CTkFrame(self.root, fg_color="#181825", height=40)
        self.toolbar.grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(
            self.toolbar,
            text="🔍 Search",
            command=self.search,
            fg_color="#89b4fa",
            hover_color="#74c7ec",
            width=100,
        ).pack(side="left", padx=5, pady=5)

        ctk.CTkButton(
            self.toolbar,
            text="📝 OCR",
            command=self.ocr,
            fg_color="#a6e3a1",
            hover_color="#94e2d5",
            width=100,
        ).pack(side="left", padx=5, pady=5)

        ctk.CTkButton(
            self.toolbar,
            text="🧹 Clear",
            command=self.clear_text,
            fg_color="#f38ba8",
            hover_color="#eba0ac",
            width=100,
        ).pack(side="left", padx=5, pady=5)

        self.main = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main.grid(row=1, column=0, sticky="nsew")

        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # Display image
        img = Image.open(self.img_path)
        self.ctk_img = ctk.CTkImage(img, size=(700, 300))

        self.image_label = ctk.CTkLabel(
            self.main,
            image=self.ctk_img,
            text="",
        )
        self.image_label.grid(row=0, column=0, pady=10)

        # Text area
        self.textbox = ctk.CTkTextbox(
            self.main, fg_color="#1a1b26", text_color="#c0caf5", corner_radius=10
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.textbox.configure(font=("JetBrains Mono", 12))

        # Status bar
        self.status = ctk.CTkLabel(
            self.root, text="✅ Ready", anchor="w", fg_color="#181825", height=25
        )
        self.status.grid(row=2, column=0, sticky="ew")

    def search(self):
        confirm = messagebox.askyesno(
            "Upload Image", "This will be uploaded to an external server. Continue?"
        )

        if confirm:
            self.status.configure(text="📤 Uploading for search...")
            try:
                YesImageMe(self.img_path)
                self.status.configure(text="🌐 Opened in browser")
            except Exception as e:
                self.status.configure(text=f"❌ Upload failed: {str(e)[:50]}")

    def ocr(self):
        self.status.configure(text="🔍 Running OCR...")
        threading.Thread(target=self._ocr_worker, daemon=True).start()

    def _ocr_worker(self):
        try:
            text = textmebro(self.img_path)
            text = format_text(text)
            self.root.after(0, self._update_textbox, text)
            self.root.after(0, lambda: self.status.configure(text="✅ OCR complete"))
        except Exception as e:
            self.root.after(0, lambda: self.status.configure(text=f"❌ OCR failed: {str(e)[:50]}"))
            self.root.after(0, lambda: self._update_textbox(f"Error: {str(e)}"))

    def _update_textbox(self, text):
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)

    def clear_text(self):
        self.textbox.delete("1.0", "end")
        self.status.configure(text="🧹 Cleared")


class YesImageMe:
    def __init__(self, img_path):
        self.img_path = img_path

        self.url = "https://tmpfiles.org/api/v1/upload"
        with open(self.img_path, "rb") as f:  # Fixed: use context manager
            responses = requests.post(self.url, files={"file": f})

        data = responses.json()
        url = data["data"]["url"]
        direct_url = url.replace("http://tmpfiles.org/", "https://tmpfiles.org/dl/")
        print(direct_url)

        link = f"https://imgops.com/{direct_url}"
        wb.open(link)


class osrthing:
    def __init__(self):
        self.process = None
        self.callback_queue = Queue()
        self.start_worker()

    def start_worker(self):
        """Start persistent OCR subprocess"""
        try:
            self.process = subprocess.Popen(
                ["python", "sub-osr-pro.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            # Start listener thread
            threading.Thread(target=self._listen, daemon=True).start()
            print("✅ OCR worker started", file=sys.stderr)
        except Exception as e:
            print(f"❌ Failed to start OCR worker: {e}", file=sys.stderr)

    def _listen(self):
        """Listen for responses from subprocess"""
        while True:
            try:
                line = self.process.stdout.readline()
                if not line:
                    print("OCR worker process ended", file=sys.stderr)
                    break
                try:
                    result = json.loads(line)
                    self.callback_queue.put(result)
                except json.JSONDecodeError:
                    print(f"Invalid JSON from worker: {line[:100]}", file=sys.stderr)
            except Exception as e:
                print(f"Error in listener: {e}", file=sys.stderr)
                break

    def ocr_async(self, img_path, callback):
        """Non-blocking OCR"""
        if not self.process or self.process.poll() is not None:
            callback("", "OCR worker not running")
            return
            
        request = json.dumps({"image_path": img_path})
        self.process.stdin.write(request + "\n")
        self.process.stdin.flush()

        # Check for result in callback queue
        def check_result():
            while True:
                try:
                    result = self.callback_queue.get(timeout=0.1)
                    if result:
                        # Handle both success and error cases
                        if result.get("success"):
                            callback(result.get("text", ""), None)
                        else:
                            callback("", result.get("error", "Unknown error"))
                        break
                except:
                    if self.process and self.process.poll() is not None:
                        callback("", "OCR process died")
                        break
                    continue

        threading.Thread(target=check_result, daemon=True).start()


# Global OCR manager
ocr_manager = osrthing()


def textmebro(img_path):
    """Synchronous wrapper for backward compatibility"""
    result_queue = Queue()

    def callback(text, error):
        result_queue.put((text, error))

    ocr_manager.ocr_async(img_path, callback)
    
    try:
        text, error = result_queue.get(timeout=30)  # 30 second timeout
        if error:
            return f"OCR Error: {error}"
        return text if text else "No text detected"
    except:
        return "OCR timeout - try again"


def format_text(text):
    """Clean up OCR text but preserve structure"""
    if not text:
        return "No text detected"
    
    # Don't strip aggressively - preserve code structure
    # Just remove excessive empty lines
    lines = text.split('\n')
    
    # Remove trailing empty lines but keep indentation
    while lines and not lines[-1].strip():
        lines.pop()
    
    # Remove leading empty lines
    while lines and not lines[0].strip():
        lines.pop(0)
    
    # Don't strip individual lines - preserve code indentation!
    # Just return joined lines
    return '\n'.join(lines)


if __name__ == "__main__":
    import sys  # Added for stderr printing
    
    boxa = tk.Tk()
    selector = bigimagebox(boxa)
    boxa.mainloop()

    if hasattr(selector, "tempfile_path"):
        root = ctk.CTk()
        ui = bluat(root, selector.tempfile_path)
        root.mainloop()
    else:
        print("No image selected - awkward...")
