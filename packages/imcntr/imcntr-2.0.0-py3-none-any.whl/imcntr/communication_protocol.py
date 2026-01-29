"""
Serial communication utilities based on :mod:`serial` (pySerial).

This module provides a high-level interface for line-based serial communication,
including threaded reading, observer-based receive handling, and extensible
callback hooks.

See also:
    :class:`serial.Serial`
    :class:`serial.threaded.ReaderThread`
"""

import serial
import serial.threaded
from .observer import Observer

class _SerialLineHandler(serial.threaded.LineReader):
    """
    Line-based protocol handler for serial communication.

    This class subclasses :class:`serial.threaded.LineReader` and forwards
    received lines and connection-loss events to a receiver object.

    The receiver must implement:
        - :meth:`receive`
        - :meth:`connection_lost`
    """

    def __init__(self):
        """
        Initialize the protocol handler with no receiver.
        """
        super().__init__()
        self._receiver = None

    @property
    def receiver(self):
        """
        Receiver for incoming data and connection events.

        :return: Receiver instance.
        :rtype: object
        """
        return self._receiver

    @receiver.setter
    def receiver(self, value):
        """
        Set the receiver for handling incoming data.

        The receiver must implement:
            - ``receive(data: str)``
            - ``connection_lost(exception: Exception)``

        :param value: Receiver instance.
        :type value: object
        """
        self._receiver = value

    def connection_lost(self, exc):
        """
        Called automatically when the serial connection is lost.

        Forwards the event to :meth:`receiver.connection_lost`.

        :param exc: Exception that caused the connection loss.
        :type exc: Exception
        """
        if self._receiver is not None:
            self._receiver.connection_lost(exc)

    def handle_line(self, line):
        """
        Called automatically when a complete line is received.

        Forwards the received line to :meth:`receiver.receive`.

        :param line: Line of data received from the serial port.
        :type line: str
        """
        if self._receiver is not None:
            self._receiver.receive(line)


