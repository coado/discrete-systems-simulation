import numpy as np
from math import ceil
from enum import Enum


class Roadway:
    d_cell_avg = 5  # [m]

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
            v_avg: float,  # [m/s]
            v_std: float,  # [m/s]
            r_type: types = types.one_line,
            traffic_light_at_end: int = -1,
    ) -> None:
        self.id: int = id
        self.distance: float = distance  # [m]
        self.lanes: int = r_type.value if r_type.value < 5 else 1
        self.v_avg: float = v_avg  # [m/s]
        self.v_std: float = v_std  # [m/s]
        self.type: Roadway.types = r_type
        self.traffic_light_at_end: int = traffic_light_at_end

        n_cell = ceil(distance / Roadway.d_cell_avg)
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
        return self.type in [
            Roadway.types.one_line,
            Roadway.types.two_line,
            Roadway.types.three_line,
            Roadway.types.four_line
        ]

    def is_type_for_pedestrians(self):
        return self.type is Roadway.types.pavement
