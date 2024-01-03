import numpy as np


class Car:
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
        self.velocity = velocity  # [m/s]
        self.target_junction: int = target_junction

        self._junction_velocity = 5 + self.get_profile_parameter()  # [m/s]

        self._color = self._generate_color()

    def _generate_color(self):
        color = np.zeros(3)
        for i in range(3):
            c = 50 + np.random.randint(150)
            color[i] = c

        return tuple(color)

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

    def __dict__(self):
        return {
            "id": self.id,
            "rw": self.rw,
            "lane": self.lane,
            "cell": self.cell,
            "profile": self.profile,
            "velocity": self.velocity,
            "target_junction": self.target_junction,
        }
