import os
import sys
import time
import shutil
from PySide6.QtWidgets import QApplication
from modules.gui.main import MainWindow, FieldWidget
from modules.constants.locations import checker_dir

# copy files into checker dir
backup_dir = os.path.join(checker_dir, "files")
testing_dir = os.path.join(checker_dir, "testing")
if os.path.exists(testing_dir):
    shutil.rmtree(testing_dir)
shutil.copytree(backup_dir, testing_dir)

# STOPGAP FOR WAYLAND QT ISSUE
# https://stackoverflow.com/questions/68417682/qt-and-opencv-app-not-working-in-virtual-environment

import os
import PySide6
from pathlib import Path

ps6_fp = PySide6.__file__
plugin_path = os.fspath(Path(ps6_fp).resolve().parent / "Qt" / "plugins")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

# END STOPGAP

app = QApplication(sys.argv)

# TEST XML FUNCTIONS

# create mainwindow from scratch (welcome series)
mainwindow = MainWindow([])

# open a series
mainwindow.openSeries(jser_fp=os.path.join(testing_dir, "shapes1.jser"))

# export to xml
mainwindow.exportToXML(export_fp=os.path.join(testing_dir, "shapes.ser"))

# open the exported xml series
mainwindow.newFromXML(series_fp=os.path.join(testing_dir, "shapes.ser"))

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST IMPORTING/EXPORTING

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes1.jser")])

# import traces
mainwindow.importTraces(os.path.join(testing_dir, "shapes2.jser"))

# import ztraces
mainwindow.importTraces(os.path.join(testing_dir, "shapes2.jser"))

# create/change to a new alignment
mainwindow.changeAlignment("identity")

# import transforms
mainwindow.importTransforms(os.path.join(testing_dir, "tforms.txt"))

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST OPENING AN OLD SERIES

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "class_series.jser")])

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST CREATING A NEW SERIES AND SAVING

# create mainwindow from scratch
mainwindow = MainWindow([])

# get the image locations
imgs = []
for f in os.listdir(testing_dir):
    if f.endswith(".tif"):
        imgs.append(os.path.join(testing_dir, f))
imgs.sort()

# create the new series
mainwindow.newSeries(
    imgs,
    series_name="shapes0",
    mag=0.002,
    thickness=0.05
)

# save the new series
mainwindow.series.jser_fp = os.path.join(testing_dir, "shapes0.jser")
mainwindow.saveToJser()

# close the series
mainwindow.close()

# TEST MISC MAINWINDOW FUNCTIONS

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])

# change the src directory
# mainwindow.changeSrcDir(os.path.join(testing_dir, "shapes_images.zarr"))

# change the username
mainwindow.changeUsername("checker")

# set fill opacity
mainwindow.setFillOpacity(0.5)

# change the brightness/contrast
for option in ("brightness", "contrast"):
    for direction in ("up", "down"):
        mainwindow.editImage(option, direction)

# increment the section
for down in (True, True, False, False):
    mainwindow.incrementSection(down=down)

# flicker the section
mainwindow.flickerSections()
mainwindow.flickerSections()

# check the history widget
mainwindow.viewSeriesHistory()
mainwindow.history_widget.close()

# set the view to an object
mainwindow.setToObject("star", 4)

# change the transform
mainwindow.changeTform([1,0,0,0,1,0])

# translate the entire section
amounts = ("small", "med", "big")
directions = ("left", "right", "up", "down")
for amount in amounts:
    for direction in directions:
        mainwindow.translate(direction, amount)

# translate the traces
mainwindow.field.selectAllTraces()
for amount in amounts:
    for direction in directions:
        mainwindow.translate(direction, amount)

# calibrate the section
mainwindow.changeSection(0)
mainwindow.calibrateMag({
    "cal1": 1,
    "cal2": 0.8
})

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST PALETTE

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])

# select the mouse modes
modes = ["pointer", "panzoom", "knife", "closedtrace", "opentrace", "stamp"]
for mode in modes:
    mainwindow.mouse_palette.activateModeButton(mode)

# select the traces
for bpos in range(20):
    mainwindow.mouse_palette.activatePaletteButton(bpos)

# toggle handedness
mainwindow.mouse_palette.toggleHandedness()

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST OBJECT LIST

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])

