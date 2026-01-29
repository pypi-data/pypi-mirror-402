""" GUI Item module """

import weakref
from pqthreads.qt import QtCore
from pqthreads import descriptors


class RootException(Exception):
    """ Root Exception of the threads module """


class ItemException(RootException):
    """ This Exception is raised if an error was raised in the worker thread """


class GUIItemContainer(QtCore.QObject):
    """
    Controller for a container with instances of user-supplied GUI element class
    """

    def __init__(self, item_class, parent=None):
        super().__init__(parent)
        self.items = []
        self.indices = []
        self.item_class = item_class

    def __repr__(self):
        return f'{self.__class__.__name__}(item_class={self.item_class.__name__})'

    @property
    def count(self):
        """ Current number of items """
        if not self.indices:
            return 0
        return max(self.indices) + 1

    def back(self):
        """ Returns the last item """
        return self.items[-1]

    def get_item(self, index):
        """ Returns the item at index """
        try:
            return self.items[index]
        except IndexError as err:
            raise ItemException(f'Index not find for {self.item_class} items') from err

    def create(self, args, kwargs):
        """ Creates a new item instance with user-supplied item class """
        index = self.count
        new_item = self.item_class(index, *args, **kwargs)
        self.items.append(new_item)
        self.indices.append(index)
        return index

    def request(self, index, args):
        """ Returns values of item attributes """
        item = self.get_item(index)
        return [getattr(item, arg) for arg in args]

    def modify(self, index, kwargs):
        """ Modifies item's attributes"""
        item = self.get_item(index)
        for key, value in kwargs.items():
            setattr(item, key, value)

    def method(self, index, func_name, args, kwargs):
        """ Execute method on item """
        item = self.get_item(index)
        func = getattr(item, func_name)
        return func(*args, **kwargs)

    def delete(self, index):
        """ Deletes the item at index """
        remove_index = self.indices.index(index)
        del self.indices[remove_index]
        item = self.items.pop(remove_index)
        item.delete()

    def __del__(self):
        """ Make sure all items are deleted """
        for item in self.items:
            if item:
                try:
                    item.deleteLater()
                except RuntimeError:
                    pass


class WorkerItem:
    """ Abstract Worker Item class """
    agent = None
    factory = None

    @classmethod
    def get_factory(cls):
        """ Instantiate a new descriptor factory """
        return descriptors.DescriptorFactory()

    @classmethod
    def with_agent(cls, agent):
        """ Set the agent """
        cls.agent = agent
        cls.factory.set_agent(agent)
        return cls

    def __init__(self, *args, **kwargs):
        self.index = self.agent.create(*args, **kwargs)

    def __repr__(self):
        return f'{self.__class__.__name__}(index={self.index})'

    def close(self):
        """ Closes the current figure on the GUI side """
        self.agent.delete(self.index)


class WorkerItemContainer:
    """ Abstract Worker Item Container class """

    def __init__(self, item_class):
        self.item_class = item_class
        self.items = []
        self.current = None

    def __repr__(self):
        repr_string = '['
        for idx, figure in enumerate(self.items):
            if idx > 0:
                repr_string += ', '
            repr_string += repr(figure)
        repr_string += ']'
        return repr_string

    def create(self, *args, **kwargs):
        """ Create a new FigureWorker and return a weak reference proxy """
        self.append(self.item_class(*args, **kwargs))
        self.current = self.back()
        return weakref.proxy(self.back())

    def append(self, item):
        """ Append an item """
        self.items.append(item)

    def back(self):
        """ Returns the last item """
        return self.items[-1]

    def close(self, item):
        """
        Remove an item from the container, closes its figure and deletes it.
        After calling this function, weak references to this item will no longer
        be valid.
        """
        index = self.items.index(item)
        worker_item = self.items.pop(index)
        worker_item.close()
