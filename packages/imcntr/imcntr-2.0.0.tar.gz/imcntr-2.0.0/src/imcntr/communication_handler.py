"""
Task and response helpers for a device connection.

This module provides utility classes for sending tasks to a device
and waiting for specific responses via a given protocol using a
threaded observer pattern.
"""

from .communication_protocol import DeviceCommunication
import threading

class WaitForResponse:
    """
    Wait for a specific response from a connected device.

    An instance of this class subscribes to the protocol's receive observer
    and blocks until the expected response is received or a timeout occurs.

    The instance itself is callable and returns a boolean indicating whether
    the response was received within the timeout period.

    This class is also used as the base class for :class:`SubmitTask`.

    Note:
        Do not modify the :attr:`response` attribute while a wait is in progress.
        Doing so may result in missed signals or inconsistent behavior.

    :param protocol: Active device communication protocol.
    :type protocol: :class:`~imcntr.device_connection.DeviceCommunication`
    :param response: Expected response string to wait for.
    :type response: str
    :param timeout: Default timeout in seconds. If ``None``, waits indefinitely.
    :type timeout: float or None
    """
    def __init__(self, protocol, response=None, timeout=None):
        self._protocol, self._receive_observer = self._validate_protocol(protocol)
        if response is not None:
            self._response = self._validate_signal(response)
        else:
            self._response = response
        if timeout is not None:
            self._timeout = self._validate_timeout(timeout)
        else:
            self._timeout = timeout
        self._event = threading.Event()

    @property
    def response(self):
        """
        Expected response string.

        :rtype: str
        """
        return self._response

    @response.setter
    def response(self, value):
        """
        Set a new expected response.

        :param value: New expected response string.
        :type value: str
        :raises TypeError: If the value is not a string.

        .. warning::
            Do not modify this attribute while a wait is in progress.
        """
        self._response = self._validate_signal(value)

    @property
    def timeout(self):
        """
        Default timeout in seconds used when waiting for a response.

        :rtype: float or None
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """
        Set the default timeout.

        :param value: Timeout in seconds (must be positive).
        :type value: float
        :raises TypeError: If the value is not numeric.
        :raises ValueError: If the value is not positive.
        """
        self._timeout = self._validate_timeout(value)

    def _receive_message(self, data):
        """
        Receive observer callback.

        This method is invoked by the protocol's receive observer whenever
        data is received. If the received data matches the expected response,
        the internal event is set, unblocking the waiting thread.

        This mechanism is shared by :class:`WaitForResponse` and
        :class:`SubmitTask`.

        :param data: Data received from the device.
        :type data: str
        """
        if data == self._response:
            self._event.set()

    def _validate_protocol(self, protocol):
        """
        Validate that the protocol exposes the required interface.

        The protocol must provide:
            - :meth:`send`
            - ``receive_observer`` with :meth:`subscribe` and :meth:`unsubscribe`

        :param protocol: Protocol instance to validate.
        :raises TypeError: If the protocol does not implement the required API.
        """
        if protocol is None:
            raise TypeError("Invalid protocol: must not be None")
        if not callable(getattr(protocol, "send", None)):
            raise TypeError(
                f"Invalid protocol: must implement send(), got '{type(protocol).__name__}'"
            )
        observer = getattr(protocol, "receive_observer", None)
        if observer is None:
            raise TypeError(
                f"Invalid protocol: must expose receive_observer, got '{type(protocol).__name__}'"
            )
        if not callable(getattr(observer, "subscribe", None)):
            raise TypeError(
                f"Invalid receive_observer: must implement subscribe(), got '{type(observer).__name__}'"
            )
        if not callable(getattr(observer, "unsubscribe", None)):
            raise TypeError(
                f"Invalid receive_observer: must implement unsubscribe(), got '{type(observer).__name__}'"
            )
        return protocol, observer

    def _validate_signal(self, value):
        """
        Validate a signal value.

        A signal can be either a response string or a task string.

        :param value: Signal value to validate.
        :type value: str
        :return: Validated signal.
        :rtype: str
        :raises TypeError: If the value is not a string.
        """
        if not isinstance(value, str):
            raise TypeError(
                f"Invalid signal: must be of type str, got '{type(value).__name__}'"
            )
        return value

    def _validate_timeout(self, value):
        """
        Validate and normalize a timeout value.

        :param value: Timeout in seconds.
        :type value: float
        :return: Validated timeout.
        :rtype: float
        :raises TypeError: If the value is not numeric.
        :raises ValueError: If the value is not positive.
        """
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Invalid timeout: must be of type int or float, got '{type(value).__name__}'"
            )
        if value <= 0:
            raise ValueError(
                f"Invalid timeout: must be non-zero positive number, got '{value}'"
            )
        return value

    def __call__(self, timeout=None):
        """
        Block until the expected response is received or a timeout occurs.

        If ``timeout`` is ``None``, the instance default :obj:`timeout`  is used.

        :param timeout: Maximum time to wait in seconds.
        :type timeout: float or None
        :return: ``True`` if the response was received before timeout,
                 ``False`` otherwise.
        :rtype: bool
        :raises ValueError: If the expected response is not set.
        """
        if timeout is not None:
            timeout = self._validate_timeout(timeout)
        else:
            timeout = self._timeout
        if self._response is None:
            raise ValueError(f"Response is not set yet, got '{self._response}'")
        self._event.clear()
        self._receive_observer.subscribe(self._receive_message)
        try:
            return self._event.wait(timeout)
        finally:
            self._receive_observer.unsubscribe(self._receive_message)
            self._event.clear()


class SubmitTask(WaitForResponse):
    """
    Send a task to the device and optionally wait for a response.

    This class extends :class:`WaitForResponse` by adding the ability to
    transmit a task via the protocol before waiting for the response.

    The instance itself is callable.

    :param protocol: Active device communication protocol.
    :type protocol: :class:`~imcntr.device_connection.DeviceCommunication`
    :param response: Expected response string.
    :type response: str
    :param task: Default task string to send.
    :type task: str
    :param timeout: Default timeout in seconds. If ``None``, waits indefinitely.
    :type timeout: float or None
    """
    def __init__(self, protocol, response, task=None, timeout=None):
        if task is not None:
            self._task = self._validate_signal(task)
        else:
            self._task = task
        super().__init__(protocol, response, timeout)

    @property
    def task(self):
        """
        Default task string sent to the device.

        :rtype: str
        """
        return self._task

    @task.setter
    def task(self, value):
        """
        Set a new default task string.

        :param value: Task string to send.
        :type value: str
        :raises TypeError: If the value is not a string.
        """
        self._task = self._validate_signal(value)

    def __call__(self, timeout = None, wait = True):
        """
        Send the task to the device and optionally wait for a response.

        If ``timeout`` is ``None``, the instance default :obj:`~WaitForResponse.timeout` is used.

        :param timeout: Maximum time to wait for the response in seconds.
        :type timeout: float or None
        :param wait: Whether to wait for the response after sending.
        :type wait: bool
        :return: ``True`` if the response was received before timeout,
                 ``False`` if timeout occurs, ``None`` if ``wait`` is False.
        :rtype: bool or None
        :raises ValueError: If the task is not set.
        """
        task = self._task
        if task is None:
            raise ValueError(f"Task is not set, got '{task}'")
        if not wait:
            self._protocol.send(task)
            return
        if timeout is not None:
            timeout = self._validate_timeout(timeout)
        else:
            timeout = self._timeout
        self._event.clear()
        self._receive_observer.subscribe(self._receive_message)
        try:
            self._protocol.send(task)
            return self._event.wait(timeout)
        finally:
            self._receive_observer.unsubscribe(self._receive_message)
            self._event.clear()
