import numpy as np

from skimage.draw import polygon
import trimesh

from PyReconstruct.modules.calc import centroid
from PyReconstruct.modules.datatypes import Trace, Transform

class Object3D():

    def __init__(self, name):
        self.name = name
        self.extremes = []  # xmin, xmax, ymin, ymax, zmin, zmax
    
    def addToExtremes(self, x, y, s):
        """Keep track of the extreme values."""
        if not self.extremes:
            self.extremes = [x, x, y, y, s, s]
        else:
            if x < self.extremes[0]: self.extremes[0] = x
            if x > self.extremes[1]: self.extremes[1] = x
            if y < self.extremes[2]: self.extremes[2] = y
            if y > self.extremes[3]: self.extremes[3] = y
            if s < self.extremes[4]: self.extremes[4] = s
            if s > self.extremes[5]: self.extremes[5] = s

class Surface(Object3D):

    def __init__(self, name):
        """Create a 3D Surface object."""
        super().__init__(name)
        self.color = None
        self.traces = {}
    
    def addTrace(self, trace : Trace, snum : int, tform : Transform = None):
        """Add a trace to the surface data."""
        if self.color is None:
            self.color = tuple([c/255 for c in trace.color])
        
        if snum not in self.traces:
            self.traces[snum] = {}
            self.traces[snum]["pos"] = []
            self.traces[snum]["neg"] = []
        
        pts = []
        for pt in trace.points:
            if tform:
                x, y = tform.map(*pt)
            else:
                x, y = pt
            self.addToExtremes(x, y, snum)
            pts.append((x, y))
        
        if trace.negative:
            self.traces[snum]["neg"].append(pts)
        else:
            self.traces[snum]["pos"].append(pts)
    
    def generate3D(self, section_mag, section_thickness, alpha=1, smoothing="none"):
        """Generate the numpy array volumes.
        """
        # set voxel resolution to arbitrary x times average sections mag
        vres = section_mag * 8

        # calculate the dimensions of bounding box for empty array
        xmin, xmax, ymin, ymax, smin, smax = tuple(self.extremes)
        vshape = (
            round((xmax-xmin)/vres)+1,
            round((ymax-ymin)/vres)+1,
            smax-smin+1
        )
    
        # create empty numpy volume
        volume = np.zeros(vshape, dtype=bool)

        # add the traces to the volume
        for snum, trace_lists in self.traces.items():
            for trace in trace_lists["pos"]:
                x_values = []
                y_values = []
                for x, y in trace:
                    x_values.append(round((x-xmin) / vres))
                    y_values.append(round((y-ymin) / vres))
                x_pos, y_pos = polygon(
                    np.array(x_values),
                    np.array(y_values)
                )
                volume[x_pos, y_pos, snum - smin] = True
            # subtract out the negative traces
            for trace in trace_lists["neg"]:
                x_values = []
                y_values = []
                for x, y in trace:
                    x_values.append(round((x-xmin) / vres))
                    y_values.append(round((y-ymin) / vres))
                x_pos, y_pos = polygon(
                    np.array(x_values),
                    np.array(y_values)
                )
                volume[x_pos, y_pos, snum - smin] = False

        # generate trimesh
        tm = trimesh.voxel.ops.matrix_to_marching_cubes(volume)
        tm : trimesh.base.Trimesh

        # add metadata
        tm.metadata["name"] = self.name
        tm.metadata["color"] = self.color
        tm.metadata["alpha"] = alpha

        # smooth trimesh
        if smoothing == "humphrey":
            trimesh.smoothing.filter_humphrey(tm)
        elif smoothing == "laplacian":
            trimesh.smoothing.filter_laplacian(tm)

        faces = tm.faces
        verts = tm.vertices

        # provide real vertex locations
        # (i.e., normalize to real world dimensions)
        verts[:,:2] *= vres
        verts[:,0] += xmin
        verts[:,1] += ymin
        verts[:,2] += smin
        verts[:,2] *= section_thickness

        mesh_data = {
            "name": self.name,
            "color": self.color,
            "alpha": alpha,
            "vertices": verts,
            "faces": faces
        }

        return mesh_data


class Spheres(Object3D):

    def __init__(self, name):
        """Create a 3D Spheres object."""
        super().__init__(name)
        self.colors = []
        self.centroids = []
        self.radii = []
    
    def addTrace(self, trace : Trace, snum : int, tform : Transform = None):
        """Add a trace to the spheres data."""
        self.colors.append(tuple([c/255 for c in trace.color]))

        x, y = centroid(trace.points)
        if tform:
            x, y = tform.map(x, y)
        self.centroids.append((x, y, snum))
        self.addToExtremes(x, y, snum)

        self.radii.append(trace.getRadius(tform))
    
    def generate3D(self, section_thickness : float, alpha=1):
        """Generate the opengl meshes for the spheres."""
        verts = []
        faces = []
        for point, radius in zip(
            self.centroids,
            self.radii
        ):
            x, y, s = point
            z = s * section_thickness
            sphere = trimesh.primitives.Sphere(radius=radius, center=(x,y,z), subdivisions=1)
            faces += (sphere.faces + len(verts)).tolist()
            verts += sphere.vertices.tolist()
        
        mesh_data = {
            "name": self.name,
            "color": self.colors[0],
            "alpha": alpha,
            "vertices": np.array(verts),
            "faces": np.array(faces)
        }
        
        return mesh_data

class Contours(Object3D):

    def __init__(self, name):
        """Create a 3D Surface object."""
        super().__init__(name)
        self.color = None
        self.traces = {}
    
    def addTrace(self, trace : Trace, snum : int, tform : Transform = None):
        """Add a trace to the surface data."""
        if self.color is None:
            self.color = tuple([c/255 for c in trace.color])
        
        if snum not in self.traces:
            self.traces[snum] = []
        
        pts = []
        for pt in trace.points:
            if tform:
                x, y = tform.map(*pt)
            else:
                x, y = pt
            self.addToExtremes(x, y, snum)
            pts.append((x, y))
        
        if trace.closed:
            pts.append(pts[0])
        
        self.traces[snum].append(pts)
    
    def generate3D(self, section_thickness, alpha=1):
        """Generate trace slabs.
        """
        verts = []
        faces = []
        for snum in self.traces:
            # get the z values
            z1 = snum * section_thickness
            z2 = z1 + section_thickness/2
            for trace in self.traces[snum]:
                for i in range(len(trace)-1):
                    # get the xy coords of the points
                    x1, y1 = trace[i]
                    x2, y2 = trace[i+1]
                    # gather the four points to create the slab section
                    verts.append([x1, y1, z1])
                    verts.append([x2, y2, z1])
                    verts.append([x2, y2, z2])
                    verts.append([x1, y1, z2])
                    # create the faces
                    l = len(verts)
                    faces.append([l-4, l-3, l-2])
                    faces.append([l-4, l-2, l-1])
        
        mesh_data = {
            "name": self.name,
            "color": self.color,
            "alpha": alpha,
            "vertices": np.array(verts),
            "faces": np.array(faces)
        }

        return mesh_data