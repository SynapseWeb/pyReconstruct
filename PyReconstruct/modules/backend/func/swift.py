"""Perform SWiFT operations."""

from pathlib import Path
from typing import Union, List, Tuple, cast

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

    def construct_command(
            self, x_off: int, y_off: int, center_tmpl: Coordinate, center: Coordinate
    ) -> str:
            """Construct a swim command."""

            cmd  = f"{self.bin} {self.window} -i 3 "
            cmd += f"-x {x_off} -y {y_off} "
            cmd += f"{self.img_template} {center_tmpl[0]} {center_tmpl[1]} "
            cmd += f"{self.img} {center[0]} {center[1]}"

            return cmd
        
    def run(self) -> List[SwimOutput]:
        """Run swim operation."""

        offsets = (
            (-250, -250),
            ( 250, -250),
            ( 250,  250),
            (-250,  250)
        )

        anon = lambda e: self.construct_command(e[0], e[1], (1000, 1000), (868.734, 936.193))
        cmds = list(map(anon, offsets))

        multi_swim = [SwimOutput(get_stdout(cmd)) for cmd in cmds]

        return multi_swim


class MirOutput:

    def __init__(self, stdout):

        self.stdout = stdout

    @staticmethod
    def parse_string():

        pass

    @staticmethod
    def parse_affine():

        pass
            

class Mir:
    """Perform mir (multi-image registration) operation."""

    def __init__(self, bin: str, multi_swim: List[SwimOutput], img: Image, img_size, background: int=128):

        self.mutli_swim = multi_swim
        self.img = img
        self.img_size = img_size
        self.background = background

    def make_mir_file(self) -> str:
        """Construct and output a mir file."""

        tmp_file = "/tmp/tmp.mir"  # TODO: Make real temp file

        with open(tmp_file, "a") as fp:

            fp.write(f"B {self.img_size[0]} {self.img_size[1]}\n")
            fp.write(f"Z {self.background}\n")

            for swim in self.mutli_swim:

                fp.write(f"{swim.co_1[0]} {swim.co_1[1]} {swim.co_2[0]} {swim.co_2[1]}\n")
        
        return tmp_file

    def run(self):
        """Run mir operation."""

        mir_file = make_mir_file()

        return None


