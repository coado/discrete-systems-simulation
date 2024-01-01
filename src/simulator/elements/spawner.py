import numpy as np


class Spawner:
    def __init__(
            self,
            junction: int,
            spawn_rate: float,  # [1/s]
            spawn_rate_std: float,
            random_delay_on_start: bool = True,
    ):
        self._junction: int = junction
        self._spawn_rate: float = spawn_rate
        self._spawn_rate_std: float = spawn_rate_std

        self._counter_max: int = 0
        self._counter: float = \
            int(-np.random.random() * self._spawn_rate / 2) \
                if random_delay_on_start \
                else 0
        self._reset_counter()

    def _reset_counter(self):
        self._counter = 0
        self._counter_max = int(1 / self._calculate_spawn_rate())

    def _calculate_spawn_rate(self):
        return min(1, max(1e-5, self._spawn_rate + np.random.random() * 2 * self._spawn_rate_std - self._spawn_rate_std))

    def step(self, dt):
        self._counter += dt
        if self._counter >= self._counter_max:
            self._reset_counter()
            return True
        return False
