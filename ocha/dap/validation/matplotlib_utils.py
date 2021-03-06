"""
Various utilities for working with matplotlib
"""
import matplotlib as mpl

# recommended palette in "Show Me The Numbers" for plot lines
SMTN_PALETTE_RGB =\
    [
        (0.30078125, 0.30078125, 0.30078125),  # medium-dark gray
        (0.6953125, 0.4609375, 0.6953125),     # medium purple
        (0.9765625, 0.640625, 0.2265625),      # creamsicle
        (0.36328125, 0.64453125, 0.8515625),   # slate blue
        (0.375, 0.73828125, 0.40625),          # medium green
        (0.6953125, 0.56640625, 0.1875),       # mustard brown
        (0.94140625, 0.484375, 0.6875),        # pink
        (0.94140625, 0.34375, 0.328125),       # medium red
    ]

# trying to not use any colors with associated qualities, e.g. "red = bad", "green = good"
REFERENCE_PALETTE_RGB =\
    [
        (0.2, 0.2, 0.7),  # dark blue
        (0.7, 0.2, 0.7),  # purple
        (0.2, 0.7, 0.7),  # cyan
    ]


DARK_GRAY = '#282828'
MEDIUM_GRAY = '#666666'
LIGHT_GRAY = '#A0A0A0'

DESIRED_SPINES = ['bottom', 'left']


def prettyplotlib_style(axes, include_legend=False):
    """
    Make similar output to "prettyplotlib", but do things manually rather than use a library.
    """
    for spine in axes.spines:
        if spine in DESIRED_SPINES:
            axes.spines[spine].set_linewidth(0.5)  # this is really nice
            axes.spines[spine].set_color(DARK_GRAY)
        else:
            axes.spines[spine].set_color('none')   # this is nice

    # Hmm, how to do this dynamically to match DESIRED_SPINES?
    axes.xaxis.set_ticks_position('bottom')
    axes.yaxis.set_ticks_position('left')

    # cleaner to not have a grid
    axes.grid(False)

    # kind of subtle
    axes.xaxis.label.set_color(DARK_GRAY)
    axes.yaxis.label.set_color(DARK_GRAY)
    axes.title.set_color(DARK_GRAY)

    if include_legend:
        legend = axes.legend(loc='best', frameon=False, fontsize=(mpl.rcParams['font.size'] - 1))
        for text in legend.texts:
            text.set_color(DARK_GRAY)


def wolfram_style(axes):
    """
    Style plot similarly to some of the examples on Stephen Wolfram's blog:
      - light gray bounding box, but dark ticks
      - legend outside box
      - title inside box, in medium gray
    """
    for spine in axes.spines:
        axes.spines[spine].set_linewidth(0.5)  # this is really nice
        axes.spines[spine].set_color(LIGHT_GRAY)

    # only have ticks on bottom and left
    axes.xaxis.set_ticks_position('bottom')
    axes.yaxis.set_ticks_position('left')

    # cleaner to not have a grid
    axes.grid(False)

    # kind of subtle
    axes.xaxis.label.set_color(DARK_GRAY)
    axes.yaxis.label.set_color(DARK_GRAY)

    # title inside box - unfortunately only works for shorter titles
    axes.title.set_position((0.5, 0.85))
    axes.title.set_color(MEDIUM_GRAY)


def add_figure_legend(figure):
    # find axes with most lines
    axes_with_most_lines = None

    # probably a "tighter" way to do this in python than is done here
    for axes in figure.get_axes():
        if axes_with_most_lines is None:
            axes_with_most_lines = axes
            continue

        if len(axes.get_lines()) > len(axes_with_most_lines.get_lines()):
            axes_with_most_lines = axes

    handles, labels = axes_with_most_lines.get_legend_handles_labels()
    figure.legend(handles, labels, 'lower center', frameon=False, ncol=len(axes_with_most_lines.get_lines()))
