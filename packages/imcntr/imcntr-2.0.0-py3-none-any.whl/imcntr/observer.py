"""
Observer utilities for event-driven notifications.

This module provides a lightweight implementation of the Observer
design pattern, allowing callables to subscribe to and be notified
of events emitted by an observable source.
"""

class Observer:
    """
    Implements the Observer design pattern.

    Allows multiple callables (observers) to subscribe to an event source.
    Each observer may be registered with predefined positional and keyword arguments.
    When the event is triggered via :meth:`call`, all subscribed observers are invoked.
    """
    def __init__(self):
        self._observers = []

    @property
    def observers(self):
        """
        Return the list of currently subscribed observers.

        :return: List of observer definitions (dicts with keys ``target``, ``arguments``, ``kwarguments``).
        :rtype: list
        """
        return self._observers

    def call(self, *args, **kwargs):
        """
        Invoke all subscribed observers.

        Each observer is called with its predefined arguments (set at subscription via :meth:`subscribe`)
        followed by the additional arguments provided here.

        :param args: Additional positional arguments passed to each observer.
        :param kwargs: Additional keyword arguments passed to each observer.
        :raises TypeError: If an observer raises a TypeError (argument mismatch).
        :raises RuntimeError: If any other exception occurs while calling an observer.
        """
        for observer in self._observers:
            try:
                observer['target'](*observer['arguments'], *args, **observer['kwarguments'], **kwargs)
            except TypeError as e:
                raise TypeError(
                    "Wrong number of arguments when calling observer!"
                ) from e
            except Exception as e:
                raise RuntimeError(
                    "An exception occurred while calling observer!"
                ) from e

    def subscribe(self, target, *args, **kwargs):
        """
        Subscribe a new observer.

        The observer will be invoked when :meth:`call` is executed.

        :param target: The callable to be notified.
        :type target: callable
        :param args: Optional positional arguments for the callable.
        :param kwargs: Optional keyword arguments for the callable.

        """
        observer_to_subscribe = {'target': target, 'arguments': args, 'kwarguments': kwargs}
        if observer_to_subscribe not in self._observers:
            self._observers.append(observer_to_subscribe)

    def unsubscribe(self, target: callable = None, *args, remove_all = False, **kwargs):
        """
        Unsubscribe observers.

        Behavior depends on the provided arguments:

        - If no ``target`` is provided, all observers are removed.
        - If ``target`` is provided and ``remove_all`` is False, only the observer
          matching the target **and** provided arguments is removed.
        - If ``target`` is provided and ``remove_all`` is True, all observers
          with the matching target are removed, regardless of their arguments.

        :param target: The observer callable to remove.
        :type target: callable, optional
        :param remove_all: Remove all observers matching the target if True.
        :type remove_all: bool
        :param args: Positional arguments used to match a specific subscription.
        :param kwargs: Keyword arguments used to match a specific subscription.
        """
        if target:
            if not remove_all:
                observer_to_unsubscribe = {'target': target, 'arguments': args, 'kwarguments': kwargs}
                if observer_to_unsubscribe in self._observers:
                    self._observers.remove(observer_to_unsubscribe)
            else:
                for observer in self._observers[:]:
                    if observer['target'] == target:
                        self._observers.remove(observer)
        else:
            self._observers.clear()
