import os

from PyReconstruct.modules.datatypes import Series, Transform
from PyReconstruct.modules.constants import getDateTime

def importTransforms(series : Series, tforms_fp : str, series_states=None, log_event=True):
        """Import transforms from a text file.
        
            Params:
                series (Series): the series to import transforms to
                tforms_fp (str): the file path for the transforms file
                series_states (SereisStates): series states object from GUI
        """
        # read through file
        with open(tforms_fp, "r") as f:
            lines = f.readlines()
        tforms = {}
        for line in lines:
            nums = line.split()
            if len(nums) != 7:
                print("Incorrect transform file format")
                return
            try:
                if int(nums[0]) not in series.sections:
                    print("Transform file section numbers do not correspond to this series")
                    return
                tforms[int(nums[0])] = [float(n) for n in nums[1:]]
            except ValueError:
                print("Incorrect transform file format")
                return
        
        # set tforms
        fname = os.path.basename(tforms_fp)
        fname = fname[:fname.rfind(".")]
        d, t = getDateTime()
        new_alignment_name = f"{fname}-{d}"
        for section_num, section in series.enumerateSections(
            message="Importing transforms...",
            series_states=series_states,
            breakable=False
        ):
            if section_num in tforms:
                tform = tforms[section_num]
                # multiply pixel translations by magnification of section
                tform[2] *= section.mag
                tform[5] *= section.mag
            else:
                tform = section.tform.getList()
            section.tforms[new_alignment_name] = Transform(tform)
            section.save()
        series.alignment = new_alignment_name
        series.save()
        
        # log event
        if log_event:
             series.addLog(None, None, f"Import transforms to alignment {series.alignment}")
