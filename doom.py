import time
from turtle import Turtle
import turtle
import math
import keyboard
from dataclasses import dataclass
from typing import Any, Union


CAM_ACCELERATION = 0
MOVE_ACCELERATION = [0, 0, 0]
COLLIDERS = []

# region Classes

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
    def forward(self) -> Vector3:
        vec = Vector3(self.position.x, self.position.y, self.position.z+1)
        vec = vec.rotate_around(self.position, self.rotation) - self.position
        return vec

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


@dataclass
class Polygon:
    points: list
    middle: Vector3
    color: tuple

    def instantiate(self):
        mid_x = 0
        mid_y = 0
        mid_z = 0
        for vector in self.points:
            mid_x += vector.x / len(self.points)
            mid_y += vector.y / len(self.points)
            mid_z += vector.z / len(self.points)
        self.middle = Vector3(mid_x, mid_y, mid_z)

        c = 0.25 -((self.facing().y + 1) / 8) + ((self.facing().x + 1) / 10) + ((self.facing().z + 1) / 20) + 0.5
        self.color = (self.color[0]*c, self.color[1]*c, self.color[2]*c)

    def facing(self) -> Vector3:
        return ((self.points[0]-self.points[1])*(self.points[0]-self.points[-1])).normalize()

@dataclass
class Sprite:
    middle: Vector3
    file: str
    scale: float

@dataclass
class PlaneCollider:
    position: Vector3
    x: float
    z: float
    y_rotation: int  # Clockwise

@dataclass
class SlopeCollider:
    position: Vector3
    x: float
    z: float
    slope: float
    y_rotation: int  # Clockwise

@dataclass
class WallCollider:
    position: Vector3
    x: float
    y: float
    y_rotation: int  # Clockwise

@dataclass
class SphereCollider:
    position: Vector3
    r: float

    def is_colliding(self, colliders) -> Union[None, PlaneCollider]:
        for col in colliders:
            if self.overlap(col) > 0:
                return col
        return None

    def overlap(self, col: Union[None, PlaneCollider]) -> float:
        if type(col) == SphereCollider:
            return (self.r + col.r) - self.position.distance(col.position)

        elif type(col) == PlaneCollider:
            pos = self.position.rotate_around(col.position, Vector3(0, col.y_rotation, 0))
            if col.position.x < pos.x < col.position.x + col.x and col.position.z < pos.z < col.position.z + col.z:
                return self.r - abs(col.position.y - pos.y)
            x = min(abs(col.position.x - pos.x), abs(col.position.x + col.x - pos.x))
            y = abs(col.position.y - pos.y)
            z = min(abs(col.position.z - pos.z), abs(col.position.z + col.z - pos.z))
            return self.r - pos.distance(Vector3(x, y, z))

        elif type(col) == SlopeCollider:
            pos = self.position.rotate_around(col.position, Vector3(0, col.y_rotation, 0))
            if col.position.x < pos.x < col.position.x + col.x and col.position.z < pos.z < col.position.z + col.z:
                return self.r - (abs(col.position.y - pos.y) + col.slope * (col.position.z - pos.z))
            x = min(abs(col.position.x - pos.x), abs(col.position.x + col.x - pos.x))
            y = abs(col.position.y - pos.y) + col.slope * (col.position.z - pos.z)
            z = min(abs(col.position.z - pos.z), abs(col.position.z + col.z - pos.z))
            return self.r - pos.distance(Vector3(x, y, z))

        elif type(col) == WallCollider:
            pos = self.position.rotate_around(col.position, Vector3(0, col.y_rotation, 0))
            if col.position.x < pos.x < col.position.x + col.x and col.position.y < pos.y < col.position.y + col.y and abs(col.position.z - pos.z) < self.r:
                return self.r - abs(col.position.z - pos.z)
            x = min(abs(col.position.x - pos.x), abs(col.position.x + col.x - pos.x))
            y = abs(col.position.z - pos.z)
            z = min(abs(col.position.y - pos.y), abs(col.position.y + col.y - pos.y))
            return self.r - pos.distance(Vector3(x, y, z))


