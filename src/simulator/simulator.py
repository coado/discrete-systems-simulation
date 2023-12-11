import numpy as np
import networkx as nx
import json
import threading

from .elements.tsf_objects.tsf_car import tsf_car
from .elements.roadway import roadway


class simulator:
    def __init__(self, source_file_name: str) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.w = 0  # [m]
        self.h = 0  # [m]
        self.cars: dict[int, tsf_car] = {}
        self.edges_map: dict[int, roadway] = {}

        self._step_time = 1  # [s]

        self._is_running = False

        self.load(source_file_name)

    def load(self, source_file_name: str) -> None:
        with open(source_file_name, "r") as source_file:
            source = json.load(source_file)

        self.w = source["width"]
        self.h = source["height"]

        for node in source["junctions"]:
            self.graph.add_node(
                node["id"],
                x=node["x"],
                y=node["y"]
            )

        for edge in source["roadways"]:
            node_src = self.graph.nodes[edge["source"]]
            node_tgt = self.graph.nodes[edge["target"]]
            distance = np.sqrt((node_tgt["x"] - node_src["x"]) ** 2 + (node_tgt["y"] - node_src["y"]) ** 2)
            rw = roadway(
                edge["id"],
                distance,
                edge["v_avg"],
                edge["v_std"],
                roadway.types[edge["type"]]
            )
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                roadway=rw
            )
            self.edges_map[edge["id"]] = rw

        for c in source["cars"]:
            car_id = c["id"]
            self.cars[car_id] = tsf_car(
                car_id,
                c["roadway"],
                c["lane"],
                c["cell"],
                c["target_junction"],
                c["velocity"]
            )
            self.edges_map[c["roadway"]].cells[c["lane"], c["cell"]] = car_id

    def stop(self) -> None:
        self._is_running = False

    def step(self, steps=1, t_gap=0) -> None:
        self._is_running = True
        for i in range(steps):
            if t_gap > 0:
                lock = threading.Lock()
                lock.acquire()
                if t_gap > 0:
                    threading.Timer(t_gap, lock.release).start()
                while lock.locked():
                    if not self._is_running:
                        return
            self._step()
        self._is_running = False

    def _step(self) -> None:
        for car in self.cars.values():
            self._step_car(car)

    def _step_car(self, car: tsf_car) -> None:
        x_rw = self.edges_map[car.rw]  # edge
        x_l = car.lane
        x_c = car.cell

        current_junction_id = list(self.graph.edges)[x_rw.id][1]
        target_junction_id = car.target_junction
        path = nx.astar_path(self.graph, current_junction_id, target_junction_id)

        # if car is at the end of the road:
        if x_c == x_rw.cells.shape[1] - 1:
            # if car is at the end of the path:
            if path[-1] == current_junction_id:
                # remove car from simulation
                self.edges_map[x_rw.id].free_cell(x_l, x_c)
                del self.cars[car.id]
                return
            else:
                # get next road - edge between path[0] and path[1]
                next_road = self.graph.edges[path[0], path[1]]['roadway'].id
                next_road_cells = self.edges_map[next_road].cells
                next_road_first_cells = next_road_cells[:, 0]
                empty_lanes = np.where(next_road_first_cells == -1)[0]
                if len(empty_lanes) == 0:
                    # stop car
                    car.velocity = 0
                    return
                else:
                    # move car to next road
                    car.set_junction_velocity()
                    x_rw.free_cell(x_l, x_c)
                    x_rw = self.edges_map[next_road]
                    x_l = empty_lanes[0]
                    x_c = 0
                    x_rw.cells[x_l, x_c] = car.id
                    car.rw = next_road
                    car.lane = x_l
                    car.cell = x_c
                    return
        # if car is on the road:
        # @TODO: changing lanes based on path

        # classic step
        d = x_rw.get_cell_distance()
        v = car.velocity
        t = self._step_time

        d_max = np.where(x_rw.get_cells(x_l) != -1)[x_c + 1:]
        a_max = 1.25 + car.get_profile_parameter(0, 1)

        v_end = car._junction_velocity if len(d_max) == 0 else 0

        d_remaining = x_rw.distance - (x_c + 1) * d
        if len(d_max) > 0:
            d_remaining = min(d_max, d_remaining)
        d_safe_stop = ((v-v_end)/a_max)*(v/2+v_end/2) + d # distance to stop
        breaking = d_remaining < d_safe_stop

        v_road = x_rw.v_avg + x_rw.v_std * car.get_profile_parameter()
        v_desired = v_end if breaking else v_road

        a = (v_desired - v) / t
        a = max(-a_max, min(a, a_max))

        v = max(0., v + a * t)
        car.velocity = v

        d_c = int((v * t) // d)  # desired distance to move
        if 0 <= d_c < 1 and v != 0:
            d_c = 1

        if x_rw.cells[x_l, x_c + d_c] != -1:
            d_c -= 1
            d_c = max(0, d_c)
            car.velocity -= d / t

        x_rw.free_cell(x_l, x_c)
        x_rw.cells[x_l, x_c + d_c] = car.id
        car.cell += d_c