# open object list
mainwindow.openObjectList()
manager = mainwindow.field.obj_table_manager

# refresh
manager.refresh()

# find an object
manager.findObject("star")
manager.findObject("star", first=False)

# delete an object
manager.deleteObjects(["circle2"])

# edit an object
manager.editAttributes(
    ["diamond"],
    name="diamond_test",
    color=(0,255,255),
    tags=set("testing"),
    mode=("transparent", "unselected")
)

# edit the radius of an object
manager.editRadius(["diamond"], 1.5)

# remove all the trace tags on an object
manager.removeAllTraceTags(["diamond"])

# hide an object
manager.hideObjects(["diamond"], hide=True)
manager.hideObjects(["diamond"], hide=False)

# edit the 3D settings for an object
manager.edit3D(
    ["square"],
    "spheres",
    0.3
)

# generate 3D
manager.generate3D(["star", "square"])
time.sleep(3)  # time for threading

# remove from the 3D
manager.remove3D(["square"])

# close the 3D scene
manager.object_viewer.close()

# view the object history
manager.viewHistory(["triangle", "star"])
manager.history_widget.close()

# create ztraces
manager.createZtrace(["square"], cross_sectioned=False)
manager.createZtrace(["triangle"], cross_sectioned=True)

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST TRACE LIST

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])

# open a trace list
mainwindow.openTraceList()
manager = mainwindow.field.trace_table_manager
section = mainwindow.field.section

# edit traces
traces = section.contours["star"].getTraces()
manager.editTraces(
    traces,
    name="test",
    color=(0, 255, 255),
    tags=set(["test"]),
    mode=("transparent", "unselected")
)

# hide traces
traces = section.contours["star"].getTraces()
manager.hideTraces(traces, hide=True)
manager.hideTraces(traces, hide=False)

# modify trace radius
traces = section.contours["circle2"].getTraces()
manager.editRadius(traces, 1.5)

# delete trace
traces = section.contours["circle2"].getTraces()
manager.deleteTraces(traces)

# view history
traces = section.contours["star"].getTraces()
manager.viewHistory(traces)

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST ZTRACE LIST

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])

# create the ztrace list
mainwindow.openZtraceList()
manager = mainwindow.field.ztrace_table_manager

# edit attributes of a ztrace
manager.editAttributes("star", "star_test", (0,255,255))

# smooth a ztrace
manager.smooth(["diamond"], 10, newztrace=True)
manager.smooth(["diamond"], 5, newztrace=False)

# delete a ztrace
manager.delete(["star_test"])

# add/remove 3D
mainwindow.openObjectList()
obj_manager = mainwindow.field.obj_table_manager
obj_manager.generate3D(["diamond"])
time.sleep(3)  # time for threading
manager.addTo3D(["diamond"])
manager.remove3D(["diamond"])

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST SECTION LIST

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])

# open the section list
mainwindow.openSectionList()
manager = mainwindow.field.section_table_manager
section_numbers = [0, 1, 2, 3, 4]

# lock/unlock the sections
manager.lockSections(section_numbers, lock=True)
manager.lockSections(section_numbers, lock=False)

# set the brightness and contrast
manager.setBC(section_numbers, 20, 20)

# match the brightness and contrast to the current section
manager.setBC([0], 0, 0)
manager.matchBC(section_numbers)

# edit the thickness of the sections
manager.editThickness(section_numbers, 0.1)

# delete sections
manager.deleteSections([3, 4])

# find a section
manager.findSection(2)

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST FIELDWIDGET FUNCTIONS

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])
field = mainwindow.field

# create a fake mouse event for testing
from modules.calc.pfconversions import fieldPointToPixmap
class MouseEvent():

    def __init__(self, field_x, field_y):
        self.xpos, self.ypos = fieldPointToPixmap(
        field_x, field_y,
        mainwindow.series.window,
        field.pixmap_dim,
        field.section.mag
    )
    
    def x(self):
        return self.xpos
    
    def y(self):
        return self.ypos

# imitate clicking on a point on the star
field.click_time = time.time()
field.lclick = True
field.pointerPress(MouseEvent(2.2, 2.81))
field.pointerRelease(MouseEvent(2.2, 2.81))
field.lclick = False
assert(len(field.section.selected_traces) == 1)
assert(field.section.selected_traces[0].name == "star")
field.deselectAllTraces()