@dataclass
class Object:
    position: Vector3
    rotation: Vector3
    collider: Union[None, SphereCollider]
    mesh: str

    def __post_init__(self):
        if self.collider is None:
            self.collider = None
        if self.mesh is None:
            self.mesh = ""
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
    poly.instantiate()
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
    polygons.append(create_poly(color, corner_, corner_z, corner_xz, corner_xz))
    polygons.append(create_poly(color, corner_, corner_y, corner_yz, corner_z))
    polygons.append(create_poly(color, corner_xyz, corner_xy, corner_x, corner_xz))
    polygons.append(create_poly(color, corner_xyz, corner_xz, corner_z, corner_yz))
    polygons.append(create_poly(color, corner_xyz, corner_xy, corner_y, corner_yz))


    return list(polygons)

def create_file_object(position: Vector3, y_rotation: float, filename: str, scale: float = 1) -> list:
    with open("Objects/" + filename + ".obj") as file:
        color = (1, 1, 1)
        vectors = []
        polygons = []
        for line in file:
            stripped = line.strip()
            split = line.split(" ")
            if (stripped == "" and len(vectors) > 1) or stripped == "end":
                poly = Polygon(vectors, Vector3(0, 0, 0), color)
                poly.instantiate()
                polygons.append(poly)
                vectors = []
            elif stripped[0] == "v":
                vec = Vector3(scale * float(split[1]), scale * float(split[2]), scale * float(split[3]))
                vec += position
                vectors.append(vec.rotate_around(position, Vector3(0, y_rotation, 0)))
            elif stripped[0] == "c":
                color = (float(split[1]), float(split[2]), float(split[3]))
    return polygons

# endregion


def init(t: Turtle()):
    """
    Sets up the initial conditions for turtle.
    """
    t.up()
    t.speed(0)
    t.hideturtle()
    turtle.tracer(False)
    t.goto(0, 0)


def Controls(cam: Camera, ground: SphereCollider, wall: SphereCollider, colliders):
    """
    Allows user to press keyboard buttons to move and rotate the camera around the virtual world.
    This function also simulates player gravity and collision.
    :param cam: The location, rotation, and all other information of the camera.
    :param ground: Collider that detects the ground.
    :param wall: Collider that detects walls.
    """
    move_fb = 0
    move_ss = 0
    move_ud = 0
    rotation = 0
    multiply = 1
    global MOVE_ACCELERATION
    global CAM_ACCELERATION
    if keyboard.is_pressed("shift"):
        multiply = 1.5
    if keyboard.is_pressed("w"):
        move_fb += 0.1
    if keyboard.is_pressed("s"):
        move_fb -= 0.1
    if keyboard.is_pressed("a"):
        move_ss += 0.1
    if keyboard.is_pressed("d"):
        move_ss -= 0.1
    if keyboard.is_pressed("left arrow"):
        rotation += 4
    if keyboard.is_pressed("right arrow"):
        rotation -= 4

    ground.position = cam.position + Vector3(0, -1.5, 0)
    wall.position = cam.position + Vector3(0, -1.3, 0)
    colliders.sort(key=lambda x: ground.overlap(x), reverse=True)

    col = ground.is_colliding(colliders)
    if col is None:
        move_ud = -0.01
    elif type(col) != WallCollider:
        MOVE_ACCELERATION[2] = ground.overlap(col) / 2
        move_ud = 0

    MOVE_ACCELERATION[0] = (MOVE_ACCELERATION[0] + move_fb*0.15)/1.15
    MOVE_ACCELERATION[1] = (MOVE_ACCELERATION[1] + move_ss*0.15)/1.15
    MOVE_ACCELERATION[2] += move_ud
    CAM_ACCELERATION = (CAM_ACCELERATION + rotation*0.2)/1.2

    previous = cam.position
    cam.position += (cam.forward().scale(MOVE_ACCELERATION[0]) +
                     cam.forward().rotate_around(Vector3(0, 0, 0), Vector3(0, 90, 0)).scale(MOVE_ACCELERATION[1]) +
                     Vector3(0, 1, 0).scale(MOVE_ACCELERATION[2])).scale(multiply)
    cam.rotation += Vector3(0, CAM_ACCELERATION, 0)
    velocity = cam.position - previous

    wall_col = wall.is_colliding(colliders)
    if type(wall_col) is WallCollider and wall.overlap(col) is not None:
        overlap = Vector3(0, 0, 1).scale(wall.overlap(wall_col))
        overlap = overlap.rotate_around(Vector3(0, 0, 0), Vector3(0, -wall_col.y_rotation, 0))
        cam.position -= overlap


