"""
Controller task definitions and high-level device interfaces.

This module defines controller command/response pairs and provides
high-level interfaces for interacting with the device controller,
sample positioning system, and shutter.

The module builds communication protocol :class:`DeviceCommunication` as well as on as
low-level command handlers provided by:class:`~imcntr.device_command_handler.SubmitTask` and
:class:`~imcntr.device_command_handler.WaitForResponse`, exposing a clear, structured, and type-safe API for
device operation.
"""

from .communication_handler import WaitForResponse, SubmitTask
from enum import Enum
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TaskDef:
    """
    Represent a task and response pair in form of a `dataclass`.

    :param task: Command string sent to the controller,
                 or ``None`` if the task cannot be submitted.
    :type task: Optional[str]
    :param response: Expected response string from the controller.
    :type response: str
    """
    task: Optional[str]
    response: str


class _Task(Enum):
    """
    Enumeration of controller tasks backed by :class:`TaskDef`.

    Each enum member's *value* is a :class:`TaskDef` instance.
    """
    READY = TaskDef(None, "controller_ready")
    PING = TaskDef("connect", "connected")
    OPEN = TaskDef("open_shutter", "shutter_opened")
    CLOSE = TaskDef("close_shutter", "shutter_closed")
    MOVE_OUT = TaskDef("move_out", "pos_out")
    MOVE_IN = TaskDef("move_in", "pos_in")
    MOVE_STOP = TaskDef("stop_lin", "lin_stopped")
    ROTATE_CW = TaskDef("rot_cw", "rot_stopped")
    ROTATE_CCW = TaskDef("rot_ccw", "rot_stopped")
    ROTATE_STOP = TaskDef("stop_rot", "rot_stopped")
    STOP = TaskDef("stop_all", "all_stopped")

class RotationTask(SubmitTask):
    """
    Submit a rotation task with a configurable number of steps.

    This class extends
    :class:`~imcntr.device_command_handler.SubmitTask`
    by appending a step count to the task string before submission.

    :param args: Positional arguments passed to
                 :class:`~imcntr.device_command_handler.SubmitTask`.
    :param kwargs: Keyword arguments passed to
                   :class:`~imcntr.device_command_handler.SubmitTask`.
    """
    def __init__(self, *args, **kwargs):
        self._steps = None
        super().__init__(*args, **kwargs)

    @property
    def steps(self):
        """
        Default rotation steps.

        :rtype: int or None
        """
        return self._steps

    @steps.setter
    def steps(self, value):
        """
        Set the default steps.

        :param value: Rotation step count.
        :type value: int
        :raises TypeError: If the value is not an integer.
        :raises ValueError: If the value is not positive.
        """
        self._steps = self._validate_steps(value)

    def _validate_steps(self, value):
        """
        Validate a rotation step value.

        :param value: Rotation step count.
        :type value: int
        :return: Validated step count.
        :rtype: int
        :raises TypeError: If the value is not an integer.
        :raises ValueError: If the value is not positive.
        """
        if not isinstance(value, int):
            raise TypeError(
                f"Invalid step: must be of type int, got '{type(value).__name__}'"
            )
        if value <= 0:
            raise ValueError(
                f"Invalid step: must be non-zero positive number, got '{value}'"
            )
        return value

    def __call__(self, steps=None, timeout=None, wait=True):
        """
        Send a rotation task with the specified number of steps.

        :param steps: Rotation step count to use for this invocation.
        :type steps: int or None
        :param timeout: Maximum time to wait for the response in seconds.
        :type timeout: float or None
        :param wait: Whether to wait for the response after sending.
        :type wait: bool
        :return: ``True`` if the response was received before timeout,
                 ``False`` if timeout occurs, ``None`` if ``wait`` is False.
        :rtype: bool or None
        :raises ValueError: If the task is not set.
        """
        if steps is not None:
            steps = self._validate_steps(steps)
        else:
            steps = self._steps
        if steps is None:
            raise ValueError(f"Steps are not set, got '{steps}'")
        raw_task = self._task
        self.task = f"{raw_task}+{steps}"
        try:
            return super().__call__(timeout, wait)
        finally:
            self._task = raw_task


