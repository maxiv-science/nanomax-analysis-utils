import numpy as np
import math

class Plane(object):
    """
    Class representing the plane
        ax + by + cz = d
    where (a,b,c) is the surface normal and 
        d = ax + by + cz
    for any arbitrary point (x,y,z) on the plane. If (a,b,c) is a unit
    vector then d is the closest distance from the origin to the plane
    in the direction of the surface normal. This is all rescaled so
    after construction the plane is  represented by p.normal and p.dist.
    Note that p.dist can be negative and that a plane has an outside
    and an inside. The plane with -p.dist and -p.normal is conincident
    with the first plane, but is considered inside out.
    """
    def __init__(self, a=None, b=None, c=None, d=None):
        normal = np.array((a, b, c))
        scaling = 1.0 / np.linalg.norm(normal)
        self.normal = normal * scaling
        self.dist = d * scaling

    def rotate(self, axis='x', angle=0):
        """
        Rotate the plane by a specified angle in degrees around the
        specified axis.
        """
        assert axis in ('x', 'y', 'z')
        sin = np.sin(angle / 180. * np.pi)
        cos = np.cos(angle / 180. * np.pi)
        if axis == 'x':
            R = np.array([[1, 0, 0], [0, cos, -sin], [0, sin, cos]])
        elif axis == 'y':
            R = np.array([[cos, 0, sin], [0, 1, 0], [-sin, 0, cos]])
        elif axis == 'z':
            R = np.array([[cos, -sin, 0], [sin, cos, 0], [0, 0, 1]])
        self.normal = np.dot(R, self.normal)

    def shift(self, shifts):
        self.dist += np.dot(np.array(shifts), self.normal)

    def side(self, point):
        """
        Checks on which side of the plane the given point lies.
        """
        #return np.dot(self.normal, point) - self.dist
        extra_dims = len(np.shape(point)) - 1
        normal = self.normal.reshape((-1,) + (1,)*extra_dims)
        return np.sum(normal * point, axis=0) - self.dist

    def contains(self, point, tol=1e-6):
        """
        Checks whether the plane contains the given point.
        """
#        if np.abs(self.side(point)) > tol:
#            return False
#        return True
        return np.abs(self.side(point)) > tol

    def _recalculate(self):
        """
        Find values of a, b and c from the normal vector and distance.
        """
        # a, b, and c form the surface normal, so...
        self._a, self._b, self._c = self.normal
        # find an arbitrary point xyz on the plane
        x, y, z = self.dist * self.normal
        self._d = self._a * x + self._b * y + self._c * z

    @property
    def a(self):
        self._recalculate()
        return self._a

    @property
    def b(self):
        self._recalculate()
        return self._b
    
    @property
    def c(self):
        self._recalculate()
        return self._c

    @property
    def d(self):
        self._recalculate()
        return self._d

class Solid(object):
    """
    Class representing any solid (cube or octahedron, say) defined by
    its bounding planes.
    """
    def __init__(self, planes=[]):
        self.planes = planes

    def contains(self, points):
        """
        Checks whether the solid contains the given point.
        """
