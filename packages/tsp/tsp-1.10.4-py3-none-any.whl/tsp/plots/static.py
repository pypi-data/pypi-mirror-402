import numpy as np
import warnings

import matplotlib.dates as mdates
import matplotlib.cm as cm
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
from typing import Optional

try:
    from scipy.interpolate import griddata
except ModuleNotFoundError:
    warnings.warn("Missing scipy module. Some functionality will be limited.")

from typing import Union

import tsp


def trumpet_curve(depth, t_max, t_min, t_mean, 
                  title:str="", max_depth:Optional[float]=None, 
                  t_units:str=u'\N{DEGREE SIGN} C', d_units:str="m",
                  data_completeness=None,
                  min_completeness:Optional[float]=None) -> Figure:
    """Plot a trumpet curve

    The function returns a matplotlib Figure object. To show the figure, you must call the `show()` method.

    Parameters
    ----------
    depth : numpy.ndarray
        A d-length array of depths at which temperature values are 
    t_max : numpy.ndarray
        A d-length array of temperature values representing the maximum temperatures over the period at each of the depths.
    t_min : numpy.ndarray
        A d-length array of temperature values representing the minimum temperatures over the period at each of the depths.
    t_mean : str
       A d-length array of temperature values representing the mean temperatures over the period at each of the depths.
    title : str, optional
        A title for the figure, by default ""
    max_depth : float, optional
        If provided, limits the maximum y-axis extent of the plot, by default None
    t_units : unicode, optional
        Units for the x-axis (assumed to be temperature), by default u'\N{DEGREE SIGN} C'
    d_units : str, optional
        Units for the y axis (depth), by default "m"
    data_completeness : numpy.ndarray
        A d-length array of representing data completeness as a fraction (e.g. 0 to 1) for each of the averaging periods ()
    min_completeness : float
        Minimum data completeness to be included in the temperature envelope

    Returns
    -------
    Figure
        A matplotlib Figure. Note that to show the figure you must call the `show()` method or `matplotlib.pyplot.show()`.

    Raises
    ------
    ValueError
        _description_
    """
    ## Sanity checks and data 
    if data_completeness is None:
        data_completeness = np.ones_like(depth)
    if min_completeness is None:
        min_completeness = 0.001

    if not len(depth) == len(t_max) == len(t_min) == len(t_mean) == len(data_completeness):
        raise ValueError("Length of input arrays must be equal")
    
    depth = - np.abs(depth)
    
    ## Create figure
    fig, ax1 = plt.subplots()

    ## Create artists
    # TODO:  https://stackoverflow.com/questions/45176584/dotted-lines-instead-of-a-missing-value-in-matplotlib
    m = np.where(data_completeness >= min_completeness, True, False)
    if m.any():
        line_max = ax1.plot(t_max[m], depth[m], color='red', gid="ln-max-temperature")
        line_min = ax1.plot(t_min[m], depth[m], color='blue', gid="ln-min-temperature")
        line_mean = ax1.plot(t_mean[m], depth[m], color='black', gid="ln-mean-temperature")

    alphas = np.where((data_completeness / min_completeness) < 1, 0.1 + (0.7 * data_completeness / min_completeness), 1)

    marker_max = ax1.scatter(t_max, depth, marker='.', c=alpha([1,0,0], alphas), gid="pt-max-temperature")
    marker_min = ax1.scatter(t_min, depth, marker='.', c=alpha([0,0,1], alphas), gid="pt-min-temperature")
    marker_mean = ax1.scatter(t_mean, depth, marker='.', c=alpha([0,0,0], alphas), gid="pt-mean-temperature")

    surface = ax1.hlines(y=0.0, xmin=-100, xmax=100, linewidth=0.5, linestyles='dotted', color='grey')
    zero = ax1.vlines(x=0.0, ymin=-100, ymax=100, linewidth=0.5, linestyles='dotted', color='grey')

     ## Set axis properties
    ax1.set_ybound(upper=1, lower=min(depth) - 3)
    
    if max_depth:
        ax1.set_ybound(lower=-abs(max_depth))

    ax1.set_xbound(lower=min(t_min) - 3, upper=max(t_max) + 3)

    ## Set axis labels
    ax1.set_xlabel(f"Temperature [{t_units}]")
    ax1.set_ylabel(f"Depth [{d_units}]")
    ax1.set_title(title)

    return fig


