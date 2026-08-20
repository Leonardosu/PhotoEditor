import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
from pathlib import Path

DEFAULT_FONT_SIZE = 180


class TextItem:
    def __init__(self, text, x, y, font_size=DEFAULT_FONT_SIZE, color="#FFFFFF"):
        self.text = text
        self.x = x
        self.y = y
        self.font_size = font_size
        self.color = color

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def move(self, dx, dy):
        self.x += dx
        self.y += dy


class PhotoTextEditor:

    def __init__(self, root):
        self.root = root
        self.root.title("Editor rápido de fotos")
        self.root.geometry("1200x850")
        self.root.minsize(900, 650)

        self.files = []
        self.index = 0
        self.image = None
        self.preview_image = None
        self.text_color = "#FFFFFF"
        self.font_size = DEFAULT_FONT_SIZE

        # Posição em coordenadas da imagem original.
        self.texts: list[TextItem] = []
        self.selected_text = None
        self.text_color = "#FFFFFF"
        self.font_size = DEFAULT_FONT_SIZE

        # Dados usados para converter coordenadas do canvas -> imagem.
        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.dragging = False

        self.output_dir = None

        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=8)

        tk.Button(top, text="Selecionar pasta", command=self.select_folder).pack(side="left")
        self.counter = tk.Label(top, text="Nenhuma foto selecionada")
        self.counter.pack(side="left", padx=15)

        controls = tk.Frame(root)
        controls.pack(fill="x", padx=10, pady=(0, 5))

        tk.Label(controls, text="Texto:").pack(side="left")
        self.text_entry = tk.Entry(
            controls,
            width=35,
            font=("Microsoft YaHei", 14)
        )
        self.text_entry.pack(side="left", padx=6)
        self.text_entry.bind(
            "<Return>",
            lambda e: self.add_text()
        )
        self.text_entry.bind("<KeyRelease>", lambda e: self.refresh())

        tk.Button(
            controls,
            text="Adicionar",
            command=self.add_text
        ).pack(side="left", padx=5)

        tk.Label(controls, text="Tamanho:").pack(side="left", padx=(15, 3))
        self.size_var = tk.IntVar(value=DEFAULT_FONT_SIZE)
        tk.Spinbox(
            controls, from_=10, to=300, textvariable=self.size_var,
            width=6, command=self.refresh
        ).pack(side="left")

        tk.Button(controls, text="Cor", command=self.choose_color).pack(side="left", padx=8)

        tk.Button(
            controls, text="Centralizar texto",
            command=self.center_text
        ).pack(side="left", padx=4)

        self.position_label = tk.Label(
            root,
            text="Clique na foto para definir onde o texto ficará • Arraste o texto para ajustar",
            anchor="w"
        )
        self.position_label.pack(fill="x", padx=12)

        self.canvas = tk.Canvas(root, bg="#222", cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=8)

        self.canvas.bind("<Button-1>", self.set_position)
        self.canvas.bind("<B1-Motion>", self.drag_position)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=8)

        tk.Button(bottom, text="← Anterior", command=self.previous).pack(side="left")
        tk.Button(
            bottom, text="Salvar e próxima  [Enter]",
            command=self.save_and_next
        ).pack(side="left", padx=10)
        tk.Button(bottom, text="Pular  [→]", command=self.next_photo).pack(side="left")
        tk.Button(bottom, text="Sair", command=root.destroy).pack(side="right")

        root.bind("<Right>", lambda e: self.next_photo())
        root.bind("<Left>", lambda e: self.previous())
        root.bind("<Control-Enter>", lambda e: self.save_and_next())

    def select_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta com as fotos")
        if not folder:
            return

        extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
        self.files = sorted([
            p for p in Path(folder).iterdir()
            if p.is_file() and p.suffix.lower() in extensions
        ])

        self.index = 0

        if not self.files:
            messagebox.showwarning(
                "Nenhuma foto",
                "Não encontrei imagens nessa pasta."
            )
            return

        self.output_dir = Path(folder) / "editadas"
        self.output_dir.mkdir(exist_ok=True)

        self.load_photo()

    def load_photo(self):
        if not self.files:
            return

        self.image = Image.open(
            self.files[self.index]
        ).convert("RGB")

        self.texts: list[TextItem] = []
        self.selected_text = None

        self.text_entry.delete(0, "end")

        self.counter.config(
            text=f"{self.index + 1} / {len(self.files)}  — "
                 f"{self.files[self.index].name}"
        )

        self.refresh()
        self.text_entry.focus_set()

    def convert_text(self, text):
        """
        Atalhos:
        12d -> 12打
        5c  -> 5盒
        """
        text = text.strip()
        if not text:
            return text

        match = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*([dDcC])", text)
        if match:
            number = match.group(1).replace(",", ".")
            suffix = "打" if match.group(2).lower() == "d" else "盒"
            return f"{number}{suffix}"

        return text

    def get_font(self, size, text=None):
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
            "C:/Windows/Fonts/simhei.ttf",  # SimHei
            "C:/Windows/Fonts/simsun.ttc",  # SimSun
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]

        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size=size)
                except Exception:
                    pass

        return ImageFont.load_default()

    def choose_color(self):
        color = colorchooser.askcolor(
            title="Escolha a cor do texto",
            initialcolor=self.text_color
        )

        if color[1]:
            self.text_color = color[1]
            self.refresh()

    def center_text(self):
        if self.image is None:
            return

        if self.selected_text is None:
            return

        if self.selected_text >= len(self.texts):
            return

        self.texts[self.selected_text].set_position(
            self.image.width // 2,
            self.image.height // 2
        )

        self.refresh()

    def calculate_display(self):
        if self.image is None:
            return None

        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)

        scale = min(
            canvas_w / self.image.width,
            canvas_h / self.image.height,
            1.0
        )

        display_w = int(self.image.width * scale)
        display_h = int(self.image.height * scale)

        offset_x = (canvas_w - display_w) / 2
        offset_y = (canvas_h - display_h) / 2

        self.display_scale = scale
        self.display_offset_x = offset_x
        self.display_offset_y = offset_y

        return display_w, display_h

    def image_coordinates_from_canvas(self, canvas_x, canvas_y):
        if self.image is None:
            return None

        display = self.calculate_display()
        if display is None:
            return None

        display_w, display_h = display

        x = (canvas_x - self.display_offset_x) / self.display_scale
        y = (canvas_y - self.display_offset_y) / self.display_scale

        x = max(0, min(self.image.width, x))
        y = max(0, min(self.image.height, y))

        return int(x), int(y)

    def set_position(self, event):
        if self.image is None:
            return

        pos = self.image_coordinates_from_canvas(
            event.x,
            event.y
        )

        if pos is None:
            return

        if self.selected_text is None:
            return

        self.texts[self.selected_text].set_position(
            pos[0],
            pos[1]
        )

        self.dragging = True
        self.refresh()

    def drag_position(self, event):
        if not self.dragging or self.image is None:
            return

        if self.selected_text is None:
            return

        pos = self.image_coordinates_from_canvas(
            event.x,
            event.y
        )

        if pos is None:
            return

        self.texts[self.selected_text].set_position(
            pos[0],
            pos[1]
        )

        self.refresh()

    def stop_drag(self, event):
        self.dragging = False

    def refresh(self, *_):
        if self.image is None:
            return

        try:
            self.font_size = int(self.size_var.get())
        except Exception:
            self.font_size = DEFAULT_FONT_SIZE

        display = self.calculate_display()
        display_w, display_h = display

        preview = self.image.resize(
            (display_w, display_h),
            Image.Resampling.LANCZOS
        )

        draw = ImageDraw.Draw(preview)

        # Desenha todos os textos existentes
        for index, text_item in enumerate(self.texts):

            text = text_item.text

            if not text:
                continue

            # Converte posição da imagem para posição da prévia
            px = int(text_item.x * self.display_scale)
            py = int(text_item.y * self.display_scale)

            preview_font_size = max(
                10,
                int(text_item.font_size * self.display_scale)
            )

            font = self.get_font(
                preview_font_size,
                text
            )

            # O ponto representa o centro do texto
            bbox = draw.textbbox(
                (0, 0),
                text,
                font=font
            )

            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            xy = (
                px - tw // 2,
                py - th // 2
            )

            stroke_width = max(
                1,
                int(2 * self.display_scale)
            )

            draw.text(
                xy,
                text,
                font=font,
                fill=text_item.color,
                stroke_width=stroke_width,
                stroke_fill="#000000"
            )

            # Marca o texto atualmente selecionado
            if index == self.selected_text:
                r = max(
                    3,
                    int(4 * self.display_scale)
                )

                draw.ellipse(
                    (
                        px - r,
                        py - r,
                        px + r,
                        py + r
                    ),
                    outline="#FFFFFF",
                    width=max(
                        1,
                        int(self.display_scale * 2)
                    )
                )

        self.preview_image = ImageTk.PhotoImage(preview)

        self.canvas.delete("all")

        self.canvas.create_image(
            self.display_offset_x,
            self.display_offset_y,
            image=self.preview_image,
            anchor="nw"
        )

    def add_text(self):
        text = self.convert_text(
            self.text_entry.get()
        )

        if not text:
            return

        text_item = TextItem(
            text=text,
            x=self.image.width // 2,
            y=self.image.height // 2,
            font_size=self.font_size,
            color=self.text_color
        )

        self.texts.append(text_item)

        self.selected_text = len(self.texts) - 1

        self.text_entry.delete(0, "end")

        self.refresh()
        self.text_entry.focus_set()

    def save_and_next(self):
        if not self.files:
            return

        if not self.texts:
            messagebox.showwarning(
                "Nenhum texto",
                "Adicione pelo menos um texto antes de salvar."
            )
            self.text_entry.focus_set()
            return

        img = self.image.copy()
        draw = ImageDraw.Draw(img)

        for text_item in self.texts:

            text = text_item.text

            if not text:
                continue

            font = self.get_font(
                text_item.font_size,
                text
            )

            bbox = draw.textbbox(
                (0, 0),
                text,
                font=font
            )

            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            xy = (
                int(text_item.x - tw // 2),
                int(text_item.y - th // 2)
            )

            draw.text(
                xy,
                text,
                font=font,
                fill=text_item.color,
                stroke_width=max(
                    2,
                    text_item.font_size // 20
                ),
                stroke_fill="#000000"
            )

        output = self.output_dir / self.files[self.index].name

        img.save(
            output,
            quality=95
        )

        if self.index < len(self.files) - 1:
            self.index += 1
            self.load_photo()

        else:
            self.counter.config(
                text=f"{len(self.files)} / "
                     f"{len(self.files)} — concluído!"
            )

            messagebox.showinfo(
                "Concluído",
                f"Todas as fotos foram processadas.\n\n"
                f"Pasta:\n{self.output_dir}"
            )

    def next_photo(self):
        if self.files and self.index < len(self.files) - 1:
            self.index += 1
            self.load_photo()

    def previous(self):
        if self.files and self.index > 0:
            self.index -= 1
            self.load_photo()


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoTextEditor(root)
    root.mainloop()
