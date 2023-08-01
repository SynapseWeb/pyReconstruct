import os

from PySide6.QtCore import Qt

from modules.gui.table import SectionTableWidget
from modules.datatypes import Series

class SectionTableManager():

    def __init__(self, series : Series, mainwindow):
        """Create the trace table manager.
        
            Params:
                series (Series): the series object
                mainwindow (MainWindow): the main window widget
        """
        self.tables = []
        self.series = series
        self.mainwindow = mainwindow
    
    def newTable(self):
        """Create a new trace list."""
        new_table = SectionTableWidget(
            self.series,
            self.mainwindow,
            self
        )
        self.tables.append(new_table)
        self.mainwindow.addDockWidget(Qt.LeftDockWidgetArea, new_table)

    # MENU-RELATED FUNCTIONS
    
    def updateTables(self):
        """Updates a table with the current data.
        
            Params:
                table (ObjectTableWidget): the table to update
        """
        for table in self.tables:
            table.createTable()
    
    def updateSection(self, snum):
        """Update the data for a section.
        
            Params:
                section (Section): the section number with data to update
        """
        for table in self.tables:
            table.updateSection(snum)
    
    def updateSections(self, section_numbers : list):
        """Update the tables for a set of sections."""
        for snum in section_numbers:
            self.updateSection(snum)
    
    def lockSections(self, section_numbers : list[int], lock : bool):
        """Lock or unlock a set of sections.
        
            Params:
                section_numbers (list): the list of section numbers to modify
                lock (bool): True if sections should be locked
        """
        self.mainwindow.saveAllData()

        for snum in section_numbers:
            section = self.series.loadSection(snum)
            section.align_locked = lock
            section.save()
        
        # update the field
        self.mainwindow.field.reload()
        self.mainwindow.seriesModified(True)

        # update the tables
        self.updateSections(section_numbers)

    def setBC(self, section_numbers : list[int], b : int, c : int):
        """Set the brightness and contrast for a set of sections.
        
            Params:
                section_numbers (list): the list of section numbers to set
                b (int): the brightness to set
                c (int): the contrast to set
        """
        self.mainwindow.saveAllData()

        for snum in section_numbers:
            section = self.series.loadSection(snum)
            if b is not None:
                section.brightness = b
            if c is not None:
                section.contrast = c
            section.save()
        
        # update the field
        self.mainwindow.field.reload()
        self.mainwindow.seriesModified(True)

        # update the tables
        self.updateSections(section_numbers)
    
    def matchBC(self, section_numbers : list[int]):
        """Match the brightness and contrast of a set of sections to the current section.
        
            Params:
                section_numbers (list): the sections to modify
        """
        b = self.mainwindow.field.section.brightness
        c = self.mainwindow.field.section.contrast
        self.setBC(section_numbers, b, c)

    def editThickness(self, section_numbers : list[int], thickness : float):
        """Set the section thickness for a set of sections.
        
            Params:
                section_numbers (list): the list of section numbers to modify
                thickness (float): the new thickness to set for the sections
        """
        self.mainwindow.saveAllData()

        for snum in section_numbers:
            section = self.series.loadSection(snum)
            section.thickness = thickness
            section.save()        
        self.mainwindow.field.reload()
        self.updateSections(section_numbers)

        # refresh any existing obj table
        if self.mainwindow.field.obj_table_manager:
            self.mainwindow.field.obj_table_manager.refresh()
        
        self.mainwindow.seriesModified(True)
    
    def editSrc(self, snum : int, new_src : str):
        """Set the image source for a single section (and possible for all sections).
        
            Params:
                snum (int): the number of the section to modify (none if edit all sections)
                new_src (str): the new image source for the section
                edit_all (bool): True if ALL section sources should be modified
        """
        self.mainwindow.saveAllData()

        # edit all sections 
        if snum is None:
            s = new_src.split("#")
            if len(s) != 2:
                return
            max_digits = len(str(max(self.series.sections.keys())))
            for snum, section in self.series.enumerateSections(message="Modifying section image sources..."):
                section_src = s[0] + str(snum).zfill(max_digits) + s[1]
                section.src = section_src
                section.save()

        # edit only the current section
        else:
            section = self.series.loadSection(snum)
            section.src = new_src
            section.save()

        self.mainwindow.field.reload()
        self.mainwindow.field.reloadImage()
        self.updateSection(snum)
        self.mainwindow.seriesModified(True)
    
    # BUG: MAKE SURE ZTRAACE POINTS GET DELETED
    def deleteSections(self, section_numbers : list[int]):
        """Delete a set of sections.
        
            Params:
                section_numbers (list): the list of sections to delete
        """
        self.mainwindow.saveAllData()
        
        for snum in section_numbers:
            # delete the file
            filename = self.series.sections[snum]
            os.remove(os.path.join(self.series.getwdir(), filename))
            # delete link to file
            del(self.series.sections[snum])
        
        # refresh the data
        self.series.data.refresh()
        if self.mainwindow.field.obj_table_manager:
            self.mainwindow.field.obj_table_manager.refresh()
        
        # switch to first section if current section is deleted
        if self.series.current_section in section_numbers:
            self.mainwindow.changeSection(sorted(list(self.series.sections.keys()))[0], save=False)
        
        self.updateTables()

        self.mainwindow.seriesModified(True)
            
    def findSection(self, section_number : int):
        """Focus the view on a specific section.
        
            Params:
                section_number (int): the section the focus on
        """
        self.mainwindow.changeSection(section_number)
        
    def close(self):
        """Close all tables."""
        for table in self.tables:
            table.close()


