# This is an example test

import os, sys, shutil
from PySide6.QtWidgets import QApplication
from src.modules.gui.main import MainWindow
from src.modules.constants.locations import checker_dir

app = QApplication(sys.argv)

# TEST 1: Open jser file (most current format)

jser_current = os.path.join(testing_dir, "shapes1_broke.jser")

# Copy temp testing files
if os.path.exists(testing_dir): shutil.rmtree(testing_dir)
shutil.copytree(backup_dir, testing_dir)

# Run test
try:
    
    mainwindow = MainWindow([])  # invoke mainwindow (opens welcome series)
    mainwindow.openSeries(jser_fp=jser_current)  # open jser
    mainwindow.series.modified = False  # override save
    mainwindow.close()  # close series
    print('Test 1 (open current jser file): pass')
    
except:
    
    print('Test 1 (open current jser file): fail')

# Clean up dirs
shutil.rmtree(testing_dir)

