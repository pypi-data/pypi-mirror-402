# gum visualization

from itertools import cycle

from .gen import C, GumData, Gum, SymPoints, SymLine, SymSpline, Plot, BarPlot, VBar
from .utl import prefix_split

##
## themes
##

DEFAULT_BASE = {
    'aspect': 2,
    'margin': 0.15,
}

DEFAULT_PLOT = {
    **DEFAULT_BASE,
    'grid': True,
    'line_stroke_width': 2,
}

DEFAULT_BARS = {
    **DEFAULT_BASE,
    'bar_border': 0,
    'bar_rounded': (0.1, 0.1, 0, 0),
    'bar_fill': C.blue,
}

COLORS = [
    C.blue,
    C.green,
    C.red,
    C.yellow,
    C.purple,
    C.orange,
]

##
## plotting interface
##

def test_data(which='brown', T=500, L=3, N=20, K1=1, K2=10):
    import numpy as np
    import pandas as pd
    if which == 'trig':
        df = pd.DataFrame({ 'theta': np.linspace(0, 2 * np.pi, 100) })
        return df.assign(sin=np.sin(df.theta), cos=np.cos(df.theta)).set_index('theta')
    elif which == 'brown':
        return pd.DataFrame({
            f'stock_{i}': np.random.randn(T).cumsum() / np.sqrt(T) for i in range(L)
        })
    elif which == 'bars':
        codes = np.random.randint(K1, K2, N)
        return pd.Series({ chr(65+c): v for c, v in enumerate(codes) }, name='value')
    else:
        raise ValueError(f'Unknown test data: {which}')

def ensure_series(data):
    import numpy as np
    import pandas as pd
    if isinstance(data, (np.ndarray, list, tuple, dict)):
        data = pd.Series(data, name='value')
    if not isinstance(data, pd.Series):
        raise ValueError(f'Unsupported type: {type(data)}')
    return data

def ensure_frame(data):
    import numpy as np
    import pandas as pd
    if isinstance(data, (np.ndarray, list, tuple)):
        data = pd.DataFrame({ 'value': data })
    elif isinstance(data, dict):
        data = pd.DataFrame({ k: ensure_series(v) for k, v in data.items() })
    elif isinstance(data, pd.Series):
        data = data.to_frame()
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f'Unsupported type: {type(data)}')
    return data

def lines(frame, spline=False, **kwargs):
    # collect arguments
    args = { **DEFAULT_PLOT, **kwargs }
    line_args, plot_args = prefix_split('line', args)

    # convert to dataframe
    frame = ensure_frame(frame)
    data = GumData.from_frame(frame)

    # get maker class
    Maker = SymSpline if spline else SymLine

    # data plotters
    lines = [
        Maker(xvals=data.index, yvals=v, **{'stroke': c, **line_args})
        for v, c in zip(data, cycle(COLORS))
    ]

    # generate svg code
    plot = Plot(*lines, **plot_args)
    return Gum(plot, vars=data)

def points(frame, shape=None, **kwargs):
    # collect arguments
    args = { **DEFAULT_PLOT, **kwargs }
    point_args, plot_args = prefix_split('point', args)

    # convert to dataframe
    frame = ensure_frame(frame)
    data = GumData.from_frame(frame)

    # data plotters
    points = [
        SymPoints(xvals=data.index, yvals=v, shape=shape, **{'stroke': c, 'fill': c, **point_args})
        for v, c in zip(data, cycle(COLORS))
    ]

    # generate svg code
    plot = Plot(*points, **plot_args)
    return Gum(plot, vars=data)

def bars(series, **kwargs):
    # collect arguments
    args = { **DEFAULT_BARS, **kwargs }
    bar_args, plot_args = prefix_split('bar', args)

    # convert to series
    series = ensure_series(series)

    # generate svg code
    bars = [ VBar(label=k, size=v, **bar_args) for k, v in series.items() ]
    return BarPlot(*bars, **plot_args)
