from simulator.plotter import Plotter
from simulator.simulator import Simulator


def main():
    sim = Simulator("assets/model_test.json")

    pl = Plotter(
        sim,
        plot_graph_on_start=True,
    )
    pl.run()

    sim.step(
        steps=100,
        t_gap=.5
    )


if __name__ == "__main__":
    main()
