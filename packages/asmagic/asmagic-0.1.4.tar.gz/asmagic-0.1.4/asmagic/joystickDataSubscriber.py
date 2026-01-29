"""
Joystick Data Subscriber for receiving joystick data over ZeroMQ.

This module provides the JoystickDataSubscriber class for subscribing to joystick data streams
via ZeroMQ using Protocol Buffers.
"""

import zmq
import numpy as np
from typing import Optional, List
from .proto import joystick_msg_pb2
from .data_types import JoystickFrame

# Default configuration
DEFAULT_PORT = 8020
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True
DEFAULT_TIMEOUT = 1000  # milliseconds


class JoystickDataSubscriber:
    """
    Subscribe to joystick data stream.
    
    Simple and Pythonic API for receiving joystick data including dual joystick positions
    and button states.
    
    Example - Basic usage:
        >>> sub = JoystickDataSubscriber("192.168.1.100")
        >>> data = sub.get()
        >>> if data:
        ...     print(f"Left: ({data.left_x}, {data.left_y})")
        ...     print(f"Right: ({data.right_x}, {data.right_y})")
        >>> sub.close()
    
    Example - Continuous streaming:
        >>> sub = JoystickDataSubscriber("192.168.1.100")
        >>> for data in sub:
        ...     print(f"Left: ({data.left_x:.3f}, {data.left_y:.3f})")
        ...     print(f"Right: ({data.right_x:.3f}, {data.right_y:.3f})")
    
    Example - Context manager:
        >>> with JoystickDataSubscriber("192.168.1.100") as sub:
        ...     for data in sub:
        ...         print(f"Buttons: {data.buttons}")
    """
    
    def __init__(
        self,
        ip: str,
        port: int = DEFAULT_PORT,
        hwm: int = DEFAULT_HWM,
        conflate: bool = DEFAULT_CONFLATE,
        verbose: bool = False,
    ) -> None:
        """
        Initialize Joystick data subscriber.
        
        Args:
            ip: Publisher's IP address
            port: Port number (default: 8020)
            hwm: High water mark - number of messages to buffer (default: 1)
            conflate: Keep only latest message when buffer full (default: True)
            verbose: Print connection info (default: False)
        """
        self._ip = ip
        self._port = port
        self._hwm = hwm
        self._conflate = conflate
        self._verbose = verbose
        self._connected = False
        
        # Initialize ZMQ
        self._context = zmq.Context()
        self._subscriber = self._context.socket(zmq.SUB)
        self._subscriber.set_hwm(hwm)
        self._subscriber.setsockopt(zmq.CONFLATE, conflate)
        
        # Connect
        address = f"tcp://{ip}:{port}"
        self._subscriber.connect(address)
        self._subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Setup poller
        self._poller = zmq.Poller()
        self._poller.register(self._subscriber, zmq.POLLIN)
        
        self._connected = True
        
        if verbose:
            print(f"Joystick Subscriber connected to {address}")
    
    @property
    def ip(self) -> str:
        """Get the IP address"""
        return self._ip
    
    @property
    def port(self) -> int:
        """Get the port number"""
        return self._port
    
    @property
    def is_connected(self) -> bool:
        """Check if subscriber is connected"""
        return self._connected
    
    def get_frame(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[JoystickFrame]:
        """
        Get a single joystick data frame.
        
        Args:
            timeout: Maximum time to wait in milliseconds (default: 1000)
        
        Returns:
            JoystickFrame object containing all joystick data, or None if timeout
        """
        if not self._connected:
            return None
        
        # Poll for messages
        socks = dict(self._poller.poll(timeout))
        
        if self._subscriber not in socks or socks[self._subscriber] != zmq.POLLIN:
            return None
        
        try:
            # Receive protobuf message
            msg_bytes = self._subscriber.recv(zmq.DONTWAIT)
            
            # Parse protobuf
            joystick_msg = joystick_msg_pb2.Joystick()
            joystick_msg.ParseFromString(msg_bytes)
            
            # Extract data into numpy arrays
            left_joystick = np.array(
                joystick_msg.l_joystick_position, 
                dtype=np.float32
            )
            
            right_joystick = np.array(
                joystick_msg.r_joystick_position,
                dtype=np.float32
            )
            
            buttons = list(joystick_msg.button_pressed)
            
            # Create JoystickFrame
            return JoystickFrame(
                timestamp=joystick_msg.timestamp,
                left_joystick=left_joystick,
                right_joystick=right_joystick,
                buttons=buttons,
            )
            
        except zmq.Again:
            return None
        except Exception as e:
            if self._verbose:
                print(f"Error receiving joystick data: {e}")
            return None
    
    def get(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[JoystickFrame]:
        """
        Get the latest joystick data frame.
        This is the recommended method for single-frame access.
        
        Args:
            timeout: Maximum time to wait in milliseconds (default: 1000)
        
        Returns:
            JoystickFrame object or None if timeout
        """
        return self.get_frame(timeout)
    
    def get_timestamp(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[float]:
        """Get only the timestamp"""
        frame = self.get_frame(timeout)
        return frame.timestamp if frame else None
    
    def get_left_joystick(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[np.ndarray]:
        """Get only the left joystick position"""
        frame = self.get_frame(timeout)
        return frame.left_joystick if frame else None
    
    def get_right_joystick(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[np.ndarray]:
        """Get only the right joystick position"""
        frame = self.get_frame(timeout)
        return frame.right_joystick if frame else None
    
    def get_buttons(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[List[bool]]:
        """Get only the button states"""
        frame = self.get_frame(timeout)
        return frame.buttons if frame else None
    
    def __iter__(self) -> "JoystickDataSubscriber":
        """Make the subscriber iterable for continuous data streaming"""
        return self
    
    def __next__(self) -> JoystickFrame:
        """
        Get the next available JoystickFrame.
        Blocks until a frame is available or connection is closed.
        """
        if not self._connected:
            raise StopIteration
        
        # Keep trying until we get a frame or connection is closed
        while self._connected:
            frame = self.get_frame(timeout=DEFAULT_TIMEOUT)
            if frame is not None:
                return frame
        
        raise StopIteration
    
    def __enter__(self) -> "JoystickDataSubscriber":
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - auto cleanup"""
        self.close()
    
    def close(self) -> None:
        """Close the subscriber connection and cleanup resources"""
        if self._connected:
            self._connected = False
            
            if hasattr(self, "_subscriber") and self._subscriber:
                self._subscriber.close()
            
            if hasattr(self, "_context") and self._context:
                self._context.term()
            
            if self._verbose:
                print("Joystick Subscriber closed")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        self.close()
