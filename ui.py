import logging

logger = logging.getLogger(__name__)

import os
import re
from PyQt5 import QtWidgets, QtGui, QtCore
from .workers import QueryThread


class EnvSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """
    Syntax highlighter for .env files.
    Highlights keys, values, comments, and quoted strings.
    """

    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Key format (e.g., AZURE_ENDPOINT)
        key_format = QtGui.QTextCharFormat()
        key_format.setForeground(QtGui.QColor("#007acc"))
        self.key_pattern = re.compile(r'^([A-Z0-9_]+)(?=\s*=)', re.MULTILINE)
        self.highlighting_rules.append((self.key_pattern, key_format))

        # Quoted value format
        quote_format = QtGui.QTextCharFormat()
        quote_format.setForeground(QtGui.QColor("#2a7b00"))
        self.quote_pattern = re.compile(r'(["\'])(.*?)(\1)')
        self.highlighting_rules.append((self.quote_pattern, quote_format))

        # Unquoted value format
        value_format = QtGui.QTextCharFormat()
        value_format.setForeground(QtGui.QColor("#2a7b00"))
        self.value_pattern = re.compile(r'=(?!\s*["\'])([^#\n\r]*)')
        self.highlighting_rules.append((self.value_pattern, value_format))

        # Comment format (lines starting with #)
        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtGui.QColor("#808080"))
        comment_format.setFontItalic(True)
        self.comment_pattern = re.compile(r'^\s*#.*$', re.MULTILINE)
        self.highlighting_rules.append((self.comment_pattern, comment_format))

    def highlightBlock(self, text):
        """
        Applies syntax highlighting rules to the provided text block.
        """
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


