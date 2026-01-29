import tkinter as tk
from tkinter import scrolledtext
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name

def tkinter_codeframes(codelanguage="Python", visualFrame="True", width=600, height=400, tk_ww="Tkinter Window", Syntax_loobom="Typepy"):
    window = tk.Toplevel() if tk_ww != "Tkinter Window" else tk.Tk()
    window.title(tk_ww)
    window.geometry(f"{width}x{height}")
    text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, font=("Consolas", 12))
    text_area.pack(expand=True, fill='both')

    if Syntax_loobom == "Typepy":
        lexer = get_lexer_by_name(codelanguage.lower(), stripall=True)
        style = get_style_by_name("colorful")
        def highlight(event=None):
            content = text_area.get("1.0", tk.END)
            text_area.tag_remove("Token", "1.0", tk.END)
            for token, content_fragment in lex(content, lexer):
                tag_name = str(token)
                text_area.tag_configure(tag_name, foreground=style.style_for_token(token)['color'] or "black")
                idx = text_area.search(content_fragment, "1.0", tk.END)
                while idx:
                    end_idx = f"{idx}+{len(content_fragment)}c"
                    text_area.tag_add(tag_name, idx, end_idx)
                    idx = text_area.search(content_fragment, end_idx, tk.END)
        text_area.bind("<KeyRelease>", highlight)

    if visualFrame == "True":
        suggestion = tk.Listbox(window, height=5)
        suggestion.pack(side="bottom", fill="x")
        suggestion.insert(tk.END, f"Example {codelanguage} code")

    window.mainloop()
    return text_area
