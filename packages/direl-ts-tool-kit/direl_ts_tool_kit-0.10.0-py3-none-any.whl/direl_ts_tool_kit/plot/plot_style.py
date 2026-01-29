import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D


plt.style.use("fast")

plt.rc("figure", autolayout=True, figsize=(12, 5))

plt.rc(
    "axes",
    labelweight="bold",
    labelsize=15,
    titleweight="bold",
    titlesize=14,
    titlepad=10,
    facecolor="white",
)

plt.rc("xtick", labelsize=15)
plt.rc("ytick", labelsize=15)
plt.rc("legend", fontsize=10)

plot_params = {
    "color": "0.75",
    "style": ".-",
    "markeredgecolor": "0.25",
    "markerfacecolor": "0.25",
    "legend": False,
}


paper_colors = {
    "BLUE_LINES": "#396AB1",
    "ORANGE_LINES": "#DA7C30",
    "GREEN_LINES": "#3E9651",
    "RED_LINES": "#CC2529",
    "GRAY_LINES": "#535154",
    "PURPLE_LINES": "#6B4C9A",
    "MAROON_LINES": "#922428",
    "GOLD_LINES": "#948B3D",
    "BLUE_BARS": "#7293CB",
    "ORANGE_BARS": "#E1974C",
    "GREEN_BARS": "#84BA5B",
    "RED_BARS": "#D35E60",
    "GRAY_BARS": "#808585",
    "PURPLE_BARS": "#90679D",
    "MAROON_BARS": "#AB6857",
    "GOLD_BARS": "#CCC210",
}
