# This is an example test

import os, sys, shutil
from PySide6.QtWidgets import QApplication

test_dir = os.path.dirname(__file__)
run_test_dir = os.path.join(test_dir, 'run')
series_dir = os.path.join(test_dir, 'series')

src_dir = os.path.join(test_dir, '../src')

if src_dir not in sys.path:
    sys.path.append(src_dir)

import modules.gui.main as main

app = QApplication(sys.argv)

# # TEST 1: Open jser file (most current format)

# Copy temp testing files
if os.path.exists(run_test_dir): shutil.rmtree(run_test_dir)
shutil.copytree(series_dir, run_test_dir)

jser_current = os.path.join(run_test_dir, "shapes1.jser")

# Run test
try:
    
    mainwindow = main.MainWindow([])  # invoke mainwindow (opens welcome series)
    mainwindow.openSeries(jser_fp=jser_current)  # open jser
    mainwindow.series.modified = False  # override save
    mainwindow.close()  # close series
    print('Test 1 (open current jser file): pass')
    
except:
    
    print('Test 1 (open current jser file): fail')

# Clean up dirs
shutil.rmtree(run_test_dir)
