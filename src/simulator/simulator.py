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
                # @FIXME : remove car from simulation
                # cars are looping over last edge
                self.edges_map[x_rw.id].free_cell(x_l, x_c)
                del self.cars[car.id]
                return
            else:
                # get next road - edge between path[0] and path[1]
                # @FIXME: include keeping line
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

        # check if car is in desired lane
        d_remaining = x_rw.distance - (x_c + 1) * x_rw.d_cell
        if d_remaining < 40 and np.random.random() > .66 \
                or d_remaining < 20 and np.random.random() > .33 \
                or d_remaining < 10\
                or car.get_profile_parameter() > .5 and np.random.random() > .5:
            l_desired_options = self._get_lane_pref_before_junction(path[0], x_rw.id, path[1])
            if x_l not in l_desired_options:
                l_desired = np.random.choice(l_desired_options)
                if x_rw.cells[l_desired, x_c] == -1 and np.random.random() > .5:
                    l_diff = l_desired - x_l
                    l_diff = max(-1, min(l_diff, 1))
                    l_new = x_l + l_diff
                    x_rw.free_cell(x_l, x_c)
                    x_rw.cells[l_new, x_c] = car.id
                    car.lane = l_new
                    return
                elif any(x_rw.cells[l_desired, x_c:] == -1):
                    pass
                else:
                    car.velocity = 0
                    return

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
        d_safe_stop = ((v - v_end) / a_max) * (v / 2 + v_end / 2) + d  # distance to stop
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

    def _get_lane_pref_before_junction(
            self,
            junction_id: int,
            rw_in_id: int,
            next_junction_id: int
    ):
        node = self.graph.nodes[junction_id]
        edge_in = [e for e in self.graph.edges.data() if e[2]['roadway'].id == rw_in_id][0]
        edges_out = [
            e for e in self.graph.edges.data()
            if e[0] == junction_id
        ]

        with np.errstate(divide='ignore', invalid='ignore'):
            diff = np.arctan(np.divide(
                node['y'] - self.graph.nodes[edge_in[0]]['y'],
                node['x'] - self.graph.nodes[edge_in[0]]['x'],
            ))

        edges_out_d = [  # calculate tan
            (np.arctan(np.divide(
                self.graph.nodes[e[1]]['y'] - node['y'],
                self.graph.nodes[e[1]]['x'] - node['x']
            )) - diff,
             e[2]['roadway'].id)
            for e in edges_out
        ]

        edges_out_d = sorted(edges_out_d, key=lambda x: x[0])
        edges_out_d = [e[1] for e in edges_out_d]

        roadway_id = edges_out_d.index(next_junction_id)
        n_lanes = self.edges_map[edges_out_d[roadway_id]].lanes
        n_roadways_out = len(edges_out_d)

        options = np.arange(n_lanes)[
                  int(np.floor(roadway_id * n_lanes / n_roadways_out)):
                  int(np.ceil((roadway_id + 1) * n_lanes / n_roadways_out))
        ]
        return options