class EnvEditorDialog(QtWidgets.QDialog):
    """
    Dialog to load, edit, and save a .env file.
    """

    def __init__(self, env_path, form):
        super().__init__(form)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.setWindowTitle(f"AzureAI Environment ({env_path})")
        self.setWindowIcon(form._get_icon("config"))
        self.resize(700, 300)
        self.env_path = env_path

        self.init_ui()
        self.load_env()
        self.show()

    def init_ui(self):
        """
        Initializes the UI components for the dialog.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Text edit for .env file content
        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setStyleSheet("border:none;")
        self.highlighter = EnvSyntaxHighlighter(self.text_edit.document())
        layout.addWidget(self.text_edit)

        # Button layout for Update button
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        # Update button
        self.update_button = QtWidgets.QPushButton("Update", self)
        self.update_button.setFixedSize(150, 30)
        self.update_button.clicked.connect(self.save_env)
        button_layout.addWidget(self.update_button)

        layout.addLayout(button_layout)

    def load_env(self):
        """
        Loads the .env file content into the text editor.
        Creates the file if it doesn't exist.
        """
        if not os.path.exists(self.env_path):
            os.makedirs(os.path.dirname(self.env_path), exist_ok=True)
            with open(self.env_path, 'w') as f:
                f.write("")

        with open(self.env_path, 'r') as f:
            content = f.read()
            self.text_edit.setPlainText(content)

    def save_env(self):
        """
        Saves the content of the text editor to the .env file.
        """
        new_content = self.text_edit.toPlainText()
        with open(self.env_path, 'w') as f:
            f.write(new_content)
        QtWidgets.QMessageBox.information(self, "Saved", ".env file updated successfully.")
        self.accept()


class Ui_Form:
    """
    Base UI layout for the chat interface.
    """

    def setup_ui(self, form):
        """
        Sets up the UI components for the form.
        """
        self.form = form
        self.layout = QtWidgets.QVBoxLayout(self.form)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # Scrollable chat thread
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.chat_content_widget = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_content_widget)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)
        self.chat_layout.setSpacing(5)
        self.chat_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area.setWidget(self.chat_content_widget)
        self.layout.addWidget(self.scroll_area)

        # Status label and action buttons
        self.action_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.action_layout)
        self.status_label = QtWidgets.QLabel(self.form)
        self.status_label.setText("Make a query..")
        self.action_layout.addWidget(self.status_label)
        self.action_layout.addStretch()

        # Env editor button
        self.env_edit_button = QtWidgets.QPushButton(self.form)
        self.env_edit_button.setToolTip("Configure AzureAI")
        self.env_edit_button.setIcon(self._get_icon("config"))
        self.env_path = os.path.join(os.path.expanduser("~"), ".netmig", "querynet.env")
        self.env_edit_button.clicked.connect(lambda: EnvEditorDialog(self.env_path, self.form))
        self.action_layout.addWidget(self.env_edit_button)

        # Devices input field
        self.devices_input = QtWidgets.QLineEdit(self.form)
        self.devices_input.setPlaceholderText("Enter comma-separated IPs or hostnames")
        self.layout.addWidget(self.devices_input)

        # Query input field
        self.query_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.query_layout)
        self.query_layout.setContentsMargins(0, 0, 0, 0)
        self.query_input = QtWidgets.QLineEdit(self.form)
        self.query_input.setPlaceholderText("Ask a question like 'Check OSPF neighbors'")
        self.query_layout.addWidget(self.query_input)

        # Send button
        self.send_button = QtWidgets.QPushButton(self.form)
        self.send_button.setToolTip("Send")
        self.send_button.setIcon(self._get_icon("send"))
        self.query_layout.addWidget(self.send_button)

        if not os.path.exists(self.env_path) or not open(self.env_path).read():
            self.send_button.setDisabled(True)
            logger.warning("Azure credentials missing or incorrect. Please configure using the GUI.")
            self.status_label.setText("Azure credentials missing or incorrect. Please configure using the GUI.")
            self.env_edit_button.click()

    def add_message(self, sender, message):
        """
        Adds a message bubble to the chat thread.
        """
        bubble = QtWidgets.QLabel(self.form)
        bubble.setTextFormat(QtCore.Qt.RichText)
        bubble.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.LinksAccessibleByMouse)
        bubble.setWordWrap(True)
        bubble.setContentsMargins(5, 5, 5, 5)
        bubble.setText(f"<b>{sender}</b>: {message}")
        bubble.setStyleSheet("border: 1px solid rgba(80, 180, 255, 80); border-radius: 5px; padding: 5px;")

        self.chat_layout.addWidget(bubble)
        QtCore.QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))

    def _get_icon(self, filename):
        """
        Loads an icon from the assets directory.
        """
        icon_path = os.path.join(os.path.dirname(__file__), "assets", f"{filename}.ico")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        return icon


class Form(QtWidgets.QWidget, Ui_Form):
    """
    Main form class combining layout and behavior.
    """

    def __init__(self, parent=None, **kwargs):
        """
        Initializes the form with the given parent and session.
        """
        super().__init__(parent)
        self.kwargs = kwargs
        self.session = kwargs.get("session")
        self.setup_ui(self)
        self.send_button.clicked.connect(self.handle_send)
        self.query_input.returnPressed.connect(self.handle_send)

    def handle_send(self):
        """
        Triggered when the user clicks Send.
        """
        query = self.query_input.text().strip()
        if not query:
            return
        self.add_message("You", query)
        self.query_input.clear()
        self.process_query(query)

    def process_query(self, query):
        """
        Processes the query by extracting devices and running the query.
        """
        devices = [ip.strip() for ip in self.devices_input.text().split(",") if ip.strip()]
        if not devices or not query:
            self.display_result.setPlainText("Please enter both devices and query.")
            return

        self.send_button.setEnabled(False)
        self.status_label.setText("Processing...")

        self.thread = QueryThread(self, devices, query)
        self.thread.result_ready.connect(self.display_result)
        self.thread.finished.connect(lambda: self.send_button.setEnabled(True))
        self.thread.start()

    def display_result(self, html):
        """
        Displays the result of the query in the chat.
        """
        self.status_label.setText("Make a query..")
        self.add_message("Bot", html)
