import cv2
import torch
from ultralytics import YOLO
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from pynput import keyboard
from googletrans import Translator
import tkinter.font as tkFont

# Load YOLO model
model = YOLO("model/model.pt")
class_names = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Colors for each class
class_colors = {
    "A": (0, 0, 255), "B": (0, 255, 0), "C": (255, 0, 0), "D": (255, 255, 0), "E": (0, 255, 255),
    "F": (255, 0, 255), "G": (128, 0, 0), "H": (0, 128, 0), "I": (0, 0, 128), "J": (128, 128, 0),
    "K": (0, 128, 128), "L": (128, 0, 128), "M": (192, 192, 192), "N": (255, 165, 0),
    "O": (255, 69, 0), "P": (255, 105, 180), "Q": (255, 228, 181), "R": (139, 0, 0),
    "S": (0, 139, 139), "T": (139, 69, 19), "U": (255, 215, 0), "V": (138, 43, 226),
    "W": (255, 255, 255), "X": (169, 169, 169), "Y": (255, 255, 224), "Z": (70, 130, 180)
}

# Camera and UI
camera = cv2.VideoCapture(0)
root = Tk()
root.title("ASL to Kannada Translator")
root.geometry("600x700")  # Optional fixed size

# Font fallback for Kannada
available_fonts = list(tkFont.families())
kannada_fonts = ["Tunga", "Nudi", "Nirmala UI", "Kartika"]
used_font = next((f for f in kannada_fonts if f in available_fonts), "Helvetica")

# Initialize vars
stop_live_feed = False
sentence = ""
current_word = ""
translator = Translator()
translated_sentence = ""

# -------------------- SCROLLABLE CANVAS SETUP --------------------
main_canvas = Canvas(root)
main_scrollbar = Scrollbar(root, orient=VERTICAL, command=main_canvas.yview)
main_frame = Frame(main_canvas)

main_frame.bind(
    "<Configure>",
    lambda e: main_canvas.configure(
        scrollregion=main_canvas.bbox("all")
    )
)

main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
main_canvas.configure(yscrollcommand=main_scrollbar.set)

main_canvas.pack(side=LEFT, fill=BOTH, expand=True)
main_scrollbar.pack(side=RIGHT, fill=Y)
# -----------------------------------------------------------------

# UI Components inside scrollable frame
image_label = Label(main_frame)
image_label.pack(pady=10)

sentence_label = Label(main_frame, text="", font=("Helvetica", 16), width=40, height=1)
sentence_label.pack(pady=10)

translated_label = Label(main_frame, text="", font=(used_font, 16), fg="green", width=40, height=1)
translated_label.pack(pady=10)

# Translate Button
def translate_to_kannada():
    global translated_sentence, stop_live_feed
    stop_live_feed = True
    camera.release()
    image_label.configure(image=None)

    # Fix: remove spaces between characters
    cleaned_sentence = "".join(sentence.strip().split())  # instead of "K I L L", becomes "KILL"

    try:
        translated = translator.translate(cleaned_sentence, dest='kn')
        translated_sentence = translated.text
    except Exception:
        translated_sentence = "Translation Error"

    translated_label.config(text=translated_sentence)


translate_button = Button(main_frame, text="Translate to Kannada", font=("Helvetica", 14),
                          command=translate_to_kannada, bg="#2ecc71", fg="white")
translate_button.pack(pady=10)

# Restart Camera Button
def restart_camera():
    global stop_live_feed, camera
    camera = cv2.VideoCapture(0)
    stop_live_feed = False
    translated_label.config(text="")
    show_live_feed()

restart_button = Button(main_frame, text="Restart Camera", font=("Helvetica", 14),
                        command=restart_camera, bg="#3498db", fg="white")
restart_button.pack(pady=5)

# Webcam Feed
def show_live_feed():
    global current_word
    ret, frame = camera.read()
    if not ret:
        return

    results = model(frame, conf=0.25)

    for box, cls in zip(results[0].boxes.xyxy, results[0].boxes.cls):
        x1, y1, x2, y2 = box.tolist()
        cls = int(cls)
        label = class_names[cls]
        color = class_colors.get(label, (255, 255, 255))
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        current_word = label

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    img_tk = ImageTk.PhotoImage(image=img)

    image_label.img_tk = img_tk
    image_label.configure(image=img_tk)

    if not stop_live_feed:
        root.after(10, show_live_feed)

# Keyboard Listener
def on_press(key):
    global sentence, current_word
    try:
        if key == keyboard.Key.enter:
            if sentence:
                sentence += " " + current_word
            else:
                sentence += current_word
            current_word = ""
        elif key in [keyboard.Key.space, keyboard.Key.tab]:
            sentence += " "
            current_word = ""
        elif key == keyboard.Key.backspace:
            words = sentence.strip().split()
            sentence = " ".join(words[:-1]) if words else ""
            current_word = ""
        sentence_label.config(text=" ".join(sentence.strip().split()))
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

# Start feed
show_live_feed()
root.mainloop()
