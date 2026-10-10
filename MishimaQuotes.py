import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import os
import sys
import platform
import subprocess
import io
import json
import pyperclip

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ================= НАСТРОЙКИ =================
BOX_LEFT, BOX_TOP = 120, 780
BOX_RIGHT, BOX_BOTTOM = 977, 1020
BOX_W = BOX_RIGHT - BOX_LEFT
BOX_H = BOX_BOTTOM - BOX_TOP

MAX_CHARS = 240
MAX_CHARS_EMOJI = 200
COUNTER_FILE = "counter.txt"
SETTINGS_FILE = "settings.json"

FONT_PATHS = [
    "arialbd.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
# =============================================

# ================= ПЕРЕВОДЫ =================
TEXTS = {
    "ru": {
        "title": "Генератор цитат Юкио Мисимы",
        "header": "Генератор цитат\nЮкио Мисимы",
        "input_label": "Введите текст цитаты:",
        "placeholder": "Если на вашей могиле не написано «Покойся с миром», вы автоматически призываетесь в войну скелетов.",
        "btn_generate": "🎨 Создать цитату",
        "btn_copy": "📋 Копировать",
        "status_ready": "Готово к работе",
        "status_no_text": "Ошибка: введите текст",
        "status_empty": "Ошибка: текст пустой",
        "status_limit": "Ошибка: макс. {n} символов",
        "status_no_template": "Ошибка: template.jpg не найден!",
        "status_template_err": "Ошибка шаблона: {err}",
        "status_saved": "✅ Сохранено: {name}",
        "status_err": "Ошибка: {err}",
        "status_nothing_to_copy": "⚠️ Сначала создайте цитату",
        "status_copied": "✅ Картинка скопирована в буфер",
        "status_copy_err": "❌ Ошибка: {err}",
        "emoji_mark": " (эмодзи)",
        "no_photo": "[нет\nфото]",
    },
    "en": {
        "title": "Yukio Mishima Quote Generator",
        "header": "Yukio Mishima\nQuote Generator",
        "input_label": "Enter quote text:",
        "placeholder": "If your grave doesn't say «Rest in Peace» on it, you are automatically drafted into the skeleton war.",
        "btn_generate": "🎨 Create quote",
        "btn_copy": "📋 Copy",
        "status_ready": "Ready",
        "status_no_text": "Error: enter text",
        "status_empty": "Error: text is empty",
        "status_limit": "Error: max {n} characters",
        "status_no_template": "Error: template.jpg not found!",
        "status_template_err": "Template error: {err}",
        "status_saved": "✅ Saved: {name}",
        "status_err": "Error: {err}",
        "status_nothing_to_copy": "⚠️ Create a quote first",
        "status_copied": "✅ Image copied to clipboard",
        "status_copy_err": "❌ Error: {err}",
        "emoji_mark": " (emoji)",
        "no_photo": "[no\nphoto]",
    },
}
# =============================================


# ================= УТИЛИТЫ =================
def resource_path(rel):
    """Путь к файлу — работает и в .py, и в собранном .exe"""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(".")
    return os.path.join(base, rel)


def load_font(size):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def open_file(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except:
        pass


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass


def copy_image_to_clipboard(img):
    if platform.system() != "Windows":
        return False, "Only supported on Windows"
    try:
        import win32clipboard
        from io import BytesIO

        output = BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True, "OK"
    except ImportError:
        return False, "Install pywin32: pip install pywin32"
    except Exception as e:
        return False, str(e)


# ================= ПРИЛОЖЕНИЕ =================
class QuoteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_json(SETTINGS_FILE, {"lang": "ru"})
        self.lang = self.settings.get("lang", "ru")

        self.title(self.t("title"))
        self.geometry("820x400")
        self.resizable(False, False)
        if os.path.exists(resource_path("mishima.ico")):
            try:
                self.iconbitmap(resource_path("mishima.ico"))
            except:
                pass

        self.last_image = None
        self._build_ui()

    def t(self, key, **kwargs):
        text = TEXTS[self.lang].get(key, key)
        return text.format(**kwargs) if kwargs else text

    def switch_lang(self, value):
        new_lang = "ru" if value == "RU" else "en"
        if new_lang == self.lang:
            return
        self.lang = new_lang
        self.settings["lang"] = new_lang
        save_json(SETTINGS_FILE, self.settings)
        self._apply_lang()

    def _apply_lang(self):
        self.title(self.t("title"))
        self.header_label.configure(text=self.t("header"))
        self.input_label.configure(text=self.t("input_label"))
        self.btn_generate.configure(text=self.t("btn_generate"))
        self.btn_copy.configure(text=self.t("btn_copy"))
        self.status.configure(text=self.t("status_ready"))

        # Обновляем плейсхолдер только если он сейчас показан
        if self.is_placeholder:
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", self.t("placeholder"))
            self.textbox.configure(text_color="gray")

    # ================= UI =================
    def _build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(15, 5))

        try:
            icon_img = ctk.CTkImage(
                light_image=Image.open(resource_path("mishima_icon.jpg")),
                dark_image=Image.open(resource_path("mishima_icon.jpg")),
                size=(60, 60)
            )
            ctk.CTkLabel(top_frame, image=icon_img, text="").pack(side="left", padx=5)
        except:
            ctk.CTkLabel(top_frame, text=self.t("no_photo"), width=60, height=60,
                         fg_color="gray20", corner_radius=10).pack(side="left", padx=5)

        self.header_label = ctk.CTkLabel(top_frame, text=self.t("header"),
                                          font=("Arial", 16, "bold"), justify="left")
        self.header_label.pack(side="left", padx=10)

        self.lang_switch = ctk.CTkSegmentedButton(
            top_frame, values=["RU", "EN"], command=self.switch_lang,
            font=("Arial", 12, "bold"), width=110
        )
        self.lang_switch.pack(side="right", padx=5)
        self.lang_switch.set("RU" if self.lang == "ru" else "EN")

        self.input_label = ctk.CTkLabel(self, text=self.t("input_label"), font=("Arial", 13))
        self.input_label.pack(anchor="w", padx=20, pady=(5, 0))

        self.textbox = ctk.CTkTextbox(self, width=760, height=130, font=("Arial", 14),
                                       text_color="white", fg_color="gray15")
        self.textbox.pack(pady=(5, 0), padx=20)

        self.counter = ctk.CTkLabel(self, text=f"0 / {MAX_CHARS}", font=("Arial", 11), text_color="gray")
        self.counter.pack(anchor="w", padx=20, pady=(2, 0))

        self.is_placeholder = True
        self.set_placeholder()
        self.textbox.bind("<FocusIn>", self.clear_placeholder)
        self.textbox.bind("<FocusOut>", self.set_placeholder)
        self.textbox.bind("<KeyRelease>", self.update_counter)

        self.status = ctk.CTkLabel(self, text=self.t("status_ready"), text_color="gray",
                                    font=("Arial", 11), height=20)
        self.status.pack(anchor="w", padx=20, pady=(2, 0))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 5))

        self.btn_generate = ctk.CTkButton(btn_frame, text=self.t("btn_generate"),
                                           command=self.generate_image,
                                           font=("Arial", 14), width=180, height=40)
        self.btn_generate.pack(side="left", padx=5)

        self.btn_copy = ctk.CTkButton(btn_frame, text=self.t("btn_copy"),
                                       command=self.copy_image,
                                       font=("Arial", 14), width=160, height=40)
        self.btn_copy.pack(side="left", padx=5)

    # ================= ПЛЕЙСХОЛДЕР =================
    def set_placeholder(self, event=None):
        """Показывает серый пример, если поле пустое и фокус не в нём"""
        if not self.textbox.get("1.0", "end-1c").strip():
            self.is_placeholder = True
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", self.t("placeholder"))
            self.textbox.configure(text_color="gray")
            self.update_counter()

    def clear_placeholder(self, event=None):
        """При клике в поле — полностью убирает пример и ставит белый цвет"""
        if self.is_placeholder:
            self.is_placeholder = False
            self.textbox.delete("1.0", "end")
            self.textbox.configure(text_color="white")

    # ================= ВАЛИДАЦИЯ =================
    def normalize_text(self, text):
        return " ".join(text.split()).strip()

    def update_counter(self, event=None):
        if self.is_placeholder:
            self.counter.configure(text=f"0 / {MAX_CHARS}", text_color="gray")
            return

        text = self.textbox.get("1.0", "end-1c")

        # Если поле пустое — не возвращаем плейсхолдер, пока фокус внутри
        if not text.strip():
            self.counter.configure(text=f"0 / {MAX_CHARS}", text_color="gray")
            return

        has_emoji = any(ord(c) > 0xFFFF for c in text)
        limit = MAX_CHARS_EMOJI if has_emoji else MAX_CHARS

        if len(text) > limit:
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", text[:limit])
            text = text[:limit]

        length = len(text)
        self.counter.configure(
            text=f"{length} / {limit}{self.t('emoji_mark') if has_emoji else ''}",
            text_color="red" if length >= limit else "gray"
        )

    # ================= ПЕРЕНОС =================
    def wrap_text(self, text, font, draw, max_width):
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                if draw.textbbox((0, 0), word, font=font)[2] > max_width:
                    temp = ""
                    for ch in word:
                        test = temp + ch
                        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
                            temp = test
                        else:
                            if temp:
                                lines.append(temp)
                            temp = ch
                    current_line = temp
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    # ================= АВТОПОДБОР =================
    def auto_fit_font(self, text, draw, box_w, box_h):
        for size in [60, 50, 40, 35, 30, 25, 20]:
            font = load_font(size)
            wrapped = self.wrap_text(text, font, draw, box_w)
            bbox = draw.textbbox((0, 0), wrapped, font=font, spacing=10, align="center")
            if (bbox[2] - bbox[0]) <= box_w and (bbox[3] - bbox[1]) <= box_h:
                return font, wrapped
        return load_font(20), self.wrap_text(text, load_font(20), draw, box_w)

    # ================= ИНДЕКСАЦИЯ =================
    def get_next_filename(self, base="result_quote", ext=".jpg"):
        counter = 0
        if os.path.exists(COUNTER_FILE):
            try:
                with open(COUNTER_FILE, "r") as f:
                    counter = int(f.read().strip())
            except:
                counter = 0
        counter += 1
        with open(COUNTER_FILE, "w") as f:
            f.write(str(counter))
        return f"{base}_{counter}{ext}"

    # ================= КОПИРОВАНИЕ =================
    def copy_image(self):
        if self.last_image is None:
            self.status.configure(text=self.t("status_nothing_to_copy"), text_color="orange")
            return

        ok, msg = copy_image_to_clipboard(self.last_image)
        if ok:
            self.status.configure(text=self.t("status_copied"), text_color="green")
        else:
            self.status.configure(text=self.t("status_copy_err", err=msg), text_color="red")

    # ================= ГЕНЕРАЦИЯ =================
    def generate_image(self):
        try:
            if self.is_placeholder:
                self.status.configure(text=self.t("status_no_text"), text_color="red")
                return

            user_text = self.normalize_text(self.textbox.get("1.0", "end-1c"))

            if not user_text:
                self.status.configure(text=self.t("status_empty"), text_color="red")
                return

            has_emoji = any(ord(c) > 0xFFFF for c in user_text)
            limit = MAX_CHARS_EMOJI if has_emoji else MAX_CHARS
            if len(user_text) > limit:
                self.status.configure(text=self.t("status_limit", n=limit), text_color="red")
                return

            template_path = resource_path("template.jpg")
            if not os.path.exists(template_path):
                self.status.configure(text=self.t("status_no_template"), text_color="red")
                return

            try:
                img = Image.open(template_path).convert("RGB")
            except Exception as e:
                self.status.configure(text=self.t("status_template_err", err=e), text_color="red")
                return

            draw = ImageDraw.Draw(img)
            font, wrapped_text = self.auto_fit_font(user_text, draw, BOX_W, BOX_H)

            text_x = BOX_LEFT + BOX_W / 2
            text_y = BOX_TOP + BOX_H / 2

            draw.text(
                (text_x, text_y), wrapped_text, fill="black",
                font=font, align="center", anchor="mm", spacing=10
            )

            output = self.get_next_filename()
            img.save(output)
            self.last_image = img

            self.status.configure(text=self.t("status_saved", name=output), text_color="green")
            open_file(output)

        except Exception as e:
            self.status.configure(text=self.t("status_err", err=e), text_color="red")


if __name__ == "__main__":
    app = QuoteApp()
    app.mainloop()