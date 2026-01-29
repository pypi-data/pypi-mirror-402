from typing import List, Tuple

from functools import partial

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

from datetime import datetime, timedelta
import numpy as np
import os
import datetime
from pathlib import Path

os.environ["JAX_PLATFORM_NAME"] = "cpu"
import jax

jax.config.update("jax_platform_name", "cpu")

from semistaticsim.datawrangling.sssd import load_sssd
from semistaticsim.groundtruth.utils import format_receptacle

from omegaconf import OmegaConf

if not OmegaConf.has_resolver("eval"):
    OmegaConf.register_new_resolver("eval", eval)

import scienceplots

# plt.style.use(["science", "latex-sans", "sans"])
plt.style.use(["science", "sans", "no-latex"])

color_palette = [(74, 35, 119), (140, 197, 227), (245, 95, 116), (89, 168, 156), (240, 197, 113)]
color_palette = [(r / 255, g / 255, b / 255) for r, g, b in color_palette]
color_palette_str = [
    "purple",
    "light_blue",
    "pink",
    "teal",
    "mustard",
]
color_palette_from_str = {k: v for k, v in zip(color_palette_str, color_palette)}

N_COLORS = 10
grey_palette = sns.color_palette("Greys", n_colors=N_COLORS + 2)

# This is a grey palette: 0 means white, 100 means black
# The line below helps indexing "10" as '10% black', while "80" means '80% black
grey_palette_from_str = {f"{p}0": v for p, v in enumerate(grey_palette)}

# The stuff below is just to facilitate semantics
grey_palette_from_str["black"] = grey_palette_from_str["100"]
grey_palette_from_str["white"] = grey_palette_from_str["00"]

plt.rcParams["font.size"] = 8


def hours_to_datetimed(hours: np.ndarray, start_day: str = "monday") -> np.ndarray:
    """
    Convert minutes (from Monday 00:00) into datetime objects.
    """
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    start_idx = days_of_week.index(start_day.lower())
    start_date = datetime.datetime(2023, 1, 2 + start_idx)  # pick arbitrary Monday
    return np.array([start_date + timedelta(hours=int(m)) for m in hours])


def save_fig(
    fig: matplotlib.figure.Figure,
    fig_name: str,
    fig_dir: str,
    fig_fmt: str,
    fig_size: Tuple[float, float] = [6.4, 4],
    save: bool = True,
    dpi: int = 300,
    transparent_png=True,
):
    """
    Code adapted from https://zhauniarovich.com/post/2022/2022-09-matplotlib-graphs-in-research-papers/
    This procedure stores the generated matplotlib figure to the specified
    directory with the specified name and format.

    Parameters
    ----------
    fig : [type]
        Matplotlib figure instance
    fig_name : str
        File name where the figure is saved
    fig_dir : str
        Path to the directory where the figure is saved
    fig_fmt : str
        Format of the figure, the format should be supported by matplotlib
        (additional logic only for pdf and png formats)
    fig_size : Tuple[float, float]
        Size of the figure in inches, by default [6.4, 4]
    save : bool, optional
        If the figure should be saved, by default True. Set it to False if you
        do not want to override already produced figures.
    dpi : int, optional
        Dots per inch - the density for rasterized format (png), by default 300
    transparent_png : bool, optional
        If the background should be transparent for png, by default True
    """
    if not save:
        return

    fig.set_size_inches(fig_size, forward=False)
    fig_fmt = fig_fmt.lower()
    fig_dir = os.path.join(fig_dir, fig_fmt)
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)
    pth = os.path.join(fig_dir, "{}.{}".format(fig_name, fig_fmt.lower()))
    if fig_fmt == "pdf":
        metadata = {"Creator": "", "Producer": "", "CreationDate": None}
        fig.savefig(pth, bbox_inches="tight", metadata=metadata)
    elif fig_fmt == "png":
        alpha = 0 if transparent_png else 1
        axes = fig.get_axes()
        fig.patch.set_alpha(alpha)
        for ax in axes:
            ax.patch.set_alpha(alpha)
        fig.savefig(
            pth,
            bbox_inches="tight",
            dpi=dpi,
        )
    else:
        try:
            fig.savefig(pth, bbox_inches="tight")
        except Exception as e:
            print("Cannot save figure: {}".format(e))


