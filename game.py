import time
import keyboard
from renderer import *
from game_objects import *

GRAVITY = -0.01

"""
This Program launches and runs the game.
"""


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
            # Loads another sprite from a file.
            elif split[0] == "sprite":    # sprite <name> <position> <scale>
                pos = Vector3(scale.x * float(split[2]), scale.y * float(split[3]), scale.z * float(split[4]))
                pos += position
                newscale = float(split[5]) * max(scale.x, scale.y, scale.z)
                polygons.append(Sprite(pos, split[1], newscale))

    return polygons, colliders


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
    if keyboard.is_pressed("escape"):
        return 1

    ground.position = cam.position + Vector3(0, -1.5, 0)
    wall.position = cam.position + Vector3(0, -1.3, 0)
    colliders.sort(key=lambda x: ground.overlap(x), reverse=True)

    col = ground.is_colliding(colliders)
    if col is None:
        move_ud = GRAVITY
    elif type(col) != WallCollider:
        cam.acceleration[2] = ground.overlap(col) / 2
        move_ud = 0

    cam.acceleration[0] = (cam.acceleration[0] + move_fb * 0.15) / 1.15
    cam.acceleration[1] = (cam.acceleration[1] + move_ss * 0.15) / 1.15
    cam.acceleration[2] += move_ud
    cam.angular_acceleration = (cam.angular_acceleration + rotation*0.2)/1.2

    cam.position += (cam.forward().scale(cam.acceleration[0]) +
                     cam.forward().rotate_around(Vector3(0, 0, 0), Vector3(0, 90, 0)).scale(cam.acceleration[1]) +
                     Vector3(0, 1, 0).scale(cam.acceleration[2])).scale(multiply)
    cam.y_rotation += cam.angular_acceleration

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
    #items.append(Sprite(Vector3(2, 4, 2), "enemy1", 0.2))

    poly, collide = create_file_object("map1", Vector3(0, 0, 0), 0, Vector3(1, 1, 1))
    items.extend(poly)
    colliders.extend(collide)

    return items, colliders


def main():
    """
    Sets up world, displays world and allows you to move camera around world.
    """
    cam = Camera(Vector3(0, 7, -3), -89, 1, [0,0,0], 0)
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