def colour_contour(depths, times, values, title="", colours: "Union[str, list]"='symmetric', contour:list=[], label_contour=False, max_depth=None, gap_fill=False, 
                   d_units="m", **kwargs) -> Figure:
    """Create a colour-contour plot. 

    The x-axis is time and the y-axis is depth. Data values are interpolated and coloured.

    Parameters
    ----------
    depths : numpy.ndarray
        A d-length array of depths at which measurements are collected.
    times : numpy.ndarray
        A t-length array of python datetimes at which measurements are collected
    values : numpy.ndarray
        An array with shape (t,d) of values at each depth-time coordinate
    title : str, optional
        A title for the figure, by default ""
    colours : Union[str, list], optional
        Either a list of colours to be used for the colour bar, or one of:
        * **symmetric**: ensure colour switch is centered at 0C
        * **dynamic**: Maximize dynamic range
        * **basic**: distinguish unfrozen, warm (>-2C) and 
        ,by default 'symmetric'
    contour : list, optional
        A list of float values. If provided, draw contours at each of those values, by default []
    label_contour : bool, optional
        Whether or not to label contour lines. Ignored if `contour` is empty, by default False
    max_depth : float, optional
        If provided, limits the maximum y-axis extent of the plot, by default None
    gap_fill : bool, optional
        _description_, by default False
    d_units : str, optional
        Units for the y axis (depth), by default "m"

    Returns
    -------
    Figure
        A matplotlib Figure. Note that to show the figure you must call the `show()` method or `matplotlib.pyplot.show()`.
    """
    t = tsp.TSP(times, depths, values)

    # Extract x, y and z (array) values
    X = t.times
    Y = -abs(t.depths)

    if gap_fill:
        try:
            smoothed = griddata(points = np.stack([t.long.dropna()['time'].values.astype(float),
                                                t.long.dropna()['depth'].values]).transpose(),
                                values = t.long.dropna()['temperature_in_ground'].values,  
                                xi = np.stack([t.long['time'].values.astype(float),
                                                t.long['depth'].values]).transpose(),
                                rescale=True, method='linear')
        except NameError:
            warnings.warn("Missing scipy library. Could not do gap filling.")
            gap_fill = False
            Z = np.array(t.wide.drop('time', axis=1)).transpose() 

        Z = smoothed.reshape(len(depths), len(values))
    
    else:
        Z = np.array(t.wide.drop('time', axis=1)).transpose()

    # Set up plot
    fig, ax1 = plt.subplots()

    clev = contour_levels(Z, colours, step=1)

    # Add data
    if colours == 'basic':
        co = ["darkblue", "lightblue", "lightgreen", "lightred"]
        cmap = None
    else: 
        co = None
        cmap = plt.cm.coolwarm

    cs = ax1.contourf(X, Y, Z, levels=clev, cmap=cmap, colors=co)
    fig.colorbar(cs, ticks = np.arange(-25,25,5))

    if len(contour) > 0:
        cs2 = ax1.contour(X, Y, Z, levels = contour, colors='k', linewidths = 1)
        if label_contour:
            plt.clabel(cs2, fontsize=8, inline=1, fmt="%1.0f")

    # Set axis properties
    if max_depth:
        ax1.set_ybound(lower=-abs(max_depth))

    ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
    fig.autofmt_xdate()
    plt.subplots_adjust(bottom = 0.2, top = 0.95, left = 0.2, right = 0.95)

    # Set axis labels
    ax1.set_xlabel('Time')
    ax1.set_ylabel(f"Depth [{d_units}]")
    ax1.set_title(title)
    

    return fig


def time_series(depths, times, values, title='', d_units='m', t_units=u'\N{DEGREE SIGN} C', legend=True) -> Figure:
    """Create a time-series plot

    Using time as the X axis and data values as the y axis. Depths are plotted as their own lines.

    Parameters
    ----------
    depths : numpy.ndarray
        1-d list or array of datetimes with length d.
    times : numpy.ndarray
        1-d list or array of datetimes with length t.
    values : array
        An array of data values with shape (t,d). 
    title : str, optional
        A title for the plot, by default ''
    d_units : str, optional
        Units of the depths variable, by default 'm'
    t_units : str, optional
        Units of the temperature variable, by default u'\N{DEGREE SIGN} C'

    Returns
    -------
    Figure
        A matplotlib Figure. Note that to show the figure you must call the `show()` method or `matplotlib.pyplot.show()`.
    """

    # Set up plot
    fig, ax = plt.subplots()

    # Add data elements
    lines = []
    for i, d in enumerate(depths):
        line_i, = ax.plot(times, values[:,i], lw=1, label=f'{d} {d_units}')
        lines.append(line_i)

    if legend:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        fig.subplots_adjust(right=0.8) # shrink plot to make space

        leg = ax.legend(loc='center left', bbox_to_anchor=(1.04, 0.5), fancybox=True, shadow=True)

        lined = {}  # Will map legend lines to original lines.
        for legline, label, origline in zip(leg.get_lines(), leg.get_texts(), lines):
            legline.set_picker(True)  # Enable picking on the legend line.
            label.set_picker(True)  # Enable picking on the legend label.
            lined[legline] = [origline, [label]]
            lined[label] = [origline, [legline]]
        
        on_pick = create_legend_picker(fig, lined)
        on_tilde = create_tilde_toggle(fig, lined)
        fig.canvas.mpl_connect('pick_event', on_pick)
        fig.canvas.mpl_connect('key_press_event', on_tilde)

    zero = ax.hlines(y=0.0, xmin=min(times), xmax=max(times), linewidth=0.5, linestyles='dotted', color='grey')
    # Set axis properties

    # Set axis labels
    ax.set_xlabel('Time')
    ax.set_ylabel(f"Temperature [{t_units}]")
    ax.set_title(title)

    return fig


