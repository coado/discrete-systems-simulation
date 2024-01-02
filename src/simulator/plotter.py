import numpy as np
import pygame as pg
import threading

from src.simulator.simulator import Simulator
from src.simulator.elements.roadway import Roadway


class Plotter:
    def __init__(
            self,
            simulator: Simulator,
            background_img: str = None,
            plot_graph_on_start: bool = False,
            bg_opacity_on_start: float = .7,
            print_controls=True
    ) -> None:
        self._simulator: simulator = simulator
        self._thread: threading.Thread = None

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
        self._scale = 1
        self._scale_max = 3
        self._scale_min = 0.9

        self._plot_graph = plot_graph_on_start
        self._bg_opacity = max(0., min(bg_opacity_on_start, 1.))

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

        running = True
        while running:
            for event in pg.event.get():
                if (event.type == pg.QUIT
                        or (event.type == pg.KEYDOWN
                            and (event.key == pg.K_ESCAPE
                                 or event.key == pg.K_q)
                        )
                ):
                    running = False
                if event.type == pg.KEYDOWN and event.key == pg.K_g:
                    self._plot_graph = not self._plot_graph
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

        if self._plot_graph:
            self._plot_nodes()

        self._plot_edges(
            plot_inactive_cells=self._plot_graph,
            # plot_lines=self._plot_graph,
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

        self._plot_controls()

        pg.display.update()

    def _plot_nodes(
            self,
    ):
        for id, node in self._simulator.graph.nodes.data():
            pg.draw.circle(
                self._surface,
                pg.Color('gray'),
                (
                    self.rescale(node['x']),
                    self.rescale(node['y'])
                ),
                self.rescale(10),
            )
            # if plot_indicator:
            #     self._blit_text(
            #         str(id),
            #         (
            #             node['x'],
            #             node['y']
            #         ),
            #         font
            #     )

    def _plot_edges(
            self,
            plot_inactive_cells=False,
            plot_lines=False,
            inactive_state=-1
    ):

        for source, target, data in self._simulator.graph.edges.data():
            source_pos = self._simulator.graph.nodes[source]
            target_pos = self._simulator.graph.nodes[target]
            rw: Roadway = data['roadway']
            lights = self._simulator.lights[rw.traffic_light_at_end] \
                if rw.traffic_light_at_end != -1 \
                else None

            lines = rw.lanes

            rot = np.arctan2(target_pos['y'] - source_pos['y'], target_pos['x'] - source_pos['x'])

            line_padding = 6
            opposite_line_padding = line_padding * 2
            line_width = 1
            cell_r = 2
            for line_index in range(lines):
                # if lane in oposite direction exists:

                shift_x, shift_y = 0, 0
                if self._simulator.graph.has_edge(target, source):
                    negative = 1
                    if target > source:
                        negative = -1
                    shift_x = np.cos(rot + np.pi / 2) * opposite_line_padding // 2 * negative
                    shift_y = np.sin(rot + np.pi / 2) * opposite_line_padding // 2 * negative

                d_x = np.cos(rot + np.pi / 2) * ((line_index - (lines - 1) / 2) * line_padding + shift_x)
                d_y = np.sin(rot + np.pi / 2) * ((line_index - (lines - 1) / 2) * line_padding + shift_y)
                start = (
                    self.rescale(source_pos['x'] + d_x),
                    self.rescale(source_pos['y'] + d_y)
                )
                end = (
                    self.rescale(target_pos['x'] + d_x),
                    self.rescale(target_pos['y'] + d_y)
                )

                # make junctions paddings
                reversed_x = int(start[0] > end[0]) * 2 - 1
                reversed_y = int(start[1] > end[1]) * 2 - 1
                d_j = self.rescale(10)
                start = (
                    start[0] + d_j * reversed_x * np.sin(rot + np.pi / 2),
                    start[1] + d_j * reversed_y * np.cos(rot + np.pi / 2),
                )
                end = (
                    end[0] + d_j * reversed_x * np.sin(rot + np.pi / 2),
                    end[1] + d_j * reversed_y * np.cos(rot + np.pi / 2),
                )

                if plot_lines:
                    pg.draw.line(
                        self._surface,
                        (0, 0, 0),
                        start,
                        end,
                        int(self.rescale(line_width))
                    )

                if lights is not None:
                    pg.draw.circle(
                        self._surface,
                        pg.color.Color('red') if lights.state == lights.state.RED else pg.color.Color('green'),
                        (
                            int(start[0] + (end[0] - start[0]) * (rw.n_cell + .5) / rw.n_cell + cell_r / 2),
                            int(start[1] + (end[1] - start[1]) * (rw.n_cell + .5) / rw.n_cell + cell_r / 2)
                        ),
                        self.rescale(cell_r + 1),
                    )

                for i, cell in enumerate(rw.get_cells(line_index)):
                    r = cell_r / 3
                    color = pg.Color('black')

                    if cell != inactive_state:
                        color = self._simulator.cars[cell]._color
                        r = cell_r
                    if cell != inactive_state or plot_inactive_cells:
                        pg.draw.circle(
                            self._surface,
                            color,
                            (
                                int(start[0] + (end[0] - start[0]) * (i + 1) / rw.n_cell + cell_r / 2),
                                int(start[1] + (end[1] - start[1]) * (i + 1) / rw.n_cell + cell_r / 2)
                            ),
                            self.rescale(r),
                        )

    def _plot_controls(self):
        header = "Controls:"
        content = self.get_controls_str().split("\n")
        pad = 10
        h = pad \
            + 24 + pad  \
            + 24 * len(content) \
            + pad
        w = pad + max([len(s) for s in content]) * 7 + pad

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
                (pad, 24 * (i + 1) + pad*2),
                font_size=16,
                surface=surface
                )
        self._root.blit(surface, (0, 0))

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

    def quit(self) -> None:
        pg.quit()

    def get_controls_str(self):
        return "\n".join([
            "Plotter controls:",
            " - quit: q/esc",
            " - movement: arrows",
            " - zoom: z/x",
            " - default zoom and position: c",
            " - hide/show graph: g",
            " - background opacity: o/p"
        ])
