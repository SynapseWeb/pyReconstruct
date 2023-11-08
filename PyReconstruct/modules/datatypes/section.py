import os
import re
import json

from .contour import Contour
from .trace import Trace
from .flag import Flag
from .transform import Transform

from PyReconstruct.modules.calc import (
    getDistanceFromTrace,
    distance
)
from PyReconstruct.modules.constants import assets_dir


class Section():

    def __init__(self, n : int, series):
        """Load the section file.
        
            Params:
                n (int): the section number
                series (Series): the series that contains the section
        """
        self.n = n
        self.series = series
        self.filepath = os.path.join(
            self.series.getwdir(),
            self.series.sections[n]
        )

        self.selected_traces = []
        self.selected_ztraces = []
        self.selected_flags = []

        self.temp_hide = []

        self.added_traces = []
        self.removed_traces = []
        self.modified_contours = set()

        with open(self.filepath, "r") as f:
            section_data = json.load(f)
        
        Section.updateJSON(section_data)  # update any missing attributes
        
        self.src = section_data["src"]
        self.brightness = section_data["brightness"]
        self.contrast = section_data["contrast"]
        self.mag = section_data["mag"]
        self.align_locked = section_data["align_locked"]

        self.tforms = {}
        for a in section_data["tforms"]:
            self.tforms[a] = Transform(section_data["tforms"][a])
        
        self.thickness = section_data["thickness"]
        self.contours = section_data["contours"]
        for name in self.contours:
            trace_list = []
            for trace_data in self.contours[name]:
                trace = Trace.fromList(trace_data, name)
                # screen for defective traces
                l = len(trace.points)
                if l == 2:
                    trace.closed = False
                if l > 1:
                    trace_list.append(trace)
            self.contours[name] = Contour(
                name,
                trace_list
            )
        
        self.flags = [Flag.fromList(l) for l in section_data["flags"]]

        self.calgrid = section_data["calgrid"]
    
    @property
    def tform(self):
        if self.series.alignment != "no-alignment":
            return self.tforms[self.series.alignment]
        else:
            return Transform([1, 0, 0, 0, 1, 0])
    @tform.setter
    def tform(self, new_tform):
        if self.series.alignment != "no-alignment":
            self.tforms[self.series.alignment] = new_tform
    
    # STATIC METHOD
    def updateJSON(section_data):
        """Add missing attributes to section JSON."""
        empty_section = Section.getEmptyDict()
        for key in empty_section:
            if key not in section_data:
                section_data[key] = empty_section[key]
        
        # modify brightness/contrast
        if abs(section_data["brightness"]) > 100:
            section_data["brightness"] = 0
        section_data["contrast"] = int(section_data["contrast"])

        # scan contours
        flagged_contours = []
        for cname in section_data["contours"]:
            flagged_traces = []
            for i, trace in enumerate(section_data["contours"][cname]):
                # convert trace to list format if needed
                if type(trace) is dict:
                    trace = [
                        trace["x"],
                        trace["y"],
                        trace["color"],
                        trace["closed"],
                        trace["negative"],
                        trace["hidden"],
                        trace["mode"],
                        trace["tags"]
                    ]
                    section_data["contours"][cname][i] = trace
                # remove history from trace if it exists
                elif len(trace) == 9:
                    trace.pop()
                # check for trace mode
                if type(trace[6]) is not list:
                    trace[6] = ["none", "none"]
                # check for empty/defective traces
                if len(trace[0]) < 2:
                    flagged_traces.append(i)
            # remove the flagged defective traces
            for i in sorted(flagged_traces, reverse=True):
                section_data["contours"][cname].pop(i)
            # check if the contour is empty
            if not section_data["contours"][cname]:
                flagged_contours.append(cname)
        # remove flagged contours
        for cname in flagged_contours:
            del(section_data["contours"][cname])
        
        # scan contour names and remove errant whitespace
        for cname in tuple(section_data["contours"].keys()):
            s_cname = cname.strip()
            if cname != s_cname:
                if s_cname not in section_data["contours"]:
                    section_data["contours"][s_cname] = []
                section_data["contours"][s_cname] += section_data["contours"][cname]
                del(section_data["contours"][cname])
        
        # remove no-alignment if present
        if "no-alignment" in section_data["tforms"]:
            del(section_data["tforms"]["no-alignment"])
        
        # iterate through flags and add resolved status
        for flag in section_data["flags"]:
            if len(flag) == 5:
                flag.append(False)

    def getDict(self) -> dict:
        """Convert section object into a dictionary.
        
            Returns:
                (dict) all of the compiled section data
        """
        d = {}
        d["src"] = self.src
        d["brightness"] = self.brightness
        d["contrast"] = self.contrast
        d["mag"] = self.mag
        d["align_locked"] = self.align_locked

        # save tforms
        d["tforms"] = {}
        for a in self.tforms:
            d["tforms"][a] = self.tforms[a].getList()

        d["thickness"] = self.thickness

        # save contours
        d["contours"] = {}
        for contour_name in self.contours:
            if not self.contours[contour_name].isEmpty():
                d["contours"][contour_name] = [
                    trace.getList(include_name=False) for trace in self.contours[contour_name]
                ]
        
        d["flags"] = [f.getList() for f in self.flags]

        d["calgrid"] = self.calgrid

        return d
    
    # STATIC METHOD
    def getEmptyDict():
        section_data = {}
        section_data["src"] = ""  # image location
        section_data["brightness"] = 0
        section_data["contrast"] = 0
        section_data["mag"] = 0.00254  # microns per pixel
        section_data["align_locked"] = True
        section_data["thickness"] = 0.05  # section thickness
        section_data["tforms"] = {}  
        section_data["tforms"]["default"]= [1, 0, 0, 0, 1, 0] # identity matrix default
        section_data["contours"] = {}
        section_data["flags"] = []
        section_data["calgrid"] = False

        return section_data
    
    # STATIC METHOD
    def new(series_name : str, snum : int, image_location : str, mag : float, thickness : float, wdir : str):
        """Create a new blank section file.
        
            Params:
                series_name (str): the name for the series
                snum (int): the section number
                image_location (str): the file path for the image
                mag (float): microns per pixel for the section
                thickness (float): the section thickness in microns
                wdir (str): the working directory for the sections
            Returns:
                (Section): the newly created section object
        """
        section_data = Section.getEmptyDict()
        section_data["src"] = os.path.basename(image_location)  # image location
        section_data["mag"] = mag  # microns per pixel
        section_data["thickness"] = thickness  # section thickness

        section_fp = os.path.join(wdir, series_name + "." + str(snum))
        with open(section_fp, "w") as section_file:
            section_file.write(json.dumps(section_data, indent=2))
   
    def save(self, update_series_data=True):
        """Save file into json."""
        try:
            if os.path.samefile(self.filepath, os.path.join(assets_dir, "welcome_series", "welcome.0")):
                return  # ignore welcome series
        except FileNotFoundError:
            pass

        # update the series data
        if update_series_data:
            self.series.data.updateSection(self, update_traces=True)
    
        d = self.getDict()
        with open(self.filepath, "w") as f:
            f.write(json.dumps(d, indent=1))
    
    def tracesAsList(self) -> list[Trace]:
        """Return the trace dictionary as a list. Does NOT copy traces.
        
            Returns:
                (list): a list of traces
        """
        trace_list = []
        for contour_name in self.contours:
            for trace in self.contours[contour_name]:
                trace_list.append(trace)
        return trace_list
    
    def setAlignLocked(self, align_locked : bool):
        """Set the alignment locked status of the section.
        
            Params:
                align_locked (bool): the new locked status
        """
        self.align_locked = align_locked
    
    def getAllModifiedNames(self):
        """Get the names of all the modified traces."""
        trace_names = set([t.name for t in self.added_traces])
        trace_names = trace_names.union(set([t.name for t in self.removed_traces]))
        trace_names = trace_names.union(self.modified_contours)
        return trace_names
    
    def clearTracking(self):
        """Clear the added_traces and removed_traces lists."""
        self.added_traces = []
        self.removed_traces = []
        self.modified_contours = set()
    
    def setMag(self, new_mag : float):
        """Set the magnification for the section.
        
            Params:
                new_mag (float): the new magnification for the section
        """
        # modify the translation component of the transformation
        for tform in self.tforms.values():
            tform.magScale(self.mag, new_mag)
        
        # modify the traces
        for trace in self.tracesAsList():
            trace.magScale(self.mag, new_mag)
        
        self.mag = new_mag
    
    def addTrace(self, trace : Trace, log_event=True):
        """Add a trace to the trace dictionary.
        
            Params:
                trace (Trace): the trace to add
                log_event (bool): true if the event should be logged
        """        
        # do not add trace if less than two points
        if len(trace.points) < 2:
            return
        # force trace to be open if only two points
        elif len(trace.points) == 2:
            trace.closed = False
        # add to log
        if log_event:
            self.series.addLog(trace.name, self.n, "Create trace(s)")

        if trace.name in self.contours:
            self.contours[trace.name].append(trace)
        else:
            self.contours[trace.name] = Contour(trace.name, [trace])
        
        self.added_traces.append(trace)
    
    def removeTrace(self, trace : Trace, log_event=True):
        """Remove a trace from the trace dictionary.
        
            Params:
                trace (Trace): the trace to remove from the traces dictionary
        """
        if trace.name in self.contours:
            self.contours[trace.name].remove(trace)
            self.removed_traces.append(trace.copy())
        if log_event:
            self.series.addLog(trace.name, self.n, "Delete trace(s)")
    
    def addFlag(self, flag : Flag, log_event=True):
        """Add a flag to the section.
        
            Params:
                flag (Flag): the flag to add to the section
        """
        self.flags.append(flag)
        if log_event:
            self.series.addLog(None, self.n, "Create flag(s)")
    
    def removeFlag(self, flag : Flag, log_event=True):
        """Remove a flag from the section.
        
            Params:
                flag (Flag): the flag to remove from the section
        """
        if flag in self.flags:
            self.flags.remove(flag)
            if log_event:
                self.series.addLog(None, self.n, "Delete flag(s)")

    def editTraceAttributes(self, traces : list[Trace], name : str, color : tuple, tags : set, mode : tuple, add_tags=False, log_event=True):
        """Change the name and/or color of a trace or set of traces.
        
            Params:
                traces (list): the list of traces to modify
                name (str): the new name
                color (tuple): the new color
                tags (set): the new set of tags
                mode (tuple): the new fill mode for the traces
                add_tags (bool): True if tags should be added (rather than replaced)
        """
        for trace in traces.copy():
            # check if trace was highlighted
            if trace in self.selected_traces:
                self.selected_traces.remove(trace)
                selected = True
            else:
                selected = False
            
            # remove the trace and modify
            self.removeTrace(trace, log_event=False)
            new_trace = trace.copy()
            if name is not None:
                new_trace.name = name
            if color is not None:
                new_trace.color = color
            if tags is not None:
                if add_tags:
                    for tag in tags:
                        new_trace.tags.add(tag)
                else:
                    new_trace.tags = tags
            fill_mode = list(new_trace.fill_mode)
            if mode is not None:
                style, condition = mode
                if style is not None:
                    fill_mode[0] = style
                if condition is not None:
                    fill_mode[1] = condition
                new_trace.fill_mode = tuple(fill_mode)
            
            # log the event
            if log_event:
                if trace.name != new_trace.name:
                    self.series.addLog(trace.name, self.n, f"Rename to {new_trace.name}")
                    self.series.addLog(new_trace.name, self.n, f"Create trace(s) from {trace.name}")
                else:
                    self.series.addLog(new_trace.name, self.n, f"Modify trace(s)")
            
            # add trace back to scene and highlight if needed
            self.addTrace(new_trace, log_event=False)
            if selected:
                self.selected_traces.append(new_trace)
    
    def editTraceRadius(self, traces : list[Trace], new_rad : float, log_event=True):
        """Change the radius of a trace or set of traces.
        
            Params:
                traces (list): the list of traces to change
                new_rad (float): the new radius for the trace(s)
        """
        for trace in traces:
            self.removeTrace(trace, log_event=False)
            trace.resize(new_rad)
            self.addTrace(trace, log_event=False)
            if log_event:
                self.series.addLog(trace.name, self.n, "Modify radius")
    
    def editTraceShape(self, traces : list[Trace], new_shape : list, log_event=True):
        """Change the shape of a trace or set of traces.
        
            Params:
                traces (list): the list of traces to change
                new_shape (list): the new shape for the trace(s)
        """
        for trace in traces:
            self.removeTrace(trace, log_event=False)
            trace.reshape(new_shape)
            self.addTrace(trace, log_event=False)
            if log_event:
                self.series.addLog(trace.name, self.n, "Modify shape")
    
    def findClosest(
            self,
            field_x : float,
            field_y : float,
            radius=0.5,
            traces_in_view : list[Trace] = None,
            include_hidden=False):
        """Find closest trace/ztrace to field coordinates in a given radius.
        
            Params:
                field_x (float): x coordinate of search center
                field_y (float): y coordinate of search center
                radius (float): 1/2 of the side length of search square
                traces_in_view (list): the traces in the window viewed by the user
                include_hidden (bool): True if hidden traces can be returned
            Returns:
                (Trace) the trace closest to the center
                None if no trace points are found within the radius
        """
        min_distance = -1
        closest = None
        closest_type = None
        min_interior_distance = -1
        closest_trace_interior = None
        tform = self.tform

        # only check the traces within the view if provided
        if traces_in_view:
            traces = traces_in_view
        else:
            traces = self.tracesAsList()
        
        # iterate through all traces to get closest
        for trace in traces:
            # skip hidden traces
            if not include_hidden and trace.hidden:
                continue
            points = []
            for point in trace.points:
                x, y = tform.map(*point)
                points.append((x,y))
            
            # find the distance of the point from each trace
            dist = getDistanceFromTrace(
                field_x,
                field_y,
                points,
                factor=1/self.mag,
                absolute=False
            )
            if closest is None or abs(dist) < min_distance:
                min_distance = abs(dist)
                closest = trace
                closest_type = "trace"
            
            # check if the point is inside any filled trace
            if (
                trace.fill_mode[0] != "none" and
                dist > 0 and 
                (closest_trace_interior is None or dist < min_interior_distance)
            ):
                min_interior_distance = dist
                closest_trace_interior = trace
        
        # check for ztrace points close by
        if self.series.options["show_ztraces"]:
            for ztrace in self.series.ztraces.values():
                for i, pt in enumerate(ztrace.points):
                    if pt[2] == self.n:
                        x, y = tform.map(*pt[:2])
                        dist = distance(field_x, field_y, x, y)
                        if closest is None or dist < min_distance:
                            min_distance = dist
                            closest = (ztrace, i)
                            closest_type = "ztrace_pt"
        
        # check for flags close by
        show_flags = self.series.options["show_flags"]
        if show_flags != "none":
            for flag in self.flags:
                if show_flags == "unresolved" and flag.resolved:
                    continue
                x, y = tform.map(flag.x, flag.y)
                dist = distance(field_x, field_y, x, y)
                if closest is None or dist < min_distance:
                    min_distance = dist
                    closest = flag
                    closest_type = "flag"
        
        # check for radius and if pointer is in interior
        if min_distance > radius:
            if closest_trace_interior:
                closest = closest_trace_interior
                closest_type = "trace"
            else:
                closest = None
                closest_type = None

        return closest, closest_type
    
    def deselectAllTraces(self):
        """Deselect all traces."""
        self.selected_traces = []
        self.selected_ztraces = []
        self.selected_flags = []
    
    def selectAllTraces(self):
        """Select all traces."""
        self.selected_traces = self.tracesAsList()
    
    def hideTraces(self, traces : list = None, hide=True, log_event=True):
        """Hide traces.
        
            Params:
                traces (list): the traces to hide
                hide (bool): True if traces should be hidden
        """
        modified = False

        if not traces:
            traces = self.selected_traces

        for trace in traces:
            modified = True
            trace.setHidden(hide)
            self.modified_contours.add(trace.name)
            if log_event:
                self.series.addLog(trace.name, self.n, "Modify trace(s)")
        
        self.selected_traces = []

        return modified
    
    def unhideAllTraces(self, log_event=True):
        """Unhide all traces on the section."""
        modified = False
        for trace in self.tracesAsList():
            hidden = trace.hidden
            if hidden:
                modified = True
                trace.setHidden(False)
                self.modified_contours.add(trace.name)
                if log_event:
                    self.series.addLog(trace.name, self.n, "Modify trace(s)")
        
        return modified
    
    def makeNegative(self, negative=True, log_event=True):
        """Make a set of traces negative."""
        traces = self.selected_traces
        for trace in traces:
            self.removeTrace(trace, log_event=False)
            trace.negative = negative
            self.addTrace(trace, log_event=False)
            if log_event:
                self.series.addLog(trace.name, self.n, "Modify trace(s)")
    
    def deleteTraces(self, traces : list = None, flags : list = None, log_event=True):
        """Delete selected traces.
        
            Params:
                traces (list): a list of traces to delete (default is selected traces)
                flags (list): a list of flags to delete (default is selected flags)
        """
        modified = False

        if traces is None:
            traces = self.selected_traces.copy()

        for trace in traces:
            modified = True
            self.removeTrace(trace, log_event)
            if trace in self.selected_traces:
                self.selected_traces.remove(trace)
        
        if flags is None:
            flags = self.selected_flags.copy()
        
        for flag in flags:
            modified = True
            self.removeFlag(flag, log_event)
            if flag in self.selected_flags:
                self.selected_flags.remove(flag)

        return modified
    
    def translateTraces(self, dx : float, dy : float, log_event=True):
        """Translate the selected traces.
        
            Params:
                dx (float): x-translate
                dy (float): y-translate
        """
        tform = self.tform

        for trace in self.selected_traces:
            self.removeTrace(trace, log_event=False)
            for i, p in enumerate(trace.points):
                # apply forward transform
                x, y = tform.map(*p)
                # apply translate
                x += dx
                y += dy
                # apply reverse transform
                x, y = tform.map(x, y, inverted=True)
                # replace point
                trace.points[i] = (x, y)
            self.addTrace(trace, log_event=False)
            if log_event:
                self.series.addLog(trace.name, self.n, "Modify trace(s)")
        
        for ztrace, i in self.selected_ztraces:
            x, y, snum = ztrace.points[i]
            # apply forward tform
            x, y = tform.map(x, y)
            # apply translate
            x += dx
            y += dy
            # apply reverse transform
            x, y = tform.map(x, y, inverted=True)
            # replace point
            ztrace.points[i] = (x, y, snum)
            # keep track of modified ztrace
            self.series.modified_ztraces.add(ztrace.name)
            if log_event:
                self.series.addLog(ztrace.name, self.n, "Modify ztrace")
        
        for flag in self.selected_flags:
            # apply forward tform
            x, y = tform.map(flag.x, flag.y)
            # apply translate
            x += dx
            y += dy
            # apply reverse tform
            x, y = tform.map(x, y, inverted=True)
            # replace point
            flag.x, flag.y = x, y
            # keep track of modified flag
            if log_event:
                self.series.addLog(None, self.n, "Modify flag")
    
    def importTraces(self, other, regex_filters=[]):
        """Import the traces from another section.
        
            Params:
                other (Section): the section with traces to import
                regex_filters (list): the list of regex filters for objects
        """
        for cname, contour in other.contours.items():
            passes_filters = False if regex_filters else True
            for rf in regex_filters:
                if bool(re.fullmatch(rf, cname)):
                    passes_filters = True

            if passes_filters:
                if cname in self.contours:
                    self.contours[cname].importTraces(contour)
                else:
                    self.contours[cname] = contour.copy()
        
        self.save()