def profile_evolution(depths, times, values, P:int=100, n:int=10):
    """ Plot sample of temperature profiles over time
    
    Parameters
    ----------
    depths : array-like
        Depths of the temperature profile
    times : array-like
        Times of the temperature profile
    values : array-like
        Temperature values of the temperature profile
    P : int, optional
        Percentage of the time series to plot, starting from the end, by default 100
    n : int, optional  
        Number of profiles to plot, evenly spaced over time period to plot, by default 10
    """
    cmap = cm.get_cmap('winter')
    clist = cmap(np.arange(0,1,1/10))

    fig, ax = plt.subplots()

    p = 100 - P
    lastP = (p*(len(times) // 100))

    true_depths = -np.abs(depths)
    plot_times = times[lastP:][::len(times[lastP:]) // n][:n]
    plot_temps = values[lastP:,][::len(times[lastP:]) // n, :][:n,]
    
    for i in range(n):
        ax.plot(plot_temps[i,:], true_depths, color=clist[i],
                alpha=0.5, label=f"{plot_times[i].year}")
    
    ax.legend(fontsize="8")
    ax.vlines(0, ymin=min(true_depths), ymax=max(true_depths), linewidth=0.5, color='black')

    return fig


def alpha(rgb, alpha):
    rgb = np.atleast_1d(rgb)
    alpha = np.atleast_1d(alpha)
    rgba = np.zeros((len(alpha), 4))
    rgba[:,3] = alpha
    rgba[:,0:3] = rgb
    return rgba
    

def contour_levels(data, levels: "Union[str,list]", step=1) -> np.ndarray:
    if levels == "dynamic":
        return np.arange(np.nanmin(data), np.nanmax(data), step)
    
    elif levels == "symmetric":
        return np.arange(min(np.nanmin(data), -np.nanmax(data) + 1),
                         max(-np.nanmin(data) - 1, np.nanmax(data)), step)
    elif levels == 'basic':
        return np.array([min(-5, np.nanmin(data)), -2, 0, max(1, np.nanmax(data))])
    else:
        try:
            lev = np.array(levels, dtype='float')
            return lev
        except Exception:
            raise TypeError("Contour levels not properly specified")


def create_legend_picker(fig, lined) -> object:
    
    def on_pick(event):
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        legline = event.artist
        origline = lined[legline][0]
        other_toggles = lined[legline][1]
        visible = not origline.get_visible()
        origline.set_visible(visible)
        # Change the alpha on the line in the legend so we can see what lines
        # have been toggled.
        legline.set_alpha(1.0 if visible else 0.2)
        for t in other_toggles:
            t.set_alpha(1.0 if visible else 0.2)
        fig.canvas.draw()
    
    return on_pick

def create_tilde_toggle(fig, lined) -> object:

    def on_click(event):
        # on the "`" keypress, toggle lines off if any are on.
        # on the "`" keypress, toggle lines on if all are off.
        if event.key == '`':
            visible = False
            for togglable, [origline, other_toggles] in lined.items():
                visible = visible or origline.get_visible()
            for togglable, [origline, other_toggles] in lined.items():
                origline.set_visible(not visible)
                togglable.set_alpha(1.0 if not visible else 0.2)
                for t in other_toggles:
                    t.set_alpha(1.0 if not visible else 0.2)
            fig.canvas.draw()
    
    return on_click

def _plot_overlay(fig, t):
    version = tsp.__version__
    site_id = t.site_id if t.site_id else ""
    latitude = f"{t.latitude:.4f}" if t.latitude else ""
    longitude = f"{t.longitude:.4f}" if t.longitude else ""
    file = t.metadata.get('_source_file', '') if t.metadata else ""
    SITE = f"Site: {site_id}" if site_id else None
    COORDS = f"Coords: ({latitude}, {longitude})" if latitude and longitude else None
    info = [s for s in [SITE, COORDS] if s]
    FILE = f"File: {file}" if file else ""
    overlay_text = f'TSP v{version} \n  {" | ".join(info)} \n {FILE}'
    fig.text(0.95, 0.01, overlay_text, ha='right', va='bottom', fontsize=8, color='gray', alpha=0.5)
    return fig