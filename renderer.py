from vectors import *
from game_objects import Camera
from dataclasses import dataclass
from turtle import Turtle
import turtle

RENDER_DISTANCE = 40

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

def init(t: Turtle()):
    """
    Sets up the initial conditions for turtle.
    """
    t.up()
    t.speed(0)
    t.hideturtle()
    turtle.tracer(False)
    t.goto(0, 0)


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
