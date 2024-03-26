import time
from turtle import Turtle
import turtle
import math
import keyboard
from dataclasses import dataclass

# region Classes

@dataclass
class Vector3:
    x: float
    y: float
    z: float

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
        return Vector3(self.x / mag, self.y / mag, self.z / mag)

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
        s_x = math.sin(rotation.x * (math.pi/180))
        c_x = math.cos(rotation.x * (math.pi/180))

        p.x -= position.x
        p.z -= position.z

        x_new = (p.x * c_y - p.z * s_y)
        z_new = (p.x * s_y + p.z * c_y)

        p.x = x_new + position.x
        p.z = z_new + position.z
        return p

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
class Quaternion:
    x: float
    y: float
    z: float
    w: float

@dataclass
class Camera:
    position: Vector3
    rotation: Vector3
    zoom: int
    def forward(self):
        vec = Vector3(self.position.x, self.position.y, self.position.z+1)
        vec = vec.rotate_around(self.position, self.rotation) - self.position
        return vec

@dataclass
class Line:
    pos1: Vector3
    pos2: Vector3

@dataclass
class Polygon:
    points: list
    middle: Vector3
    color: tuple
    def set_middle(self):
        mid_x = 0
        mid_y = 0
        mid_z = 0
        for vector in self.points:
            mid_x += vector.x / len(self.points)
            mid_y += vector.y / len(self.points)
            mid_z += vector.z / len(self.points)
        self.middle = Vector3(mid_x, mid_y, mid_z)
# endregion


# region Objects
def create_poly(color: tuple, *args: Vector3):
    """
    Creates a polygon object out of a series of points and a color.
    :param color: A tuple of 3 floats that represent the RGB content of a color.
    :arguments: Each argument given is a point making up the polygon, 3 recommended.
    """
    midpoint = Vector3(0, 0, 0)
    poly = Polygon(list(args), midpoint, color)
    poly.set_middle()
    return poly

def create_cube(side: float, position: Vector3, color: tuple) -> list:
    """
    Creates a list of polygon objects that form a cube with one color.
    :param color: A tuple of 3 floats that represent the RGB content of a color.
    :param position: The position of the corner of the lowest corner of the cube.
    :param side: How long the sides of the cube are.
    """
    polygons = list()
    corner_ = Vector3(position.x, position.y, position.z)
    corner_x = Vector3(position.x+side, position.y, position.z)
    corner_xy = Vector3(position.x+side, position.y+side, position.z)
    corner_y = Vector3(position.x, position.y+side, position.z)
    corner_z = Vector3(position.x, position.y, position.z+side)
    corner_yz = Vector3(position.x, position.y+side, position.z+side)
    corner_xz = Vector3(position.x+side, position.y, position.z+side)
    corner_xyz = Vector3(position.x+side, position.y+side, position.z+side)

    polygons.append(create_poly(color, corner_, corner_x, corner_xy, corner_y))
    polygons.append(create_poly(color, corner_, corner_x, corner_xz, corner_z))
    polygons.append(create_poly(color, corner_, corner_z, corner_yz, corner_y))
    polygons.append(create_poly(color, corner_xyz, corner_xy, corner_x, corner_xz))
    polygons.append(create_poly(color, corner_xyz, corner_yz, corner_z, corner_xz))
    polygons.append(create_poly(color, corner_xyz, corner_yz, corner_y, corner_xy))


    return list(polygons)

def create_file_object(position: Vector3, filename: str) -> list:
    with open("Objects/" + filename) as file:
        color = (1, 1, 1)
        vectors = []
        polygons = []
        for line in file:
            stripped = line.strip()
            split = line.split(" ")
            if (stripped == "" and len(vectors) > 1) or stripped == "end":
                poly = Polygon(vectors, Vector3(0, 0, 0), color)
                poly.set_middle()
                polygons.append(poly)
                vectors = []
            elif stripped[0] == "v":
                vec = Vector3(float(split[1]), float(split[2]), float(split[3]))
                vec += position
                vectors.append(vec)
            elif stripped[0] == "c":
                color = (float(split[1]), float(split[2]), float(split[3]))
    print(polygons)
    return polygons

