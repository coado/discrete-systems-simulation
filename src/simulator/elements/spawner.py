from __future__ import annotations

import numpy as np
from queue import Queue

from src.simulator.elements.pedestrian import Pedestrian
from src.simulator.elements.car import Car


class Spawner:
    def __init__(
            self,
            junction: int,
            spawns_pedestrians: bool = False,
            spawn_freq: float = .5,  # [1/s]
            spawn_freq_std: float = 0,
            random_delay_on_start: bool = True,
    ):
        self._junction: int = junction
        self._spawns_pedestrians = spawns_pedestrians
        self._spawn_freq: float = spawn_freq
        self._spawn_freq_std: float = spawn_freq_std

        self._queue: int = 0

        self._counter_max: int = 0
        self._counter: float = \
            - int(np.random.random() * self._calculate_counter_max()) \
                if random_delay_on_start \
                else 0
        self._reset_counter()

    def _reset_counter(self):
        self._counter = 0
        self._counter_max = self._calculate_counter_max()

    def _calculate_counter_max(self):
        return 1 / max(
            0.001,
            self._spawn_freq + np.random.random() * 2 * self._spawn_freq_std - self._spawn_freq_std
        )

    def step(self, dt):
        self._counter += dt
        if self._counter >= self._counter_max:
            self._reset_counter()
            return True
        return False

    def add_to_queue(self):
        self._queue += 1

    def is_queue_empty(self):
        return self._queue == 0

    def get_from_queue(self):
        if self._queue > 0:
            self._queue -= 1
            return True
        return False

    def is_for_pedesrians(self):
        return self._spawns_pedestrians

    def is_for_cars(self):
        return not self._spawns_pedestrians