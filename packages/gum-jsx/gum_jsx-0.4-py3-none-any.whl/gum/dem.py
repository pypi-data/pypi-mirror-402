# element demos

from .gen import C, V
from . import gen as G

##
## colors
##

GRAY = '#333'

##
## utility functions
##

def linspace(start, stop, num):
    delta = (stop - start) / (num - 1)
    return [ start + i * delta for i in range(num) ]

##
## core elements
##

def demo_gum():
    return G.Frame(
        G.Text('GUM'),
        padding=True,
        rounded=True,
    )

def demo_element():
    Tri = lambda pos0, pos1, pos2, **attr: G.Shape(pos0, pos1, pos2, **attr)
    return Tri((0.5, 0.1), (0.9, 0.9), (0.1, 0.9), fill=GRAY)

def demo_group():
    return G.Group(
        G.Rect(pos=(0.3, 0.3), rad=0.1, spin=15),
        G.Ellipse(pos=(0.7, 0.7), rad=0.1),
    )

## layout elements

def demo_box():
    return G.Frame(
        G.Text('hello!'),
        padding=True,
        rounded=True,
        border_stroke_dasharray=5,
    )

def demo_stack():
    return G.VStack(
        G.Rect(rounded=True, fill=C.blue),
        G.HStack(
            G.Square(rounded=True, fill=C.red),
            G.Square(rounded=True, fill=C.green),
            stack_size=0.5,
            spacing=True,
        ),
        spacing=True,
    )

def demo_grid():
    return G.Frame(
        G.Grid(
            *[
                G.Frame(
                    G.Group(
                        G.Arrow(direc=0, tail=1, pos=(1, 0.5), rad=0.5),
                        aspect=1,
                        spin=th,
                    ),
                    padding=True,
                    rounded=True,
                    fill=True,
                )
                for th in linspace(0, 360, 10)[:9]
            ],
            rows=3,
            spacing=True,
        ),
        padding=True,
        rounded=True,
    )

def demo_points():
    siner = lambda a: (lambda x: C.sin(a*x))
    return G.Plot(
        G.Points((0, 0.5), (0.5, 0), (-0.5, 0), (0, -0.5), size=0.02),
        G.Rect(pos=(0.5, 0.5), rad=0.1),
        G.Circle(pos=(-0.5, -0.5), rad=0.1),
        *[G.SymLine(fy=siner(a)) for a in (0.5, 0.9, 1.5)],
        xlim=(-1, 1),
        ylim=(-1, 1),
        grid=True,
        margin=0.3,
        aspect=1,
        xlabel='time (seconds)',
        ylabel='space (meters)',
        title='Spacetime Vibes',
    )

## shape elements

def demo_rect():
    return G.Rect(pos=(0.25, 0.5), rad=(0.1, 0.2))

def demo_ellipse():
    return G.Group(
        G.Ellipse(pos=(0.3, 0.2), rad=(0.2, 0.1)),
        G.Ellipse(pos=(0.6, 0.6), rad=(0.2, 0.25)),
    )

def demo_line():
    return G.Group(
        G.Line((0.2, 0.2), (0.8, 0.8), stroke=C.blue),
        G.Line((0.3, 0.3), (0.3, 0.7), (0.7, 0.7), (0.7, 0.3), stroke=C.red),
    )

def demo_shape():
    return G.Group(
        G.Shape((0.5, 0.2), (0.8, 0.8), (0.2, 0.8), fill=C.blue, stroke=C.none),
        G.Shape((0.3, 0.3), (0.3, 0.7), (0.7, 0.7), (0.7, 0.3), fill=C.green, stroke=C.none, opacity=0.5),
    )

def demo_spline():
    points = [
        (0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75), (0.50, 0.50)
    ]
    return G.Frame(
        G.Spline(*points, closed=True, stroke=C.blue, fill=GRAY),
        G.Shape(*points, stroke=C.red),
        G.Points(*points, size=0.0075),
        rounded=True,
        margin=True,
    )

## text elements

def demo_text():
    return G.TextFrame(
        G.Text('Hello World! You can mix text and '),
        G.Square(rounded=True, fill=C.blue),
        G.Text(' other elements together.'),
        rounded=True,
        wrap=10,
    )

# NOTE: this doesn't work yet
def demo_latex():
    return G.VStack(
        G.TextFrame(G.Equation('\\int_0^{\\infty} \\exp(-x^2) dx = \\sqrt{\\pi}')),
        G.TextFrame(G.Equation('\\sin^2(\\theta) + \\cos^2(\\theta) = 1')),
        spacing=True,
    )

