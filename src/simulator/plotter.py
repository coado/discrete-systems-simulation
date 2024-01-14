from __future__ import annotations

import numpy as np
import pygame as pg
import threading
from enum import Enum

from src.simulator.simulator import Simulator
from src.simulator.elements.road import Road


class Plotter:
    class PlotGraphEnum(Enum):
        NO = 0
        YES = 1
        YES_WITH_LABELS = 2

    def __init__(
            self,
            simulator: Simulator,
            background_img: str = None,
            plot_graph_on_start: PlotGraphEnum = PlotGraphEnum.NO,
            bg_opacity_on_start: float = .7,
            scale_on_start: float = 1,
            print_controls=True
    ) -> None:
        self._simulator: simulator = simulator
        self._thread: threading.Thread | None = None

        (width, height) = (1920, 1080)
        root = pg.display.set_mode((width, height))  # , pg.FULLSCREEN)
        pg.display.set_caption('Traffic Simulator')
        root.fill((50, 50, 50))
        self._root: pg.Surface = root
        self._surface: pg.Surface = pg.Surface((
            self.rescale(self._simulator.w),
            self.rescale(self._simulator.h)
        ))

        self._background_img = background_img

        self._d_x = 0
        self._d_y = 0
        self._scale_max = 3
        self._scale_min = 0.9
        self._scale = min(max(scale_on_start, self._scale_min), self._scale_max)

        self._plot_graph: Plotter.PlotGraphEnum = plot_graph_on_start
        self._bg_opacity = max(0., min(bg_opacity_on_start, 1.))

        self._running = False

        if print_controls:
            print(self.get_controls_str())

    def run(self):
        self._thread = threading.Thread(target=self._run, args=[])
        self._thread.start()

    def rescale(self, value: float) -> float:
        resolution = 2
        return value * resolution

    def _run(self) -> None:
        pg.font.init()
        pg.font.SysFont('Arial', 32)

        self._running = True
        while self._running:
            for event in pg.event.get():
                if (event.type == pg.QUIT
                        or (event.type == pg.KEYDOWN
                            and (event.key == pg.K_ESCAPE
                                 or event.key == pg.K_q)
                        )
                ):
                    self._running = False
                    break
                if event.type == pg.KEYDOWN and event.key == pg.K_g:
                    self._plot_graph = Plotter.PlotGraphEnum((self._plot_graph.value + 1) % 3)
            if not self._running:
                break
            pressed_keys = pg.key.get_pressed()
            if pressed_keys[pg.K_UP]:
                self._d_y += 10 * self._scale
            if pressed_keys[pg.K_DOWN]:
                self._d_y -= 10 * self._scale
            if pressed_keys[pg.K_LEFT]:
                self._d_x += 10 * self._scale
            if pressed_keys[pg.K_RIGHT]:
                self._d_x -= 10 * self._scale
            if pressed_keys[pg.K_z]:
                if self._scale < self._scale_max:
                    self._scale += 0.1
                else:
                    self._scale = self._scale_max
            if pressed_keys[pg.K_x]:
                if self._scale > self._scale_min:
                    self._scale -= 0.1
                else:
                    self._scale = self._scale_min
            if pressed_keys[pg.K_c]:
                self._d_x = 0
                self._d_y = 0
                self._scale = 1
            if pressed_keys[pg.K_o]:
                self._bg_opacity = min(self._bg_opacity + .1, 1)
            if pressed_keys[pg.K_p]:
                self._bg_opacity = max(self._bg_opacity - .1, 0)

            self._draw()
        self._simulator.stop()

    def _draw(self):

        # plot background

        self._root.fill((50, 50, 50))

        if self._background_img is not None:
            try:
                bg_img = pg.image.load(self._background_img)
                bg_img = pg.transform.scale(bg_img, (
                    self.rescale(self._simulator.w),
                    self.rescale(self._simulator.h)
                ))
                self._surface.blit(bg_img, (0, 0))
            except Exception as e:
                print("Error loading background image: " + str(e))
                self._background_img = None
        if self._background_img is None:
            self._surface.fill(pg.Color('black'))

        s = pg.Surface((
            self.rescale(self._simulator.w),
            self.rescale(self._simulator.h)
        ))
        s.set_alpha(int(self._bg_opacity * 255))  # alpha level
        s.fill(pg.Color('white'))  # this fills the entire surface
        self._surface.blit(s, (0, 0))  # (0,0) are the top-left coordinates

        # plot all shit

        if self._plot_graph.value > Plotter.PlotGraphEnum.NO.value:
            self._plot_nodes(
                plot_indicators=self._plot_graph == Plotter.PlotGraphEnum.YES_WITH_LABELS
            )

        self._plot_edges(
            plot_inactive_cells=self._plot_graph.value > Plotter.PlotGraphEnum.NO.value,
            plot_indicators=self._plot_graph == Plotter.PlotGraphEnum.YES_WITH_LABELS,
            inactive_state=-1
        )

        # plot view

        init_scale_x = self._root.get_width() / self._surface.get_width()
        init_scale_y = self._root.get_height() / self._surface.get_height()
        init_scale = min(init_scale_x, init_scale_y)

        init_pos_x = (self._root.get_width() - self._surface.get_width()) / 2
        init_pos_y = (self._root.get_height() - self._surface.get_height()) / 2

        old_w = self._surface.get_width()
        old_h = self._surface.get_height()
        scale = self._scale
        new_surface = self._surface
        new_surface = pg.transform.scale(new_surface, (
            int(old_w * scale * init_scale),
            int(old_h * scale * init_scale)
        ))

        d_x = (old_w - new_surface.get_width()) // 2
        d_y = (old_h - new_surface.get_height()) // 2

        self._root.blit(
            new_surface,
            (
                init_pos_x + self._d_x + d_x,
                init_pos_y + self._d_y + d_y
            )
        )

        x, y = pg.mouse.get_pos()
        x -= init_pos_x+ self._d_x + d_x
        y -= init_pos_y+ self._d_y + d_y
        x = x / new_surface.get_width() * self._simulator.w
        y = y / new_surface.get_height() * self._simulator.h

        self._plot_controls()

        self._plot_stats(mouse_pos=(x, y))

        pg.display.update()

    def _plot_nodes(
            self,
            plot_indicators=False,
    ):
        for id, node in self._simulator.graph.nodes.data():
            node_r = 6
            pg.draw.circle(
                self._surface,
                pg.Color('gray'),
                (
                    self.rescale(node['x']),
                    self.rescale(node['y'])
                ),
                self.rescale(node_r),
            )
            border_width = 2
            if id in self._simulator.spawners.keys():
                additional_bw = border_width if id in self._simulator.terminal_junctions else 0
                pg.draw.circle(
                    self._surface,
                    pg.Color('red'),
                    (
                        self.rescale(node['x']),
                        self.rescale(node['y'])
                    ),
                    self.rescale(node_r + additional_bw),
                    int(self.rescale(border_width + additional_bw)),
                )
            if id in self._simulator.terminal_junctions:
                pg.draw.circle(
                    self._surface,
                    pg.Color('black'),
                    (
                        self.rescale(node['x']),
                        self.rescale(node['y'])
                    ),
                    self.rescale(node_r),
                    int(self.rescale(border_width)),
                )
            if plot_indicators:
                self.__blit_text(
                    str(id),
                    (
                        self.rescale(node['x']),
                        self.rescale(node['y'])
                    ),
                    font_size=12,
                    center_x=True,
                    center_y=True,
                    color=pg.Color('white'),
                    surface=self._surface,
                )

    def _plot_edges(
            self,
            plot_inactive_cells=False,
            plot_indicators=False,
            inactive_state=-1
    ):

        for source, target, data in self._simulator.graph.edges.data():
            start_point = self._simulator.graph.nodes[source]
            start_point = np.array([start_point['x'], start_point['y']])
            end_point = self._simulator.graph.nodes[target]
            end_point = np.array([end_point['x'], end_point['y']])

            rd: Road = data['road']
            lights = self._simulator.lights[rd.traffic_light_at_end] \
                if rd.traffic_light_at_end != -1 \
                else None

            lines = rd.lanes

            is_pavement = rd.is_type_for_pedestrians()

            deg = np.arctan2(
                end_point[1] - start_point[1],
                end_point[0] - start_point[0]
            ) # radians
            # deg = np.arctan2(
            #     end_point['y'] - start_point['y'],
            #     end_point['x'] - start_point['x']
            # ) # radians

            line_padding = 6
            opposite_line_padding = line_padding * 2
            cell_r = 2.5
            node_r = 6
            for line_index in range(lines):
                # if lane in oposite direction exists:

                d_left = (line_index - (lines - 1) / 2) * line_padding

                if self._simulator.graph.has_edge(target, source):
                    d_left += opposite_line_padding // 2

                d_start = self._calculate_line_shift(
                    deg,
                    -node_r / 2 if not is_pavement else 0,
                    d_left
                )
                d_end = self._calculate_line_shift(
                    deg,
                    -node_r - cell_r * 2 if lights is not None else (
                        -node_r if not is_pavement else 0
                    ),
                    d_left
                )
                start = (
                    self.rescale(start_point[0] + d_start[0]),
                    self.rescale(start_point[1] + d_start[1])
                )
                end = (
                    self.rescale(end_point[0] + d_end[0]),
                    self.rescale(end_point[1] + d_end[1])
                )

                if lights is not None and (line_index == 0 or not is_pavement):
                    lights_r = cell_r + 1
                    if is_pavement:
                        lights_r -= .5
                    d_end_lights = self._calculate_line_shift(
                        deg,
                        -node_r,
                        d_left
                    )
                    pg.draw.circle(
                        self._surface,
                        pg.color.Color('red') if lights.state == lights.state.RED else pg.color.Color('green'),
                        (
                            self.rescale(end_point[0] + d_end_lights[0]),
                            self.rescale(end_point[1] + d_end_lights[1])
                        ),
                        self.rescale(lights_r),
                    )

                for i, cell in enumerate(rd.get_cells(line_index)):
                    r = cell_r / 3
                    color = pg.Color('black')

                    if cell != inactive_state:
                        if rd.is_type_for_cars():
                            color = self._simulator.cars[cell]._color
                            r = cell_r
                        elif rd.is_type_for_pedestrians():
                            color = pg.Color('white')
                            r = cell_r / 2
                    if cell != inactive_state or plot_inactive_cells:
                        pg.draw.circle(
                            self._surface,
                            color,
                            (
                                int(start[0] + (end[0] - start[0]) * (i + 1) / rd.n_cell + cell_r / 2),
                                int(start[1] + (end[1] - start[1]) * (i + 1) / rd.n_cell + cell_r / 2)
                            ),
                            self.rescale(r),
                        )

            if plot_indicators:
                x_avg = (start_point[0] + end_point[0]) / 2
                y_avg = (start_point[1] + end_point[1]) / 2
                self.__blit_text(
                    str(rd.id),
                    (
                        self.rescale(x_avg),
                        self.rescale(y_avg)
                    ),
                    font_size=12,
                    center_x=True,
                    center_y=True,
                    color=pg.Color('black'),
                    surface=self._surface,
                )

    def _calculate_line_shift(self, deg, d_up, d_left) -> np.array:
        d_x = d_up * np.cos(deg) + d_left * np.cos(deg + np.pi / 2)
        d_y = d_up * np.sin(deg) + d_left * np.sin(deg + np.pi / 2)
        return np.array([d_x, d_y])

    def _plot_controls(self):
        header = "Controls:"
        content = self.get_controls_str().split("\n")
        pad = 10
        h = pad \
            + 24 + pad \
            + 24 * len(content) \
            + pad
        w = pad + max([len(s) for s in content]) * 7.5 + pad

        surface = pg.Surface((w, h))
        surface.fill(pg.Color('white'))
        self.__blit_text(
            header,
            (pad, 10),
            font_size=24,
            surface=surface
        )
        for i, line in enumerate(content):
            self.__blit_text(
                line,
                (pad, 24 * (i + 1) + pad * 2),
                font_size=16,
                surface=surface
            )
        self._root.blit(surface, (0, 0))

    def _plot_stats(self, mouse_pos: tuple[float, float]):
        header = "Stats:"
        t_s = self._simulator.get_step_time()
        t = self._simulator.get_time_elapsed()
        content = [
            f"Gap time: {self._simulator.get_t_gap()} [s]",
            f"Step time: {t_s} [s]",
            f"Step: {self._simulator.get_current_step()} / {self._simulator.get_max_steps()}",
            f"Time elapsed: {t // 60} [min] {t % 60} [s] ({t} [s])",
            f"Total cars: {len(self._simulator.cars)}",
            f"Mouse position: ({mouse_pos[0]:.0f}, {mouse_pos[1]:.0f}) [m]",
        ]
        pad = 10
        h = pad \
            + 24 + pad \
            + 24 * len(content) \
            + pad
        w = pad + max(max([len(s) for s in content]), 42) * 7.5 + pad

        surface = pg.Surface((w, h))
        surface.fill(pg.Color('white'))
        self.__blit_text(
            header,
            (pad, 10),
            font_size=24,
            surface=surface
        )
        for i, line in enumerate(content):
            self.__blit_text(
                line,
                (pad, 24 * (i + 1) + pad * 2),
                font_size=16,
                surface=surface
            )
        self._root.blit(surface, (self._root.get_width() - w, 0))

    def __blit_text(
            self,
            text,
            pos,
            font=None,
            font_size=32,
            color=pg.Color('black'),
            surface=None,
            center_x=False,
            center_y=False
    ):
        if font is None:
            font = pg.font.SysFont('Arial', font_size)
        span_id = font.render(text, True, color)
        w, h = span_id.get_width(), span_id.get_height()
        pos_x, pos_y = pos
        if center_x:
            pos_x -= w // 2
        if center_y:
            pos_y -= h // 2
        pos = (pos_x, pos_y)
        if surface is None:
            surface = self._root
        surface.blit(span_id, pos)

    def stop(self) -> None:
        self._running = False

    def get_controls_str(self):
        return "\n".join([
            "Plotter controls:",
            " - quit: q/esc",
            " - movement: arrows",
            " - zoom: z/x",
            " - reset zoom and position: c",
            " - change graph visibility: g",
            " - change background opacity: o/p"
        ])
