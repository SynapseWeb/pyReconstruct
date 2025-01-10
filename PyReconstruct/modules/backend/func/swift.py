"""Perform SWiFT operations."""

from pathlib import Path
from typing import Union, Tuple, cast

from PyReconstruct.modules.backend.func import get_stdout


Coordinate = Tuple[float, float]
Image = str


class Swift:
    """Conduct a SWiFT procedure."""

    def __init__(self, img_0, img_1):

        self.img_0 = img_0
        self.img_1 = img_1

    def run(self):
        """Run SWiFT operation."""

        ## Estimate translational offset

        ## Run first-pass SWift

        ##

        pass


class SwimOutput():

    def __init__(self, swift_stdout: str):
        
        super().__init__()

        self.stdout = swift_stdout
        self.parsed = SwimOutput.parse_string(swift_stdout)

        self.snr                 = self.parsed[0]
        self.img_1, self.co_1    = self.parsed[1:3]
        self.img_2, self.co_2    = self.parsed[3:5]
        self.shape, self.offset  = self.parsed[5:]

    @staticmethod
    def parse_string(swim_str_output) -> tuple:
        """Parse swim output string."""

        split = swim_str_output.strip().replace(":", "").replace("  ", " ").replace("(", "").split()

        snr: Swim.SNR = float(split[0])
        
        img_1: Image = split[1]
        coordinate_1: Coordinate = cast(
            Coordinate, tuple(map(float, split[2:4]))
        )
        
        img_2: Image = split[4]
        coordinate_2: Coordinate = cast(
            Coordinate, tuple(map(float, split[5:7]))
        )

        shape: Swim.ShapeMatrix = cast(
            Swim.ShapeMatrix, tuple(map(float, split[7:11]))
        )
        offset: Swim.OffsetMatrix = cast(
            Swim.OffsetMatrix, tuple(map(float, split[11:13]))
        )
        
        return snr, img_1, coordinate_1, img_2, coordinate_2, shape, offset        
        

class Swim:
    """Perform swim operation."""

    ## Swim-specific types
    OffsetMatrix = Tuple[float, float]
    ShapeMatrix = Tuple[float, float, float]
    SNR = float

    def __init__(self, bin: Union[str, Path], window, img_template, img):

        self.bin = bin
        self.window = window  # swim window size
        self.img_template = img_template
        self.img = img

    def estimate_translation(self) -> SwimOutput:
        """Estimate translational offset of two images."""

        cmd = f"{self.bin} {self.window} -i 3 {self.img_template} {self.img}"
        
        estimate_string = get_stdout(cmd)
        estimate_output = SwimOutput(estimate_string)

        return estimate_output
        
    def run(self):

        pass        


class Mir:
    """Perform mir (multi-image registration) operation."""

    pass



