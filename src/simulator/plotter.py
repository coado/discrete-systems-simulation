import numpy as np
import pygame as pg
import threading

from src.simulator.simulator import Simulator


class Plotter:
    def __init__(
            self,
            simulator: Simulator,
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

        self._d_x = 0
        self._d_y = 0
        self._scale = 1
        self._scale_max = 3
        self._scale_min = 0.9

        self._plot_graph = plot_graph_on_start
        self._bg_opacity = max(0., min(bg_opacity_on_start, 1.))

        if print_controls:
            self.print_controls()

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

        bg_img = pg.image.load('assets/tlo-symulacji.png')
        bg_img = pg.transform.scale(bg_img, (
            self.rescale(self._simulator.w),
            self.rescale(self._simulator.h)
        ))
        self._surface.blit(bg_img, (0, 0))

        s = pg.Surface((
            self.rescale(self._simulator.w),
            self.rescale(self._simulator.h)
        ))
        s.set_alpha(int(self._bg_opacity * 255))  # alpha level
        s.fill(pg.Color('white'))  # this fills the entire surface
        self._surface.blit(s, (0, 0))  # (0,0) are the top-left coordinates

        # plot all shit

        if self._plot_graph:
            self.__blit_nodes()

        self.__blit_edges(
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

        pg.display.update()

    def __blit_nodes(
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

    def __blit_edges(
            self,
            plot_inactive_cells=False,
            plot_lines=False,
            inactive_state=-1
    ):

        for source, target, data in self._simulator.graph.edges.data():
            source_pos = self._simulator.graph.nodes[source]
            target_pos = self._simulator.graph.nodes[target]
            lights = self._simulator.lights[source]
            rd = data['roadway']

            lines = rd.lanes

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

                if plot_lines:
                    pg.draw.line(
                        self._surface,
                        (0, 0, 0),
                        start,
                        end,
                        int(self.rescale(line_width))
                    )

                line_length = len(rd.get_cells(line_index))
                for i, cell in enumerate(rd.get_cells(line_index)):
                    r = cell_r / 3
                    color = pg.Color('black')

                    if lights is not None and i == line_length - 1:
                        if lights.state == lights.state.RED:
                            color = pg.Color('red')
                        elif lights.state == lights.state.GREEN:
                            color = pg.Color('green')

                    if cell != inactive_state:
                        color = self._simulator.cars[cell]._color
                        r = cell_r
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

    def __blit_text(self, text, pos, font, color=pg.Color('black')):
        span_id = font.render(text, False, color)
        w, h = span_id.get_width(), span_id.get_height()
        pos = (pos[0] - w // 2, pos[1] - h // 2)
        self._surface.blit(span_id, pos)

    def quit(self) -> None:
        pg.quit()

    def print_controls(self):
        print("Plotter controls:")
        print(" - quit: q/esc")
        print(" - movement: arrows")
        print(" - zoom: z/x")
        print(" - default zoom and position: c")
        print(" - hide/show graph: g")
        print(" - background opacity: o/p")