def item_setup(cam, colliders) -> list:
    items = list()
    items.append(Sprite(Vector3(0, 2, 0), "enemy1", 0.2))
    items.extend(create_cube(5, Vector3(-1, 0, 2), (0.5, 0.5, 1)))
    items.append(create_poly((0.8, 0.5, 0.5), Vector3(-10,0,-2.5),
                             Vector3(10,0,-2.5), Vector3(10,0,2), Vector3(-10,0,2)))
    items.append(create_poly((1, 0.5, 0.5), Vector3(-10, 0, -12.5),
                             Vector3(10, 0, -12.5), Vector3(10, 0, -7.5), Vector3(-10, 0, -7.5)))
    items.append(create_poly((1, 0.5, 0.5), Vector3(-10, 0, -7.5),
                             Vector3(-4.5, 0, -7.5), Vector3(-4.5, 0, -2.5), Vector3(-10, 0, -2.5)))
    items.append(create_poly((1, 0.5, 0.5), Vector3(0.5, 0, -7.5),
                             Vector3(10, 0, -7.5), Vector3(10, 0, -2.5), Vector3(0.5, 0, -2.5)))
    items.extend(create_file_object(Vector3(-2, 0, -5), 90, "ramp", 5))

    colliders.append(SphereCollider(Vector3(-5, -5, 0), 5))
    colliders.append(PlaneCollider(Vector3(-10, 0, -12.5), 20, 20, 0))
    colliders.append(SlopeCollider(Vector3(0.5, 0, -7.5), 5, 5, 0.5, -90))
    colliders.append(WallCollider(Vector3(-1, 0, 2), 5, 5, 0))
    colliders.append(WallCollider(Vector3(4, 0, 2), 5, 2.5, 270))
    return items