# endregion


def init(t: Turtle()):
    """
    Sets up the initial conditions for turtle.
    """
    t.up()
    t.speed(0)
    turtle.tracer(False)
    t.hideturtle()
    t.goto(0, 0)


def Controls(cam: Camera):
    """
    Allows user to press keyboard buttons to move and rotate the camera around the virtual world
    :param cam: The location, rotation, and all other information of the camera.
    """
    if keyboard.is_pressed("w"):
        cam.position += cam.forward().scale(0.1)
    if keyboard.is_pressed("s"):
        cam.position += cam.forward().scale(-0.1)
    if keyboard.is_pressed("a"):
        cam.position += cam.forward().rotate_around(Vector3(0, 0, 0), Vector3(0, 90, 0)).scale(0.1)
    if keyboard.is_pressed("d"):
        cam.position += cam.forward().rotate_around(Vector3(0, 0, 0), Vector3(0, -90, 0)).scale(0.1)
    if keyboard.is_pressed("q"):
        cam.position += Vector3(0, 0.1, 0)
    if keyboard.is_pressed("e"):
        cam.position += Vector3(0, -0.1, 0)
    if keyboard.is_pressed("left arrow"):
        cam.rotation += Vector3(0, 2, 0)
    if keyboard.is_pressed("right arrow"):
        cam.rotation += Vector3(0, -2, 0)


def render(cam: Camera, items: list, t: Turtle()):
    """
    Moves the turtle so that it draws a three-dimensional image on a 2D screen.
    :param cam: The location, rotation, and all other information of the camera.
    :param items: A List of Polygons and other 3D objects to be rendered.
    """
    t.clear()
    init(t)
    turtle.setworldcoordinates(-cam.zoom, -cam.zoom, cam.zoom, cam.zoom)
    for item in items:
        if type(item) == Polygon:
            t.fillcolor(item.color)
            # Setup points
            relative_points = []
            for point in item.points:
                pos = point.rotate_around(cam.position, -cam.rotation)
                relative_points.append(Vector3(pos.x - cam.position.x,
                                               pos.y - cam.position.y,
                                               pos.z - cam.position.z))
            # Check if Polygon is in view.
            in_range = False
            for point in relative_points:
                if point.z > 0:
                    in_range = True
                else:
                    point.z = 0.0001
            # Draw
            if in_range:
                first = relative_points.pop(0)
                relative_points.append(first)
                t.goto(first.x / first.z, first.y / first.z)
                t.down()
                t.begin_fill()
                for point in relative_points:
                    t.goto(point.x / point.z, point.y / point.z)
                t.end_fill()
                t.up()
            t.end_fill()
    turtle.tracer(True)

def main():
    """
    Sets up world, displays world and allows you to move camera around world.
    """
    cam = Camera(Vector3(-1, 0.5, 0), Vector3(0, 0, 0), 1)
    polygons = []
    polygons.extend(create_cube(1, Vector3(0, 0, 2), (1, 0.5, 0.5)))
    polygons.extend(create_cube(1, Vector3(1, 0, 2), (0.5, 0.5, 1)))
    polygons.extend(create_file_object(Vector3(-2, 1, 2), "testing.obj"))
    update = Vector3(0, 0, 0)
    turtle1 = Turtle()
    turtle2 = Turtle()

    for i in range(1000):
        if i % 2 == 0:
            t = turtle1
        else:
            t = turtle2
        # Controls
        Controls(cam)
        # Visuals
        sorted_polys = sorted(polygons, key=lambda x: x.middle.distance(cam.position), reverse=True)
        render(cam, sorted_polys, t)
        time.sleep(0.01)


if __name__ == "__main__":
    main()
