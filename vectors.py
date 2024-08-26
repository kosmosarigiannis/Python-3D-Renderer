import math
from dataclasses import dataclass

@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def other(self):
        return Vector3(self.x, self.y, self.z)

    def scale(self, multiplier: float):
        """
        Returns the vector but [multiplier] times the magnitude.
        """
        return Vector3(self.x * multiplier, self.y * multiplier, self.z * multiplier)

    def magnitude(self) -> float:
        """
        Returns the magnitude of the vector.
        """
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self):
        """
        Returns the vector pointing the same direction, but with a magnitude of 1.
        """
        mag = self.magnitude()
        if mag == 0:
            return self
        return Vector3(self.x / mag, self.y / mag, self.z / mag)

    def directional_component(self, other):
        """
        Returns the component of this vector pointing in the direction of the other vector.
        """
        mag = self.magnitude()
        angle = self.get_angle() - other.get_angle
        return other.normalize().scale(mag * math.cos(angle))

    def distance(self, V):
        """
        Finds the distance between two points.
        """
        return math.sqrt((self.x - V.x)**2 + (self.y - V.y)**2 + (self.z - V.z)**2)

    def rotate_around(self, position, rotation):
        """
        Rotates a vector by [rotation] around a point [position], only y rotation works.
        """
        p = Vector3(self.x, self.y, self.z)
        s_y = math.sin(rotation.y * (math.pi/180))
        c_y = math.cos(rotation.y * (math.pi/180))

        p.x -= position.x
        p.z -= position.z

        x_new = (p.x * c_y - p.z * s_y)
        z_new = (p.x * s_y + p.z * c_y)

        p.x = x_new + position.x
        p.z = z_new + position.z
        return p

    def get_angle(self):
        if self.z != 0:
            angle = math.atan(self.x / self.z) * (180/math.pi)
        else:
            angle = 90
        if self.x < 0:
            angle += 180
        return angle

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def __add__(self, V):
        return Vector3(self.x + V.x, self.y + V.y, self.z + V.z)

    # Method to subtract 2 Vectors
    def __sub__(self, V):
        return Vector3(self.x - V.x, self.y - V.y, self.z - V.z)

    # Method to calculate the dot product of two Vectors
    def __xor__(self, V):
        return self.x * V.x + self.y * V.y + self.z * V.z

    # Method to calculate the cross product of 2 Vectors
    def __mul__(self, V):
        return Vector3(self.y * V.z - self.z * V.y,
                      self.z * V.x - self.x * V.z,
                      self.x * V.y - self.y * V.x)


@dataclass
class Line:
    pos1: Vector3
    pos2: Vector3

    def length(self) -> float:
        leng = self.pos1.distance(self.pos2)
        return leng

    def set_length(self, leng: float):
        change = self.pos1 - self.pos2
        change = change.normalize()
        self.pos2 = self.pos1 + change.scale(leng)

    def scale(self, mod: float):
        change = self.pos1 - self.pos2
        self.pos2 = self.pos1 + change.scale(mod)

    def extend(self):
        change = self.pos1 - self.pos2
        self.pos1 += change.scale(100)
        self.pos2 -= change.scale(100)

    def line_intersection(self, other):
        self.extend()
        other.extend()
        A = (self.pos1.x, self.pos1.z)
        B = (self.pos2.x, self.pos2.z)
        C = (other.pos1.x, other.pos1.z)
        D = (other.pos2.x, other.pos2.z)
        line1 = (A, B)
        line2 = (C, D)
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        zdiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, zdiff)
        if div == 0:
            pass
            raise Exception('lines do not intersect')

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        z = det(d, zdiff) / div
        return x, z
