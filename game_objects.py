from vectors import *
from typing import Any, Union
from dataclasses import dataclass


@dataclass
class GameObject:
    position: Vector3
    y_rotation: int  # Clockwise


@dataclass
class Camera(GameObject):
    zoom: int
    acceleration: [3]
    angular_acceleration: float

    def forward(self) -> Vector3:
        vec = Vector3(self.position.x, self.position.y, self.position.z+1)
        vec = vec.rotate_around(self.position, Vector3(0, self.y_rotation, 0)) - self.position
        return vec

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