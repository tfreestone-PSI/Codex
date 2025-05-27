import base64
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from openai import OpenAI
import threading

# ── OpenAI client ──────────────────────────────────────────────
OPENAI_API_KEY = {your_Key_here}
client = OpenAI(api_key=OPENAI_API_KEY)
MODEL_NAME = "gpt-image-1" # adjust if you use a different model

# ── Tkinter app ────────────────────────────────────────────────
class ImageGenGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpenAI Image Generator")
        self.geometry("600x650")

        # Prompt label + text box
        ttk.Label(self, text="Image prompt:").pack(anchor="w", padx=8, pady=(8, 0))
        self.prompt_text = tk.Text(self, height=4, wrap="word")
        self.prompt_text.pack(fill="x", padx=8, pady=(0, 8))
        self.prompt_text.insert("1.0",
            "A children's book drawing of a veterinarian using a stethoscope "
            "to listen to the heartbeat of a baby otter."
        )

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=4)
        self.gen_btn  = ttk.Button(btn_frame, text="Generate", command=self.generate_image)
        self.save_btn = ttk.Button(btn_frame, text="Save…",    command=self.save_image, state="disabled")
        self.gen_btn.grid(row=0, column=0, padx=4)
        self.save_btn.grid(row=0, column=1, padx=4)

        # Canvas to display the image
        self.canvas = tk.Canvas(self, width=512, height=512, bg="light gray")
        self.canvas.pack(padx=8, pady=8)

        # Holders for current image
        self.current_image_bytes = None   # raw PNG bytes
        self.current_tk_image    = None   # PhotoImage reference

    # ── OpenAI call ──────────────────────────────────────────
    # ── non-blocking image generation ──────────────────────────
    def generate_image(self):
        prompt = self.prompt_text.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("No prompt", "Please enter a prompt.")
            return

        # UI feedback
        self.gen_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.canvas.delete("all")
        self.canvas.create_text(256, 256, text="Generating…",
                                font=("TkDefaultFont", 20))

        # run the slow OpenAI call in a background thread
        threading.Thread(target=self._worker, args=(prompt,), daemon=True).start()

    # --------------- background thread -------------------------
    def _worker(self, prompt: str):
        try:
            result    = client.images.generate(model=MODEL_NAME, prompt=prompt)
            img_bytes = base64.b64decode(result.data[0].b64_json)
            self.after(0, lambda b=img_bytes: self._render(b))          # back to GUI
        except Exception as e:
            self.after(0, lambda err=e: self._worker_failed(err))       # back to GUI

    # --------------- GUI-thread helpers ------------------------
    def _render(self, img_bytes: bytes):
        self.current_image_bytes = img_bytes
        pil_img = Image.open(io.BytesIO(img_bytes))
        pil_img.thumbnail((512, 512))
        self.current_tk_image = ImageTk.PhotoImage(pil_img)

        self.canvas.config(width=pil_img.width, height=pil_img.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.current_tk_image)

        self.save_btn.config(state="normal")
        self.gen_btn.config(state="normal")

    def _worker_failed(self, err: Exception):
        messagebox.showerror("Error", f"Image generation failed:\n{err}")
        self.canvas.delete("all")
        self.gen_btn.config(state="normal")

    # ── Save dialog ──────────────────────────────────────────
    def save_image(self):
        if not self.current_image_bytes:
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
            title="Save generated image"
        )
        if file_path:
            try:
                with open(file_path, "wb") as f:
                    f.write(self.current_image_bytes)
                messagebox.showinfo("Saved", f"Image saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save failed", str(e))


if __name__ == "__main__":
    ImageGenGUI().mainloop()
