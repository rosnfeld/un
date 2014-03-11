"""
Various utilities for working with matplotlib
"""

# recommended palette in "Show Me The Numbers" for plot lines
COLOR_PALETTE_RGBA =\
    [
        (0.30078125, 0.30078125, 0.30078125),  # medium-dark gray
        (0.6953125, 0.4609375, 0.6953125),     # medium purple
        (0.9765625, 0.640625, 0.2265625),      # creamsicle
        (0.94140625, 0.484375, 0.6875),        # pink
        (0.36328125, 0.64453125, 0.8515625),   # slate blue
        (0.375, 0.73828125, 0.40625),          # medium green
        (0.94140625, 0.34375, 0.328125),       # medium red
        (0.6953125, 0.56640625, 0.1875)        # mustard brown
    ]

DARK_GRAY = '#282828'

DESIRED_SPINES = ['bottom', 'left']


def prettyplotlib_style(figure):
    """
    Make similar output to "prettyplotlib", but do things manually rather than use a library.
    """
    ax = figure.gca()

    for spine in ax.spines:
        if spine in DESIRED_SPINES:
            ax.spines[spine].set_linewidth(0.5)  # this is really nice
            ax.spines[spine].set_color(DARK_GRAY)
        else:
            ax.spines[spine].set_color('none')   # this is nice

    # Hmm, how to do this dynamically to match DESIRED_SPINES?
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    # cleaner to not have a grid
    ax.grid(False)

    # kind of subtle
    ax.xaxis.label.set_color(DARK_GRAY)
    ax.yaxis.label.set_color(DARK_GRAY)
    ax.title.set_color(DARK_GRAY)

    # fix up the legend
    legend = ax.legend(loc='best', frameon=False)
    for text in legend.texts:
        text.set_fontsize(11)
        text.set_color(DARK_GRAY)
