from simulator.plotter import plotter
from simulator.simulator import simulator


def main():
    sim = simulator("assets/model_test.json")

    pl = plotter(
        sim,
        plot_graph_on_start = True,
    )
    pl.run()

    sim.step(
        steps=50,
        t_gap=.5
    )


if __name__ == "__main__":
    main()