def demo_titleframe():
    emoji = ['🍇', '🥦', '🍔', '🍉', '🍍', '🌽', '🍩', '🥝', '🍟']
    return G.TitleFrame(
        G.Grid(
            *[
                G.Frame(
                    G.Text(e),
                    aspect=True,
                    rounded=True,
                    fill=True,
                    padding=True,
                )
                for e in emoji
            ],
            rows=3,
            spacing=0.05,
        ),
        title='Fruits & Veggies',
        margin=True,
        padding=True,
        rounded=True,
    )

def demo_slide():
    return G.Slide(
        G.Text('Here\'s a plot of a sine wave below. It has to be the right size to fit in with the figure correctly.'),
        G.Plot(
            G.SymLine(fy=C.sin, stroke=C.blue, stroke_width=2),
            xlim=(0, 2*C.pi),
            ylim=(-1.5, 1.5),
            fill=True,
            grid=True,
            margin=(0.25, 0.05),
            aspect=2,
        ),
        G.Text('It ranges from low to high and has some extra vertical space to allow us to see the full curve.'),
        title='The Art of the Sine Wave',
    )

## symbolic elements

def demo_sympoints():
    pill = lambda x, y: G.Rect(fill=C.white, rounded=0.3, aspect=2, spin=-C.r2d*C.atan(C.cos(x)))
    return G.Plot(
        G.SymLine(fy=C.sin, stroke=C.blue, stroke_width=2),
        G.SymPoints(fy=C.sin, size=0.125, shape=pill, N=11),
        xlim=(0, 2*C.pi),
        ylim=(-1.5, 1.5),
        fill=GRAY,
        grid=True,
        margin=0.25,
        aspect='auto',
    )

def demo_symline():
    return G.Plot(
        G.SymLine(fy=C.sin, stroke=C.red, stroke_width=2),
        G.SymLine(fy=lambda x: C.sin(x) + 0.2*C.sin(5*x), stroke=C.blue, stroke_width=2),
        xlim=(0, 2*C.pi),
        ylim=(-1.5, 1.5),
        aspect=C.phi,
        margin=0.2,
        grid=True,
    )

def demo_symshape():
    rad = lambda t: 1 - 0.3 * C.cos(2.5 * t)**2
    fx = lambda t: rad(t) * C.sin(t)
    fy = lambda t: rad(t) * C.cos(t)
    return G.Frame(
        G.SymShape(
            fx=fx, fy=fy, tlim=(0, 2*C.pi),
            N=200, aspect=1, fill=C.blue
        ),
        rounded=True,
        padding=True,
        margin=True,
    )

def demo_symspline():
    decay = lambda x: C.exp(-x/2) * C.sin(3*x)
    return G.Plot(
        G.SymLine(fy=decay, N=200, opacity=0.25),
        G.SymSpline(fy=decay, N=10, stroke=C.blue, stroke_width=2),
        G.SymPoints(fy=decay, N=10, size=0.05, fill=C.red),
        xlim=(0, 2*C.pi),
        ylim=(-1, 1),
        aspect=C.phi,
        margin=0.15,
        grid=True,
    )

def demo_symfill():
    decay = lambda x: C.exp(-0.1*x) * C.sin(x)
    return G.Graph(
        G.SymFill(fy1=decay, fy2=0, fill=C.blue, fill_opacity=0.5, N=250),
        G.SymLine(fy=decay, N=250),
        xlim=(0, 6*C.pi),
        ylim=(-1, 1),
        aspect=C.phi,
    )

## plotting elements

def demo_graph():
    square = lambda x, y: G.Square(rounded=True, spin=C.r2d*x)
    return G.Graph(
        G.SymPoints(fy=C.sin, xlim=(0, 2*C.pi), size=0.5, shape=square, N=150),
        ylim=(-1.5, 1.5),
        padding=0.2,
        aspect=2,
    )

def demo_plot():
    xticks = [(x*C.pi, f'{x:.2g} π') for x in linspace(0, 2, 6)[1:]]
    return G.Plot(
        G.SymLine(fy=lambda x: -C.sin(x), xlim=(0, 2*C.pi)),
        aspect=C.phi,
        xanchor=0,
        xticks=xticks,
        grid=True,
        xlabel='phase',
        ylabel='amplitude',
        title='Inverted Sine Wave',
        xaxis_tick_side='both',
        grid_stroke_dasharray=3,
        margin=0.25,
    )

