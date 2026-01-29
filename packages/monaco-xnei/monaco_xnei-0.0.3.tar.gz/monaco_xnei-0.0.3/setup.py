from setuptools import setup, find_packages

setup(
    name="monaco_xnei",
    version="0.0.3",
    author="Your Name",
    description="""You can import tkinter, customtkinter, and pyqt from the monaco-xnei library to use them in your Python projects.

monaco-xnei.tkinter_codeframes opens a code editor inside a specified Tkinter window. You can set the programming language with codelanguage="Python". If you set visualFrame="True", it will show autocomplete suggestions for the closest matching Python code while you type, displayed as a list at the bottom-right corner of the editor. Syntax_loobom="Typepy" enables syntax highlighting for the code.

monaco-xnei.pyqt_codeframes works similarly but opens the code editor inside a PyQt6 window. Setting codelanguage="C++" makes the editor for C++ code. visualFrame="True" shows code suggestions, and Syntax_loobom="Typepy" enables syntax highlighting.

monaco-xnei.customtkinter_codeframes opens a code editor for CustomTkinter windows. Using codelanguage="C#" sets it for C# code, and Syntax_loobom="Typepy" enables syntax highlighting as well.

Supported languages: C#, HTML, CSS, JS, C++, C, Python, Java, GO, md, json
""",
    long_description="""You can import tkinter, customtkinter, and pyqt from the monaco-xnei library to use them in your Python projects.

monaco-xnei.tkinter_codeframes opens a code editor inside a specified Tkinter window. You can set the programming language with codelanguage="Python". If you set visualFrame="True", it will show autocomplete suggestions for the closest matching Python code while you type, displayed as a list at the bottom-right corner of the editor. Syntax_loobom="Typepy" enables syntax highlighting for the code.

monaco-xnei.pyqt_codeframes works similarly but opens the code editor inside a PyQt6 window. Setting codelanguage="C++" makes the editor for C++ code. visualFrame="True" shows code suggestions, and Syntax_loobom="Typepy" enables syntax highlighting.

monaco-xnei.customtkinter_codeframes opens a code editor for CustomTkinter windows. Using codelanguage="C#" sets it for C# code, and Syntax_loobom="Typepy" enables syntax highlighting as well.

Supported languages: C#, HTML, CSS, JS, C++, C, Python, Java, GO, md, json
""",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "customtkinter",
        "PyQt6",
        "pygments"
    ],
    python_requires=">=3.8"
)
