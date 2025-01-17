import time
from turtle import Turtle
import turtle
import keyboard
from vectors import *
from dataclasses import dataclass
from typing import Any, Union


CAM_ACCELERATION = 0
MOVE_ACCELERATION = [0, 0, 0]
RENDER_DISTANCE = 40

GRAVITY = -0.01

"""
This is where you play the game.
"""

# region Classes


@dataclass
class GameObject:
    position: Vector3
    y_rotation: int  # Clockwise


@dataclass
class Camera(GameObject):
    zoom: int

    def forward(self) -> Vector3:
        vec = Vector3(self.position.x, self.position.y, self.position.z+1)
        vec = vec.rotate_around(self.position, Vector3(0, self.y_rotation, 0)) - self.position
        return vec


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
class PlaneCollider(GameObject):
    x: float
    z: float


@dataclass
class SlopeCollider(GameObject):
    x: float
    z: float
    slope: float


@dataclass
class WallCollider(GameObject):
    x: float
    y: float

@dataclass
class SphereCollider(GameObject):
    r: float

    def is_colliding(self, colliders) -> Union[None, PlaneCollider, SlopeCollider, WallCollider]:
        for col in colliders:
            if self.overlap(col) > 0:
                return col
        return None

    def overlap(self, col: Union[None, PlaneCollider, SlopeCollider, WallCollider]) -> float:
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
            if col.position.x < pos.x < col.position.x + col.x and col.position.y < pos.y < col.position.y + col.y and col.position.z - pos.z < self.r:
                return self.r - abs(col.position.z - pos.z)
            x = min(abs(col.position.x - pos.x), abs(col.position.x + col.x - pos.x))
            y = abs(col.position.z - pos.z)
            z = min(abs(col.position.y - pos.y), abs(col.position.y + col.y - pos.y))
            return self.r - pos.distance(Vector3(x, y, z))
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


# Allow files to add colliders
# Allow files to load other files as part of the file.
def create_file_object(filename: str, position: Vector3 = Vector3(0,0,0), y_rotation: float = 0, scale: Vector3 = Vector3(1, 1, 1)) -> tuple:
    """
    Creates a new custom object, the shape and colliders of which is stored in a file.
    :param position: Where you want to place the object.
    :param y_rotation: How you want the object to be rotated.
    :param filename: The name of the file to generate the object from.
    :param scale: How big you want the object to be.
    :return: A list of the objects polygons for rendering.
    """
    with open("Objects/" + filename + ".obj") as file:
        color = (1, 1, 1)
        vectors = []
        polygons = []
        colliders = []
        for line in file:
            stripped = line.strip()
            split = line.split(" ")
            # Turns all the previous points into a new polygon.
            if (stripped == "" and len(vectors) > 1) or stripped == "end":
                poly = Polygon(vectors, Vector3(0, 0, 0), color)
                poly.instantiate()
                polygons.append(poly)
                vectors = []
            # Sets a point for a polygon.
            elif split[0] == "v":
                vec = Vector3(scale.x * float(split[1]), scale.y * float(split[2]), scale.z * float(split[3]))
                vec += position
                vectors.append(vec.rotate_around(position, Vector3(0, y_rotation, 0)))
            # Sets the next polygons' color.
            elif split[0] == "c":
                color = (float(split[1]), float(split[2]), float(split[3]))
            # Creates a Wall Collider.
            elif split[0] == "wcol":
                pos = Vector3(scale.x * float(split[1]), scale.y * float(split[2]), scale.z * float(split[3]))
                pos += position
                colliders.append(WallCollider(pos.rotate_around(position, Vector3(0, y_rotation, 0)),
                                              float(split[4]) - y_rotation,
                                              (scale.z * (0.5 * math.cos(float(split[4]) * (math.pi/180)) + 0.5) +
                                               scale.x * (0.5 * -math.cos(float(split[4]) * (math.pi/180)) + 0.5)) * float(split[5]),
                                              scale.y * float(split[6])))
            # Creates a Slope Collider.
            elif split[0] == "rcol":
                pos = Vector3(scale.x * float(split[1]), scale.y * float(split[2]), scale.z * float(split[3]))
                pos += position
                colliders.append(SlopeCollider(pos.rotate_around(position, Vector3(0, y_rotation, 0)),
                                               float(split[4]) - y_rotation, scale.x * float(split[5]),
                                               scale.z * float(split[6]), (scale.y / scale.z) * float(split[7])))
            # Creates a Sphere Collider.
            elif split[0] == "scol":
                pos = Vector3(scale.x * float(split[1]), scale.y * float(split[2]), scale.z * float(split[3]))
                pos += position
                colliders.append(SphereCollider(pos.rotate_around(position, Vector3(0, y_rotation, 0)), 0, float(split[4])))
            # Creates a Platform Collider
            elif split[0] == "pcol":
                pos = Vector3(scale.x * float(split[1]), scale.y * float(split[2]), scale.z * float(split[3]))
                pos += position
                colliders.append(PlaneCollider(pos.rotate_around(position, Vector3(0, y_rotation, 0)),
                                               float(split[4]) - y_rotation, scale.x * float(split[5]),
                                               scale.z * float(split[6])))
            # Loads another object from a file.
            elif split[0] == "file":    # file <name> <position> <yrotation> <scale>
                pos = Vector3(scale.x * float(split[2]), scale.y * float(split[3]), scale.z * float(split[4]))
                pos += position
                newscale = Vector3(scale.x * float(split[6]), scale.y * float(split[7]), scale.z * float(split[8]))
                poly, collide = create_file_object(split[1], pos.rotate_around(position, Vector3(0, y_rotation, 0)),
                                                   float(split[5]) + y_rotation, newscale)
                polygons.extend(poly)
                colliders.extend(collide)
    return polygons, colliders

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


