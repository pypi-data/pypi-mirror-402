""" Module with helper class for decorator definition """

import functools
import wrapt
from pqthreads import controllers
from pqthreads import refs


class DecoratorCore:
    """ Helper class for decorator definition """
    gui_agents = {}
    worker_agents = {}

    @classmethod
    def add_agent(cls, name, gui_class, worker_class):
        """ Add GUI agent classes """
        if name in cls.gui_agents or name in cls.worker_agents:
            raise ValueError(f'Duplicate agent name: {name}')
        cls.gui_agents[name] = gui_class
        cls.worker_agents[name] = worker_class

    def __init__(self, **dec_kwargs):
        """ Reimplement this to make use of decorator's keyword arguments """
        self.dec_kwargs = dec_kwargs
        self.gui_agency_class = controllers.GUIAgency
        self.add_gui_agents(self.gui_agency_class)

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        return self.wrapper(wrapped, args, kwargs)

    def wrapper(self, wrapped, args, kwargs):
        """ Simplified short hand for caller function """
        gui_agency = self.gui_agency_class(worker=wrapped, *args, **kwargs)
        self.add_worker_agents(gui_agency.worker_agency)
        gui_agency.execute()
        refs.gui.clear()
        refs.worker.clear()
        return gui_agency.result

    def add_gui_agents(self, gui_agency_class):
        """ Add GUI agents """
        for name, gui_class in self.gui_agents.items():
            gui_agency_class.add_agent(name, gui_class)

    def add_worker_agents(self, work_agency):
        """ Add worker agents """
        for name, worker_class in self.worker_agents.items():
            work_agency.add_container(name, worker_class)


class Decorator: # pylint: disable=too-few-public-methods
    """ Helper class for decorator definition """

    def __init__(self, decorator_class: DecoratorCore):
        self.decorator_class = decorator_class

    def __call__(self, wrapped=None, **kwargs):
        """ Enables usage with and without decorator keyword arguments """
        if wrapped is None:
            return functools.partial(self.__call__, **kwargs)
        return self.decorator_class(**kwargs)(wrapped)