class TaskFactory:
    """
    Factory for creating
    :class:`~imcntr.device_command_handler.SubmitTask` and
    :class:`~imcntr.device_command_handler.WaitForResponse`
    instances from :class:`_Task` definitions.

    :param protocol: Communication protocol instance.
    :type protocol: :class:`~imcntr.device_connection.DeviceCommunication`
    """
    def __init__(self, protocol):
        self._protocol = protocol

    def rotate(self, task):
        """
        Create a :class:`RotationTask` for a rotation-capable controller task.

        :param task: Task enum with members of type :class:`TaskDef`.
        :type task: :class:`Enum`
        :return: Configured rotation task instance.
        :rtype: RotationTask
        """
        return RotationTask(
            protocol = self._protocol,
            task = task.value.task,
            response = task.value.response,
        )

    def submit(self, task):
        """
        Create a :class:`~imcntr.device_command_handler.SubmitTask`
        for a submit-capable controller task.

        :param task: Task enum with members of type :class:`TaskDef`.
        :type task: :class:`Enum`
        :return: Configured submit task instance.
        :rtype: SubmitTask
        """
        return SubmitTask(
            protocol = self._protocol,
            task = task.value.task,
            response = task.value.response,
        )

    def wait(self, task):
        """
        Create a
        :class:`~imcntr.device_command_handler.WaitForResponse`
        for a task's expected response.

        :param task: Task enum with members of type :class:`TaskDef`.
        :type task: :class:`Enum`
        :return: Configured wait task instance.
        :rtype: WaitForResponse
        """
        return WaitForResponse(
            protocol = self._protocol,
            response = task.value.response,
        )


class Controller:
    """
    Controller interface.

    Provides methods to wait for controller readiness and to check connection
    status.

    :param protocol: Communication protocol instance.
    :type protocol: :class:`~imcntr.DeviceCommunication`
    """

    def __init__(self, protocol):
        factory = TaskFactory(protocol)
        self._ready = factory.wait(_Task.READY)
        self._ping = factory.submit(_Task.PING)

    @property
    def ping(self):
        """
        Command to check if controller is connected.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._ping

    @property
    def ready(self):
        """
        Command to wait for the controller to report it is ready after startup

        Returns a callable :class:`~imcntr.device_command_handler.WaitForResponse` instance. Calling this object
        waits for corresponding response.

        The returned object exposes configurable properties such as the
        default response string or timeout.

        See :class:`~imcntr.device_command_handler.WaitForResponse` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._ready


class Sample:
    """
    Interface for sample movement and rotation control.

    Provides methods to move sample in/out, rotate, and stop movements.

    :param protocol: Communication protocol instance.
    :type protocol: :class:`~imcntr.DeviceCommunication`
    """
    def __init__(self, protocol):
        factory = TaskFactory(protocol)
        self._move_in = factory.submit(_Task.MOVE_IN)
        self._move_out = factory.submit(_Task.MOVE_OUT)
        self._move_stop = factory.submit(_Task.MOVE_STOP)
        self._rotate_cw = factory.rotate(_Task.ROTATE_CW)
        self._rotate_ccw = factory.rotate(_Task.ROTATE_CCW)
        self._rotate_stop = factory.submit(_Task.ROTATE_STOP)
        self._stop = factory.submit(_Task.STOP)

    @property
    def move_in(self):
        """
        Command to move the sample in.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._move_in

    @property
    def move_out(self):
        """
        Command to move the sample out.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._move_out

    @property
    def move_stop(self):
        """
        Command to stop linear sample movement.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._move_stop

    @property
    def rotate_cw(self):
        """
        Command to rotate the sample clockwise.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._rotate_cw

    @property
    def rotate_ccw(self):
        """
        Command to rotate the sample counterclockwise.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._rotate_ccw

    @property
    def rotate_stop(self):
        """
        Command to stop sample rotation.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._rotate_stop

    @property
    def stop(self):
        """
        Command to stop all sample movements.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._stop


class Shutter:
    """
    Interface for shutter control.

    Provides methods to open or close the shutter.

    :param protocol: Communication protocol instance.
    :type protocol: :class:`~imcntr.DeviceCommunication`
    """
    def __init__(self, protocol):
        factory = TaskFactory(protocol)
        self._open = factory.submit(_Task.OPEN)
        self._close = factory.submit(_Task.CLOSE)

    @property
    def close(self):
        """
        Command to close the shutter.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._close

    @property
    def open(self):
        """
        Command to open the shutter.

        Returns a callable :class:`~imcntr.device_command_handler.SubmitTask` instance. Calling this object
        sends the corresponding task to the device and optionally waits for
        a response.

        The returned object exposes configurable properties such as the
        default task string, response string or timeout.

        See :class:`~imcntr.device_command_handler.SubmitTask` for available properties and detailed behavior.

        :rtype: SubmitTask
        """
        return self._open