# imitate clicking on the star ztrace
field.click_time = time.time()
field.lclick = True
field.pointerPress(MouseEvent(2.19, 2.03))
field.pointerRelease(MouseEvent(2.19, 2.03))
field.lclick = False
assert(len(field.section.selected_ztraces) == 1)
assert(field.section.selected_ztraces[0][0].name == "star")
field.deselectAllTraces()

# imitate drawing a lasso
field.click_time = time.time()
field.lclick = True
field.pointerPress(MouseEvent(3, 1.5))
time.sleep(field.max_click_time)
points = [
    (3, 1.5),
    (3, 0.2),
    (4.5, 0.2),
    (4.5, 1.5)
]
for pt in points:
    field.pointerMove(MouseEvent(*pt))
field.pointerRelease(MouseEvent(4.5, 1.5))
field.lclick = False
assert(len(field.section.selected_traces) == 1)
assert(field.section.selected_traces[0].name == "circle2")
assert(len(field.section.selected_ztraces) == 1)
assert(field.section.selected_ztraces[0][0].name == "circle2")
field.deselectAllTraces()

# select the star trace
field.click_time = time.time()
field.lclick = True
field.pointerPress(MouseEvent(2.2, 2.81))
field.pointerRelease(MouseEvent(2.2, 2.81))
field.lclick = False

# imitate dragging a trace
field.click_time = time.time()
field.lclick = True
field.pointerPress(MouseEvent(2.2, 2.81))
time.sleep(field.max_click_time)
points = [
    (2.5, 2),
    (2, 1.5),
    (1.5, 1)
]
for pt in points:
    field.pointerMove(MouseEvent(*pt))
field.pointerRelease(MouseEvent(1.5, 1))
field.lclick = False

# unselect the trace
field.click_time = time.time()
field.lclick = True
field.pointerPress(MouseEvent(1.5, 1))
field.pointerRelease(MouseEvent(1.5, 1))
field.lclick = False
assert(len(field.section.selected_traces) == 0)

# undo the move
field.undoState()

# imitate eraser
field.erasing = True
field.eraserMove(MouseEvent(2.2, 2.81))
field.erasing = False
assert(len(field.section.contours["star"]) == 0)

# undo the erase
field.undoState()

# imitate pan
original_window = mainwindow.series.window.copy()
field.click_time = time.time()
field.lclick = True
field.mousePanzoomPress(MouseEvent(1, 1))
points = [
    (1.2, 1.2),
    (1.4, 1.4),
    (1.6, 1.6),
    (1.8, 1.8),
    (2, 2)
]
for pt in points:
    field.mousePanzoomMove(MouseEvent(*pt))
field.mousePanzoomRelease(MouseEvent(2, 2))
field.lclick = False
x1, y1 = tuple(original_window[:2])
x2, y2 = tuple(mainwindow.series.window[:2])
assert(abs(x2 - x1 + 1) < 0.1)
assert(abs(y2 - y1 + 1) < 0.1)

# imitate zoom
original_mag = mainwindow.series.screen_mag
field.click_time = time.time()
field.rclick = True
field.mousePanzoomPress(MouseEvent(1, 1))
points = [
    (1.2, 1.2),
    (1.4, 1.4),
    (1.6, 1.6),
    (1.8, 1.8),
    (2, 2)
]
for pt in points:
    field.mousePanzoomMove(MouseEvent(*pt))
field.mousePanzoomRelease(MouseEvent(2, 2))
field.rclick = False
assert(original_mag < mainwindow.series.screen_mag)

# set the view magnification
field.setViewMagnification(300)

# reset the window
mainwindow.series.window = original_window
field.generateView()

# select the circle1 trace
mainwindow.mouse_palette.activatePaletteButton(0)

# imitate drawing a trace
field.mouse_mode = FieldWidget.CLOSEDTRACE
field.lclick = True
field.tracePress(MouseEvent(1, 1))
time.sleep(field.max_click_time)
points = [
    (1,2),
    (2,2),
    (2,1)
]
for pt in points:
    field.traceMove(MouseEvent(*pt))
assert(not field.is_line_tracing)
field.traceRelease(MouseEvent(2, 1))
field.lclick = False
assert(len(field.section.contours["circle1"]) == 1)

