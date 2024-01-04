import numpy as np
from math import ceil
from enum import Enum


class Road:
    d_cell_avg_cars = 5  # [m]
    d_cell_avg_pedestrians = 2  # [m]

    class types(Enum):
        one_line = 1
        two_line = 2
        three_line = 3
        four_line = 4
        pavement = 5

    def __init__(
            self,
            id: int,
            distance: float,  # [m]
            lanes: int = 1,
            v_avg: float = 0,  # [m/s]
            v_std: float = 0,  # [m/s]
            is_pavement: bool = False,
            traffic_light_at_end: int = -1,
    ) -> None:
        self.id: int = id
        self.distance: float = distance  # [m]
        self.lanes: int = lanes
        self.v_avg: float = v_avg  # [m/s]
        self.v_std: float = v_std  # [m/s]
        self.is_pavement: bool = is_pavement
        self.traffic_light_at_end: int = traffic_light_at_end

        d_cell_avg = Road.d_cell_avg_pedestrians if is_pavement else Road.d_cell_avg_cars
        n_cell = ceil(distance / d_cell_avg)
        self.n_cell: int = n_cell
        self.d_cell: float = distance / n_cell

        self.cells: np.ndarray = np.zeros((self.lanes, self.n_cell), dtype=int) - 1

    def get_cells(self, lane: int = None) -> np.ndarray:
        if lane is None:
            return self.cells
        if lane < 0 or lane >= self.lanes:
            raise ValueError("lane must be in range [0, lanes)")
        return self.cells[lane, :]

    def get_cell_distance(self):
        return self.d_cell

    def free_cell(self, lane: int, cell: int) -> None:
        self.cells[lane, cell] = -1

    def is_type_for_cars(self):
        return not self.is_pavement

    def is_type_for_pedestrians(self):
        return self.is_pavement

    def __dict__(self):
        return {
            "id": self.id,
            "distance": self.distance,
            "lanes": self.lanes,
            "v_avg": self.v_avg,
            "v_std": self.v_std,
            "is_pavement": self.is_pavement,
            "traffic_light_at_end": self.traffic_light_at_end,
        }