def controls(cam: Camera, ground: SphereCollider, wall: SphereCollider, colliders):
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
        move_ud = GRAVITY
    elif type(col) != WallCollider:
        MOVE_ACCELERATION[2] = ground.overlap(col) / 2
        move_ud = 0

    MOVE_ACCELERATION[0] = (MOVE_ACCELERATION[0] + move_fb*0.15)/1.15
    MOVE_ACCELERATION[1] = (MOVE_ACCELERATION[1] + move_ss*0.15)/1.15
    MOVE_ACCELERATION[2] += move_ud
    CAM_ACCELERATION = (CAM_ACCELERATION + rotation*0.2)/1.2

    cam.position += (cam.forward().scale(MOVE_ACCELERATION[0]) +
                     cam.forward().rotate_around(Vector3(0, 0, 0), Vector3(0, 90, 0)).scale(MOVE_ACCELERATION[1]) +
                     Vector3(0, 1, 0).scale(MOVE_ACCELERATION[2])).scale(multiply)
    cam.y_rotation += CAM_ACCELERATION

    wall_col = wall.is_colliding(colliders)
    if type(wall_col) is WallCollider and wall.overlap(col) is not None:
        overlap = Vector3(0, 0, 1).scale(wall.overlap(wall_col))
        overlap = overlap.rotate_around(Vector3(0, 0, 0), Vector3(0, -wall_col.y_rotation, 0))
        cam.position -= overlap


def item_setup(cam) -> list:
    """
    Generates the scene.
    :param cam: The camera
    :param colliders: The scenes colliders
    :return: List of polygons to be added to the render list.
    """
    items = list()
    colliders = list()
    items.append(Sprite(Vector3(2, 4, 2), "enemy1", 0.2))

    poly, collide = create_file_object("map1", Vector3(0, 0, 0), 0, Vector3(1, 1, 1))
    items.extend(poly)
    colliders.extend(collide)
    poly, collide = create_file_object("map1", Vector3(20, 0, 0), 0, Vector3(1, 1, 1))
    items.extend(poly)
    colliders.extend(collide)
    poly, collide = create_file_object("map1", Vector3(0, 0, 20), 0, Vector3(1, 1, 1))
    items.extend(poly)
    colliders.extend(collide)

    return items, colliders


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
        if (type(item) == Polygon and item.middle.distance(cam.position) < RENDER_DISTANCE
                and (item.facing() ^ (cam.position - item.middle).normalize()) <= 0):
            t.fillcolor(item.color)
            t.pencolor(item.color)
            # Setup points
            relative_points = []
            for point in item.points:
                pos = point.rotate_around(cam.position, Vector3(0, -cam.y_rotation, 0))
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
            pos = item.middle.rotate_around(cam.position, Vector3(0, -cam.y_rotation, 0))
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
                        if command:
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
    cam = Camera(Vector3(0, 7, -3), -89, 1)
    ground = SphereCollider(cam.position + Vector3(0, -1.5, 0), 0, 0.4)
    wall = SphereCollider(cam.position + Vector3(0, -1.3, 0), 0, 0.5)

    items, colliders = item_setup(cam)
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
        controls(cam, ground, wall, colliders)
        # Visuals
        render(cam, items, t)
        time.sleep(0.02)


if __name__ == "__main__":
    main()
