print("diskwrangler __main__.py")
import os
import sys
from pathlib import Path
from PyQt6 import QtWidgets

sys.path.append(os.path.dirname(__file__))
from d64py import *
import DiskWrangler, DirTableModel
