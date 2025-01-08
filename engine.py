import time
import keyboard
from renderer import *
from game_objects import *
from game import create_file_object

"""
This Program launches and runs the game so you can add objects and save the 
scene to render later.
"""

SELECTED = 0
CHANGE = False
CHANGE_CHECK = False
ITEMS = ["cube", "ramp"]

def controls(cam: Camera, items: list) -> int:
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
    global SELECTED
    global CHANGE
    global CHANGE_CHECK
    item_changed = False
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
    if keyboard.is_pressed("e"):
        move_ud += 0.1
    if keyboard.is_pressed("q"):
        move_ud -= 0.1
    if keyboard.is_pressed("left arrow"):
        rotation += 4
    if keyboard.is_pressed("right arrow"):
        rotation -= 4
    if keyboard.is_pressed("escape"):
        return 1
    if keyboard.is_pressed("1"):
        SELECTED = 0
        item_changed = True
        CHANGE = True
    if keyboard.is_pressed("2"):
        SELECTED = 1
        item_changed = True
        CHANGE = True
    if not keyboard.is_pressed("1") and not keyboard.is_pressed("2"):
        CHANGE = False

    cam.acceleration[0] = (cam.acceleration[0] + move_fb * 2) / 2
    cam.acceleration[1] = (cam.acceleration[1] + move_ss * 2) / 2
    cam.acceleration[2] = (cam.acceleration[2] + move_ud * 2) / 2
    cam.angular_acceleration = (cam.angular_acceleration + rotation*0.2)/1.2

    cam.position += (cam.forward().scale(cam.acceleration[0]) +
                     cam.forward().rotate_around(Vector3(0, 0, 0), Vector3(0, 90, 0)).scale(cam.acceleration[1]) +
                     Vector3(0, 1, 0).scale(cam.acceleration[2])).scale(multiply)
    cam.y_rotation += cam.angular_acceleration

    if item_changed and CHANGE_CHECK != CHANGE:
        poly, collide = create_file_object(ITEMS[SELECTED], cam.position, cam.y_rotation, Vector3(1, 1, 1))
        items.extend(poly)
    CHANGE_CHECK = CHANGE

    return 0


def item_setup(cam, file) -> list:
    """
    Generates the scene.
    :param cam: The camera
    :param colliders: The scenes colliders
    :return: List of polygons to be added to the render list.
    """
    items = list()

    poly, collide = create_file_object(file, Vector3(0, 0, 0), 0, Vector3(1, 1, 1))
    items.extend(poly)

    return items


def main():
    """
    Sets up world, displays world and allows you to move camera around world.
    """
    file = input("Enter file name:")

    cam = Camera(Vector3(0, 2, -3), -89, 1, [0, 0, 0], 0)

    items = item_setup(cam, file)
    turtle1 = Turtle()
    turtle2 = Turtle()
    init(turtle1)
    init(turtle2)

    i = 0
    end = 0
    while end == 0:
        if i % 2 == 0:
            t = turtle1
        else:
            t = turtle2
        i += 1
        # Controls
        end = controls(cam, items)
        # Visuals
        render(cam, items, t)
        time.sleep(0.02)


if __name__ == "__main__":
    main()