#        for plane in self.planes:
#            if plane.side(point) > tol:
#                return False
#        return True
        results = []
        for plane in self.planes:
            results.append(plane.side(points))
        results = np.array(results)
        return np.all(results < 0, axis=0)

    def rotate(self, *args, **kwargs):
        for p in self.planes:
            p.rotate(*args, **kwargs)

    def shift(self, *args, **kwargs):
        for p in self.planes:
            p.shift(*args, **kwargs)

    def scale(self, factor):
        """
        Scale a solid around the origin.
        """
        for p in self.planes:
            p.dist *= factor

    def vertices(self):
        """
        Numerically searches for and returns the found vertices.
        """
        N = len(self.planes)
        vertices = []
        for i in range(N):
            for j in range(i):
                for k in range(j):
                    A = np.array([[self.planes[i].a, self.planes[i].b, self.planes[i].c],
                                  [self.planes[j].a, self.planes[j].b, self.planes[j].c],
                                  [self.planes[k].a, self.planes[k].b, self.planes[k].c]])
                    b = np.array([self.planes[i].d, self.planes[j].d, self.planes[k].d])
                    try:
                        x = np.linalg.solve(A, b)
                        if self.contains(x):
                            vertices.append(x)
                        else:
                            pass
                    except np.linalg.LinAlgError:
                        pass
        vertices = np.unique(vertices, axis=0)
        return tuple(vertices)

    def faces(self):
        """
        Searches for groups of vertices on the bounding planes and returns
        a tuple of faces.
        """
        vertices = self.vertices() # the polyhedron's vertices
        found_faces = []
        for p in self.planes:
            corners = [] # the corners of the facet
            for v in vertices:
                if p.contains(v):
                    corners.append(v)
            if len(corners) >= 3:
                if len(corners) > 3:
                    # sort the corners so we get a convex polygon
                    center = np.mean(corners, axis=0)
                    # orthonormal basis in the facet plane
                    v1 = corners[0] - center
                    v2 = np.cross(p.normal, v1)
                    v1 /= np.linalg.norm(v1)
                    v2 /= np.linalg.norm(v2)
                    v1v1 = np.dot(v1, v1)
                    v2v2 = np.dot(v2, v2)
                    # angles are found from projections on these
                    angles = []
                    for c in corners:
                        c_v1 = np.dot(c-center, v1) / v1v1
                        c_v2 = np.dot(c-center, v2) / v1v1
                        angle = math.atan2(c_v1, c_v2)
                        angles.append(angle)
                    order = np.argsort(angles)
                    corners = [corners[o] for o in order]
                found_faces.append(corners)
        return found_faces

    def volume(self):
        return None


class Octahedron(Solid):
    """
    Class representing a regular octahedron standing in the unit cube.
    """
    def __init__(self):
        planes = [Plane(1, 1, 1, 2),
                  Plane(-1, 1, 1, 1),
                  Plane(-1, -1, 1, 0),
                  Plane(1, -1, 1, 1),
                  Plane(1, -1, -1, 0),
                  Plane(1, 1, -1, 1),
                  Plane(-1, 1, -1, 0),
                  Plane(-1, -1, -1, -1),
                  ]
        super(Octahedron, self).__init__(planes=planes)

class Cube(Solid):
    """
    Class representing the unit cube.
    """
    def __init__(self):
        planes = [Plane(1, 0, 0, 1),
                  Plane(0, 1, 0, 1),
                  Plane(0, 0, 1, 1),
                  Plane(-1, 0, 0, 0),
                  Plane(0, -1, 0, 0),
                  Plane(0, 0, -1, 0),
                  ]
        super(Cube, self).__init__(planes=planes)

class TruncatedOctahedron(Octahedron):
    """
    An octahedron standing in the the unit cube, truncated by a centered
    cube of size "scale"
    """
    def __init__(self, scale):
        super(TruncatedOctahedron, self).__init__()
        cube = Cube()
        cube.shift([-.5, -.5, -.5])
        cube.scale(scale)
        cube.shift([.5, .5, .5])
        self.planes += cube.planes


if __name__ == '__main__':

    # make an octahedron and lie it down on the xy plane,
    # with the tips pointing along the x axis.
    o = TruncatedOctahedron(.69)
    o.shift([-.5, -.5, -.5])
    o.rotate('z', 45)
    o.rotate('y', 109.5/2)
    o.scale(2)

    #rotate that
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(ncols=3)
    oldangle = 0
    for i, angle in enumerate(np.linspace(0, 180, 20)):
        o.rotate('z', angle - oldangle)
        oldangle = angle
        x = np.linspace(-1, 1, 50)
        xx, yy, zz = np.meshgrid(x, x, x)
        arr = o.contains((xx, yy, zz))

        for i, name in enumerate('xyz'):
            ax[i].clear()
            ax[i].imshow(np.flipud(np.mean(arr, axis=i).T), interpolation='none')
            ax[i].set_title('along %s'%name)

        plt.draw()
        plt.pause(.5)
