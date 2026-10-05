import os
from PyQt6.QtCore import QThread, pyqtSignal
from docling.document_converter import DocumentConverter

class DocumentParser(QThread):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            converter = DocumentConverter()
            result = converter.convert(self.file_path)
            text = result.document.export_to_markdown()

            filename = os.path.basename(self.file_path)

            self.finished.emit(text, filename)

        except Exception as e:
            self.error.emit(str(e))