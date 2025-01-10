import os
import json
import numpy as np

from PyReconstruct.modules.datatypes import Series, Transform
from PyReconstruct.modules.constants import getDateTime


class IncorrectFormatError(Exception):
    pass


class IncorrectSecNumError(Exception):
    pass


def cafm_to_matrix(t):
    """Convert c_afm to Numpy matrix."""
    
    if isinstance(t, str):
        
        t = [float(elem) for elem in t.split(" ")]

        return np.matrix([
                [t[0], t[1], t[2]],
                [t[3], t[4], t[5]],
                [0, 0, 1]
            ])

    else:
        
        return np.matrix([
            [t[0][0], t[0][1], t[0][2]],
            [t[1][0], t[1][1], t[1][2]],
            [0, 0, 1]
        ])


def cafm_to_sanity(t, dim, scale_ratio=1, old_swift=False):
    """Convert c_afm to something sane."""

    ## Convert to matrix
    t = cafm_to_matrix(t)

    ## Transforms in older SWiFT project files are stored as inverted matrices
    if old_swift: t = np.linalg.inv(t)
    
    ## Get translation of bottom left corner from img height (px)
    BL_corner = np.array([[0], [dim], [1]])  # original BL corner
    BL_translation = np.matmul(t, BL_corner) - BL_corner

    ## Add BL corner translation to c_afm (x and y translation)
    t[0, 2] = BL_translation[0, 0]  # x translation in px
    t[1, 2] = BL_translation[1, 0]  # y translation in px

    ## Flip y axis by changing signs of a2, b1, and b3
    t[0, 1] *= -1  # a2
    t[1, 0] *= -1  # b1
    t[1, 2] *= -1  # b3
    
    ## Apply any scale ratio difference
    t[0, 2] *= scale_ratio
    t[1, 2] *= scale_ratio

    return t


def get_img_dim(scale_data):
    """Get image dimensions (height and width) from scale data."""
    return scale_data["swim_settings"]["img_size"]


def make_pyr_transforms(project_file, scale=1, cal_grid=False):
    """Return a list of PyReconstruct-formatted transformations."""

    with open(project_file, "r") as fp: swift_json = json.load(fp)

    pyr_transforms = [np.identity(3)] if cal_grid else []  # list to hold transforms

    stack_data = swift_json.get("stack")  # if exists

    if stack_data:  # new swift project file
    
        scale = f's{str(scale)}'  # requested scale as properly formatted string

        for section in stack_data:

            # Get all scales (or "levels")
        
            scales_all = section.get("levels") # all scales
            scale_req = scales_all.get(scale)  # requested scale
            scale_1 = scales_all.get("s1")     # scale 1
            
            # When scaling, only height (px) is considered by this script.
            # Will change if aligning non-square images,
            # which is not currently supported by AlignEM-SWiFT.
            
            img_height_1, img_width_1 = get_img_dim(scale_1)
            img_height, img_width = get_img_dim(scale_req)
        
            height_ratio = img_height_1 / img_height
            width_ratio = img_width_1 / img_width  # left here for now 
        
            # Get section transform, make sane, append to list
            transform = scale_req.get("cafm")
            transform = cafm_to_sanity(transform, dim=img_height, scale_ratio=height_ratio)
            pyr_transforms.append(transform)

    else:  # old swift project file

        scale = f'scale_{str(scale)}'
        scales_all = swift_json["data"]["scales"]
        
        scale_data = scales_all[scale]
        scale_data_1 = scales_all["scale_1"]
    
        stack_data = scale_data.get("stack")
        
        img_height_1, img_width_1 = scale_data_1.get('image_src_size')
        img_height, img_width = scale_data.get('image_src_size')

        height_ratio = img_height_1 / img_height
        width_ratio = img_width_1 / img_width

        for section in stack_data:
        
            # Get transform, make sane, append to list
            transform = section["alignment"]["method_results"]["cumulative_afm"]
            transform = cafm_to_sanity(transform, dim=img_height, scale_ratio=height_ratio, old_swift=True)
            pyr_transforms.append(transform)
    
    del transform

    return pyr_transforms


def transforms_as_strings(recon_transforms, output_file=None):
    """Return transform matrices as string."""

    output = ''
    
    for i, t in enumerate(recon_transforms):
        string = f'{i} {t[0, 0]} {t[0, 1]} {t[0, 2]} {t[1, 0]} {t[1, 1]} {t[1, 2]}\n'
        output += string

    if output_file:
        with open(output_file, "w") as fp: fp.write(output)

    return output

        
def importSwiftTransforms(series: Series, project_fp: str, scale: int = 1, cal_grid: bool = False, series_states=None, log_event=True):

    new_transforms = make_pyr_transforms(project_fp, scale, cal_grid)
    new_transforms = transforms_as_strings(new_transforms)
    transforms_list = new_transforms.strip().split("\n")

    if len(transforms_list) != len(series.sections):
        raise IncorrectSecNumError("Mismatch between number of sections and number of transformations you are trying to import.")

    tforms = {}  # Empty dictionary to hold transformations
    
    for line in transforms_list:
        
        swift_sec, *matrix = line.split()
        
        if len(matrix) != 6:
            
            raise IncorrectFormatError(f"Project file (at index {swift_sec}) incorrect number of elements.")
        
        try:

            if int(swift_sec) not in series.sections:
                raise IncorrectSecNumError("Section numbers in project file do not correspond to current series.")

            current_tform = { int(swift_sec): [float(elem) for elem in matrix] }
            
            tforms.update(current_tform)
            
        except ValueError:
            
            raise IncorrectFormatError("Incorrect project file format.")
        
    # set tforms
    fname = os.path.basename(project_fp)
    fname = fname[:fname.rfind(".")]
    d, _ = getDateTime()
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
        series.addLog(None, None, f"Import SWIFT transforms to alignment {series.alignment}")

    print("SWiFT transforms imported!")
