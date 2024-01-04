from src.simulator.plotter import Plotter
from src.simulator.simulator import Simulator

import matplotlib.pyplot as plt


def main():

    # preparing simulation

    sim = Simulator("assets/model_test.json")

    # visualizing simulation

    pl = Plotter(
        sim,
        background_img="assets/background.png",
        # plot_graph_on_start=Plotter.PlotGraphEnum.YES_WITH_LABELS,
        # scale_on_start=2.5,
    )

    pl.run()

    # running simulation

    sim.step(
        # steps is the number of steps to run the simulation
        steps=100,
        # t_gap is the time between each step, in seconds.
        #   if t_gap is 0 (default), the simulation will run as fast as possible
        t_gap=.2,
    )

    # simple iteration is also possible...
    # for _ in range(10):
    #     sim.step(
    #         t_gap=.1,
    #     )
    #   ... especially if you want to add some logic in between steps
    #       or run the simulation until a condition is met.
    #   Note that the dynamic dataframes (see below) are updated with each step.
    #   This means that you can analyze the simulation results after the simulation is done.

    # closing visualizing simulation

    # pl.stop()

    # getting basic information about the simulation

    t_elapsed = sim.get_time_elapsed()
    s_made = sim.get_current_step()
    # sim.get_t_gap()

    print("-" * 50)
    print(f"Simulation stopped after: {s_made} step{'s' if s_made > 1 else ''}")
    print(f"Time elapsed: {t_elapsed // 60} [min] {t_elapsed % 60} [s] ({t_elapsed} [s])")

    # using methods for more advanced analysis

    ## static dataframes (do not change over time)
    sim.get_junctions_dataframe()
    sim.get_roadways_dataframe()

    ## dynamic dataframes (change with each simulation step)
    cars_df = sim.get_cars_dataframe()
    sim.get_lights_dataframe()
    # these dataframes can be used to analyze the simulation results.
    #   they store the state of the simulation at each step.

    # this information can be used to evaluate the performance of the simulated environment.
    #   e.g. the average number of cars stopped can be used to compare different traffic light configurations:
    cars_df_steps_grouped = cars_df.groupby("step")
    # count the number of cars stopped (cars that velocity is 0) at each step
    cars_stopped_steps_grouped = cars_df_steps_grouped["velocity"].apply(lambda x: (x == 0).sum())
    # count the number of cars in the simulation at each step
    cars_count_step_grouped = cars_df_steps_grouped["id"].count()
    # calculate the average number of cars stopped
    cars_stopped_avg = cars_stopped_steps_grouped.mean()
    # calculate the average number of cars in the simulation
    cars_count_avg = cars_count_step_grouped.mean()
    # calculate the average number of cars stopped per step
    cars_stopped_avg = cars_stopped_avg / cars_count_avg

    print("-" * 50)
    print(f"Average number of cars stopped: {round(cars_stopped_avg, 2)}")
    print(f"Average number of cars in the simulation: {round(cars_count_avg, 2)}")

    # plotting the results
    plt.plot(cars_stopped_steps_grouped, label="cars stopped")
    plt.plot(cars_count_step_grouped, label="total cars")
    plt.xlabel("steps")
    plt.ylabel("number of cars")
    plt.legend()
    # plt.show()
    plt.savefig("results/cars.png")


if __name__ == "__main__":
    main()
