"""
Thread communicator module for sending and receiving information from one thread
to another using a sender and receiver
"""

from copy import copy
from contextlib import contextmanager
from pqthreads.qt import QtCore
from pqthreads import utils
from pqthreads.config import params


class RootTCException(Exception):
    """ Root Exception of the threads module """


class WorkerAgentException(RootTCException):
    """ This Exception is raised if no signal was sent to a slot and thus no
    message was received"""


class GUIAgentException(RootTCException):
    """ This Exception is raised if an error at receiver side was detected """


class WorkerAgent(QtCore.QObject):
    """ Enables exchange of data with GUIAgent using signal/slots """
    createSignal = QtCore.Signal(list, dict)
    modifySignal = QtCore.Signal(int, dict)
    requestSignal = QtCore.Signal(int, list)
    methodSignal = QtCore.Signal(int, str, list, dict)
    deleteSignal = QtCore.Signal(int)
    dataRecevied = QtCore.Signal()
    stopSignalwait = QtCore.Signal()
    no_message = object()

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.error = False
        self.message = self.no_message
        self.name = name
        self.signal_waiter = utils.SignalWaiter(self.dataRecevied,
                                                error_signal=self.stopSignalwait,
                                                timeout=params.signal_slot_timeout,
                                                parent=self)

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name})'

    def connect_agent(self, gui_agent):
        """ Connects the sender to a gui_agent """
        self.createSignal.connect(gui_agent.create_slot)
        self.modifySignal.connect(gui_agent.modify_slot)
        self.requestSignal.connect(gui_agent.request_slot)
        self.methodSignal.connect(gui_agent.method_slot)
        self.deleteSignal.connect(gui_agent.delete_slot)

    def create(self, *args, **kwargs):
        """ Send out a signal and obtain data from gui_agent"""
        with self.signal_waiter:
            self.createSignal.emit(args, kwargs)
        return self.read_message()

    def modify(self, index, **kwargs):
        """ Send out a one-way signal with given arguments and keyword arguments """
        with self.signal_waiter:
            self.modifySignal.emit(index, kwargs)
        self.read_message()

    def request(self, index, *args):
        """ Obtain data from gui_agent"""
        with self.signal_waiter:
            self.requestSignal.emit(index, args)
        return self.read_message()

    def method(self, index, func_name, *args, **kwargs):
        """ Send out a signal to execute a method on the gui_agent class """
        with self.signal_waiter:
            self.methodSignal.emit(index, func_name, args, kwargs)
        return self.read_message()

    def delete(self, index):
        """ Send out a signal to delete object at index on the gui_agent class """
        with self.signal_waiter:
            self.deleteSignal.emit(index)
        self.read_message()

    def read_message(self):
        """ Helper method, that reads message set by slot and returns a copy """
        if self.message is self.no_message:
            if self.error:
                return self.message
            if not self.error:
                raise WorkerAgentException('No message received')
        message = copy(self.message)
        self.message = self.no_message
        return message

    @QtCore.Slot(object)
    def slot(self, data):
        """ Slot for receiving data """
        self.message = data
        self.dataRecevied.emit()

    @QtCore.Slot(object)
    def error_detected(self):
        """ If a gui_agent error is detected ... """
        self.error = True

    def deleteLater(self): # pylint: disable=invalid-name
        """ Make sure all eventloops in utils.signal_wait are quit before the
        agent is deleted """
        self.stopSignalwait.emit()
        super().deleteLater()


class GUIAgent(QtCore.QObject):
    """ A receiver for operations whose instructions were sent by WorkerAgent """
    signal = QtCore.Signal(object)
    error = QtCore.Signal()

    def __init__(self, name, container, parent=None):
        super().__init__(parent)
        self.name = name
        self.create = container.create
        self.modify =  container.modify
        self.request = container.request
        self.method = container.method
        self.delete = container.delete

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name})'

    def connect_agent(self, worker_agent):
        """ Connects the sender to a worker_agent """
        self.signal.connect(worker_agent.slot)
        self.error.connect(worker_agent.error_detected)

    @contextmanager
    def register_exception(self):
        """ Shorthand to register errors at receiver side """
        try:
            yield
        except BaseException:
            self.error.emit()
            raise

    @QtCore.Slot(list, dict)
    def create_slot(self, args, kwargs):
        """ Slot for creating a new class instance """
        with self.register_exception():
            val = self.create(args, kwargs)
            self.signal.emit(val)

    @QtCore.Slot(int, dict)
    def modify_slot(self, index, kwargs):
        """ Slot for modifying an instance attribute """
        with self.register_exception():
            self.modify(index, kwargs)
            self.signal.emit(True)

    @QtCore.Slot(int, list)
    def request_slot(self, index, args):
        """ Slot for requesting an instance attribute """
        with self.register_exception():
            self.signal.emit(self.request(index, args))

    @QtCore.Slot(int, str, list, dict)
    def method_slot(self, index, func, args, kwargs):
        """ Slot for calling a class instance method """
        with self.register_exception():
            self.signal.emit(self.method(index, func, args, kwargs))

    @QtCore.Slot(int)
    def delete_slot(self, index):
        """ Slot for closing/deleting a class instance object at index """
        with self.register_exception():
            self.delete(index)
            self.signal.emit(True)
