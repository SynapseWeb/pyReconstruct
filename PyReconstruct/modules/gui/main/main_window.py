"""The main window."""


from .main_imports import *


class MainWindow(QMainWindow):

    def __init__(self, filename):
        """Constructs a skeleton for an empty main window."""
        super().__init__() # initialize QMainWindow

        ## Catch all exceptions and display errors
        sys.excepthook = customExcepthook  # defined in gui.utils

        self.setWindowTitle("PyReconstruct")
        self.setWindowIcon(QPixmap(icon_path))

        ## Set main window to slightly less than monitor
        screen = QApplication.primaryScreen()
        self.screen_info = get_screen_info(screen)

        self.setGeometry(
            50,                               # x
            80,                               # y 
            self.screen_info["width"] - 100,  # width
            self.screen_info["height"] - 160  # height
        )

        self.series                 =  None
        self.series_data            =  None
        self.field                  =  None
        self.menubar                =  None
        self.mouse_palette          =  None
        self.zarr_palette           =  None
        self.viewer                 =  None
        self.shortcuts_widget       =  None
        self.is_zooming             =  False
        self.restart_mainwindow     =  False
        self.check_actions_enabled  =  False
        self.actions_initialized    =  False

        ## Set constant tracking for mouse modes
        self.setMouseTracking(True)

        ## Create status bar bottom of main window
        self.statusbar = self.statusBar()

        ## Open series if requested thru CLI
        if filename and Path(filename).exists():
            
            self.openSeries(jser_fp=filename)

        ## Otherwise open welcome series
        else:

            self.openWelcomeSeries()

        ## Set main window as parent of progress bar
        setMainWindow(self)

        ## Set theme
        self.setTheme(self.series.getOption("theme"))

        self.show()

        ## Prompt for username
        self.changeUsername()

    def openWelcomeSeries(self):
        """Open a welcome series."""

        w_ser, w_secs, w_src = get_welcome_setup()
        welcome_series = Series(w_ser, w_secs)
        welcome_series.src_dir = w_src
            
        self.openSeries(series_obj=welcome_series)

    def test(self) -> None:
        """Run test here."""
        
        ##print(f"{QApplication.font().pointSize() = }")
        ##notify("Test message!")

        usage = self.series.getOption("cpu_max")
        cpus_to_use = determine_cpus(usage)

        print(f"{cpus_to_use = }")
        
    def createMenuBar(self):
        """Create the menu for the main window."""
        menu = return_menubar(self)

        if self.menubar:
            
            self.menubar.clear()
            
        else:
            
            self.menubar = self.menuBar()
            self.menubar.setNativeMenuBar(False)

        ## Populate menu bar with menus and options
        populateMenuBar(self, self.menubar, menu)

    def createContextMenus(self):
        """Create right-click menus used in the field."""
        ## Create user columns options
        field_menu_list = get_field_menu_list(self)
        self.field_menu = QMenu(self)
        populateMenu(self, self.field_menu, field_menu_list)

        ## Organize actions
        self.trace_actions = [
            self.tracemenu,
            self.objectmenu,
            self.cut_act,
            self.copy_act,
            self.pasteattributes_act,
        ]
        self.ztrace_actions = [
            self.ztracemenu
        ]

        ## Create label menu
        label_menu_list = [
            # ("importlabels_act", "Import label(s)", "", self.importLabels),
            # ("mergelabels_act", "Merge labels", "", self.mergeLabels)
        ]
        self.label_menu = QMenu(self)
        populateMenu(self, self.label_menu, label_menu_list)

        ## Check alignment in alignment submenu
        self.changeAlignment(self.series.alignment)

    def checkActions(self, context_menu=False, clicked_trace=None, clicked_label=None):
        """Define enabled and disabled actions based on field context.
        
            Params:
                context_menu (bool): True if context menu is being generated
                clicked_trace (Trace): the trace that was clicked on IF the cotext menu is being generated
        """
        ## Skip if actions not initialized
        if not self.actions_initialized:
            return

        field_section = self.field.section
        selected_traces = field_section.selected_traces
        selected_ztraces = field_section.selected_ztraces
        
        ## Allow only general field options if
        ##   1. both traces and z traces highlighted or
        ##   2. nothing highlighted
        
        if not (bool(selected_traces) ^ bool(selected_ztraces)):
            
            for a in self.trace_actions: a.setEnabled(False)
            for a in self.ztrace_actions: a.setEnabled(False)
                
        ## If selected trace in highlighted traces
        
        elif ((not context_menu and selected_traces) or
              (context_menu and clicked_trace in selected_traces)
        ):
            
            for a in self.ztrace_actions: a.setEnabled(False)
            for a in self.trace_actions: a.setEnabled(True)
                
        ## If selected ztrace in highlighted ztraces
        
        elif ((not context_menu and field_section.selected_ztraces) or
              (context_menu and clicked_trace in field_section.selected_ztraces)
        ):
            
            for a in self.trace_actions: a.setEnabled(False)
            for a in self.ztrace_actions: a.setEnabled(True)
            
        else:
            
            for a in self.trace_actions: a.setEnabled(False)
            for a in self.ztrace_actions: a.setEnabled(False)

        # check labels
        if clicked_label:
            if clicked_label in self.field.zarr_layer.selected_ids:
                self.importlabels_act.setEnabled(True)
                if len(self.zarr_layer.selected_ids) > 1:
                    self.mergelabels_act.setEnabled(True)
            else:
                self.importlabels_act.setEnabled(False)
                self.mergelabels_act.setEnabled(False)
        
        #### Menubar ###############################################################################

        ## Disable saving welcome series
        is_not_welcome_series = not self.series.isWelcomeSeries()
        self.save_act.setEnabled(is_not_welcome_series)
        self.saveas_act.setEnabled(is_not_welcome_series)
        self.backupmenu.setEnabled(is_not_welcome_series)

        ## Check for palette
        self.togglepalette_act.setChecked(not self.mouse_palette.palette_hidden)
        self.toggleinc_act.setChecked(not self.mouse_palette.inc_hidden)
        self.togglebc_act.setChecked(not self.mouse_palette.bc_hidden)
        self.togglesb_act.setChecked(not self.mouse_palette.sb_hidden)

        ## Group visibility
        for group, viz in self.series.groups_visibility.items():
            try:
                menu_attr = getattr(self, f"{group}_viz_act")
                menu_attr.setChecked(viz)
            except AttributeError:
                pass

        ## Undo/redo
        can_undo_3D, can_undo_2D, _ = self.field.series_states.canUndo(self.field.section.n)
        self.undo_act.setEnabled(can_undo_3D or can_undo_2D)
        can_redo_3D, can_redo_2D, _ = self.field.series_states.canUndo(self.field.section.n, redo=True)
        self.redo_act.setEnabled(can_redo_3D or can_redo_2D)

        ## Check clipboard for paste options
        if self.field.clipboard:
            self.paste_act.setEnabled(True)
        else:
            self.paste_act.setEnabled(False)
            self.pasteattributes_act.setEnabled(False)

        ## Zarr images
        self.zarrimage_act.setEnabled(not self.field.section_layer.is_zarr_file)
        self.scalezarr_act.setEnabled(self.field.section_layer.is_zarr_file)

        ## Calibrate
        self.calibrate_act.setEnabled(bool(self.field.section.selected_traces))

        # ## Zarr layer
        # self.removezarrlayer_act.setEnabled(bool(self.series.zarr_overlay_fp))
            
    def createShortcuts(self):
        """Create shortcuts that are NOT included in any menus."""
        # domain translate motions
        shortcuts = [
            ("Backspace", self.backspace),

            ("Ctrl+Left", lambda : self.translate("left", "small")),
            ("Left", lambda : self.translate("left", "med")),
            ("Shift+Left", lambda : self.translate("left", "big")),
            ("Ctrl+Right", lambda : self.translate("right", "small")),
            ("Right", lambda : self.translate("right", "med")),
            ("Shift+Right", lambda : self.translate("right", "big")),
            ("Ctrl+Up", lambda : self.translate("up", "small")),
            ("Up", lambda : self.translate("up", "med")),
            ("Shift+Up", lambda : self.translate("up", "big")),
            ("Ctrl+Down", lambda : self.translate("down", "small")),
            ("Down", lambda : self.translate("down", "med")),
            ("Shift+Down", lambda : self.translate("down", "big")),

            ("Ctrl+Shift+Left", self.field.rotateTform),
            ("Ctrl+Shift+Right", lambda : self.field.rotateTform(cc=False)),

            ("F1", lambda : self.field.scaleTform(sx=1.005)),
            ("Shift+F1", lambda : self.field.scaleTform(sx=0.995)),
            ("F2", lambda : self.field.scaleTform(sy=1.005)),
            ("Shift+F2", lambda : self.field.scaleTform(sy=0.995)),
            ("F3", lambda : self.field.shearTform(sx=0.005)),
            ("Shift+F3", lambda : self.field.shearTform(sx=-0.005)),
            ("F4", lambda : self.field.shearTform(sy=0.005)),
            ("Shift+F4", lambda : self.field.shearTform(sy=-0.005)),
        ]

        for kbd, act in shortcuts:
            self.addAction("", kbd, act)
    
    def createPaletteShortcuts(self):
        """Create shortcuts associate with the mouse palette."""
        # trace palette shortcuts (1-20)
        trace_shortcuts = []
        for i in range(1, 21):
            sc_str = ""
            if (i-1) // 10 > 0:
                sc_str += "Shift+"
            sc_str += str(i % 10)
            s_switch = (
                sc_str,
                lambda pos=i-1 : self.mouse_palette.activatePaletteButton(pos)
            )
            s_modify = (
                "Ctrl+" + sc_str,
                lambda pos=i-1 : self.mouse_palette.modifyPaletteButton(pos)
            )
            trace_shortcuts.append(s_switch)
            trace_shortcuts.append(s_modify)
        
        for kbd, act in trace_shortcuts:
            self.addAction("", kbd, act)

        
        # mouse mode shortcuts (F1-F8)
        mode_shortcuts = [
            ("usepointer_act", lambda : self.mouse_palette.activateModeButton("Pointer")),
            ("usepanzoom_act", lambda : self.mouse_palette.activateModeButton("Pan/Zoom")),
            ("useknife_act", lambda : self.mouse_palette.activateModeButton("Knife")),
            ("usectrace_act", lambda : self.mouse_palette.activateModeButton("Closed Trace")),
            ("useotrace_act", lambda : self.mouse_palette.activateModeButton("Open Trace")),
            ("usestamp_act", lambda : self.mouse_palette.activateModeButton("Stamp")),
            ("usegrid_act", lambda : self.mouse_palette.activateModeButton("Grid")),
            ("useflag_act", lambda : self.mouse_palette.activateModeButton("Flag")),
            ("usehost_act", lambda : self.mouse_palette.activateModeButton("Host")),
        ]
  
        for act_name, act in mode_shortcuts:
            setattr(
                self, 
                act_name, 
                self.addAction("", self.series.getOption(act_name), act)
            )
    
    def changeSrcDir(self, new_src_dir : str = None, notify=False):
        """Open a series of dialogs to change the image source directory.
        
            Params:
                new_src_dir (str): the new image directory
                notify (bool): True if user is to be notified with a pop-up
        """
        if notify:
            reply = QMessageBox.question(
                self,
                "Images Not Found",
                "Images not found.\nWould you like to locate them?",
                QMessageBox.Yes,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        if new_src_dir is None:
            new_src_dir = FileDialog.get(
                "dir",
                self,
                "Select folder containing images",
            )
        if not new_src_dir: return
        
        self.series.src_dir = new_src_dir
        if self.field:
            self.field.reloadImage()
        self.seriesModified(True)
        
        # prompt user to scale zarr images if not scaled
        if (self.field.section_layer.image_found and 
            self.field.section_layer.is_zarr_file and
            not self.field.section_layer.is_scaled):
            reply = QMessageBox.question(
                self,
                "Zarr Scaling",
                "Zarr file not scaled.\nWould you like to update the zarr with scales?",
                QMessageBox.Yes,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.srcToZarr(create_new=False)
    
    def srcToZarr(self, create_new=True):
        """Convert the series images to scaled zarr."""
        if not self.field.section_layer.image_found:
            notify("Images not found.")
            return
        
        if self.field.section_layer.is_zarr_file and create_new:
            notify("Images are already scaled.")
            return
        
        elif not self.field.section_layer.is_zarr_file and not create_new:
            notify(
                "Images are not in zarr format.\n"
                "Please convert to zarr first."
            )
            return
        
        if create_new:
            zarr_fp = FileDialog.get(
                "save",
                self,
                "Convert Images to scaled zarr",
                file_name=f"{self.series.name}_images.zarr",
                filter="Zarr Directory (*.zarr)"
            )
            if not zarr_fp: return

        python_bin = sys.executable
        zarr_converter = Path(assets_dir) / "scripts/start_process.py"

        cores = determine_cpus(  # determine number of cores to use
            self.series.getOption("cpu_max")
        )
        
        if create_new:
            
            convert_cmd = [
                python_bin,
                str(zarr_converter.absolute()),
                "convert_zarr",
                str(cores),
                self.series.src_dir, zarr_fp
            ]
            
        else:
            
            convert_cmd = [
                python_bin,
                str(zarr_converter.absolute()),
                "convert_zarr",
                str(cores),
                self.series.src_dir
            ]

        if os.name == 'nt':

            subprocess.Popen(
                convert_cmd, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
        else:

            convert_cmd = " ".join(convert_cmd)
            subprocess.Popen(convert_cmd, shell=True, stdout=None, stderr=None)

    def changeUsername(self, new_name : str = None):
        """Edit the login name used to track history.
        
            Params:
                new_name (str): the new username
        """
        if new_name is None:
            new_name, confirmed = QInputDialog.getText(
                self,
                "Username",
                "Enter your username:",
                text=QSettings("KHLab", "PyReconstruct").value("username", self.series.user),
            )
            if not confirmed or not new_name:
                return
        
        QSettings("KHLab", "PyReconstruct").setValue("username", new_name)
        self.series.user = new_name

        self.notifyNewEditor()
    
    def setFillOpacity(self, opacity : float = None):
        """Set the opacity of the trace highlight.
        
            Params:
                opacity (float): the new fill opacity
        """
        if opacity is None:
            opacity, confirmed = QInputDialog.getText(
                self,
                "Fill Opacity",
                "Enter fill opacity (0-1):",
                text=str(round(self.series.getOption("fill_opacity"), 3))
            )
            if not confirmed:
                return
        
        try:
            opacity = float(opacity)
        except ValueError:
            return
        
        if not (0 <= opacity <= 1):
            return
        
        self.series.setOption("fill_opacity", opacity)
        self.field.generateView(generate_image=False)

    def openSeries(self, series_obj=None, jser_fp=None, query_prev=True):
        """Open an existing series and create the field.
        
            Params:
                series_obj (Series): the series object (optional)
                query_prev (bool): True if query user about saving data
        """

        if self.series:  # series open and save yes
            
            first_open = False

            if query_prev:
                
                response = self.saveToJser(notify=True, close=True)
                
                if response == "cancel":
                    return
            else:

                self.series.close()
                    
        else:

            first_open = True
        
        if not series_obj:  # if series is not provided            
            # get the new series
            new_series = None
            if not jser_fp:
                jser_fp = FileDialog.get("file", self, "Open Series", filter="*.jser")
                if not jser_fp: return  # exit function if user does not provide series

            # check for a hidden series folder
            sdir = os.path.dirname(jser_fp)
            sname = os.path.basename(jser_fp)
            sname = sname[:sname.rfind(".")]
            hidden_series_dir = os.path.join(sdir, f".{sname}")

            if os.path.isdir(hidden_series_dir):
                # find the series and timer files
                new_series_fp = ""
                sections = {}
                for f in os.listdir(hidden_series_dir):
                    # check if the series is currently being modified
                    if "." not in f:
                        current_time = round(time.time())
                        time_diff = current_time - int(f)
                        if time_diff <= 7:  # the series is currently being operated on
                            QMessageBox.information(
                                self,
                                "Series In Use",
                                "This series is already open in another window.",
                                QMessageBox.Ok
                            )
                            if not self.series:
                                exit()
                            else:
                                return
                    else:
                        ext = f[f.rfind(".")+1:]
                        if ext.isnumeric():
                            sections[int(ext)] = f
                        elif ext == "ser":
                            new_series_fp = os.path.join(hidden_series_dir, f)                    

                # if a series file has been found
                if new_series_fp:
                    # ask the user if they want to open a previously unsaved series
                    open_unsaved = unsavedNotify()
                    if open_unsaved:
                        new_series = Series(new_series_fp, sections)
                        new_series.modified = True
                        new_series.jser_fp = jser_fp
                    else:
                        # remove the folder if not needed
                        for f in os.listdir(hidden_series_dir):
                            os.remove(os.path.join(hidden_series_dir, f))
                        os.rmdir(hidden_series_dir)
                else:
                    # remove the folder if no series file detected
                    for f in os.listdir(hidden_series_dir):
                        os.remove(os.path.join(hidden_series_dir, f))
                    os.rmdir(hidden_series_dir)

            # open the JSER file if no unsaved series was opened
            if not new_series:
                new_series = Series.openJser(jser_fp)
                # user pressed cancel
                if new_series is None:
                    if self.series is None:
                        exit()
                    else:
                        return
            
            # clear the series
            if self.series and not self.series.isWelcomeSeries():
                self.series.close()

            self.series = new_series

        # else series already provided
        else:
            # clear current series
            if self.series and not self.series.isWelcomeSeries():
                self.series.close()
                
            # set new series
            self.series = series_obj
        
        # set the title of the main window
        self.seriesModified(self.series.modified)

        # set explorer filepath
        if not self.series.isWelcomeSeries() and self.series.jser_fp:
            settings = QSettings("KHLab", "PyReconstruct")
            settings.setValue("last_folder", os.path.dirname(self.series.jser_fp))

        # create field
        if self.field is not None:  # close previous field widget
            self.field.createField(self.series)
        else:
            self.field = FieldWidget(self.series, self)
            self.setCentralWidget(self.field)

        # create mouse palette
        if self.mouse_palette: # close previous mouse dock
            self.mouse_palette.reset()
        else:
            self.mouse_palette = MousePalette(self)
            self.createPaletteShortcuts()
        palette_group, index = tuple(self.series.palette_index)
        self.changeTracingTrace(
            self.series.palette_traces[palette_group][index]
        ) # set the current trace

        # ensure that images are found
        if not self.field.section_layer.image_found:
            # check jser directory
            src_path = os.path.join(
                os.path.dirname(self.series.jser_fp),
                os.path.basename(self.field.section.src)
            )
            images_found = os.path.isfile(src_path)
            
            if images_found:
                self.changeSrcDir(src_path)
            else:
                self.changeSrcDir(notify=True)
        # prompt user to scale zarr images if not scaled
        elif (self.field.section_layer.image_found and 
            self.field.section_layer.is_zarr_file and
            not self.field.section_layer.is_scaled):
            reply = QMessageBox.question(
                self,
                "Zarr Scaling",
                "Zarr not scaled.\nWould you like to scale now?",
                QMessageBox.Yes,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.srcToZarr(create_new=False)
        
        # get the series code from the user if needed
        if not self.series.isWelcomeSeries() and not self.series.code:
            detected_code = re.search(
                self.series.getOption("series_code_pattern"), 
                self.series.name
            )
            if detected_code:
                self.series.code = detected_code.group()
            self.setSeriesCode(cancelable=False)
            self.seriesModified()
        
        # notify new users of any warnings
        if not first_open:
            self.notifyNewEditor()
        
        # create the menus
        self.createMenuBar()
        self.createContextMenus()
        if not self.actions_initialized:
            self.createShortcuts()
        self.actions_initialized = True

        # add the series to recently opened
        self.addToRecentSeries()
        
    def newSeries(
        self,
        image_locations : list = None,
        series_name : str = None,
        mag : float = None,
        thickness : float = None,
        from_zarr : bool = False
    ):
        """Create a new series from a set of images.
        
            Params:
                image_locations (list): the filepaths for the section images.
        """

        ## Save existing backend series
        self.saveToJser(notify=True, close=False)
        
        ## Query user for images
        if not image_locations:
            if from_zarr:
                valid_zarr = False
                while not valid_zarr:
                    zarr_fp = FileDialog.get(
                        "dir",
                        self,
                        "Select Zarr"
                    )
                    if not zarr_fp: return
                    
                    # get the image names in the zarr
                    if "scale_1" in os.listdir(zarr_fp):
                        valid_zarr = True
                        image_locations = []
                        for f in os.listdir(os.path.join(zarr_fp, "scale_1")):
                            if not f.startswith("."):
                                image_locations.append(os.path.join(zarr_fp, "scale_1", f))
                    else:
                        notify("Please select a valid zarr file.")                
            else:
                image_locations = FileDialog.get(
                    "files",
                    self,
                    "Select Images",
                    filter="*.jpg *.jpeg *.png *.tif *.tiff *.bmp"
                )
                if len(image_locations) == 0: return
        
        ## Query user for series name
        if series_name is None:
            series_name, confirmed = QInputDialog.getText(
                self, "New Series", "Enter series name:")
            if not confirmed:
                return
            
        ## Query user for calibration (microns per px)
        if mag is None:
            mag, confirmed = QInputDialog.getDouble(
                self, "New Series", "Enter image calibration (μm/px):",
                0.00254, minValue=0.000001, decimals=6)
            if not confirmed:
                return
            
        ## Query user for section thickness (microns)
        if thickness is None:
            thickness, confirmed = QInputDialog.getDouble(
                self, "New Series", "Enter section thickness (μm):",
                0.05, minValue=0.000001, decimals=6)
            if not confirmed:
                return

        ## Create new series
        series = Series.new(
            sorted(image_locations),
            series_name,
            mag,
            thickness
        )
    
        ## Open series
        ## No need to query user about saving prev (already done above)
        self.openSeries(series, query_prev=False)

        ## Set view to entire image
        self.field.home()

        ## Prompt user to save series
        self.saveAsToJser()
    
    def newFromXML(self, series_fp : str = None):
        """Create a new series from a set of XML files.
        
            Params:
                series_fp (str): the filepath for the XML series
        """

        # get xml series from user
        if not series_fp:
            series_fp = FileDialog.get(
                "file",
                self,
                "Select XML Series",
                filter="*.ser"
            )
            if not series_fp: return  # exit function if no series provided

        # convert the series
        series = xmlToJSON(os.path.dirname(series_fp))

        if not series:
            return

        # open new series
        self.openSeries(series)

        # prompt user to save series
        self.saveAsToJser()
    
    def newFromNgZarr(self):
        """Create a new series from a neuroglancer zarr."""
        zarr_fp = FileDialog.get(
            "dir",
            self,
            "Select Zarr File"
        )
        if not zarr_fp:
            return
                
        if not zarr_fp.endswith("zarr"):
            notify("Selected file is not a valid zarr.")
        
        groups = [f for f in os.listdir(zarr_fp) if not f.startswith(".") and not f=="raw"]

        structure = [
            ["New series name:", (True, "text", ""), " "],
            ["Labels to import:"],
            [("multicombo", groups, [])],
        ]
        response, confirmed = QuickDialog.get(self, structure, "New from NG Zarr")
        if not confirmed:
            return
        
        name = response[0]
        label_groups = [g for g in response[1] if g in groups]

        series = zarrToNewSeries(zarr_fp, label_groups, name)

        if not series:
            return

        # open new series
        self.openSeries(series)

        # prompt user to save series
        self.saveAsToJser()
    
    def exportToXML(self, export_fp : str = None):
        """Export the current series to XML.
        
            Params:
                export_fp (str): the filepath for the XML .ser file
        """

        # save the current data
        self.saveAllData()

        # get the new xml series filepath from the user
        if not export_fp:
            export_fp = FileDialog.get(
                "save",
                self,
                "Export Series",
                file_name=f"{self.series.name}.ser",
                filter="XML Series (*.ser)"
            )
            if not export_fp: return False
        
        # convert the series
        jsonToXML(self.series, os.path.dirname(export_fp))
    
    def seriesModified(self, modified=True):
        """Change the title of the window reflect modifications."""
        # check for welcome series
        if self.series.isWelcomeSeries():
            self.setWindowTitle("PyReconstruct")
            return
        
        if modified:
            self.setWindowTitle(self.series.name + "*")
        else:
            self.setWindowTitle(self.series.name)
        self.series.modified = modified

        if self.field:
            self.checkActions()
    
    def importTransforms(self, tforms_fp : str = None):
        """Import transforms from a text file.
        
            Params:
                tforms_file (str): the filepath for the transforms file
        """
        self.saveAllData()
        # get file from user
        if tforms_fp is None:
            tforms_fp = FileDialog.get(
                "file",
                self,
                "Select file containing transforms"
            )
        if not tforms_fp: return
        
        # import the transforms
        importTransforms(self.series, tforms_fp, series_states=self.field.series_states)
        
        # reload the section
        self.field.reload()

        # refresh the data and lists
        self.field.table_manager.recreateTables()

        notify("Transforms imported successfully.")

    def importSwiftTransforms(self, swift_fp=None):
        """Import transforms from a text file.
        
            Params:
                swift_fp (str): the filepath for the transforms file
        """

        self.saveAllData()
        
        # get file from user
        if not swift_fp:
            swift_fp = FileDialog.get("file", self, "Select SWiFT project file")
            
        if not swift_fp:
            return

        # get scales from the swift project file
        with open(swift_fp, "r") as fp: swift_json = json.load(fp)

        scale_names = swift_json.get("level_data")

        if scale_names:  # new swift project file formatting
        
            scale_names = list(swift_json["level_data"].keys())
            scales_available = [int(scale[1:]) for scale in scale_names]

        else:  # old swift project file formatting

            scales_data = swift_json["data"]["scales"]
            scale_names = list(scales_data.keys())
            scales_available = [int(scale[6:]) for scale in scale_names]

        scales_available.sort()
        
        print(f'Available SWiFT project scales: {scales_available}')

        structure = [
            ["Scale:", (True, "combo", [str(s) for s in scales_available])],
            [("check", ("Includes cal grid", False))]
        ]

        response, confirmed = QuickDialog.get(self, structure, "Import SWiFT Transforms")
        if not confirmed:
            return
        scale = response[0]
        cal_grid = response[1][0][1]

        # import transforms
        print(f'Importing SWiFT transforms at scale {scale}...')
        if cal_grid: print('Cal grid included in series')
        importSwiftTransforms(self.series, swift_fp, scale, cal_grid, series_states=self.field.series_states)
        
        self.field.reload()

        # refresh the data and lists
        self.field.table_manager.recreateTables()

        notify("Transforms imported successfully.")
    
    def editImage(self, option : str, direction : str, log_event=True):
        """Edit the brightness or contrast of the image.
        
            Params:
                option (str): brightness or contrast
                direction (str): up or down
        """
        if option == "brightness" and direction == "up":
            self.field.changeBrightness(1)
        elif option == "brightness" and direction == "down":
            self.field.changeBrightness(-1)
        elif option == "contrast" and direction == "up":
            self.field.changeContrast(2)
        elif option == "contrast" and direction == "down":
            self.field.changeContrast(-2)
        self.mouse_palette.updateBC()
    
    def changeMouseMode(self, new_mode):
        """Change the mouse mode of the field (pointer, panzoom, tracing...).

        Called when user clicks on mouse mode palette.

            Params:
                new_mode: the new mouse mode to set
        """
        self.field.setMouseMode(new_mode)
    
    def changeTraceMode(self):
        """Change the trace mode and shape."""

        current_shape = self.field.closed_trace_shape
        current_mode = self.series.getOption("trace_mode")

        structure = [
            ["Mode:"],
            [("radio",
                ("Scribble", current_mode == "scribble"),
                ("Poly", current_mode == "poly"),
                ("Combo", current_mode == "combo")
            )],
            ["Closed Trace Shape:"],
            [("radio",
                ("Trace", current_shape == "trace"),
                ("Rectangle", current_shape == "rect"),
                ("Ellipse", current_shape == "circle")
            )],
            [("check", ("Automatically merge selected traces", self.series.getOption("auto_merge")))],
            [("check", ("Apply rolling average while scribbling", self.series.getOption("roll_average"))),
             ("int", self.series.getOption("roll_window"))]
        ]

        response, confirmed = QuickDialog.get(self, structure, "Closed Trace Mode")

        if not confirmed:
            return
        
        if response[0][0][1]:
            new_mode = "scribble"

        elif response[0][1][1]:
            new_mode = "poly"

        else:
            new_mode = "combo"
        
        if response[1][1][1]:
            new_shape = "rect"

        elif response[1][2][1]:
            new_shape = "circle"

        else:
            new_shape = "trace"
        
        self.series.setOption("trace_mode", new_mode)
        self.field.closed_trace_shape = new_shape
        
        self.series.setOption("auto_merge", response[2][0][1])
        self.series.setOption("roll_average", response[3][0][1])
        self.series.setOption("roll_window", response[4])

    def changeTracingTrace(self, trace):
        """Change trace utilized by the user.

        Called when user clicks on trace palette.

            Params:
                trace: the new tracing trace to set
        """
        self.field.setTracingTrace(trace)
    
    def changeSection(self, section_num : int = None, save=True):
        """Change the section of the field.
        
            Params:
                section_num (int): the section number to change to
                save (bool): saves data to files if True
        """
        if section_num is None:
            
            section_num, confirmed = QInputDialog.getText(
                self,
                "Go To Section",
                "Enter a section number:",
                text=str(self.series.current_section))
            if not confirmed:
                return
            try:
                section_num = int(section_num)
            except ValueError:
                return
        
        # end the field pending events
        self.field.endPendingEvents()
        # save data
        if save:
            self.saveAllData()
        # change the field section
        self.field.changeSection(section_num)
        # update status bar
        self.field.updateStatusBar()
        # update the mouse palette
        self.mouse_palette.updateBC()
    
    def flickerSections(self):
        """Switch between the current and b sections."""
        if self.field.b_section:
            self.changeSection(self.field.b_section.n, save=False)

    def exportSectionSVG(self):
        """Export untransformed traces as svg."""

        if not modules_available("svgwrite", notify=True):
            return

        self.saveToJser()

        s = self.series.current_section

        fp = FileDialog.get(
            "save",
            self,
            "Save section as svg",
            filter="*.svg",
            file_name=f"{self.series.name}_{s}.svg"
        )
        if not fp: return
        
        svg = self.series.loadSection(s).exportAsSVG(fp)
        
        notify(f"Traces exported to file:\n\n{svg}")

    def exportSectionPNG(self):
        """Export untransformed traces as png."""

        if not modules_available(["svgwrite", "cairosvg"], notify=True):
            return

        self.saveToJser()

        s = self.series.current_section

        fp = FileDialog.get(
            "save",
            self,
            "Save section as png",
            filter="*.png",
            file_name=f"{self.series.name}_{s}.png"
        )
        if not fp: return

        scale, confirmed = QInputDialog.getText(
            self,
            "Resolution",
            "Scale image (Full resolution = 1.0):",
            text='1.0'
        )
        if not confirmed:
            return False
        
        png = self.series.loadSection(s).exportAsPNG(fp, float(scale))
        
        notify(f"Traces exported to file:\n\n{png}")

    def downloadExample(self):
        """Download example kharris2015 images to local machine."""
                
        if not modules_available(["cloudvolume", "tifffile"], notify=True):
            return

        confirm = notifyConfirm(
            "Harris2015 is a published volume (~2 nm/px, ~50 nm section thickness) from the "
            "middle of stratum radiatum in hippocampal area CA1 of an adult rat (p77). It is "
            "stored remotely at neurodata.io and a small subvolume of 10 sections can be "
            "downloaded here.\n\n"
            "See the publication:\n\n"
            "Harris et al. (2015) A resource from 3D electron microscopy of hippocampal "
            "neuropil for user training and tool development. Sci Data Sep 1;2:150046. PMID:"
            "26347348\n\n"
            "Click OK to select a location to store example images."
        )

        if not confirm: return

        download_dir = FileDialog.get(
                "dir",
                self,
                "Select folder to store images",
            )
        
        if not download_dir: return

        success = download_vol_as_tifs(
            kharris2015,
            [[2560, 4560], [2072, 4072], [48, 58]],
            output_dir=download_dir,
            output_prefix="harris2015"
        )

        if success:

            notify(
                "harris2015 example images downloaded successfully to:\n\n"
                f"{download_dir}\n\n"
                "Start a new series by going to File > New from images and selecting "
                "the downloaded images."
            )

        if not success:

            notify(
                "Something went wrong. Please try downloading example images again."
            )

    def randomizeProject(self):

        response = notifyConfirm(
            (
                "This feature randomizes images from multiple series, codes the images, "
                "and produces a single jser. You must provide a project directory that "
                "contains one to many subdirectories, each containing images for a "
                "series.<br><br>Something like this:"
                "<p style='font-family: monospace;'>&nbsp;&nbsp;project_dir<br>"
                "&nbsp;&nbsp;├── series_1<br>"
                "&nbsp;&nbsp;│   ├── 1.tif<br>"
                "&nbsp;&nbsp;│   └── 2.tif<br>"
                "&nbsp;&nbsp;└── series_2<br>"
                "&nbsp;&nbsp;&nbsp;&nbsp;    ├── 1.tif<br>"
                "&nbsp;&nbsp;&nbsp;&nbsp;    └── 2.tif</p>"
                "Would you like to continue to select a project directory?"
            )
        )
        if response == False:
            return

        project_dir = FileDialog.get(
            "dir",
            self,
            "Select a project directory",
        )
        if not project_dir: return

        response = notifyConfirm(
            (
                "You are about to randomize images for the following project:\n\n"
                f"{project_dir}\n\n"
                "Are you sure you want to proceed?"
            )
        )
        if response == False:
            return

        jser_coded = randomize_project(project_dir)
        
        notify(
            "Project randomized and ready in:\n\n"
            f"{jser_coded}\n\n"
            "Note: A file with decoding information (decode.txt) is available in "
            "the project dir. Do not lose that file -- you will need it later to "
            "de-randomize your images."
        )

    def derandomizeProject(self):

        response = notifyConfirm(
            "You are about to de-randomize and decode a project. "
            "Are you sure you want to continue to select a coded jser?"
        )

        if response == False:
            return

        coded_jser = FileDialog.get(
            "file",
            self,
            "Select coded jser",
            filter="*.jser"
        )

        if not coded_jser:
            return

        if self.series.jser_fp == coded_jser:

            notify(
                "You have this series open right now. Please save and close it "
                "before proceeding."
            )

            return

        decode_info = Path(coded_jser).parent / "decode.txt"

        if not decode_info.exists():
            
            notify(
                f"No decoding information available at:\n\n{decode_info}"
                "\n\nPlease make sure this file exists in the proper format. "
                "(This file was created when the project was randomized.)"
            )

            return

        response = notifyConfirm(
            (
                "You are about to de-randomize and decode the following project:\n\n"
                f"{coded_jser}\n\n"
                "Are you sure you want to proceed?"
            )
        )

        if response == False:
            return

        project_dir = derandomize_project(coded_jser)

        notify(
            "Project decoded and ready in:\n\n"
            f"{project_dir}"
        )

    def incrementSection(self, down=False):
        """Increment the section number by one.
        
            Params:
                down (bool): the direction to move
        """
        section_numbers = sorted(list(self.series.sections.keys()))  # get list of section numbers
        section_number_i = section_numbers.index(self.series.current_section)  # get current section index
        if down:
            if section_number_i > 0:
                self.changeSection(section_numbers[section_number_i - 1])  
        else:   
            if section_number_i < len(section_numbers) - 1:
                self.changeSection(section_numbers[section_number_i + 1])       
    
    def wheelEvent(self, event):
        """Called when mouse scroll is used."""
        # do nothing if middle button is clicked
        if self.field.mclick:
            return
        
        modifiers = QApplication.keyboardModifiers()

        # if zooming
        if modifiers == Qt.ControlModifier:
            self.activateWindow()
            field_cursor = self.field.cursor()
            p = self.field.mapFromGlobal(field_cursor.pos())
            x, y = p.x(), p.y()
            if not self.is_zooming:
                # check if user just started zooming in
                self.field.panzoomPress(x, y)
                self.zoom_factor = 1
                self.is_zooming = True

            if event.angleDelta().y() > 0:  # if scroll up
                self.zoom_factor *= 1.1
            elif event.angleDelta().y() < 0:  # if scroll down
                self.zoom_factor *= 0.9
            self.field.panzoomMove(zoom_factor=self.zoom_factor)
        
        # if changing sections
        elif modifiers == Qt.NoModifier:
            # check for the position of the mouse
            mouse_pos = event.point(0).pos()
            field_geom = self.field.geometry()
            if not field_geom.contains(mouse_pos.x(), mouse_pos.y()):
                return
            # change the section
            if event.angleDelta().y() > 0:  # if scroll up
                self.incrementSection()
            elif event.angleDelta().y() < 0:  # if scroll down
                self.incrementSection(down=True)
    
    def keyReleaseEvent(self, event):
        """Overwritten: checks for Ctrl+Zoom."""
        if self.is_zooming and event.key() == 16777249:
            self.field.panzoomRelease(zoom_factor=self.zoom_factor)
            self.is_zooming = False
        
        super().keyReleaseEvent(event)
    
    def saveAllData(self):
        """Write current series and section data into hidden files."""
        if self.series.isWelcomeSeries():
            return
        # # save the trace palette
        # self.series.palette_traces = []
        # for button in self.mouse_palette.palette_buttons:  # get trace palette
        #     self.series.palette_traces.append(button.trace)
        #     if button.isChecked():
        #         self.series.current_trace = button.trace
        self.field.section.save(update_series_data=False)
        self.series.save()
    
    def backup(self, check_auto=False, comment=""):
        """Automatically backup the jser if requested."""
        if check_auto and not self.series.getOption("autobackup"):
            return
        
        # make sure the backup directory exists
        if not os.path.isdir(self.series.getOption("backup_dir")):
            notify(
                "Backup folder not found.\n" + 
                "Please set the backup folder in following dialog."
            )
            self.series.setOption("backup_dir", "")
            self.setBackup()
        
        # double check if user entered a valid backup directory
        if os.path.isdir(self.series.getOption("backup_dir")):
            fp = self.series.getBackupPath(comment)
            self.series.saveJser(fp)
        else:
            notify(
                "Backup folder not found.\n" +
                "Backup file not saved."
            )
            self.series.setOption("backup_dir", "")
            self.series.setOption("autobackup", False)
    
    def saveToJser(self, notify=False, close=False):
        """Store data in JSER file.
        
        Params:
            notify (bool): If true, display notification.
            close (bool): If true, delete hidden series files.
        """

        ## If welcome series, close without saving
        if self.series.isWelcomeSeries():
            return

        ## Populate hidden files with unsaved data
        self.saveAllData()

        ## Notify (query) user when series modified
        if notify and self.series.modified:
            save = saveNotify()
            if save == "no":
                if close:
                    self.series.close()
                return
            elif save == "cancel":
                return "cancel"
        
        # User closing and series not modified
        if close and not self.series.modified:
            self.series.close()
            return

        ## Save-as if no jser filepath
        if not self.series.jser_fp:
            self.saveAsToJser(close=close)
        else:  
            self.backup(check_auto=True)
            self.series.saveJser(close=close)
        
        # mark series as unmodified
        self.seriesModified(False)
    
    def saveAsToJser(self, close=False):
        """Prompt user for save location."""
        ## Store series data in hidden files
        self.saveAllData()

        ## If welcome series, close without saving
        if self.series.isWelcomeSeries():
            return

        ## Query user for location
        new_jser_fp = FileDialog.get(
            "save",
            self,
            "Save Series",
            filter="*.jser",
            file_name=f"{self.series.name}.jser"
        )
        if not new_jser_fp: return
        
        ## Move hidden folder to new jser directory        
        self.series.move(
            new_jser_fp,
            self.field.section,
            self.field.b_section
        )
        
        # clear section states
        self.field.series_states.clear()
        self.field.series_states[self.field.section]
        if self.field.b_section:
            self.field.series_states[self.field.b_section]
        
        # save file
        self.backup(check_auto=True)
        self.series.saveJser(close=close)

        # mark series as unmodified
        self.seriesModified(False)
    
    def setBackup(self):
        """Set up backup directory and settings."""
        confirmed = BackupDialog(self, self.series).exec()
        self.seriesModified()
    
    def manualBackup(self):
        """Back up series to a specified location."""
        self.saveAllData()

        response, confirmed = BackupCommentDialog(self, self.series).exec()
        if not confirmed:
            return
        
        comment, open_settings = response
        if open_settings:
            self.setBackup()
            self.manualBackup()
        else:
            self.backup(comment=comment)
    
    def viewSeriesHistory(self):
        """View the history for the entire series."""
        HistoryTableWidget(self.series.getFullHistory(), self)
    
    def toggleZtraces(self):
        """Toggle whether ztraces are shown."""
        self.field.deselectAllTraces()
        self.series.setOption("show_ztraces", not self.series.getOption("show_ztraces"))
        self.field.generateView(generate_image=False)
    
    def setToObject(self, obj_name : str, section_num : int):
        """Focus the field on an object from a specified section.
        
            Params:
                obj_name (str): the name of the object
                section_num (int): the section the object is located
        """
        if obj_name is not None and section_num is not None:
            self.changeSection(section_num)
            self.field.findContour(obj_name)
            self.field.setFocus()
    
    def setToFlag(self, flag : Flag):
        """Focus the field on a flag.
        
            Params:
                flag (Flag): the flag
        """
        if flag is not None:
            self.changeSection(flag.snum)
            self.field.findFlag(flag)
            self.field.setFocus()
    
    def findObjectFirst(self, obj_name=None):
        """Find the first or last contour in the series.
        
            Params:
                obj_name (str): the name of the object to find
        """
        if obj_name is None:
            obj_name, confirmed = QInputDialog.getText(
                self,
                "Find Object",
                "Enter the object name:",
            )
            if not confirmed:
                return

        # find the contour
        self.setToObject(obj_name, self.series.data.getStart(obj_name))
    
    def changeTform(self, new_tform_list : list = None):
        """Open dialog to edit section transform."""        

        ## Ensure not in no-alignment
        if self.series.alignment == "no-alignment":
            notify(
                "Cannot edit section transform in alignment:\n\n\"no-alignment\"\n\n"
                "Change to another alignment by opening the alignment panel (ctrl + shift + A)."
            )
            return

        ## Check section lock status
        if self.field.section.align_locked:
            notify(
                "Unlock the section to adjust its transformation.\n\n"
                "(You can do this in the section list or "
                "you can unlock the current section with ctrl + shift + U)"
            )
            return
        
        if new_tform_list is None:
            current_tform = " ".join(
                [str(round(n, 5)) for n in self.field.section.tform.getList()]
            )
            new_tform_list, confirmed = QInputDialog.getText(
                self, "New Transform", "Edit section transform:", text=current_tform)
            if not confirmed:
                return
            try:
                new_tform_list = [float(n) for n in new_tform_list.split()]
                if len(new_tform_list) != 6:
                    return
            except ValueError:
                return

        self.field.changeTform(Transform(new_tform_list))
    
    def translate(self, direction : str, amount : str):
        """Translate the current transform.
        
            Params:
                direction (str): left, right, up, or down
                amount (str): small, med, or big
        """
        if amount == "small":
            num = self.series.getOption("small_dist")
        elif amount == "med":
            num = self.series.getOption("med_dist")
        elif amount == "big":
            num = self.series.getOption("big_dist")
        if direction == "left":
            x, y = -num, 0
        elif direction == "right":
            x, y = num, 0
        elif direction == "up":
            x, y = 0, num
        elif direction == "down":
            x, y = 0, -num
        self.field.translate(x, y)
    
    def newAlignment(self, new_alignment_name : str):
        """Add a new alignment (based on existing alignment).
        
            Params:
                new_alignment_name (str): the name of the new alignment
        """
        if new_alignment_name in self.field.section.tforms:
            QMessageBox.information(
                self,
                " ",
                "This alignment already exists.",
                QMessageBox.Ok
            )
            return
        self.series.newAlignment(
            new_alignment_name,
            self.series.alignment
        )
    
    def modifyAlignments(self):
        """Open dialog to modify alignments."""
        self.saveAllData()
        
        alignments = list(self.field.section.tforms.keys())

        response, confirmed = AlignmentDialog(
            self,
            alignments,
            self.series.alignment
        ).exec()
        if not confirmed:
            return
        
        alignment_name, alignment_dict = response

        modified = False
        if alignment_dict:
            for k, v in alignment_dict.items():
                if k != v:
                    modified = True
                    break
            if modified:
                self.series.modifyAlignments(alignment_dict, self.field.series_states)
                self.createContextMenus()
        
        if alignment_name:
            self.changeAlignment(alignment_name, overwrite=True)
        else:
            self.changeAlignment(self.series.alignment, overwrite=True)

    def changeAlignment(self, new_alignment : str, overwrite=False):
        """Change the current series alignment.
        
            Params:
                alignment (str): the alignment to switch to
                overwrite (bool): change the alignment even if the name is the same
        """
        attr = getattr(self, f"{new_alignment}_alignment_act")
        attr.setChecked(True)

        current_alignment = self.series.alignment
        if overwrite or new_alignment != current_alignment:
            attr = getattr(self, f"{current_alignment}_alignment_act")  # generated from createContextMenu
            attr.setChecked(False)
            self.field.changeAlignment(new_alignment)
    
    def changeBCProfiles(self):
        """Open dialog to modify and change brightness/contrast profiles."""
        self.saveAllData()
        
        bc_profiles = list(self.field.section.bc_profiles.keys())

        response, confirmed = BCProfilesDialog(
            self,
            bc_profiles,
            self.series.bc_profile
        ).exec()
        if not confirmed:
            return
        
        profile_name, profiles_dict = response

        modified = False
        if profiles_dict:
            for k, v in profiles_dict.items():
                if k != v:
                    modified = True
                    break
            if modified:
                self.series.modifyBCProfiles(profiles_dict, self.field.series_states)
                self.field.reload()
        
        if profile_name:
            self.field.changeBCProfile(profile_name)
        elif modified:
            self.field.changeBCProfile(self.series.bc_profile)
            
    def calibrateMag(self, trace_lengths : dict = None):
        """Calibrate the pixel size for the series.
        
            Params:
                trace_lengths (dict): the lengths of traces to calibrate
        """
        self.saveAllData()
        
        if trace_lengths is None:
            # gather trace names
            names = []
            for trace in self.field.section.selected_traces:
                if trace.name not in names:
                    names.append(trace.name)
            
            if len(names) == 0:
                notify("Please select traces for calibration.")
            
            # prompt user for length of each trace name
            trace_lengths = {}
            for name in names:
                d, confirmed = QInputDialog.getText(
                    self,
                    "Trace Length",
                    f'Length of "{name}" in microns:'
                )
                if not confirmed:
                    return
                try:
                    d = float(d)
                except ValueError:
                    return
                trace_lengths[name] = d
        
        self.field.calibrateMag(trace_lengths)
    
    def setSeriesMag(self):
        """Manually set (or view) the series magnification."""
        response, confirmed = QInputDialog.getDouble(
            self, 
            "Set Magnification", 
            "Series magnification (microns per image pixel):",
            self.series.avg_mag,
            decimals=8,
            step = 0.001
        )
        if not confirmed:
            return
        if response <= 0:
            notify("Magnification cannot be less than or equal to zero.")
        
        self.saveAllData()
        
        self.field.setMag(response)
    
    def modifyPointer(self, event=None):
        """Modify the pointer properties."""
        s, t = tuple(self.series.getOption("pointer"))
        structure = [
            ["Shape:"],
            [("radio", ("Rectangle", s=="rect"), ("Lasso", s=="lasso"))],
            ["Select:"],
            [("radio", ("All touched traces", t=="inc"), ("Only completed encircled traces", t=="exc"))],
            [("check", ("Display closest field item", self.series.getOption("display_closest")))]
        ]
        response, confirmed = QuickDialog.get(self, structure, "Pointer Settings")
        if not confirmed:
            return
        
        s = "rect" if response[0][0][1] else "lasso"
        t = "inc" if response[1][0][1] else "exc"
        self.series.setOption("pointer", [s, t])
        self.series.setOption("display_closest", response[2][0][1])
        self.seriesModified()
    
    def modifyGrid(self, event=None):
        """Modify the grid properties."""
        response, confirmed = GridDialog(
            self,
            tuple(self.series.getOption("grid")),
            self.series.getOption("sampling_frame_grid")
        ).exec()
        if not confirmed:
            return
        
        grid_response, sf_grid = response
        self.series.setOption("grid", grid_response)
        self.series.setOption("sampling_frame_grid", sf_grid)
        self.seriesModified()
    
    def modifyKnife(self, event=None):
        """Modify the knife properties."""
        structure = [
            [
                "Delete traces smaller than this percent:\n"
            ],
            [
                "% original trace:",
                ("float", self.series.getOption("knife_del_threshold"), (0, 100))
            ],
            [
                "\nOptionally smooth while cutting:"
            ],
            [
                ("check", ("Smooth cuts", self.series.getOption("roll_knife_average"))),
                ("int", self.series.getOption("roll_knife_window"))
            ]
        ]
        response, confirmed = QuickDialog.get(self, structure, "Knife")
        if not confirmed:
            return

        self.series.setOption("knife_del_threshold", response[0])
        self.series.setOption("roll_knife_average", response[1][0][1])
        self.series.setOption("roll_knife_window", response[2])
        
        self.seriesModified()
    
    def resetTracePalette(self):
        """Reset the trace palette to default traces."""
        self.mouse_palette.resetPalette()
        self.saveAllData()
        self.seriesModified()
    
    def setZarrLayer(self, zarr_dir=None):
        """Set a zarr layer."""
        if not zarr_dir:
            zarr_dir = FileDialog.get(
                "dir",
                self,
                "Select overlay zarr",
            )
            if not zarr_dir: return

        self.series.zarr_overlay_fp = zarr_dir
        self.series.zarr_overlay_group = None

        groups = []
        for g in os.listdir(zarr_dir):
            if os.path.isdir(os.path.join(zarr_dir, g)):
                groups.append(g)

        self.zarr_palette = ZarrPalette(groups, self)
    
    def setLayerGroup(self, group_name):
        """Set the specific group displayed in the zarr layer."""
        if not group_name:
            group_name = None
        if self.zarr_palette.cb.currentText != group_name:
            self.zarr_palette.cb.setCurrentText(group_name)
        self.series.zarr_overlay_group = group_name
        self.field.createZarrLayer()
        self.field.generateView()
    
    def removeZarrLayer(self):
        """Remove an existing zarr layer."""
        self.series.zarr_overlay_fp = None
        self.series.zarr_overlay_group = None
        if self.zarr_palette:
            self.zarr_palette.close()
        self.field.createZarrLayer()
        self.field.generateView()

    def exportToZarr(self):
        """Export series as a neuroglancer-compatible zarr."""

        if not modules_available("dask"):

            notify(
                "The 'dask' module (needed to rechunk your zarr after conversion) is not "
                "available, but conversion will continue with a chunk size of (1, 256, 256)."
            )

        all_sections = sorted(list(self.series.sections.keys()))

        ## Get options from user
        
        structure = [
            ["From section", ("int", all_sections[1]),
             "to section", ("int", all_sections[-1]), " "],
            ["Group padding (px):", ("int", 50)],
            ["Groups:"],
            [("multicombo", self.series.object_groups.getGroupList(), None)],
            [("check", ("Export all tissue", True))]
        ]
        
        response, confirmed = QuickDialog.get(self, structure, "Create Neuroglancer Zarr", spacing=10)

        if not confirmed: return
        
        start, end, padding = response[0:3]
        groups = " ".join(response[3])
        max_tissue = response[4][0][1]

        ## Ask for save location

        ser_name = self.series.name

        output = FileDialog.get(
            "save",
            self,
            "Save as zarr",
            filter="*.zarr",
            file_name=f"{ser_name}-ng-export.zarr"
        )
        
        if not output: return

        if max_tissue:

            args = {
                
                "--groups"        : groups,
                "--start_section" : start,
                "--end_section"   : end,
                "--max_tissue"    : max_tissue,
                "--output"        : output
                
            }
            
        else:

            args = {
                
                "--start_section" : start,
                "--end_section"   : end,
                "--output"        : output,
                "--groups"        : groups,
                
            }

        python_bin = sys.executable
        zarr_converter = Path(assets_dir) / "scripts/start_process.py"
        
        convert_cmd = [
            python_bin,
            str(zarr_converter.absolute()),
            "create_ng_zarr",
            f"\"{self.series.jser_fp}\""
        ]

        print(f"{convert_cmd = }")

        for argname, arg in args.items():
            if arg or arg == 0:
                if type(arg) is bool:
                    convert_cmd.append(argname)
                else:
                    
                    if argname == "--output":

                        convert_cmd += [
                            "--output",
                            f"\"{arg}\""
                        ]
                        
                    else:

                        convert_cmd += [argname] + str(arg).split()

        if os.name == 'nt':

            subprocess.Popen(
                convert_cmd,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
        else:

            convert_cmd = " ".join(convert_cmd)
            subprocess.Popen(convert_cmd, shell=True, stdout=None, stderr=None)
    
    # AUTOSEG FUNCTIONS TEMPORARILY REMOVED

    # def train(self, retrain=False):
    #     """Train an autosegmentation model."""
    #     self.saveAllData()
    #     self.removeZarrLayer()

    #     model_paths = {"a":{"b":"a/b/m.py"}}

    #     opts = self.series.options["autoseg"]

    #     response, confirmed = TrainDialog(self, self.series, model_paths, opts, retrain).exec()
    #     if not confirmed: return
        
    #     (data_fp, iterations, save_every, group, model_path, cdir, \
    #      pre_cache, min_masked, downsample) = response

    #     training_opts = {
    #         'zarr_current': data_fp,
    #         'iters': iterations,
    #         'save_every': save_every,
    #         'group': group,
    #         'model_path': model_path,
    #         'checkpts_dir': cdir,
    #         'pre_cache': pre_cache,
    #         'min_masked': min_masked,
    #         'downsample_bool': downsample
    #     }

    #     for k, v in training_opts.items():
    #         opts[k] = v
    #     self.seriesModified(True)

    #     print("Exporting labels to zarr directory...")
        
    #     if retrain:
    #         group_name = f"labels_{self.series.getRecentSegGroup()}_keep"
    #         seriesToLabels(self.series, data_fp)
            
    #     else:
    #         group_name = f"labels_{group}"
    #         seriesToLabels(self.series, data_fp, group)

    #     print("Zarr directory updated with labels!")

    #     if retrain:
    #         self.field.reload()
    #         self.field.table_manager.refresh()

    #     print("Starting training....")

    #     print("Importing training modules...")

    #     from autoseg import train, make_mask, model_paths

    #     make_mask(data_fp, group_name)
        
    #     sources = [{
    #         "raw" : (data_fp, "raw"),
    #         "labels" : (data_fp, group_name),
    #         "unlabelled" : (data_fp, "unlabelled")
    #     }]

    #     train(
    #         iterations=iterations,
    #         save_every=save_every,
    #         sources=sources,
    #         model_path=model_path,
    #         pre_cache=pre_cache,
    #         min_masked=min_masked,
    #         downsample=downsample,
    #         checkpoint_basename=os.path.join(cdir, "model")  # where existing checkpoints
    #     )

    #     print("Done training!")
    
    # def markKeep(self):
    #     """Add the selected trace to the most recent "keep" segmentation group."""
    #     keep_tag = f"{self.series.getRecentSegGroup()}_keep"
    #     for trace in self.field.section.selected_traces:
    #         trace.addTag(keep_tag)
    #     # deselect traces and hide
    #     self.field.hideTraces()
    #     self.field.deselectAllTraces()

    # def predict(self, data_fp : str = None):
    #     """Run predictons.
        
    #         Params:
    #             data_fp (str): the filepath for the zarr
    #     """
    #     self.saveAllData()
    #     self.removeZarrLayer()

    #     print("Importing models...")
        
    #     from autoseg import predict, model_paths
    #     # model_paths = {"a":{"b":"a/b/m.py"}}

    #     opts = self.series.options["autoseg"]

    #     response, dialog_confirmed = PredictDialog(self, model_paths, opts).exec()

    #     if not dialog_confirmed: return

    #     data_fp, model_path, cp_path, write_opts, increase, downsample, full_out_roi = response

    #     predict_opts = {
    #         'zarr_current': data_fp,
    #         'model_path': model_path,
    #         'checkpts_dir': os.path.dirname(cp_path),
    #         'write': write_opts,
    #         'increase': increase,
    #         'downsample_bool': downsample,
    #         'full_out_roi': full_out_roi
    #     }

    #     for k, v in predict_opts.items():
    #         opts[k] = v
    #     self.seriesModified(True)
                
    #     print("Running predictions...")

    #     zarr_datasets = predict(
    #         sources=[(data_fp, "raw")],
    #         out_file=data_fp,
    #         checkpoint_path=cp_path,
    #         model_path=model_path,
    #         write=write_opts,
    #         increase=increase,
    #         downsample=downsample,
    #         full_out_roi=full_out_roi
    #     )

    #     # display the affinities
    #     self.setZarrLayer(data_fp)
    #     for zg in os.listdir(data_fp):
    #         if zg.startswith("pred_affs"):
    #             self.setLayerGroup(zg)
    #             break

    #     print("Predictions done.")
        
    # def segment(self, data_fp : str = None):
    #     """Run an autosegmentation.
        
    #         Params:
    #             data_fp (str): the filepath for the zarr
    #     """
    #     self.saveAllData()
    #     self.removeZarrLayer()

    #     print("Importing modules...")
        
    #     from autoseg import hierarchical

    #     opts = self.series.options["autoseg"]

    #     response, dialog_confirmed = SegmentDialog(self, opts).exec()

    #     if not dialog_confirmed: return

    #     data_fp, thresholds, downsample, norm_preds, min_seed, merge_fun = response

    #     segment_opts = {
    #         "zarr_current": data_fp,
    #         "thresholds": thresholds,
    #         "downsample_int": downsample,
    #         "norm_preds": norm_preds,
    #         "min_seed": min_seed,
    #         "merge_fun": merge_fun
    #     }

    #     for k, v in segment_opts.items():
    #         opts[k] = v
    #     self.seriesModified(True)

    #     print("Running hierarchical...")

    #     dataset = None
    #     for d in os.listdir(data_fp):
    #         if "affs" in d:
    #             dataset = d
    #             break

    #     print("Segmentation started...")
            
    #     hierarchical.run(
    #         data_fp,
    #         dataset,
    #         thresholds=list(sorted(thresholds)),
    #         normalize_preds=norm_preds,
    #         min_seed_distance=min_seed,
    #         merge_function=merge_fun
    #     )

    #     print("Segmentation done.")

    #     # display the segmetnation
    #     self.setZarrLayer(data_fp)
    #     for zg in os.listdir(data_fp):
    #         if zg.startswith("seg"):
    #             self.setLayerGroup(zg)
    #             break
    
    # def importLabels(self, all=False):
    #     """Import labels from a zarr."""
    #     if not self.field.zarr_layer or not self.field.zarr_layer.is_labels:
    #         return
        
    #     # get necessary data
    #     data_fp = self.series.zarr_overlay_fp
    #     group_name = self.series.zarr_overlay_group

    #     labels = None if all else self.field.zarr_layer.selected_ids
        
    #     labelsToObjects(
    #         self.series,
    #         data_fp,
    #         group_name,
    #         labels
    #     )
    #     self.field.reload()
    #     self.removeZarrLayer()
    #     self.field.table_manager.refresh()

    #     notify("Labels imported successfully.")
    
    # def mergeLabels(self):
    #     """Merge selected labels in a zarr."""
    #     if not self.field.zarr_layer:
    #         return
        
    #     self.field.zarr_layer.mergeLabels()
    #     self.field.generateView()
    
    def hideSeriesTraces(self, hidden=True):
        """Hide or unhide all traces in the entire series.
        
            Params:
                hidden (bool) True if traces will be hidden
        """
        self.saveAllData()
        self.series.hideAllTraces(hidden)
        self.field.reload()
    
    def setFindZoom(self):
        """Set the magnification for find contour."""
        z, confirmed = QInputDialog.getInt(
            self,
            "Find Contour Zoom",
            "Enter the find contour zoom (0-100):",
            value=self.series.getOption("find_zoom"),
            minValue=0,
            maxValue=100
        )
        if not confirmed:
            return

        self.series.setOption("find_zoom", z)
    
    def deleteDuplicateTraces(self):
        """Remove all duplicate traces from the series."""
        self.saveAllData()

        structure = [
            ["Overlap threshold:", ("float", 0.95, (0, 1))],
            [("check", ("check locked traces", True))]
        ]
        response, confirmed = QuickDialog.get(self, structure, "Remove duplicate traces")
        if not confirmed:
            return
        threshold = response[0]
        include_locked = response[1][0][1]
        
        removed = self.series.deleteDuplicateTraces(threshold, include_locked, self.field.series_states)

        if removed:
            message = "The following duplicate traces were removed:"
            for snum in removed:
                message += f"\nSection {snum}: " + ", ".join(removed[snum])
            TextWidget(self, message, title="Removed Traces")
        else:
            notify("No duplicate traces found.")

        self.field.reload()
        self.seriesModified(True)

    def addTo3D(self, names, ztraces=False):
        """Generate the 3D view for a list of objects.
        
            Params:
                obj_names (list): a list of object names
        """
        self.saveAllData()
        
        if not self.viewer or self.viewer.is_closed:
            
            self.viewer = CustomPlotter(self, names, ztraces)
            
        else:
            
            if ztraces:
                self.viewer.addToScene([], names)
            else:
                self.viewer.addToScene(names, [])
        
        self.viewer.activateWindow()
        
    def removeFrom3D(self, obj_names: list, ztraces: Union[List, None]=None):
        """Remove objects from 3D viewer.
        
            Params:
                obj_names (list): a list of object names
        """
        self.saveAllData()
        
        if not self.viewer or self.viewer.is_closed:
            return
        
        if ztraces:
            
            self.viewer.removeObjects(None, ztraces)
            
        else:
            
            self.viewer.removeObjects(obj_names, None)

        self.viewer.activateWindow()

    def exportAs3D(self, obj_names, export_type, ztraces=False):
        """Export 3D objects."""
        self.saveAllData()
        export_dir = FileDialog.get(
                "dir",
                self,
                "Select folder to export objects to",
            )
        if not export_dir: return
        export3DObjects(self.series, obj_names, export_dir, export_type)
    
    def toggleCuration(self):
        """Quick shortcut to toggle curation on/off for the tables."""
        self.field.table_manager.toggleCuration()
    
    def backspace(self):
        """Called when backspace is pressed."""
        # use table if focused; otherwise, use field
        w = self.getFocusWidget()
        if w: w.backspace()
    
    def copy(self):
        """Called when Ctrl+C is pressed."""
        w = self.getFocusWidget()
        if w: w.copy()
    
    def undo(self, redo=False):
        """Perform an undo/redo action.
        
            Params:
                redo (bool): True if redo should be performed
        """
        self.saveAllData()
        can_3D, can_2D, linked = self.field.series_states.canUndo(redo=redo)
        def act2D():
            self.field.undoState(redo)
        def act3D():
            self.field.series_states.undoState(redo)
            self.field.reload()
            self.field.table_manager.recreateTables()

        # both 3D and 2D possible and they are linked
        if can_3D and can_2D and linked:
            mbox = QMessageBox(self)
            mbox.setWindowTitle("Redo" if redo else "Undo")
            mbox.setText("This action is linked to multiple sections.\nPlease select how you would like to proceed.")
            mbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            mbox.setButtonText(QMessageBox.Yes, "All sections")
            mbox.setButtonText(QMessageBox.No, "Only this section")
            mbox.setButtonText(QMessageBox.Cancel, "Cancel")
            response = mbox.exec()
            if response == QMessageBox.Yes:
                act3D()
            elif response == QMessageBox.No:
                act2D()
        # both 3D and 2D possible but they are not linked
        elif can_3D and can_2D and not linked:
            favor_3D = self.field.series_states.favor3D(redo=redo)
            if favor_3D:
                act3D()
            else:
                act2D()
        # only 3D possible
        elif can_3D:
            act3D()
        # only 2D possible
        elif can_2D:
            act2D()
        
    def pasteAttributesToPalette(self, use_shape=False):
        """Paste the attributes from the first clipboard trace to the selected palette button."""
        if not self.field.clipboard and not self.field.section.selected_traces:
            return
        elif not self.field.clipboard:
            trace = self.field.section.selected_traces[0]
        else:
            trace = self.field.clipboard[0]
        self.mouse_palette.pasteAttributesToButton(trace, use_shape)
    
    def displayShortcuts(self):
        """Display the shortcuts."""
        response, confirmed = ShortcutsDialog(self, self.series).exec()
        if not confirmed:
            return
        
        self.resetShortcuts(response)

    def openWebsite(self, site):
        """Open website in user's browser."""
        webbrowser.open(site)

    def copyCommit(self):
        """Copy current commit or repo."""
        clipboard = QApplication.clipboard()
        clipboard.setText(repo_info["commit"])

    def updateCurationFromHistory(self):
        """Update the series curation from the history."""
        self.field.series_states.addState()
        self.series.updateCurationFromHistory()
        self.field.table_manager.recreateTables()
        self.seriesModified()
    
    def allOptions(self):
        """Display the series options dialog."""
        confirmed = AllOptionsDialog(self, self.series).exec()
        if confirmed:
            self.field.generateView()
            self.mouse_palette.reset()
            self.setTheme(self.series.getOption("theme"))
    
    def optimizeBC(self, sections : list = None):
        """Optimize the brightness and contrast of the series.
        
            Params:
                sections (list): the list of section numbers
        """
        structure = [
            ["Mean (0-255):", ("int", 128, range(256))],
            ["Standard Devation:", ("float", 60)],
            [("radio", ("Use full image", True), ("Use current window view only", False))],
        ]
        response, confirmed = QuickDialog.get(self, structure, "Optimize Images")
        if not confirmed:
            return
        
        mean = response[0]
        std = response[1]
        full_image = response[2][0][1]
        
        if not noUndoWarning():
            return
        
        if sections is None:
            sections = list(self.series.sections.keys())
        
        optimizeSeriesBC(
            self.series, 
            mean,
            std,
            sections,
            None if full_image else self.series.window.copy()
        )
        self.field.reload()
        self.field.table_manager.updateSections(sections)
    
    def resetShortcuts(self, shortcuts_dict : dict = None):
        """Reset the shortcuts for the window.
        
            Params:
                shortcuts_dict: the action name : shortcut pairs (will use series opts if not provided)
        """
        if shortcuts_dict is None:
            shortcuts_dict = {}
            for k in Series.qsettings_defaults:
                if k.endswith("_act") and getattr(self, k):
                    shortcuts_dict[k] = self.series.getOption(k)
        
        for act_name, kbd in shortcuts_dict.items():
            getattr(self, act_name).setShortcut(kbd)
            self.series.setOption(act_name, kbd)
    
    def displayAbout(self):
        """Display the widget display information about the series."""
        # update the editors
        editors = self.series.getEditorsFromHistory()
        self.series.editors = self.series.editors.union(editors)

        AboutWidget(self, self.series)
    
    def exportTracePaletteCSV(self):
        """Export the current trace palette as CSV file."""
        name = self.series.palette_index[0]
        fp = FileDialog.get(
            "save",
            self,
            "Export Trace Palette",
            filter="*.csv",
            file_name=f"{name}.csv"
        )
        if not fp: return

        self.series.exportTracePaletteCSV(fp)
    
    def importTracePaletteCSV(self):
        """Import a trace palette from a CSV file."""
        fp = FileDialog.get(
            "file",
            self,
            "Import Trace Palette",
            filter="*.csv"
        )
        if not fp: return

        # get the new name of the palette
        name = os.path.basename(fp)
        name = name[:name.rfind(".")]

        i = 0
        while name in self.series.palette_traces:
            i += 1
            name = f"{name}-{i}"

        self.series.importTracePaletteCSV(fp, name)
        self.series.palette_index[0] = name

        self.mouse_palette.reset()

        notify(f"Trace palette '{name}' successfully imported.\n" +
               f"Press {self.series.getOption('modifytracepalette_act')} to view all palettes.")
    
    def notifyNewEditor(self):
        """Provide any relevant notifications to new editors."""
        if (
            not self.series.isWelcomeSeries() and
            self.series.user not in self.series.editors and
            len(self.series.getAlignments()) > 2
        ):
            notify(
                "Note: this series has multiple alignments.\n" + 
                f"Press {self.series.getOption('changealignment_act')} to view"
            )
    
    def editSeriesCodePattern(self):
        """Edit the regex pattern used to automatically detect series codes."""
        response, confirmed = QInputDialog.getText(
            self,
            "Series Code Pattern",
            "Enter the regex pattern for series codes:",
            text=self.series.getOption("series_code_pattern")
        )
        if not confirmed:
            return
        
        self.series.setOption("series_code_pattern", response)
    
    def setSeriesCode(self, cancelable=True):
        """Set the series code (ensure that user enters a valid series code)."""
        code_is_valid = False
        while not code_is_valid:
            structure = [
                ["The series code is a unique set of characters that identifies\n" + 
                "a specific series, regardless of the file name."],
                [" "],
                ["Series code:", (True, "text", self.series.code)]
            ]
            response, confirmed = QuickDialog.get(self, structure, "Series Code", cancelable=cancelable)
            if confirmed:
                self.series.code = response[0]
            
            code_is_valid = bool(self.series.code)

            if not code_is_valid:
                notify("Please enter a code for the series.")
    
    def setPaletteButtonFromObj(self, name : str):
        """Set the name for the selected palette button.
        
        (Used by the object list)
        
            Params:
                name (str): the name to set the button
        """
        # get the first instance of the object
        first_section = self.series.data.getStart(name)
        if first_section is None:
            return
        
        section = self.series.loadSection(first_section)
        obj_trace = section.contours[name][0].copy()

        pname, i = self.series.palette_index
        trace = self.series.palette_traces[pname][i]
        trace.name = name
        trace.color = obj_trace.color
        trace.fill_mode = obj_trace.fill_mode
        self.mouse_palette.modifyPaletteButton(i, trace)
    
    def load3DScene(self):
        """Load a 3D scene."""
        load_fp = FileDialog.get(
            "file",
            self,
            "Load 3D Scene",
            "JSON file (*.json)"
        )
        if not load_fp:
            return
        
        if not self.viewer or self.viewer.is_closed:
            self.viewer = CustomPlotter(self, load_fp=load_fp)
        else:
            self.viewer.loadScene(load_fp)
        
        self.viewer.setFocus()
    
    def setTheme(self, new_theme=None):
        """Change the theme."""
        if new_theme is None:
            theme = self.series.getOption("theme")
            structure = [
                ["Theme:"],
                [("radio", ("Default", theme=="default"), ("Dark", theme=="qdark"))]
            ]
            response, confirmed = QuickDialog.get(
                self, structure, "Theme"
            )
            if not confirmed:
                return
            
            if response[0][0][1]:
                new_theme = "default"
            elif response[0][1][1]:
                new_theme = "qdark"
            else:
                return
        
        app = QApplication.instance()
        if new_theme == "default":
            self.series.setOption("theme", "default")
            app.setStyleSheet("")
            app.setPalette(app.style().standardPalette())
        elif new_theme == "qdark":
            try:
                import qdarkstyle
            except:
                notify("Unable to import dark theme.")
                return
            self.series.setOption("theme", "qdark")
            app.setStyleSheet(
                qdarkstyle.load_stylesheet_pyside6() + 
                qdark_addon
            )
    
    def addToRecentSeries(self, series_fp : str = None):
        """Add a series to the recently opened series list."""
        if series_fp is None:
            if self.series.isWelcomeSeries():
                return
            series_fp = self.series.jser_fp
        
        opened = self.series.getOption("recently_opened_series")

        # remove redundant filepaths
        while series_fp in opened:
            opened.remove(series_fp)
        
        opened.insert(0, series_fp)

        # limit to ten items
        if len(opened) > 10:
            opened.pop()
                
        self.series.setOption("recently_opened_series", opened)
    
    def importFromSeries(self):
        """Import from another series."""
        jser_fp = FileDialog.get(
            "file",
            self,
            "Select Series",
            filter="*.jser"
        )
        if not jser_fp: return  # exit function if user does not provide series

        self.saveAllData()

        # open the other series
        o_series = Series.openJser(jser_fp)

        # check the manigifcations
        if not checkMag(self.series, o_series):
            o_series.close()
            return
        
        response, confirmed = ImportSeriesDialog(self, self.series, o_series).exec()
        if not confirmed or not response:
            o_series.close()
            return
        
        if "traces" in response:
            (
                srange,
                regex_filters,
                group_filters,
                threshold,
                flag_conflicts,
                check_history,
                import_obj_attrs,
                keep_above,
                keep_below,
            ) = tuple(response["traces"])

            self.series.importTraces(
                o_series, 
                srange, 
                regex_filters,
                group_filters,
                threshold, 
                flag_conflicts, 
                check_history,
                import_obj_attrs,
                keep_above,
                keep_below, 
                self.field.series_states
            )
        
        if "z-traces" in response:
            regex_filters = response["z-traces"][0]
            import_attrs = response["z-traces"][1][0][1]
            self.series.importZtraces(
                o_series, 
                regex_filters,
                import_attrs,
                series_states=self.field.series_states
            )
            
        if "flags" in response:
            srange = (
                response["flags"][0],
                response["flags"][1] + 1
            )
            self.series.importFlags(
                o_series, 
                srange,
                self.field.series_states
            )
        
        if "attributes" in response:
            bools = [b for n, b in response["attributes"][0]]
            if bools[0]:
                self.series.importObjectGroups(o_series)
            if bools[1]:
                self.series.importHostTree(o_series)
            if bools[2]:
                self.series.importUserCols(o_series)
            if bools[3]:
                self.series.importZtraceGroups(o_series)
            if bools[4]:
                self.series.importObjAttrs(o_series)
        
        if "alignments" in response:
            import_as = response["alignments"]
            self.series.importTransforms(
                o_series,
                import_as,
                self.field.series_states
            )
            self.createContextMenus()

        if "palettes" in response:
            import_as = response["palettes"]
            self.series.importPalettes(  # cannot be undone
                o_series,
                import_as
            )

        if "brightness/contrast profiles" in response:
            import_as = response["brightness/contrast profiles"]
            self.series.importBC(  # cannot be undone
                o_series,
                import_as
            )

        # close other series
        o_series.close()

        # refresh the data and lists
        self.field.reload()
        self.field.table_manager.refresh()

        notify("Import successful.")
    
    def importFromZarrLabels(self):
        """Import label data from a neuroglancer zarr."""
        zarr_fp = FileDialog.get(
            "dir",
            self,
            "Select Zarr File"
        )
        if not zarr_fp:
            return
                
        if not zarr_fp.endswith("zarr"):
            notify("Selected file is not a valid zarr.")
        
        groups = [f for f in os.listdir(zarr_fp) if not f.startswith(".") and not f=="raw"]

        structure = [
            ["Label group names:"],
            [(True, "multicombo", groups, [])],
        ]
        response, confirmed = QuickDialog.get(self, structure, "Import Labels")
        if not confirmed:
            return
        
        groups = response[0]
        
        for group in groups:
            if group in os.listdir(zarr_fp):
                labelsToObjects(
                    self.series,
                    zarr_fp,
                    group,
                )
                self.field.reload()
        
    def toggleGroupViz(self, group):
        """Toggle visibility of a group."""

        group_viz = self.series.groups_visibility
        group_viz[group] = not group_viz[group]

        self.field.reload()
    
    def saveFieldView(self, save_to_file=False) -> None:
        """Export mainwindow to clipboard."""

        exported_image = QImage(
            self.rect().width(),
            self.rect().height(),
            QImage.Format_ARGB32
        )
        
        exported_image.fill(Qt.transparent)

        ## Draw base image
        with QPainter(exported_image) as painter:

            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            painter.drawImage(
                exported_image.rect(),
                QImage(self.field.section.src_fp),
                self.rect()
            )

        ## Capture paint events in a separate step
        temp_pixmap = QPixmap(exported_image.size())
        temp_pixmap.fill(Qt.transparent)

        with QPainter(temp_pixmap) as temp_painter:
            
            # Call the widget's paint method and replay paint events
            self.render(
                temp_painter,
                QPoint(0, 0),  # target position
                QRegion(self.rect()),  # source region
                QWidget.RenderFlag.DrawChildren | QWidget.RenderFlag.DrawWindowBackground
            )

        ## Combine layers
        with QPainter(exported_image) as painter:
            painter.drawPixmap(0, 0, temp_pixmap)

        if save_to_file:

            fp = FileDialog.get(
                "save",
                self,
                "Field view",
                file_name=f"field_sec_{self.series.current_section}.png",
                filter="*.tif, *.tiff, *.jpeg, *jgp, *.png"
            )
            
            if not fp: return False
            
            exported_image.save(fp)

        else:
            
            ## Create clipboard and set
            clipboard = QApplication.clipboard()
        
            clipboard.setPixmap(
                QPixmap.fromImage(exported_image)
            )

        return None

    def addScaleBar(self):
        """Add scale bar to the field."""

        structure = [
            ["Width (μm):", (True, "float", 2.0), " "],
            ["Height (μm):", (True, "float", 0.2), " "]
        ]

        response, confirmed = QuickDialog.get(
            self, structure, "Scale bar settings"
        )
        
        if not confirmed:
            return

        w, h = response
        
        scale_bar_trace = Trace.get_scale_bar()
        pix_x, pix_y = get_center_pixel(self)

        self.field.placeGrid(
            pix_x, pix_y,
            scale_bar_trace,
            w, h, 0, 0, 1, 1,
            scale_bar=True
        )
    
    def getFocusWidget(self):
        """Get the widget the user is focused on.
        
        Currently will only return a DataTable or the FieldWidget.
        """
        table = self.field.table_manager.hasFocus()
        if table:
            return table
        else:
            return self.field

    def restart(self):
        self.restart_mainwindow = True

        # Clear console
        
        if os.name == 'nt':  # Windows
            _ = os.system('cls')
        
        else:  # Mac and Linux
            _ = os.system('clear')
        
        self.close()

    def closeEvent(self, event):
        """Save all data to files when the user exits."""
        response = self.saveToJser(notify=True, close=True)
        if response == "cancel":
            event.ignore()
            return
        if self.viewer and not self.viewer.is_closed:
            self.viewer.close()
        event.accept()

qdark_addon = """
QPushButton {border: 1px solid transparent}
QComboBox {padding-right: 40px}
"""

## Removed following as it overrides background color of qtablewidgetitems
## QTableWidget:item:alternate {background-color: #222C36;}  