# Depth Buffer?
# Back face culling? <<
def render(cam: Camera, items: list, t: Turtle()):
    """
    Moves the turtle so that it draws a three-dimensional image on a 2D screen.
    :param cam: The location, rotation, and all other information of the camera.
    :param items: A List of Polygons and other 3D objects to be rendered.
    :param t: turtle rendering this frame.
    """
    items = sorted(items, key=lambda x: x.middle.distance(cam.position), reverse=True)
    t.clear()
    init(t)
    turtle.setworldcoordinates(-cam.zoom, -cam.zoom, cam.zoom, cam.zoom)
    cam_close = 0.25  # How close you want to render items: Do not put at 0 or below.
    for item in items:
        if (type(item) == Polygon and item.middle.distance(cam.position) < 20
                and (item.facing() ^ (cam.position - item.middle).normalize()) <= 0):
            t.fillcolor(item.color)
            t.pencolor(item.color)
            # Setup points
            relative_points = []
            for point in item.points:
                pos = point.rotate_around(cam.position, -cam.rotation)
                relative_points.append(Vector3(pos.x - cam.position.x,
                                               pos.y - cam.position.y,
                                               pos.z - cam.position.z))
            # Check if Polygon is in view.
            in_range = False
            popped = 0
            for i in range(len(relative_points)):
                i -= popped
                point = relative_points[i]
                if (i + 1) > len(relative_points) - 1:
                    next_point = relative_points[0]
                else:
                    next_point = relative_points[i + 1]

                def find_y(point1, point2, new_x) -> float:
                    if point2.x - point1.x != 0:
                        return (point2.y - point1.y) * ((new_x - point1.x) / (point2.x - point1.x))
                    else:
                        return 0

                if point.z > cam_close:
                    in_range = True
                    # If it's not in view, then move the point to appear like it's being cut off by the camera.
                elif next_point.z > cam_close and relative_points[i - 1].z > cam_close:
                    # If only one point is cut off, then split it in two
                    line1 = Line(point.other(), next_point.other())
                    line2 = Line(point.other(), relative_points[i - 1].other())
                    point.z = cam_close
                    line = Line(point.other() + Vector3(20, 0, 0), point.other() + Vector3(-20, 0, 0))
                    x, z = line.line_intersection(line1)
                    x_, z_ = line.line_intersection(line2)
                    other_point = point.other()

                    other_point.x = x_
                    other_point.y += find_y(point, relative_points[i - 1], x_)
                    point.y += find_y(point, next_point, x)
                    point.x = x
                    relative_points.insert(i, other_point)
                elif next_point.z > cam_close:
                    # If two points are cut off, then move them to the camera cut-off.
                    line1 = Line(point.other(), next_point.other())
                    point.z = cam_close
                    line = Line(point.other() + Vector3(20, 0, 0), point.other() + Vector3(-20, 0, 0))
                    x, z = line.line_intersection(line1)
                    point.y += find_y(point, next_point, x)
                    point.x = x
                elif relative_points[i - 1].z > cam_close:
                    # If two points are cut off, then move them to the camera cut-off.
                    line1 = Line(point.other(), relative_points[i - 1].other())
                    point.z = cam_close
                    line = Line(point.other() + Vector3(20, 0, 0), point.other() + Vector3(-20, 0, 0))
                    x, z = line.line_intersection(line1)
                    point.y += find_y(point, relative_points[i - 1], x)
                    point.x = x
                else:
                    # If the points around this point are cut off, then remove this point.
                    relative_points.pop(i)
                    popped += 1

            # Draw
            if in_range:
                t.up()
                first = relative_points.pop(0)
                relative_points.append(first)
                t.goto(first.x / first.z, first.y / first.z)
                t.down()
                t.begin_fill()
                for point in relative_points:
                    t.goto(point.x / point.z, point.y / point.z)
                t.end_fill()
                t.up()

        elif type(item) == Sprite:
            # Calculate sprite center
            pos = item.middle.rotate_around(cam.position, -cam.rotation)
            point = Vector3(pos.x - cam.position.x,
                            pos.y - cam.position.y,
                            pos.z - cam.position.z)
            # Find if sprite is visible
            in_range = True
            if point.z <= cam_close:
                in_range = False

            if in_range:  # Draw using .tur file.
                t.up()
                t.goto(point.x / point.z, point.y / point.z)
                with open("Sprites/" + item.file + ".tur") as file:
                    t.setheading(0)
                    for line in file:
                        strip = line.strip()
                        command = strip.split()
                        if command != []:
                            if command[0] == "f":
                                t.forward((item.scale * float(command[1])) / point.z)
                            elif command[0] == "c":
                                if len(command) == 3:
                                    t.circle((item.scale * float(command[1])) / point.z, command[2])
                                elif len(command) == 4:
                                    t.circle((item.scale * float(command[1])) / point.z, command[2], command[3])
                                else:
                                    t.circle((item.scale * float(command[1])) / point.z)
                            elif command[0] == "u":
                                t.up()
                            elif command[0] == "d":
                                t.down()
                            elif command[0] == "r":
                                t.right(float(command[1]))
                            elif command[0] == "f_b":
                                t.begin_fill()
                            elif command[0] == "f_e":
                                t.end_fill()
                            elif command[0] == "f_c":
                                t.fillcolor((float(command[1]), float(command[2]), float(command[3])))
                            else:
                                pass
    turtle.update()


def main():
    """
    Sets up world, displays world and allows you to move camera around world.
    """
    cam = Camera(Vector3(0, 7, -3), Vector3(0, -90, 0), 1)
    ground = SphereCollider(cam.position + Vector3(0, -1.5, 0), 0.4)
    wall = SphereCollider(cam.position + Vector3(0, -1.3, 0), 0.5)
    items = item_setup(cam, COLLIDERS)
    turtle1 = Turtle()
    turtle2 = Turtle()
    init(turtle1)
    init(turtle2)

    i = 0
    while True:
        if i % 2 == 0:
            t = turtle1
        else:
            t = turtle2
        i += 1
        # Controls
        Controls(cam, ground, wall, COLLIDERS)
        # Visuals
        render(cam, items, t)
        time.sleep(0.02)


if __name__ == "__main__":
    main()
