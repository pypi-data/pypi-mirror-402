# gum generation

from .utl import Var, Con, Element, Group, DataGroup, RawGroup, DisplayMixin

##
## gum constructors
##

class VarGen:
    def __getattr__(self, name):
        def generator(value):
            return Var(name, value)
        return generator

class ConGen:
    def __getattr__(self, name):
        return Con(name)

    def __call__(self, value):
        return Con(value)

# singleton instances
V = VarGen()
C = ConGen()

##
## context elements
##

class Context(Element):
    def __init__(self, **args):
        super().__init__('Context', True, **args)

## layout elements

class Box(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='Box', **args)

class Frame(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='Frame', **args)

class Stack(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='Stack', **args)

class HStack(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='HStack', **args)

class VStack(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='VStack', **args)

class Grid(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='Grid', **args)

class Points(DataGroup):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Points', **kwargs)

## shape elements

class Rect(Element):
    def __init__(self, **kwargs):
        super().__init__('Rect', True, **kwargs)

class Ellipse(Element):
    def __init__(self, **kwargs):
        super().__init__('Ellipse', True, **kwargs)

class Line(DataGroup):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Line', **kwargs)

class Shape(DataGroup):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Shape', **kwargs)

class Spline(DataGroup):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Spline', **kwargs)

class Square(Element):
    def __init__(self, **kwargs):
        super().__init__('Square', True, **kwargs)

class Circle(Element):
    def __init__(self, **kwargs):
        super().__init__('Circle', True, **kwargs)

class HLine(Element):
    def __init__(self, **kwargs):
        super().__init__('HLine', True, **kwargs)

class VLine(Element):
    def __init__(self, **kwargs):
        super().__init__('VLine', True, **kwargs)

## text elements

class Text(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Text', **kwargs)

class TextFrame(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='TextFrame', **kwargs)

class Latex(RawGroup):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Latex', **kwargs)

class Equation(RawGroup):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Equation', **kwargs)

## data elements

class SymPoints(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='SymPoints', **kwargs)

class SymLine(Element):
    def __init__(self, *children, **kwargs):
        super().__init__('SymLine', True, **kwargs)

class SymShape(Element):
    def __init__(self, **kwargs):
        super().__init__('SymShape', True, **kwargs)

class SymSpline(Element):
    def __init__(self, **kwargs):
        super().__init__('SymSpline', True, **kwargs)

class SymFill(Element):
    def __init__(self, **kwargs):
        super().__init__('SymFill', True, **kwargs)

class SymField(Element):
    def __init__(self, **kwargs):
        super().__init__('SymField', True, **kwargs)

## graph elements

class Graph(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Graph', **kwargs)

class Plot(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='Plot', **args)

class Axis(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Axis', **kwargs)

class HAxis(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='HAxis', **kwargs)

class VAxis(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='VAxis', **kwargs)

##
## bar elements
##

class Bar(Element):
    def __init__(self, **kwargs):
        super().__init__('Bar', True, **kwargs)

class VBar(Element):
    def __init__(self, **kwargs):
        super().__init__('VBar', True, **kwargs)

class HBar(Element):
    def __init__(self, **kwargs):
        super().__init__('HBar', True, **kwargs)

class BarPlot(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='BarPlot', **args)

## network elements

class ArrowHead(Element):
    def __init__(self, **kwargs):
        super().__init__('ArrowHead', True, **kwargs)

class Arrow(Element):
    def __init__(self, **kwargs):
        super().__init__('Arrow', True, **kwargs)

class ArrowSpline(Element):
    def __init__(self, **kwargs):
        super().__init__('ArrowSpline', True, **kwargs)

class Node(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Node', **kwargs)

class Edge(Element):
    def __init__(self, **kwargs):
        if 'from_' in kwargs:
            kwargs['from'] = kwargs.pop('from_')
        super().__init__('Edge', True, **kwargs)

class Network(Group):
    def __init__(self, *children, **kwargs):
        super().__init__(*children, tag='Network', **kwargs)

## container elements

class TitleFrame(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='TitleFrame', **args)

class Slide(Group):
    def __init__(self, *children, **args):
        super().__init__(*children, tag='Slide', **args)

##
## dataframe notion
##

def ensure_var(var, name=None):
    import numpy as np
    import pandas as pd
    if isinstance(var, (np.ndarray, list, tuple)):
        var = pd.Series(var)
    elif isinstance(var, pd.Index):
        var = var.to_series()
    if isinstance(var, pd.Series):
        var = Var.from_series(var, name=name)
    elif not isinstance(var, Var):
        raise ValueError(f'Unsupported type: {type(var)}')
    return var

class GumData:
    def __init__(self, data, index=None):
        self.index = ensure_var(index, name='index')
        self._data = [ ensure_var(v, name=f'value_{i}') for i, v in enumerate(data) ]

    @classmethod
    def from_frame(cls, frame):
        data = [ frame[col] for col in frame ]
        return cls(data, index=frame.index)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, name):
        return self._data[name]

    def __setitem__(self, name, value):
        self._data[name] = ensure_var(value, name=name)

    def define(self):
        return '\n'.join([ v.define() for v in [ self.index, *self._data ] ])

##
## top level
##

class Gum(DisplayMixin):
    def __init__(self, cont, vars=None):
        if vars is None:
            vars = []
        elif not isinstance(vars, (tuple, list)):
            vars = [ vars ]
        self.vars = vars
        self.content = cont

    def __str__(self):
        header = '\n'.join([ v.define() for v in self.vars ])
        if len(header) > 0:
            return f'{header}\n\nreturn {self.content}'
        else:
            return str(self.content)
