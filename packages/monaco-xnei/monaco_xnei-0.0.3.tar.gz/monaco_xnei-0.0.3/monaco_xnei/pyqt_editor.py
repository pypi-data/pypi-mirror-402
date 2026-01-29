from PyQt6.QtWidgets import QApplication, QTextEdit, QWidget, QVBoxLayout, QListWidget
from PyQt6.QtGui import QFont
from pygments import lex
from pygments.lexers import get_lexer_by_name
import sys

def pyqt_codeframes(codelanguage="C++", visualFrame="True", width=600, height=400, qt_ww="PyQt Window", Syntax_loobom="Typepy"):
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle(qt_ww)
    window.resize(width, height)

    layout = QVBoxLayout()
    text_area = QTextEdit()
    text_area.setFont(QFont("Consolas", 12))
    layout.addWidget(text_area)

    if Syntax_loobom == "Typepy":
        lexer = get_lexer_by_name(codelanguage.lower(), stripall=True)
        # Daha ileri syntax highlight buraya eklenebilir

    if visualFrame == "True":
        suggestion = QListWidget()
        suggestion.addItem(f"Example {codelanguage} code")
        layout.addWidget(suggestion)

    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())
