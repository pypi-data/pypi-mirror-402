""" Module with end user functions """

from pqthreads.examples import window
from pqthreads import refs
from pqthreads import containers
from pqthreads import decorator


class FigureWorkerException(Exception):
    """ Exception for FigureWorker """


# Setup worker side
class FigureWorker(containers.WorkerItem):
    """ Worker thread figure to control FigureWindow on the GUI thread"""
    factory = containers.WorkerItem.get_factory()
    raise_window = factory.method()
    change_title = factory.method()
    title = factory.attribute()
    raise_exception = factory.method()

    def raise_worker_exception(self):
        """ Method to raise custom exception for testing purposes """
        raise FigureWorkerException('Custom exception')


class GraphWorker(containers.WorkerItem):
    """ Worker thread graph to control GraphWindow on the GUI thread"""
    factory = containers.WorkerItem.get_factory()
    test_method = factory.method()


def figure(*args, **kwargs):
    """ Create, raise or modify FigureWorker objects """
    container = refs.worker.get('figure')
    if not args:
        return container.create(**kwargs)
    figure_worker = args[0]
    container.current = figure_worker
    return figure_worker


def graph(*args, **kwargs):
    """ Create, raise or modify GraphWorker objects """
    container = refs.worker.get('graph')
    if not args:
        return container.create(**kwargs)
    graph_worker = args[0]
    container.current = graph_worker
    return graph_worker


global_kwargs = {}


# Configure decorators
class ExampleDecoratorCore(decorator.DecoratorCore):
    """ Exemplary decorator core class, with extra testing functionality for
    global keyword arguments """

    def __init__(self, **dec_kwargs):
        """ Reimplement this to make use of decorator's keyword arguments """
        global_kwargs.update(dec_kwargs)
        super().__init__(**dec_kwargs)


ExampleDecoratorCore.add_agent('figure', window.FigureWindow, FigureWorker)
ExampleDecoratorCore.add_agent('graph', window.GraphWindow, GraphWorker)
decorator_example = decorator.Decorator(ExampleDecoratorCore)
