import numpy as np
import networkx as nx
import json
import threading
import pandas as pd

from simulator.elements.pedestrian import Pedestrian
from src.simulator.elements.spawner import Spawner
from simulator.elements.car import Car
from src.simulator.elements.road import Road
from src.simulator.elements.light import Light


class Simulator:
    def __init__(self, source_file_name: str) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.w = 0  # [m]
        self.h = 0  # [m]
        self.cars: dict[int, Car] = {}
        self.pedestrians: dict[int, Pedestrian] = {}
        self.edges_map: dict[int, Road] = {}
        self.spawners: dict[int, Spawner] = {}
        self.terminal_junctions: list[int] = []
        self.lights: dict[int, Light] = {}  # junction - light

        self._step_time = 1  # [s]

        self._is_running = False
        self._current_step = 0
        self._max_steps = 0
        self._t_gap = 0

        self._cars_df = pd.DataFrame()
        self._lights_df = pd.DataFrame()

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
            if node["terminal"]:
                self.terminal_junctions.append(node["id"])

        for edge in source["roads"]:
            node_src = self.graph.nodes[edge["source"]]
            node_tgt = self.graph.nodes[edge["target"]]
            distance = np.sqrt((node_tgt["x"] - node_src["x"]) ** 2 + (node_tgt["y"] - node_src["y"]) ** 2)
            rd = Road(
                edge["id"],
                distance,
                edge["lanes"],
                edge["v_avg"],
                edge["v_std"],
                edge["is_sidewalk"],
            )
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                road=rd
            )
            self.edges_map[edge["id"]] = rd

        for c in source["cars"]:
            car_id = c["id"]
            if c["road"] not in self.edges_map.keys():
                raise RuntimeError(f"Car {car_id} is on road {c['road']}, "
                                   f"but {c['road']} does not exist!")
            if self.edges_map[c["road"]].is_pavement:
                raise RuntimeError(f"Car {car_id} is on road {c['road']}, "
                                   f"but {c['road']} is a pavement!")
            self.cars[car_id] = Car(
                car_id,
                c["road"],
                c["lane"],
                c["cell"],
                c["target_junction"],
                c["velocity"]
            )
            self.edges_map[c["road"]].cells[c["lane"], c["cell"]] = car_id

        for p in source["pedestrians"]:
            ped_id = p["id"]
            if p["road"] not in self.edges_map.keys():
                raise RuntimeError(f"Pedestrian {ped_id} is on road {p['road']}, "
                                   f"but {p['road']} does not exist!")
            if not self.edges_map[p["road"]].is_pavement:
                raise RuntimeError(f"Pedestrian {ped_id} is on road {p['road']}, "
                                   f"but {p['road']} is not a pavement!")
            self.pedestrians[ped_id] = Pedestrian(
                ped_id,
                p["road"],
                p["lane"],
                p["cell"],
                p["target_junction"],
                p["velocity"],
                p["t_walk_lights"]
            )
            self.edges_map[p["road"]].cells[p["lane"], p["cell"]] = ped_id

        for l in source["lights"]:
            state_map = {
                True: Light.State.GREEN,
                False: Light.State.RED
            }
            if "complementary_to" in l:
                if l["complementary_to"] not in self.lights.keys():
                    raise RuntimeError(f"Light {l['id']} is complementary to {l['complementary_to']}, "
                                       f"but {l['complementary_to']} does not exist!")
                other = self.lights[l["complementary_to"]]
                negates = l["negates"]
                duration_green = other.duration_red if l["negates"] else other.duration_green
                duration_red = other.duration_green if l["negates"] else other.duration_red
                state = state_map[negates ^ (other.state == Light.State.GREEN)]

            else:
                duration_green = l["duration_green"]
                duration_red = l["duration_red"]
                state = state_map[l["state"] == "green"]

            self.lights[l["id"]] = Light(
                l["id"],
                l["road"],
                duration_green,
                duration_red,
                state
            )
            self.edges_map[l["road"]].traffic_light_at_end = l["id"]

        for s in source['spawners']:
            if not s['spawns_pedestrians'] and len([e for e in self.graph.edges.data() if e[0] == s['junction']]) == 0:
                raise RuntimeError(f"Spawner {s['junction']} does not have any outgoing edges!")
            self.spawners[s['junction']] = Spawner(
                s['junction'],
                s['spawns_pedestrians'],
                s['spawn_freq'],
                s['spawn_freq_std'],
                s['random_delay_on_start']
            )

    def stop(self) -> None:
        self._is_running = False

    def step(self, steps=1, t_gap=0):
        # returns (time elapsed, avg cars stopped)
        self._is_running = True
        self._max_steps += steps
        self._t_gap = t_gap

        for i in range(steps):
            self._current_step += 1
            if t_gap > 0:
                lock = threading.Lock()
                lock.acquire()
                if t_gap > 0:
                    threading.Timer(t_gap, lock.release).start()
                while lock.locked():
                    if not self._is_running:
                        break
            if not self._is_running:
                break
            self._step()

        self._is_running = False

    def _step(self):
        self._step_lights()

        cars_ids_for_removal = []
        for car in self.cars.values():
            indicator = self._step_car(car)
            if indicator == -1:
                cars_ids_for_removal.append(car.id)
        for id in cars_ids_for_removal:
            self.cars.pop(id)

        pedestrians_ids_for_removal = []
        for ped in self.pedestrians.values():
            indicator = self._step_pedestrian(ped)
            if indicator == -1:
                pedestrians_ids_for_removal.append(ped.id)
        for id in pedestrians_ids_for_removal:
            self.pedestrians.pop(id)

        for s in self.spawners.values():
            if s.step(self._step_time) or not s.is_queue_empty():
                if not s.is_for_pedesrians():
                    self._spawn_car(s._junction)
                else:
                    self._spawn_pedestrian(s._junction)

        self._update_cars_dataframe()
        self._update_lights_dataframe()

    def _step_lights(self):
        for light in self.lights.values():
            light.step(self._step_time)

    def _step_car(self, car: Car) -> int:
        x_rd: Road = self.edges_map[car.rd]  # edge
        x_l = car.lane
        x_c = car.cell

        car_roads_subgraph = self._get_roads_for_cars_subgraph()

        closest_junction_id = [
            e[1] for e in car_roads_subgraph.edges.data()
            if e[2]['road'].id == x_rd.id  # cannot use enumeration and compare i with id because of nx sorting edges
        ][0]
        target_junction_id = car.target_junction

        if car.velocity == 0:
            car.increment_jam_counter(self._step_time)
            if car.get_jam_counter() > 60 * (3 + car.get_profile_parameter()):
                car.reset_jam_counter()
                destinations = self.terminal_junctions
                dest_ok = False
                destination = np.random.choice(destinations)
                while not dest_ok:
                    try:
                        nx.astar_path(
                            car_roads_subgraph,
                            closest_junction_id,
                            destination
                        )
                        dest_ok = True
                    except nx.NetworkXNoPath:
                        destinations = [j for j in destinations if j != destination]
                        if len(destinations) == 0:
                            raise RuntimeError("No destinations for cars!")
                        destination = np.random.choice(destinations)
                car.target_junction = destination

        try:
            path = nx.astar_path(
                car_roads_subgraph,
                closest_junction_id,
                target_junction_id
            )
        except nx.NetworkXNoPath:
            raise RuntimeError(f"Path between car {car.id} "
                               f"current position ({closest_junction_id}) "
                               f"and its destination ({target_junction_id}) does not exist!")

        # ======================
        # if car is at the end of the road:
        if x_c == x_rd.cells.shape[1] - 1:

            # ============
            # reaching destination
            if path[-1] == closest_junction_id:
                self.edges_map[x_rd.id].free_cell(x_l, x_c)
                return -1

            # ============
            # lights
            potential_lights = x_rd.traffic_light_at_end
            if potential_lights != -1:
                lights = self.lights[potential_lights]
                if lights.state == Light.State.RED:
                    car.velocity = 0
                    return 0

            # ============
            # changing road

            next_road = car_roads_subgraph.edges[path[0], path[1]]['road'].id
            next_road_cells = self.edges_map[next_road].cells
            next_road_first_cells = next_road_cells[:, 0]

            n_lanes_in = x_rd.lanes
            n_lanes_out = len(next_road_first_cells)
            lane_id = x_l

            l_bound = int(np.floor(lane_id / n_lanes_in * n_lanes_out))
            u_bound = int(np.ceil((lane_id + 1) / n_lanes_in * n_lanes_out))

            options = np.arange(n_lanes_out)[l_bound:u_bound]

            next_lane = -1
            for ln in options:
                if next_road_first_cells[ln] == -1:
                    next_lane = ln
                    break

            if next_lane == -1:
                # stop car
                car.velocity = 0
                return 0
            else:
                # move car to next road
                car.set_junction_velocity()
                x_rd.free_cell(x_l, x_c)
                x_rd = self.edges_map[next_road]
                x_l = next_lane
                x_c = 0
                x_rd.cells[x_l, x_c] = car.id
                car.rd = next_road
                car.lane = x_l
                car.cell = x_c
                return 0

        # ======================
        # changing line before junctions

        d_remaining = x_rd.distance - (x_c + 1) * x_rd.d_cell
        if d_remaining < 40 and np.random.random() > .66 \
                or d_remaining < 20 and np.random.random() > .33 \
                or d_remaining < 10 \
                or np.random.random() > .6:
            # or car.get_profile_parameter() > .5 and np.random.random() > .5:

            # choosing lanes that satisfy the conditions
            if len(path) > 1:
                l_desired_options = self._get_lane_pref_before_junction(path[0], x_rd.id, path[1])
            else:  # last edge
                l_desired_options = np.arange(x_rd.lanes)[::-1]

            # ============
            # if car is not on the desired road ...
            if x_l not in l_desired_options:
                l_desired = l_desired_options[0] if x_l > l_desired_options[0] else l_desired_options[
                    -1]  # > because reversed

                # ... and there is a free lane on the desired road, change lane
                if x_rd.cells[l_desired, x_c] == -1 and np.random.random() > .5:
                    l_diff = l_desired - x_l
                    l_diff = max(-1, min(l_diff, 1))
                    l_new = x_l + l_diff
                    x_rd.free_cell(x_l, x_c)
                    x_rd.cells[l_new, x_c] = car.id
                    car.lane = l_new
                    return 0
                # ... and there is no free lane on the desired road,
                #     but there is some space ahead, continue ahead
                elif any(x_rd.cells[l_desired, x_c:] == -1):
                    pass
                # ... and there is no free lane on the desired road,
                #     and there is no space ahead, stop
                else:
                    car.velocity = 0
                    return 0
            # if car is on the desired road ...
            else:
                # ... move car to maximal right lane of the desired lanes
                for ln in l_desired_options:
                    if ln == x_l:
                        break
                    if (abs(ln - x_l) == 1  # if lane is adjacent
                            and x_rd.cells[ln, x_c] == -1  # if lane is empty
                            and np.random.random() > .5  # randomize
                    ):
                        x_rd.free_cell(x_l, x_c)
                        x_rd.cells[ln, x_c] = car.id
                        car.lane = ln
                        x_l = ln
                        # return 0

        # ======================
        # classic movement ahead

        d = x_rd.get_cell_distance()
        v = car.velocity
        t = self._step_time

        d_max = np.where(x_rd.get_cells(x_l) != -1)[x_c + 1:]
        a_max = 1.25 + car.get_profile_parameter(0, 1)

        # v for slowing down before junction or breaking
        v_special = car._junction_velocity if len(d_max) == 0 else 0

        d_remaining = x_rd.distance - (x_c + 1) * d
        if len(d_max) > 0:
            d_remaining = min(d_max, d_remaining)

        breaking = False
        if v > v_special:
            d_safe_stop = ((v - v_special) / a_max) * (v / 2 + v_special / 2) + d  # distance to stop
            breaking = d_remaining < d_safe_stop

        v_diff_half = a_max / self._step_time / 2
        v_normal = max(0, min(
            car.velocity + v_diff_half * (1 + car.get_profile_parameter(l_bound=0)),
            x_rd.v_avg + x_rd.v_std * car.get_profile_parameter()
        ))
        v_desired = v_special if breaking else v_normal

        a = (v_desired - v) / t
        a = max(-a_max, min(a, a_max))

        float(v)
        v = max(0., v + a * t)
        car.velocity = v

        d_c = int((v * t) // d)  # desired distance to move
        if 0 <= d_c < 1 and v != 0:
            d_c = 1
        if x_c + d_c >= x_rd.n_cell:
            d_c = x_rd.n_cell - x_c - 1

        if x_rd.cells[x_l, x_c + d_c] != -1:
            # @FIXME: this smells
            d_c -= 1
            d_c = max(0, d_c)
            car.velocity = max(0, d_c / t)

        # ======================
        # passing other cars

        x_l_old = x_l
        future_cell = car.cell + d_c
        # if car is not at the end of the road ...
        if x_l != 0 and future_cell < x_rd.n_cell - 3:
            ahead_cell = future_cell + 1
            cells_ahead = x_rd.get_cells(car.lane)[car.cell + 1:ahead_cell + 3]
            car_ahead_id = np.where(cells_ahead != -1)[0]
            # ... and there is a car ahead ...
            if len(car_ahead_id) != 0:
                car_ahead_id = cells_ahead[car_ahead_id[0]]
                car_ahead = self.cars[car_ahead_id]
                v_other = car_ahead.velocity
                # ... and it is slower than the current car ...
                if v_other != 0 \
                        and v / v_other >= 1.5:
                    move_cells = x_rd.get_cells(x_l - 1)[future_cell - 2: future_cell]
                    # ... and there is a free lane on the left, change lane and accelerate to pass
                    if all(move_cells == -1) and np.random.random() > .5:
                        x_l -= 1
                        car.velocity += 2

        # ======================
        # update car position

        x_rd.free_cell(x_l_old, x_c)
        x_rd.cells[x_l, x_c + d_c] = car.id
        car.lane = x_l
        car.cell += d_c

    def _get_lane_pref_before_junction(
            self,
            junction_id: int,
            rd_in_id: int,
            next_junction_id: int
    ):
        car_roads_subgraph = self._get_roads_for_cars_subgraph()
        node = car_roads_subgraph.nodes[junction_id]
        edge_in = [e for e in car_roads_subgraph.edges.data() if e[2]['road'].id == rd_in_id][0]
        edges_out = [
            e for e in car_roads_subgraph.edges.data()
            if e[0] == junction_id
        ]

        with np.errstate(divide='ignore', invalid='ignore'):
            diff = np.arctan(np.divide(
                node['y'] - car_roads_subgraph.nodes[edge_in[0]]['y'],
                node['x'] - car_roads_subgraph.nodes[edge_in[0]]['x'],
            ))

        edges_out_d = [  # calculate tan
            (np.arctan(np.divide(
                car_roads_subgraph.nodes[e[1]]['y'] - node['y'],
                car_roads_subgraph.nodes[e[1]]['x'] - node['x']
            )) - diff,
             e[2]['road'].id, e[1])
            for e in edges_out
        ]

        edges_out_d = sorted(edges_out_d, key=lambda x: x[0])
        edges_out_d = np.array([[e[1], e[2]] for e in edges_out_d])  # road ids, next junction ids
        road_id = np.argwhere(edges_out_d[:, 1] == next_junction_id)[0][0]
        n_lanes = edge_in[2]['road'].lanes
        n_roads_out = len(edges_out_d)

        l_bound = int(np.floor(road_id / n_roads_out * n_lanes))
        u_bound = int(np.ceil((road_id + 1) / n_roads_out * n_lanes))

        options = np.arange(n_lanes)[l_bound:u_bound]
        return options[::-1]  # reverse order

    def _step_pedestrian(self, pedestrian):
        x_rd: Road = self.edges_map[pedestrian.rd]
        x_l = pedestrian.lane
        x_c = pedestrian.cell

        pedestrian_roads_subgraph = self._get_roads_for_pedestrians_subgraph()
        pedestrian_roads_subdigraph = self._get_roads_for_pedestrians_subgraph(digraph=True)

        die = [
            e for e in pedestrian_roads_subdigraph.edges.data()
            if e[2]['road'].id == x_rd.id
        ][0]
        e = [
            e for e in pedestrian_roads_subgraph.edges.data()
            if e[2]['road'].id == x_rd.id  # cannot use enumeration and compare i with id because of nx sorting edges
        ][0]
        closest_junction_id = e[1]
        target_junction_id = pedestrian.target_junction

        try:
            path = nx.astar_path(
                pedestrian_roads_subgraph,
                closest_junction_id,
                target_junction_id
            )
        except nx.NetworkXNoPath:
            raise RuntimeError(f"Path between pedestrian {pedestrian.id} "
                               f"current position ({closest_junction_id}) "
                               f"and its destination ({target_junction_id}) does not exist!")

        reversed_order = False
        if len(path) > 1 and die[0] == path[1]:
            closest_junction_id = path[1]
            path = path[1:]
            reversed_order = True
        if len(path) > 1 and die[1] == path[1]:
            closest_junction_id = path[1]
            path = path[1:]
        elif len(path) == 1:
            if closest_junction_id == die[0]: # if our front is back of current edge
                reversed_order = True
        next_reversed_order = False
        if len(path) > 1:
            next_reversed_order = len( [
                e for e in self.graph.edges.data() # we need to analyze digraph for direction
                if e[0] == path[0] and e[1] == path[1]
            ]) == 0

        if not reversed_order and x_c == x_rd.cells.shape[1] - 1 or reversed_order and x_c == 0:
            if path[-1] == closest_junction_id:
                self.edges_map[x_rd.id].free_cell(x_l, x_c)
                return -1

            if x_rd.traffic_light_at_end != -1:
                lights = self.lights[x_rd.traffic_light_at_end]
                if lights.state == Light.State.RED:
                    pedestrian.velocity = 0
                    return 0
                if lights.state == Light.State.GREEN:
                    t_remaining = lights.get_remaining_time()
                    if t_remaining < pedestrian.t_walk_lights:
                        pedestrian.velocity = 0
                        return 0

            next_road = pedestrian_roads_subgraph.edges[path[0], path[1]]['road'].id
            next_road_cells = self.edges_map[next_road].cells
            next_road_first_cells = next_road_cells[:, 0] if not next_reversed_order else next_road_cells[:, -1]
            is_next_free = next_road_first_cells[x_l] == -1
            if is_next_free:
                should_negate = next_reversed_order ^ reversed_order
                l = x_l if not should_negate  else x_rd.lanes - x_l - 1
                next_line = len(next_road_first_cells) * l // x_rd.lanes
            else:
                next_lines = np.where(next_road_first_cells == -1)[0]
                if len(next_lines) == 0:
                    pedestrian.velocity = 0
                    return 0
                next_line = np.random.choice(next_lines)

            self.edges_map[x_rd.id].free_cell(x_l, x_c)
            x_rd = self.edges_map[next_road]
            x_l = next_line
            x_c = 0 if not next_reversed_order else x_rd.n_cell - 1
            x_rd.cells[x_l, x_c] = pedestrian.id
            pedestrian.rd = next_road
            pedestrian.lane = x_l
            pedestrian.cell = x_c
            return 0

        if np.random.random() > .8:
            pedestrian.velocity = 0
            return 0

        # make pedestrian use right side of the road
        if np.random.random() > .5:
            if not reversed_order:
                right_lanes = list(range(x_rd.lanes // 2, x_rd.lanes))
                if x_l not in right_lanes and np.random.random() > .5:
                    x_rd.free_cell(x_l, x_c)
                    x_l += 1
                    pedestrian.lane = x_l
                    x_rd.cells[x_l, x_c] = pedestrian.id
                if x_l in right_lanes and x_l < x_rd.lanes -1 and np.random.random() > .75:
                    x_rd.free_cell(x_l, x_c)
                    x_l -= 1
                    pedestrian.lane = x_l
                    x_rd.cells[x_l, x_c] = pedestrian.id
            else:
                left_lanes = list(range(x_rd.lanes // 2))
                if x_l not in left_lanes and np.random.random() > .5:
                    x_rd.free_cell(x_l, x_c)
                    x_l -= 1
                    pedestrian.lane = x_l
                    x_rd.cells[x_l, x_c] = pedestrian.id
                if x_l in left_lanes and x_l > 0 and np.random.random() > .75:
                    x_rd.free_cell(x_l, x_c)
                    x_l += 1
                    pedestrian.lane = x_l
                    x_rd.cells[x_l, x_c] = pedestrian.id


        # now move forward (backward if reversed_order)
        cell_ahead = x_c + 1 if not reversed_order else x_c - 1
        if x_rd.cells[x_l, cell_ahead] != -1:
            pedestrian.velocity = 0
            return 0

        x_rd.free_cell(x_l, x_c)
        next_cell = x_c + 1 if not reversed_order else x_c - 1
        x_rd.cells[x_l, next_cell] = pedestrian.id
        pedestrian.cell = next_cell
        pedestrian.velocity = 1.1

        return 0

    def _get_roads_for_cars_subgraph(self):
        g = nx.DiGraph()
        g.add_nodes_from(self.graph.nodes.data())
        e = [e for e in self.graph.edges.data() if e[2]['road'].is_type_for_cars()]
        g.add_edges_from(e)
        return g

    def _get_roads_for_pedestrians_subgraph(self, digraph=False):
        g = nx.Graph() if not digraph else nx.DiGraph()
        g.add_nodes_from(self.graph.nodes.data())
        e = [e for e in self.graph.edges.data() if e[2]['road'].is_type_for_pedestrians()]
        g.add_edges_from(e)
        return g

    def _spawn_car(self, junction_id: int):
        spawner = self.spawners[junction_id]
        car_roads_subgraph = self._get_roads_for_cars_subgraph()
        edges_out = [e for e in car_roads_subgraph.edges.data() if e[0] == junction_id]
        edges_out = np.array(edges_out)
        edges_out = edges_out[np.random.permutation(len(edges_out))]
        edge = edges_out[0]
        rd: Road = edge[2]['road']
        first_cells = rd.cells[:, 0]
        empty_lanes = np.where(first_cells == -1)[0]

        if len(empty_lanes) == 0:
            spawner.add_to_queue()
            return
        spawner.get_from_queue()

        lane = np.random.choice(empty_lanes)
        cell = 0
        car_id = max(self.cars.keys()) + 1 if len(self.cars) > 0 else 0

        destinations = [j for j in self.terminal_junctions if j != junction_id]
        if len(destinations) == 0:
            raise RuntimeError("No destinations for cars!")
        destination = np.random.choice(destinations)

        dest_ok = False
        while not dest_ok:
            try:
                nx.astar_path(
                    car_roads_subgraph,
                    edge[1],
                    destination
                )
                dest_ok = True
            except nx.NetworkXNoPath:
                destinations = [j for j in destinations if j != destination]
                if len(destinations) == 0:
                    raise RuntimeError("No destinations for cars!")
                destination = np.random.choice(destinations)

        self.cars[car_id] = Car(
            car_id,
            rd.id,
            lane,
            cell,
            destination
        )


    def _spawn_pedestrian(self, junction_id: int):
        spawner = self.spawners[junction_id]
        pedestrians_roads_subgraph = self._get_roads_for_pedestrians_subgraph()
        edges_out = [e for e in pedestrians_roads_subgraph.edges.data() if e[0] == junction_id or e[1] == junction_id]
        edges_out = np.array(edges_out)
        edges_out = edges_out[np.random.permutation(len(edges_out))]
        edge = edges_out[0]
        rd: Road = edge[2]['road']
        first_cells = rd.cells[:, 0]
        empty_lanes = np.where(first_cells == -1)[0]

        if len(empty_lanes) == 0:
            spawner.add_to_queue()
            return
        spawner.get_from_queue()

        lane = np.random.choice(empty_lanes)
        cell = 0
        pedestrian_id = max(self.pedestrians.keys()) + 1 if len(self.pedestrians) > 0 else 0

        destinations = [j for j in self.terminal_junctions if j != junction_id]
        if len(destinations) == 0:
            raise RuntimeError("No destinations for pedestrians!")
        destination = np.random.choice(destinations)

        dest_ok = False
        while not dest_ok:
            try:
                nx.astar_path(
                    pedestrians_roads_subgraph,
                    edge[1],
                    destination
                )
                dest_ok = True
            except nx.NetworkXNoPath:
                destinations = [j for j in destinations if j != destination]
                if len(destinations) == 0:
                    raise RuntimeError("No destinations for cars!")
                destination = np.random.choice(destinations)

        self.pedestrians[pedestrian_id] = Pedestrian(
            pedestrian_id,
            rd.id,
            lane,
            cell,
            destination
        )

    def get_step_time(self):
        return self._step_time

    def get_current_step(self):
        return self._current_step

    def get_max_steps(self):
        return self._max_steps

    def get_time_elapsed(self):
        return self._current_step * self._step_time

    def get_t_gap(self):
        return self._t_gap

    def _update_cars_dataframe(self):
        cars = []
        for car in self.cars.values():
            d = car.__dict__()
            d.update({
                "step": self._current_step,
                "closest_junction": [e[1] for e in self.graph.edges.data() if e[2]['road'].id == car.rd][0],
            })
            cars.append(d)
        self._cars_df = pd.concat([self._cars_df, pd.DataFrame(cars)])

    def _update_lights_dataframe(self):
        lights = []
        for light in self.lights.values():
            d = light.__dict__()
            d.update({
                "step": self._current_step,
            })
            lights.append(d)
        self._lights_df = pd.concat([self._lights_df, pd.DataFrame(lights)])

    def get_junctions_dataframe(self) -> pd.DataFrame:
        junctions = []
        for junction in self.graph.nodes.data():
            junctions.append({
                "id": junction[0],
                "x": junction[1]['x'],
                "y": junction[1]['y'],
            })
        return pd.DataFrame(junctions)

    def get_roads_dataframe(self) -> pd.DataFrame:
        edges = []
        for edge in self.graph.edges.data():
            d = {
                "source": edge[0],
                "target": edge[1],
            }
            d.update(
                edge[2]['road'].__dict__()
            )
            edges.append(d)
        return pd.DataFrame(edges)

    def get_cars_dataframe(self) -> pd.DataFrame:
        return self._cars_df

    def get_lights_dataframe(self) -> pd.DataFrame:
        return self._lights_df