class DeviceCommunication:
    """
    Manages a serial device connection using pySerial and a reader thread.

    This class encapsulates:
        - Serial port management (:class:`serial.Serial`)
        - Threaded I/O (:class:`serial.threaded.ReaderThread`)

    It also supports usage as a context manager.

    :param port: Serial port identifier (e.g. ``'COM3'`` or ``'/dev/ttyUSB0'``).
    :type port: str or None
    """
    def __init__(self, port=None):
        self._port = None
        if port is not None:
            self.port = port
        self._serial_connection = None
        self._thread = None
        self._transport = None
        self._protocol = None
        self._receive_observer = Observer()

    @property
    def connected(self):
        """
        Whether the device is currently connected.

        :return: ``True`` if the serial connection is open and the reader thread
                 is running.
        :rtype: bool
        """
        return bool(
            self._serial_connection
            and self._serial_connection.is_open
            and self._thread
            and self._thread.is_alive()
        )

    @property
    def connection(self):
        """
        Active serial connection.

        :return: Serial connection instance or ``None``.
        :rtype: serial.Serial or None
        """
        return self._serial_connection

    @property
    def port(self):
        """
        Configured serial port.

        :return: Serial port identifier.
        :rtype: str or None
        """
        return self._port

    @port.setter
    def port(self, value):
        """
        Set the serial port.

        :param value: Serial port identifier.
        :type value: str
        :raises TypeError: If ``value`` is not a string.
        """
        if not isinstance(value, str):
            raise TypeError("port must be a string")
        self._port = value

    @property
    def receive_observer(self):
        """
        Observer notified when data is received.

        Subscribers are called with the received data string.

        :return: Receive observer instance.
        :rtype: Observer
        """
        return self._receive_observer

    @property
    def thread(self):
        """
        Reader thread managing serial I/O.

        :return: Reader thread instance or ``None``.
        :rtype: serial.threaded.ReaderThread or None
        """
        return self._thread

    def connection_lost(self, exception):
        """
        Handle connection loss.

        Resets internal state and forwards the event to
        :meth:`connection_lost_callback`.

        :param exception: Exception that caused the connection loss.
        :type exception: Exception
        """
        self._reset_connection()
        self.connection_lost_callback(exception)

    def connection_lost_callback(self, exception):
        """
        Optional hook invoked when the connection is lost.

        Override in subclasses or monekey patch to implement custom handling.

        :param exception: Exception that caused the connection loss.
        :type exception: Exception
        """
        pass

    def receive(self, data):
        """
        Handle received data from the serial device.

        Notifies all subscribers via :attr:`receive_observer` and then calls
        :meth:`receive_callback`.

        :param data: Received data.
        :type data: str
        """
        self._receive_observer.call(data)
        self.receive_callback(data)

    def receive_callback(self, data):
        """
        Optional hook invoked when data is received.

        Override in subclasses or monekey patch to implement custom handling.

        .. note::
            This callback is executed in the serial reader thread.

        :param data: Received data.
        :type data: str
        """
        pass

    def send(self, data):
        """
        Send data to the device.

        :param data: Data string to send.
        :type data: str
        :raises RuntimeError: If not connected or sending fails.
        """
        if not self.connected:
            raise RuntimeError("Not connected to serial port")
        try:
            self._protocol.write_line(data)
        except Exception as e:
            raise RuntimeError("Writing data to serial port failed!") from e
        self.send_callback(data)

    def send_callback(self, data):
        """
        Optional hook invoked after data is sent.

        Override in subclasses or monekey patch to implement custom handling.

        :param data: Sent data.
        :type data: str
        """
        pass

    def start(self):
        """
        Establish the serial connection and start the reader thread.

        :raises ValueError: If the serial port is not set.
        :raises RuntimeError: If already connected or connection fails.
        """
        if not self._port:
            raise ValueError("Serial port must be specified before connecting")
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Connection already established")
        self._connect_to_serial_port()
        self._start_serial_reader_thread()

    def stop(self):
        """
        Close the serial connection and stop the reader thread.

        :raises RuntimeError: If the connection cannot be closed cleanly.
        """
        try:
            if self._thread and self._thread.is_alive():
                self._thread.close()
            if self._serial_connection and self._serial_connection.is_open:
                self._serial_connection.close()
        except Exception as e:
            raise RuntimeError("Connection not closed!") from e
        else:
            self._reset_connection()

    def _connect_to_serial_port(self):
        """
        Open the serial port.

        :raises RuntimeError: If the port cannot be opened.
        """
        try:
            self._serial_connection = serial.Serial(self._port)
        except ValueError as e:
            raise RuntimeError("Parameter out of range when opening serial connection") from e
        except serial.SerialException as e:
            raise RuntimeError("Serial port not available") from e
        except Exception as e:
            raise RuntimeError("Unspecified error when opening serial connection") from e

    def _reset_connection(self):
        """
        Reset all internal connection state.

        Internal use only.
        """
        self._serial_connection = None
        self._thread = None
        self._transport = None
        self._protocol = None

    def _start_serial_reader_thread(self):
        """
        Start the reader thread for serial communication.

        Initializes the protocol handler and assigns the receiver.

        :raises RuntimeError: If the reader thread fails to start.
        """
        self._thread = serial.threaded.ReaderThread(
            self._serial_connection,
            _SerialLineHandler,
        )
        try:
            self._thread.start()
        except Exception as e:
            raise RuntimeError("Connecting communication thread failed!") from e
        self._transport, self._protocol = self._thread.connect()
        self._protocol.receiver = self

    def __enter__(self):
        """
        Enter context manager and connect.

        :return: This instance.
        :rtype: DeviceCommunication
        """
        self.start()
        if not self.connected:
            raise RuntimeError("Connection not possible!")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit context manager and disconnect.

        Exceptions raised inside the ``with`` block are propagated.

        :return: ``False`` to propagate exceptions.
        :rtype: bool
        """
        try:
            self.stop()
        except Exception:
            pass
        return False
