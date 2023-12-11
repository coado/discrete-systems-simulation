from .tsf_base_object import tsf_base_object
import numpy as np


class tsf_car(tsf_base_object):
    def __init__(
            self,
            id: int,
            rw: int,
            lane: int,
            cell: int,
            target_junction: int,
            velocity: float = 0
    ):
        self.id: int = id
        self.rw: int = rw
        self.lane: int = lane
        self.cell: int = cell
        self.profile: float = np.random.random()
        self.velocity = velocity # [m/s]
        self.target_junction: int = target_junction

        self._junction_velocity = 5 + self.get_profile_parameter()  # [m/s]

        self._color = self._generate_color()

    def _generate_color(self):
        l_bound, u_bound = 50, 205
        R = np.random.randint(l_bound, u_bound)
        G = np.random.randint(l_bound, u_bound)
        B = np.random.randint(l_bound, u_bound)
        return (R, G, B)

    def adjust_velocity(self, velocity_diff: float):
        self.velocity += velocity_diff

    def move_to(self, rw: int, lane: int, cell: int):
        self.rw = rw
        self.lane = lane
        self.cell = cell

    def set_junction_velocity(self):
        self.velocity = self._junction_velocity

    def get_profile_parameter(
            self,
            l_bound: float = -1,
            u_bound: float = 1,
            multiplier: float = 1
    ):
        return (l_bound + (u_bound - l_bound) * self.profile) * multiplier

    def get_velocity(self, kmh: bool = False):
        if kmh:
            return self.velocity * 3.6
        return self.velocity