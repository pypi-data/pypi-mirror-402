""" Reference module """

import weakref


class MissingReferenceError(Exception):
    """ Exception for missing references """


class WeakReferences:
    """ Class for holding weak references """
    def __init__(self):
        self.references = {}

    def add(self, name, agent):
        """ Adds a new weak reference """
        self.references[name] = weakref.proxy(agent)

    def get(self, name):
        """ Returns the weak reference """
        try:
            ref = self.references[name]
        except KeyError as exc:
            raise KeyError(f'No weak reference found for {name}') from exc
        if not ref:
            raise MissingReferenceError(f'No weak reference set to {name}')
        return ref

    def clear(self):
        """ Clears all weak references """
        self.references = {}


worker = WeakReferences()
gui = WeakReferences()
