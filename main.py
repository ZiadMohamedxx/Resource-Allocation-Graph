
import sys
sys.path.append(".")
from PyQt6.QtWidgets import QApplication
from ui import ResourceAllocationSimulator

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResourceAllocationSimulator()
    window.show()
    sys.exit(app.exec())