def demo_axis():
    emoji = ['🗻', '🚀', '🐳', '🍉', '🍩']
    ticks = C.zip(C.linspace(0, 1, len(emoji)), emoji)
    return G.Box(
        G.HAxis(
            aspect=10,
            ticks=ticks,
            tick_side='outer',
            label_size=1,
        ),
        padding=(0.5, 1),
    )

def demo_barplot():
    return G.BarPlot(
        G.Bar(label='A', size=3, fill=C.red),
        G.Bar(label='B', size=8.5, fill=C.blue),
        G.Bar(label='C', size=6.5, fill=C.green),
        ylim=[0, 10],
        yticks=6,
        title='Example BarPlot',
        xlabel='Category',
        ylabel='Value',
        bar_rounded=True,
        bar_border=0,
        margin=0.25,
    )

## network elements

def demo_node():
    return G.Network(
        G.Node('Hello', id='hello', pos=(0.25, 0.25)),
        G.Node('World!', id='world', pos=(0.75, 0.75)),
        G.Edge(from_='hello', to='world'),
        node_fill=GRAY,
    )

def demo_edge():
    return G.Network(
        G.Node('Hello', id='hello', pos=(0.25, 0.25)),
        G.Node('World!', id='world', pos=(0.75, 0.75)),
        G.Edge(from_='hello', to='world', from_fill=C.red, to_fill=C.blue),
        node_fill=GRAY,
        edge_arrow=True,
    )

def demo_network():
    return G.Network(
        G.Node('Hello world', id='hello', pos=(0.25, 0.5), wrap=3),
        G.Node('This is a test of wrapping capabilities', id='test', pos=(0.75, 0.25), wrap=6),
        G.Node(G.Ellipse(aspect=1.5, fill=C.blue), id='ball', pos=(0.75, 0.75)),
        G.Edge(from_='hello', to='test'),
        G.Edge(from_='hello', to='ball', from_dir='s', curve=3),
        aspect=1.5,
        node_yrad=0.15,
        node_rounded=True,
        node_fill=GRAY,
        edge_arrow_fill=C.white,
    )

## functions

def demo_math():
    return G.Frame(
        G.Plot(
            G.SymLine(fy=lambda x: C.exp(C.sin(x))),
            aspect=C.phi,
            xlim=(0, 2*C.pi),
            ylim=(0, 3),
            grid=True,
        ),
        margin=0.15,
    )

def demo_arrays():
    emoji = ['🗻', '🚀', '🐋', '🍉', '🍩']
    return G.Plot(
        *[G.Text(e, pos=(i+1, i+1), rad=0.4) for i, e in enumerate(emoji)],
        xlim=[0, 6],
        ylim=[0, 6],
        xticks=7,
        yticks=7,
        margin=0.15,
    )

def demo_colors():
    func = lambda x: -C.sin(x)
    pal = V.pal(C.palette(C.blue, C.red, (-1, 1)))
    size_func = lambda x, y: 0.1 * (1 + C.abs(y)) / 2
    shape_func = lambda x, y: G.Circle(fill=C.pal(y))
    xticks = [(x*C.pi, f'{x:.2g} π') for x in linspace(0, 2, 6)[1:]]
    plot = G.Plot(
        G.SymLine(fy=func),
        G.SymPoints(fy=func, size=size_func, shape=shape_func, N=21),
        xlim=(0, 2*C.pi),
        ylim=(-1, 1),
        aspect=1.5,
        xanchor=0,
        xaxis_tick_side='both',
        xticks=xticks,
        grid=True,
        xlabel='phase',
        ylabel='amplitude',
        title='Inverted Sine Wave',
        margin=0.25,
    )
    return G.Gum(plot, vars=[pal])

DEMOS = {
    'gum': demo_gum,
    'element': demo_element,
    'group': demo_group,
    'box': demo_box,
    'stack': demo_stack,
    'grid': demo_grid,
    'points': demo_points,
    'rect': demo_rect,
    'ellipse': demo_ellipse,
    'line': demo_line,
    'shape': demo_shape,
    'spline': demo_spline,
    'text': demo_text,
    'latex': demo_latex,
    'titleframe': demo_titleframe,
    'slide': demo_slide,
    'sympoints': demo_sympoints,
    'symline': demo_symline,
    'symshape': demo_symshape,
    'symspline': demo_symspline,
    'symfill': demo_symfill,
    'graph': demo_graph,
    'plot': demo_plot,
    'axis': demo_axis,
    'barplot': demo_barplot,
    'node': demo_node,
    'edge': demo_edge,
    'network': demo_network,
    'math': demo_math,
    'arrays': demo_arrays,
    'colors': demo_colors,
}

def demo(name):
    func = DEMOS[name]
    return func()
