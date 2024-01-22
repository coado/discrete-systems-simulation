import numpy as np

class Pedestrian:
    def __init__(
            self,
            id: int,
            rw: int,
            lane: int,
            cell: int,
            target_junction: int,
            velocity: float = 1.1, # [m/s]
            t_walk_lights: float = 5 # [s]
    ):
        self.id: int = id
        self.rd: int = rw
        self.lane: int = lane
        self.cell: int = cell
        self.profile: float = np.random.random()
        self.target_junction: int = target_junction
        self.velocity = velocity
        self.t_walk_lights: float = t_walk_lights


        self._color = self._generate_color()

    def _generate_color(self):
        color = np.zeros(3)
        for i in range(3):
            c = 50 + np.random.randint(150)
            color[i] = c

        return tuple(color)