class Plotter:
    def __init__(self, exp_name: str, viz: bool = True, res_path: str = None, fig_fmt="pdf") -> None:
        self.viz = viz

        # Create a directory to store the results if viz is False
        script_directory = os.path.abspath(os.curdir)
        self.res_path = res_path
        if self.res_path is None:
            self.res_path = os.path.join(script_directory, "assets", datetime.datetime.now().isoformat(), exp_name)
        print(f"Saving results to {self.res_path}")
        if not os.path.exists(self.res_path):
            os.makedirs(self.res_path)
        # Conversion utils
        self.mm = 1 / 25.4  # conversion from millimeters to inches
        self.cm = 1 / 2.54  # conversion from centimeters to inches
        self.pt = 1 / 72.27  # conversion from points to inches

        # The values below are obtained from LaTeX, using \the\columnwidth and \the\textwidth
        self.PAPER_COLUMN = 252.0  # points
        self.PAPER_TEXTWIDTH = 516.0  # points
        # Savefig partial
        self.savefig = partial(save_fig, fig_dir=self.res_path, fig_fmt=fig_fmt, transparent_png=False)

    def plot_observations(
        self,
        sampling_times: np.ndarray,
        assignments: np.ndarray,
        receptacles_name: List[str],
        pickupable_name: str,
        location: str = "lower left",
        f_name: str = "ground_truth",
        last_week_only: bool = False,
    ) -> None:
        """
        Plot binary observations against the true state over time.

        Args:
            sampling_times (List[float]): Time points for the true state samples.
            true_state (List[float]): True state values at sampling times.
            t (List[float]): Time points for the observations.
            obs (List[int]): Binary observations at times `t`.
            location (str, optional): Legend location in the plot. Default is "lower left".
            figure_size (Optional[Tuple[int, int]], optional): Figure size in inches. Defaults to `self.figure_size`.
            f_name (str, optional): File name for saving the plot. Default is "observations".
            last_week_only (bool, optional): If True, only plot the trailing 7 days of data. Default is False.

        Returns:
            None
        """
        dates = hours_to_datetimed(sampling_times, "monday")

        if last_week_only and len(dates) > 0:
            cutoff_date = dates[-1] - timedelta(days=8)
            mask_week = dates >= cutoff_date
            dates = dates[mask_week]
            assignments = assignments[mask_week]

        # Obtain max number of unique receptacles across all pickupables (columns)
        n_receptacles = len(np.unique(assignments))

        im_width, im_height = self.PAPER_TEXTWIDTH * self.pt, 4 * self.cm * n_receptacles
        figure_size = (im_width, im_height)

        # Create figure
        fig, axes = plt.subplots(n_receptacles, 1, figsize=figure_size, sharex=True, dpi=300, constrained_layout=True)
        if n_receptacles == 1:
            axes = [axes]

        for _ in range(n_receptacles):
            receptacles_id = np.unique(assignments).astype(int).tolist()
            for i, receptacle_id in enumerate(receptacles_id):
                mask = assignments == receptacle_id
                states = mask.astype(int)
                # format receptacle name
                r_name = receptacles_name[receptacle_id]
                r_name = format_receptacle(r_name)
                # Plot state
                axes[i].plot(dates, states, color=color_palette_from_str["purple"], ls="-", linewidth=0.5)
                axes[i].set_title(f"{pickupable_name} @ {r_name}")
                print(f"{pickupable_name} @ {r_name}")
                # Set y limits to 1 = present and 0 = absent
                axes[i].set_ylim(-0.1, 1.1)
                axes[i].set_yticks([0, 1])
                axes[i].set_yticklabels(["Absent", "Present"])
                # axes[p_id, i].xaxis.set_major_locator(mdates.MonthLocator())             # one tick per month
                # axes[p_id, i].xaxis.set_major_formatter(mdates.DateFormatter("%b"))      # Jan, Feb, Mar, ...
                axes[i].xaxis.set_major_locator(mdates.DayLocator())  # ticks per day
                axes[i].xaxis.set_major_formatter(mdates.DateFormatter("%a"))  # Mon, Tue, ...
                # Make x label bigger
                axes[i].set_xlabel("Weekday")

        if self.viz:
            self.savefig(fig, fig_name=f_name, save=False, fig_size=figure_size)
            plt.show()
        else:
            self.savefig(fig, fig_name=f_name, save=True, fig_size=figure_size)

        plt.close()


def plot_ground_truth():
    # Load a config file
    # Use path library to parse the path
    scene_id = 153
    last_week_only = False
    folder = Path(f"generated_data/semistaticsim/test/{scene_id}/0/groundtruth")
    sssd_data = load_sssd(f"generated_data/semistaticsim/test/{scene_id}/0/groundtruth")
    assignments: List[np.ndarray] = []
    timestamps: List[np.ndarray] = []
    for data in sssd_data.get_generator_of_selves():
        assignments.append(data._assignment)
        timestamps.append(data._timestamp)

    assignments = np.concatenate(assignments, axis=0)
    # Make assignments thing format and not one-hot
    assignments = np.argmax(assignments, axis=2)
    timestamps = np.concatenate(timestamps, axis=0)
    pickupables = sssd_data.pickupable_names
    receptacles = sssd_data.receptacle_names

    # Hyperparameters
    plotter = Plotter(exp_name="ground_truth", viz=False, res_path=folder, fig_fmt="png")

    # Plot first pickupable for now
    for pickupable_id in range(len(pickupables)):
        pickupable_name = pickupables[pickupable_id].split("|")[0]
        receptacles_assignments = assignments[:, pickupable_id]
        plotter.plot_observations(
            sampling_times=timestamps,
            assignments=receptacles_assignments,
            receptacles_name=receptacles,
            pickupable_name=pickupable_name,
            location="upper right",
            f_name=f"{pickupable_name}_ground_truth",
            last_week_only=last_week_only,
        )
        print(f"Plotted {pickupable_name}")


if __name__ == "__main__":
    plot_ground_truth()
