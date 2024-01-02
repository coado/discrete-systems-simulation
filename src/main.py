from simulator.plotter import Plotter
from simulator.simulator import Simulator


def main():
    sim = Simulator("assets/model_test.json")

    pl = Plotter(
        sim,
        background_img="assets/background.png",
        plot_graph_on_start=False,
    )
    pl.run()

    sim.step(
        steps=500,
        t_gap=.5
    )


if __name__ == "__main__":
    main()
