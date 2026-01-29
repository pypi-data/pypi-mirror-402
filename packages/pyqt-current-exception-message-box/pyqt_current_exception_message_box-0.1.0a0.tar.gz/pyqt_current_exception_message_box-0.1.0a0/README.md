# `pyqt-current-exception-message-box`

A simple utility to display the current exception in a PyQt message box.

## Features

- Shows error dialog (QMessageBox) with the exception message and traceback
- Easy to call from your own PyQt applications
- Cross-binding: Supports PyQt6, PyQt5, PyQt4, PySide6, PySide2, or PySide

## Installation

```bash
pip install pyqt-current-exception-message-box
```

## Usage

### Simple Usage

```python
import sys
from pyqt_current_exception_message_box import pyqt_current_exception_message_box
# from PySide6.QtWidgets import QApplication
# from PyQt5.QtWidgets import QApplication
# from PySide2.QtWidgets import QApplication
# from PyQt4.QtGui import QApplication
# from PySide.QtGui import QApplication
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

try:
    # Code that may raise
    raise RuntimeError('Something went wrong!')
except RuntimeError:
    pyqt_current_exception_message_box(parent=None)
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).