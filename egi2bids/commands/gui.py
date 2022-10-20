import argparse
import sys

from PyQt6.QtWidgets import QApplication

from ..gui import bidsToEgiGui


def run():
    """Run sys_info() command."""
    parser = argparse.ArgumentParser(
        prog=f"{__package__.split('.')[0]}-gui",
        description="EGI to BIDS GUI converter.",
    )
    parser.parse_args()

    app = QApplication(sys.argv)
    ex = bidsToEgiGui()
    ex.resize(800, 500)
    ex.show()
    sys.exit(app.exec())