# undo trace draw
field.undoState()

# imitate line-drawing a trace
points = [
    (0.5, 0.5),
    (0.5, 1.5),
    (1.5, 1.5),
    (1.5, 0.5)
]
for pt in points:
    field.lclick = True
    field.tracePress(MouseEvent(*pt))
    field.traceRelease(MouseEvent(*pt))
    field.lclick = True
field.backspace()  # test backspace function
assert(field.is_line_tracing)
field.rclick = True
field.tracePress(MouseEvent(1, 1))
field.traceRelease(MouseEvent(1, 1))
field.rclick = False
assert(len(field.section.contours["circle1"]) == 1)
assert(len(field.section.contours["circle1"][0].points) == 3)

# undo line draw
field.undoState()

# imitate placing a stamp
field.lclick = True
field.stampPress(MouseEvent(2, 2))
field.stampRelease(MouseEvent(2, 2))
field.lclick = False
assert(len(field.section.contours["circle1"]) == 1)

# undo stamp
field.undoState()

# imitate the knife tool
field.section.selected_traces = field.section.contours["square"].getTraces()
field.lclick = True
field.knifePress(MouseEvent(1.3, 1))
points = [
    (1.3, 0.8),
    (1.3, 0.6),
    (1.3, 0.4),
    (1.3, 0.2),
    (1.3, 0.01)
]
for pt in points:
    field.knifeMove(MouseEvent(*pt))
field.knifeRelease(MouseEvent(1.3, 0.01))
field.lclick = False
assert(len(field.section.contours["square"]) == 2)

# undo knife
field.undoState()

# redo knife
field.redoState()
assert(len(field.section.contours["square"]) == 2)

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# TEST FIELDVIEW FUNCTIONS

# create mainwindow from existing series
mainwindow = MainWindow(["", os.path.join(testing_dir, "shapes2.jser")])
field = mainwindow.field
original_window = mainwindow.series.window.copy()

# test reload functions
field.reload()
field.reloadImage()

# find a trace
field.findTrace("star", 0)
assert(field.section.selected_traces == field.section.contours["star"].getTraces())

# find a contour
field.findContour("square")
assert(field.section.selected_traces == field.section.contours["square"].getTraces())

# set view to home
field.home()

# move to a section and coords
field.moveTo(1, 1, 1)

# toggle hide all
field.toggleHideAllTraces()
field.toggleHideAllTraces()

# toggle show all
field.toggleShowAllTraces()
field.toggleShowAllTraces()

# test linear align
original_tform = field.section.tforms[mainwindow.series.alignment].getList()
field.changeSection(0)
field.section.selected_traces = field.section.contours["linalign"].getTraces()
field.changeSection(1)
field.section.selected_traces = field.section.contours["linalign"].getTraces()
field.linearAlign()
new_tform = field.section.tforms[mainwindow.series.alignment].getList()
assert(original_tform != new_tform)
field.changeSection(0)

# delete a trace
field.deleteTraces(field.section.contours["triangle"].getTraces())

# merge traces
field.deselectAllTraces()
field.findContour("merge")
field.mergeSelectedTraces()

# select/deselect all traces
field.selectAllTraces()
field.deselectAllTraces()

# hide and unhide traces
traces = field.section.contours["star"].getTraces()
traces += field.section.contours["square"].getTraces()
field.hideTraces(traces)
for trace in traces:
    assert(trace.hidden)
field.unhideAllTraces()
for trace in traces:
    assert(not trace.hidden)

# make negative, then positive
field.section.selected_traces = traces
field.makeNegative()
for trace in traces:
    assert(trace.negative)
field.makeNegative(False)
for trace in traces:
    assert(not trace.negative)
field.deselectAllTraces()

# test cut/copy/paste
field.findContour("star")
field.cut()
assert(len(field.section.contours["star"]) == 0)
field.paste()
assert(len(field.section.contours["star"]) == 1)
field.copy()
assert(len(field.section.contours["star"]) == 1)
field.paste()
assert(len(field.section.contours["star"]) == 2)
field.findContour("square")
field.pasteAttributes()
assert(len(field.section.contours["star"]) == 3)

# close the series (override save)
mainwindow.series.modified = False
mainwindow.close()

# delete the testing dir
shutil.rmtree(testing_dir)