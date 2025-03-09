import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
from tkinter import filedialog
import cv2
import numpy as np

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

SIZE = 10 
MOVE = 10 
colors = {
    1: "#DC143C", 2: "#4682B4", 3: "#8A2BE2", 4: "#FFD700", 5: "#FF69B4", 6: "#98c379"
}

# Morse code dictionaries
morse_code = {
    'A': '12', 'B': '2111', 'C': '2121', 'D': '211', 'E': '1', 'F': '1121', 'G': '221',
    'H': '1111', 'I': '11', 'J': '1222', 'K': '212', 'L': '1211', 'M': '22', 'N': '21',
    'O': '222', 'P': '1221', 'Q': '2212', 'R': '121', 'S': '111', 'T': '2', 'U': '112',
    'V': '1112', 'W': '122', 'X': '2122', 'Y': '2212', 'Z': '1122', '0': '22222',
    '1': '12222', '2': '11222', '3': '11122', '4': '11112', '5': '11111', '6': '21111',
    '7': '22111', '8': '22211', '9': '22221'
}

reverse_morse = {v: k.lower() for k, v in morse_code.items()}

def to_morse(input_str):
    result = ""
    for i, char in enumerate(input_str):
        if char == ' ':
            continue
        if char.isupper():
            result += "4"
        if char.upper() in morse_code:
            result += morse_code[char.upper()]
            result += '5' if (i + 1 < len(input_str) and input_str[i+1] == ' ') else '3'
    return result

def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (b, g, r)

BGR_START = hex_to_bgr("#abcdef") 
BGR_COLOR1, BGR_COLOR2, BGR_COLOR3 = hex_to_bgr(colors[1]), hex_to_bgr(colors[2]), hex_to_bgr(colors[3])
BGR_COLOR4, BGR_COLOR5 = hex_to_bgr(colors[4]), hex_to_bgr(colors[5])
BGR_GREEN = hex_to_bgr(colors[6]) 
BGR_END = hex_to_bgr("#fedcba") 

def color_matches(sample, target, tol=50):
    return all(abs(int(sample[i]) - target[i]) < tol for i in range(3))

class MorseCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("我的加密圖片")
        self.root.geometry("800x600")
        
        self.points = []
        self.loaded_image = None 
        self.image_tk = None
        
        self.main_frame = ctk.CTkFrame(root, fg_color="#242424")
        self.main_frame.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)
        
        self.top_frame = ctk.CTkFrame(self.main_frame, fg_color="#242424")
        self.top_frame.place(relx=0, rely=0, relwidth=1, relheight=0.18)
        
        self.left_input_frame = ctk.CTkFrame(self.top_frame, fg_color="#242424")
        self.left_input_frame.place(relx=0, rely=0, relwidth=0.48, relheight=1)
        self.left_entry = ctk.CTkEntry(self.left_input_frame, font=("Arial", 14), height=30, fg_color="white", text_color="black")
        self.left_entry.place(relx=0.5, rely=0.3, anchor="center", relwidth=0.8)
        self.left_entry.bind("<KeyRelease>", self.on_entry_change)
        self.export_button = ctk.CTkButton(self.left_input_frame, text="輸出圖片", command=self.export_image, fg_color="#4682B4", hover_color="#336699")
        self.export_button.place(relx=0.5, rely=0.7, anchor="center", relwidth=0.8)
        
        self.right_input_frame = ctk.CTkFrame(self.top_frame, fg_color="#242424")
        self.right_input_frame.place(relx=0.52, rely=0, relwidth=0.48, relheight=1)
        self.right_string_var = ctk.StringVar()
        self.right_entry = ctk.CTkEntry(self.right_input_frame, textvariable=self.right_string_var, font=("Arial", 14), height=30, state="readonly", fg_color="white", text_color="black")
        self.right_entry.place(relx=0.5, rely=0.3, anchor="center", relwidth=0.8)
        self.export_text_button = ctk.CTkButton(self.right_input_frame, text="輸出文字檔", command=self.export_text, fg_color="#4682B4", hover_color="#336699")
        self.export_text_button.place(relx=0.5, rely=0.7, anchor="center", relwidth=0.8)
        
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="#242424")
        self.bottom_frame.place(relx=0, rely=0.22, relwidth=1, relheight=0.78)
        
        self.canvas_frame = ctk.CTkFrame(self.bottom_frame, fg_color="white", border_width=2, corner_radius=8)
        self.canvas_frame.place(relx=0, rely=0, relwidth=0.48, relheight=1)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.offset_x = 0
        self.offset_y = 0
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B3-Motion>", self.on_right_drag)
        
        self.image_frame = ctk.CTkFrame(self.bottom_frame, fg_color="white", border_width=2, corner_radius=8)
        self.image_frame.place(relx=0.52, rely=0, relwidth=0.48, relheight=1)
        self.image_canvas = tk.Canvas(self.image_frame, bg="white", highlightthickness=0)
        self.image_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.image_canvas.bind("<Configure>", self.draw_image_placeholder)
        self.image_canvas.bind("<Button-1>", self.open_image)
    
    def on_entry_change(self, event=None):
        self.draw_path()
    
    def on_right_click(self, event):
        self.last_x = event.x
        self.last_y = event.y
    
    def on_right_drag(self, event):
        delta_x = event.x - self.last_x
        delta_y = event.y - self.last_y
        self.offset_x += delta_x
        self.offset_y += delta_y
        self.last_x = event.x
        self.last_y = event.y
        self.canvas.move("all", delta_x, delta_y)
    
    def draw_path(self):
        self.canvas.delete("all")
        self.points = []
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        current_x = width // 2 + self.offset_x
        current_y = height // 2 + self.offset_y
        
        self.points.append((current_x, current_y, "#abcdef"))
        self.canvas.create_rectangle(current_x, current_y, current_x+SIZE, current_y+SIZE, fill="#abcdef")
        
        visited = {(current_x, current_y)}
        directions = [(MOVE, 0), (0, -MOVE), (-MOVE, 0), (0, MOVE)]
        direction_index = 0
        morse_str = to_morse(self.left_entry.get())
        i = 1
        for char in morse_str:
            try:
                steps = int(char)
            except:
                continue
            if steps == 0:
                continue
            dx, dy = directions[direction_index]
            for _ in range(steps):
                next_x = current_x + dx
                next_y = current_y + dy
                while (next_x, next_y) in visited:
                    current_x = next_x
                    current_y = next_y
                    next_x = current_x + dx
                    next_y = current_y + dy
                color = colors[i]
                self.canvas.create_rectangle(next_x, next_y, next_x+SIZE, next_y+SIZE, fill=color)
                self.points.append((next_x, next_y, color))
                visited.add((next_x, next_y))
                i = (i % 5) + 1
                current_x, current_y = next_x, next_y
            direction_index = (direction_index + 1) % 4
            self.canvas.create_rectangle(current_x, current_y, current_x+SIZE, current_y+SIZE, fill=colors[6])
            self.points.append((current_x, current_y, colors[6]))
    
    def draw_image_placeholder(self, event=None):
        if self.loaded_image is not None:
            return
        self.image_canvas.delete("all")
        w, h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        cx, cy = w // 2, h // 2
        plus_size = min(w, h) // 8
        self.image_canvas.create_line(cx - plus_size, cy, cx + plus_size, cy, fill="#888", width=2)
        self.image_canvas.create_line(cx, cy - plus_size, cx, cy + plus_size, fill="#888", width=2)
    
    def open_image(self, event=None):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;")])
        if file_path:
            self.image_canvas.delete("all")
            self.image_canvas.create_text(self.image_canvas.winfo_width() // 2, self.image_canvas.winfo_height() // 2, text="載入圖片中，請稍候...", fill="black", font=("Arial", 14))
            self.image_canvas.update()
            self.load_image(file_path)
            self.decode_from_image()
    
    def load_image(self, file_path):
        self.loaded_image = Image.open(file_path)
        self.image_tk = ImageTk.PhotoImage(self.loaded_image)
        self.image_canvas.delete("all")
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        self.image_canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.image_tk, anchor="center")
        self.image_canvas.update()
    
    def export_image(self):
        if not self.points:
            return
        min_x, max_x = min(point[0] for point in self.points), max(point[0] for point in self.points)
        min_y, max_y = min(point[1] for point in self.points), max(point[1] for point in self.points)
        padding = SIZE * 2
        width = max_x - min_x + SIZE + padding * 2
        height = max_y - min_y + SIZE + padding * 2
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        for x, y, color in self.points:
            x_offset = x - min_x + padding
            y_offset = y - min_y + padding
            draw.rectangle([x_offset, y_offset, x_offset+SIZE, y_offset+SIZE], fill=color, outline="black")
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            image.save(file_path)
    
    def export_text(self):
        text = self.right_string_var.get()
        if not text:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
    
    def update_red_dot(self, point):
        pass
    
    def decode_from_image(self):
        if self.loaded_image is None:
            return
        
        self.image_canvas.create_text(self.image_canvas.winfo_width() // 2, self.image_canvas.winfo_height() // 2, text="解碼中，請稍候...", fill="black", font=("Arial", 14))
        self.image_canvas.update()
        
        cv_img = cv2.cvtColor(np.array(self.loaded_image), cv2.COLOR_RGB2BGR)
        h, w = cv_img.shape[:2]
        
        start_point = None
        for y in range(h):
            for x in range(w):
                if color_matches(cv_img[y, x], BGR_START, tol=50):
                    start_point = (x, y)
                    break
            if start_point:
                break
        
        if start_point is None:
            return
        
        visited = set()
        current_point = (start_point[0] + SIZE // 2, start_point[1] + SIZE // 2)
        visited.add(current_point)
        directions = [(MOVE, 0), (0, -MOVE), (-MOVE, 0), (0, MOVE)]
        digit_string = ""
        direction_idx = 0
        
        while direction_idx < 4:
            direction = directions[direction_idx]
            step_count = 0
            while True:
                next_point = (int(current_point[0] + direction[0]), int(current_point[1] + direction[1]))
                if next_point in visited:
                    current_point = next_point
                    continue
                if not (0 <= next_point[0] < w and 0 <= next_point[1] < h):
                    break
                sample = cv_img[next_point[1], next_point[0]]
                visited.add(next_point)
                if color_matches(sample, BGR_GREEN, tol=50):
                    step_count += 1
                    current_point = next_point
                    self.update_red_dot(current_point)
                    break
                elif any(color_matches(sample, c, tol=50) for c in [BGR_COLOR1, BGR_COLOR2, BGR_COLOR3, BGR_COLOR4, BGR_COLOR5]):
                    step_count += 1
                    current_point = next_point
                    self.update_red_dot(current_point)
                else:
                    current_point = next_point
            digit_string += str(step_count)
            direction_idx = (direction_idx + 1) % 4
            if direction_idx < 4:
                next_dir = directions[direction_idx]
                test_point = (int(current_point[0] + next_dir[0]), int(current_point[1] + next_dir[1]))
                if not (0 <= test_point[0] < w and 0 <= test_point[1] < h) or np.all(cv_img[test_point[1], test_point[0]] >= 240):
                    break
        
        decoded_text = self.decode_morse_string(digit_string)
        self.image_canvas.delete("all")
        self.image_canvas.create_image(self.image_canvas.winfo_width() // 2, self.image_canvas.winfo_height() // 2, image=self.image_tk, anchor="center")
        self.right_string_var.set(decoded_text)
    
    # Convert Morse digit string to text
    def decode_morse_string(self, digit_string):
        result = ""
        buffer = ""
        i = 0
        while i < len(digit_string):
            ch = digit_string[i]
            if ch in ('3', '5'):
                if buffer:
                    uppercase = buffer[0] == '4'
                    code = buffer[1:] if uppercase else buffer
                    letter = reverse_morse.get(code, '?')
                    if uppercase:
                        letter = letter.upper()
                    result += letter
                    if ch == '5':
                        result += " "
                    buffer = ""
                i += 1
            else:
                buffer += ch
                i += 1
        return result

if __name__ == "__main__":
    root = ctk.CTk()
    app = MorseCodeApp(root)
    root.mainloop()