import numpy as np
import pygame as pg
import threading

from src.simulator.simulator import simulator


class plotter:
    def __init__(
            self,
            simulator: simulator,
            plot_graph_on_start: bool = False
    ) -> None:
        self.simulator: simulator = simulator
        self.thread: threading.Thread = None

        (width, height) = (1920, 1080)
        root = pg.display.set_mode((width, height))  # , pg.FULLSCREEN)
        pg.display.set_caption('Traffic Simulator')
        root.fill((50, 50, 50))
        self.root: pg.Surface = root
        self.surface: pg.Surface = pg.Surface((
            self.rescale(self.simulator.w),
            self.rescale(self.simulator.h)
        ))

        self.d_x = 0
        self.d_y = 0
        self.scale = 1
        self.scale_max = 3
        self.scale_min = 0.9

        self.plot_graph = plot_graph_on_start

    def run(self):
        self.thread = threading.Thread(target=self._run, args=[])
        self.thread.start()

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
                    self.plot_graph = not self.plot_graph
            pressed_keys = pg.key.get_pressed()
            if pressed_keys[pg.K_UP]:
                self.d_y += 10 * self.scale
            if pressed_keys[pg.K_DOWN]:
                self.d_y -= 10 * self.scale
            if pressed_keys[pg.K_LEFT]:
                self.d_x += 10 * self.scale
            if pressed_keys[pg.K_RIGHT]:
                self.d_x -= 10 * self.scale
            if pressed_keys[pg.K_z]:
                if self.scale < self.scale_max:
                    self.scale += 0.1
                else:
                    self.scale = self.scale_max
            if pressed_keys[pg.K_x]:
                if self.scale > self.scale_min:
                    self.scale -= 0.1
                else:
                    self.scale = self.scale_min
            if pressed_keys[pg.K_c]:
                self.d_x = 0
                self.d_y = 0
                self.scale = 1

            self._draw()
        self.simulator.stop()

    def _draw(self):

        # plot background

        self.root.fill((50, 50, 50))

        bg_img = pg.image.load('assets/tlo-symulacji.png')
        bg_img = pg.transform.scale(bg_img, (
            self.rescale(self.simulator.w),
            self.rescale(self.simulator.h)
        ))
        self.surface.blit(bg_img, (0, 0))

        # plot all shit

        if self.plot_graph:
            self.__blit_nodes()

        self.__blit_edges(
            plot_inactive_cells=self.plot_graph,
            plot_lines=self.plot_graph,
            inactive_state=-1
        )

        # plot view

        init_scale_x = self.root.get_width() / self.surface.get_width()
        init_scale_y = self.root.get_height() / self.surface.get_height()
        init_scale = min(init_scale_x, init_scale_y)

        init_pos_x = (self.root.get_width() - self.surface.get_width()) / 2
        init_pos_y = (self.root.get_height() - self.surface.get_height()) / 2

        old_w = self.surface.get_width()
        old_h = self.surface.get_height()
        scale = self.scale
        new_surface = self.surface
        new_surface = pg.transform.scale(new_surface, (
            int(old_w * scale * init_scale),
            int(old_h * scale * init_scale)
        ))

        d_x = (old_w - new_surface.get_width()) // 2
        d_y = (old_h - new_surface.get_height()) // 2

        self.root.blit(
            new_surface,
            (
                init_pos_x + self.d_x + d_x,
                init_pos_y + self.d_y + d_y
            )
        )

        pg.display.update()

    def __blit_nodes(
            self,
    ):
        for id, node in self.simulator.graph.nodes.data():
            pg.draw.circle(
                self.surface,
                pg.Color('gray'),
                (
                    self.rescale(node['x']),
                    self.rescale(node['y'])
                ),
                self.rescale(10)
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

        for source, target, data in self.simulator.graph.edges.data():
            source_pos = self.simulator.graph.nodes[source]
            target_pos = self.simulator.graph.nodes[target]
            rd = data['roadway']

            lines = rd.lanes

            rot = np.arctan2(target_pos['y'] - source_pos['y'], target_pos['x'] - source_pos['x'])

            line_padding = 6
            opposite_line_padding = line_padding * 2
            line_width = 1
            cell_r = 2
            for i in range(lines):
                # if lane in oposite direction exists:

                shift_x, shift_y = 0, 0
                if self.simulator.graph.has_edge(target, source):
                    negative = 1
                    if target > source:
                        negative = -1
                    shift_x = np.cos(rot + np.pi / 2) * opposite_line_padding // 2 * negative
                    shift_y = np.sin(rot + np.pi / 2) * opposite_line_padding // 2 * negative

                d_x = np.cos(rot + np.pi / 2) * ((i - (lines - 1) / 2) * line_padding + shift_x)
                d_y = np.sin(rot + np.pi / 2) * ((i - (lines - 1) / 2) * line_padding + shift_y)
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
                        self.surface,
                        (0, 0, 0),
                        start,
                        end,
                        int(self.rescale(line_width))
                    )

                for i, cell in enumerate(rd.get_cells(i)):
                    color = pg.Color('black')
                    if cell != inactive_state:
                        color = self.simulator.cars[cell]._color
                    if cell != inactive_state or plot_inactive_cells:
                        pg.draw.circle(
                            self.surface,
                            color,
                            (
                                int(start[0] + (end[0] - start[0]) * (i + 1) / rd.n_cell + cell_r / 2),
                                int(start[1] + (end[1] - start[1]) * (i + 1) / rd.n_cell + cell_r / 2)
                            ),
                            self.rescale(cell_r)
                        )

    def __blit_text(self, text, pos, font, color=pg.Color('black')):
        span_id = font.render(text, False, color)
        w, h = span_id.get_width(), span_id.get_height()
        pos = (pos[0] - w // 2, pos[1] - h // 2)
        self.surface.blit(span_id, pos)

    def quit(self) -> None:
        pg.quit()
