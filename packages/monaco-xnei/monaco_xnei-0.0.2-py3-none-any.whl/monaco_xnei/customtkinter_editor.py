import customtkinter as ctk
from tkinter import scrolledtext
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name

def customtkinter_codeframes(codelanguage="C#", visualFrame="True", width=600, height=400, qt_ww="CustomTk Window", Syntax_loobom="Typepy"):
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    window = ctk.CTk()
    window.title(qt_ww)
    window.geometry(f"{width}x{height}")

    text_area = scrolledtext.ScrolledText(window, wrap="word", font=("Consolas", 12))
    text_area.pack(expand=True, fill="both")

    if Syntax_loobom == "Typepy":
        lexer = get_lexer_by_name(codelanguage.lower(), stripall=True)
        style = get_style_by_name("colorful")

        def highlight(event=None):
            content = text_area.get("1.0", "end")
            text_area.tag_remove("Token", "1.0", "end")

            for token, content_fragment in lex(content, lexer):
                tag_name = str(token)
                color = style.style_for_token(token)['color']
                if color:
                    if not color.startswith("#"):
                        color = f"#{color}"
                else:
                    color = "white"

                text_area.tag_configure(tag_name, foreground=color)

                idx = text_area.search(content_fragment, "1.0", "end")
                while idx:
                    end_idx = f"{idx}+{len(content_fragment)}c"
                    text_area.tag_add(tag_name, idx, end_idx)
                    idx = text_area.search(content_fragment, end_idx, "end")

        text_area.bind("<KeyRelease>", highlight)

    if visualFrame == "True":
        suggestion = ctk.CTkLabel(window, text=f"Example {codelanguage} code")
        suggestion.pack(side="bottom")

    window.mainloop()
    return text_area
