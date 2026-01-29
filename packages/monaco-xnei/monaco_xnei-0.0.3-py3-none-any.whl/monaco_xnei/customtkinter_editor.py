import customtkinter as ctk
from tkinter import scrolledtext
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name

def customtkinter_codeframes(codelanguage="C#", visualFrame="True", width=800, height=500, qt_ww="CustomTk Window", Syntax_loobom="Typepy"):
    # CustomTkinter ayarları
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Pencere oluştur
    window = ctk.CTk()
    window.title(qt_ww)
    window.geometry(f"{width}x{height}")

    # Text alanı oluştur
    text_area = scrolledtext.ScrolledText(window, wrap="none", font=("Consolas", 12), bg="#1e1e1e", fg="white", insertbackground="white")
    text_area.pack(expand=True, fill="both")

    if Syntax_loobom == "Typepy":
        lexer = get_lexer_by_name(codelanguage.lower(), stripall=True)
        style = get_style_by_name("colorful")

        def highlight(event=None):
            content = text_area.get("1.0", "end-1c")  # son newline hariç
            text_area.tag_remove("Token", "1.0", "end")
            text_area.tag_configure("Token", foreground="white")  # normal yazı beyaz

            for token, content_fragment in lex(content, lexer):
                tag_name = str(token)
                color = style.style_for_token(token)['color']
                if color:
                    if not color.startswith("#"):
                        color = f"#{color}"
                else:
                    color = "white"
                text_area.tag_configure(tag_name, foreground=color)

                # Her fragmente tag uygula
                idx = "1.0"
                while True:
                    idx = text_area.search(content_fragment, idx, nocase=False, stopindex="end")
                    if not idx:
                        break
                    end_idx = f"{idx}+{len(content_fragment)}c"
                    text_area.tag_add(tag_name, idx, end_idx)
                    idx = end_idx

        text_area.bind("<KeyRelease>", highlight)

    # Visual frame (örnek kod alt label)
    if visualFrame == "True":
        suggestion = ctk.CTkLabel(window, text=f"Example {codelanguage} code", fg_color="#333333")
        suggestion.pack(side="bottom", fill="x")

    window.mainloop()
    return text_area

# Örnek kullanım
if __name__ == "__main__":
    customtkinter_codeframes(codelanguage="C++", visualFrame="True", width=800, height=500, qt_ww="MonacoX C++ Editor", Syntax_loobom="Typepy")
