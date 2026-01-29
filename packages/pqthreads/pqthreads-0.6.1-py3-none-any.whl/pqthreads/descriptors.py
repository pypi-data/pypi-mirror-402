"""
Descriptors for attributes and methods for work thread classes in mlpyqtgraph

"""


class AbstractDescriptor:
    """
    Abstract descriptor class that serves as base class for Descriptors
    """
    agent = None

    @classmethod
    def with_agent(cls, agent):
        """ Define a Descriptor class with defined agent """
        cls.agent = agent
        return cls

    def __init__(self):
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, owner=None):
        raise NotImplementedError

    def __repr__(self):
        return f'Descriptor(agent={repr(self.agent)}'


class AttributeDescriptor(AbstractDescriptor):
    """
    Custom descriptor for setting and getting class attributes in the main event
    loop

    This descriptor enables setting and getting object instance attributes using
    a agent. It expects the presence of a agent object and index on
    its parent object instance.
    """
    def __get__(self, obj, owner=None):
        return self.agent.request(obj.index, self.name)[0]

    def __set__(self, obj, value):
        kwargs = {self.name: value}
        self.agent.modify(obj.index, **kwargs)

    def __repr__(self):
        return 'Attribute' + super().__repr__()


class MethodDescriptor(AbstractDescriptor):
    """
    Custom descriptor for calling methods in the main event loop

    This descriptor enables calling method of an object instance using a custom
    agent. It expects the presence of a agent object and index on its
    parent object instance.
    """
    def __init__(self):
        super().__init__()
        self.index = None

    def __get__(self, obj, owner=None):
        try:
            self.index = obj.index
        except AttributeError:
            pass
        return self

    def __call__(self, *args, **kwargs):
        return self.agent.method(self.index, self.name, *args, **kwargs)

    def __repr__(self):
        return 'Method' + super().__repr__()



class DescriptorFactory:
    """
    Factory for attribute and method descriptors that correlate to attributes
    and methods of a class in another thread. Interaction is organized through a
    agent, which is required by the attribute and method descriptors.

    Note that we need to copy the classes AttributeDescriptor and
    MethodDescriptor (using inheritance) to avoid agent clashes with other
    factory instances.
    """
    def __init__(self, agent=None):
        self.agent = agent
        self.attributes = []
        self.attribute_descriptor_class = self.copy_class(AttributeDescriptor)
        self.method_descriptor_class = self.copy_class(MethodDescriptor)

    def set_agent(self, agent):
        """ Set the agent """
        self.agent = agent
        for attribute in self.attributes:
            attribute.agent = agent

    @staticmethod
    def copy_class(original_class):
        """ Creates a copy of a class using inheritance """
        class ClassCopy(original_class): # pylint: disable=too-few-public-methods
            """ Copy of Class original_class """
        return ClassCopy

    def __repr__(self):
        return f'{self.__class__.__name__}(agent={self.agent})'

    @property
    def attribute(self):
        """ Produce attribute descriptor class """
        self.attributes.append(self.attribute_descriptor_class)
        return self.attributes[-1]

    @property
    def method(self):
        """ Produce method descriptor class """
        self.attributes.append(self.method_descriptor_class)
        return self.attributes[-1]
