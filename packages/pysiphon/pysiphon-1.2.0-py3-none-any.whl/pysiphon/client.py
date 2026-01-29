"""Core SiphonClient implementation for gRPC communication."""

import grpc
import time
import threading
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from PIL import Image

from .generated import siphon_service_pb2 as pb2
from .generated import siphon_service_pb2_grpc as pb2_grpc
from .utils import parse_config_file, hex_to_bytes, bytes_to_hex, save_frame_image


class SiphonClient:
    """
    Python client for Siphon gRPC service.
    
    Provides methods for memory manipulation, input control, screen capture,
    command execution, and recording capabilities.
    """
    
    def __init__(self, host: str = "localhost:50051"):
        """
        Initialize Siphon client.
        
        Args:
            host: Server address (default: localhost:50051)
        """
        self.host = host
        
        # Configure channel with large message size limits (100MB like C++ client)
        options = [
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.max_send_message_length', 100 * 1024 * 1024),
        ]
        
        # Create channel and stub
        self.channel = grpc.insecure_channel(host, options=options)
        self.stub = pb2_grpc.SiphonServiceStub(self.channel)
    
    def close(self):
        """Close the gRPC channel."""
        self.channel.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # Configuration & Initialization Methods
    
    def set_process_config(self, config_file_path: str) -> Dict[str, Any]:
        """
        Load TOML config and send to server.
        
        Args:
            config_file_path: Path to TOML configuration file
        
        Returns:
            Dictionary with success, message, and config details
        """
        try:
            # Parse config file
            process_name, process_window_name, attributes = parse_config_file(config_file_path)
            
            # Build protobuf request
            request = pb2.SetProcessConfigRequest()
            request.process_name = process_name
            request.process_window_name = process_window_name
            
            for attr_name, attr_config in attributes.items():
                attr_proto = request.attributes.add()
                attr_proto.name = attr_name
                attr_proto.pattern = attr_config["pattern"]
                attr_proto.offsets.extend(attr_config["offsets"])
                attr_proto.type = attr_config["type"]
                attr_proto.length = attr_config["length"]
                attr_proto.method = attr_config["method"]
                attr_proto.mask = attr_config["mask"]
            
            # Send to server
            response = self.stub.SetProcessConfig(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "process_name": process_name,
                "window_name": process_window_name,
                "num_attributes": len(attributes)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "process_name": "",
                "window_name": "",
                "num_attributes": 0
            }
    
    def initialize_memory(self) -> Dict[str, Any]:
        """
        Initialize memory subsystem.
        
        Returns:
            Dictionary with success, message, and process_id
        """
        try:
            request = pb2.InitializeMemoryRequest()
            response = self.stub.InitializeMemory(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "process_id": response.process_id
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "process_id": 0
            }
    
    def initialize_input(self, window_name: str = "") -> Dict[str, Any]:
        """
        Initialize input subsystem.
        
        Args:
            window_name: Optional window name override
        
        Returns:
            Dictionary with success and message
        """
        try:
            request = pb2.InitializeInputRequest()
            if window_name:
                request.window_name = window_name
            
            response = self.stub.InitializeInput(request)
            
            return {
                "success": response.success,
                "message": response.message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}"
            }
    
    def initialize_capture(self, window_name: str = "") -> Dict[str, Any]:
        """
        Initialize capture subsystem.
        
        Args:
            window_name: Optional window name override
        
        Returns:
            Dictionary with success, message, and window dimensions
        """
        try:
            request = pb2.InitializeCaptureRequest()
            if window_name:
                request.window_name = window_name
            
            response = self.stub.InitializeCapture(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "window_width": response.window_width,
                "window_height": response.window_height
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "window_width": 0,
                "window_height": 0
            }
    
    def get_server_status(self) -> Dict[str, Any]:
        """
        Get server initialization status.
        
        Returns:
            Dictionary with server status information
        """
        try:
            request = pb2.GetServerStatusRequest()
            response = self.stub.GetServerStatus(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "config_set": response.config_set,
                "memory_initialized": response.memory_initialized,
                "input_initialized": response.input_initialized,
                "capture_initialized": response.capture_initialized,
                "process_name": response.process_name,
                "window_name": response.window_name,
                "process_id": response.process_id
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "config_set": False,
                "memory_initialized": False,
                "input_initialized": False,
                "capture_initialized": False,
                "process_name": "",
                "window_name": "",
                "process_id": 0
            }
    
    def init_all(self, config_file: str, wait_time: float = 2.0) -> bool:
        """
        Convenience method to initialize all subsystems.
        
        Args:
            config_file: Path to TOML config file
            wait_time: Time to wait between config and memory init (seconds)
        
        Returns:
            True if all initialization succeeded, False otherwise
        """
        # Set config
        result = self.set_process_config(config_file)
        if not result["success"]:
            print(f"Failed to set config: {result['message']}")
            return False
        
        print(f"Config loaded - Process: {result['process_name']}, "
              f"Window: {result['window_name']}, "
              f"Attributes: {result['num_attributes']}")
        
        # Wait for process
        print(f"Waiting {wait_time}s for process to be ready...")
        time.sleep(wait_time)
        
        # Initialize memory
        result = self.initialize_memory()
        if not result["success"]:
            print(f"Failed to initialize memory: {result['message']}")
            return False
        print(f"Memory initialized (PID: {result['process_id']})")
        
        # Initialize input
        result = self.initialize_input()
        if not result["success"]:
            print(f"Failed to initialize input: {result['message']}")
            return False
        print("Input initialized")
        
        # Initialize capture
        result = self.initialize_capture()
        if not result["success"]:
            print(f"Failed to initialize capture: {result['message']}")
            return False
        print(f"Capture initialized ({result['window_width']}x{result['window_height']})")
        
        print("\n=== Initialization Complete! ===")
        return True
    
    # Attribute Operations
    
    def get_attribute(self, name: str) -> Dict[str, Any]:
        """
        Get attribute value from server.
        
        Args:
            name: Attribute name
        
        Returns:
            Dictionary with success, message, value, and value_type
        """
        try:
            request = pb2.GetSiphonRequest()
            request.attributeName = name
            
            response = self.stub.GetAttribute(request)
            
            if not response.success:
                return {
                    "success": False,
                    "message": response.message,
                    "value": None,
                    "value_type": None
                }
            
            # Extract value based on type
            value_case = response.WhichOneof("value")
            
            if value_case == "int_value":
                return {
                    "success": True,
                    "message": response.message,
                    "value": response.int_value,
                    "value_type": "int"
                }
            elif value_case == "float_value":
                return {
                    "success": True,
                    "message": response.message,
                    "value": response.float_value,
                    "value_type": "float"
                }
            elif value_case == "array_value":
                return {
                    "success": True,
                    "message": response.message,
                    "value": response.array_value,
                    "value_type": "array"
                }
            elif value_case == "bool_value":
                return {
                    "success": True,
                    "message": response.message,
                    "value": response.bool_value,
                    "value_type": "bool"
                }
            else:
                return {
                    "success": False,
                    "message": "No value returned from server",
                    "value": None,
                    "value_type": None
                }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "value": None,
                "value_type": None
            }
    
    def set_attribute(self, name: str, value: Union[int, float, bytes, bool], 
                     value_type: str) -> Dict[str, Any]:
        """
        Set attribute value on server.
        
        Args:
            name: Attribute name
            value: Value to set (int, float, bytes, or bool)
            value_type: Type string ("int", "float", "array", "bool")
        
        Returns:
            Dictionary with success and message
        """
        try:
            request = pb2.SetSiphonRequest()
            request.attributeName = name
            
            if value_type == "int":
                request.int_value = int(value)
            elif value_type == "float":
                request.float_value = float(value)
            elif value_type == "array":
                if isinstance(value, str):
                    value = hex_to_bytes(value)
                request.array_value = value
            elif value_type == "bool" or value_type == "binary":
                request.bool_value = bool(value)
            else:
                return {
                    "success": False,
                    "message": f"Unknown value type: {value_type}"
                }
            
            response = self.stub.SetAttribute(request)
            
            return {
                "success": response.success,
                "message": response.message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}"
            }
    
    # Input Control Methods
    
    def input_key_tap(self, keys: List[str], hold_ms: int = 50, 
                     delay_ms: int = 0) -> Dict[str, Any]:
        """
        Tap one or more keys.
        
        Args:
            keys: List of key names
            hold_ms: How long to hold keys (milliseconds)
            delay_ms: Delay between key presses (milliseconds)
        
        Returns:
            Dictionary with success and message
        """
        try:
            request = pb2.InputKeyTapRequest()
            request.keys.extend(keys)
            request.hold_ms = hold_ms
            request.delay_ms = delay_ms
            
            response = self.stub.InputKeyTap(request)
            
            return {
                "success": response.success,
                "message": response.message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}"
            }
    
    def input_key_toggle(self, key: str, toggle: bool) -> Dict[str, Any]:
        """
        Toggle key state (press or release).
        
        Args:
            key: Key name
            toggle: True to press, False to release
        
        Returns:
            Dictionary with success and message
        """
        try:
            request = pb2.InputKeyToggleRequest()
            request.key = key
            request.toggle = toggle
            
            response = self.stub.InputKeyToggle(request)
            
            return {
                "success": response.success,
                "message": response.message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}"
            }
    
    def move_mouse(self, delta_x: int, delta_y: int, steps: int = 1) -> Dict[str, Any]:
        """
        Move mouse by delta.
        
        Args:
            delta_x: X movement (pixels)
            delta_y: Y movement (pixels)
            steps: Number of interpolated steps
        
        Returns:
            Dictionary with success and message
        """
        try:
            request = pb2.MoveMouseRequest()
            request.delta_x = delta_x
            request.delta_y = delta_y
            request.steps = steps
            
            response = self.stub.MoveMouse(request)
            
            return {
                "success": response.success,
                "message": response.message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}"
            }
    
    # Capture Methods
    
    def capture_frame(self, as_image: bool = True) -> Optional[Union[Image.Image, Dict[str, Any]]]:
        """
        Capture a frame from the window.
        
        Args:
            as_image: If True, return PIL Image; if False, return dict with raw data
        
        Returns:
            PIL Image if as_image=True and successful, or dictionary with frame data
        """
        try:
            request = pb2.CaptureFrameRequest()
            response = self.stub.CaptureFrame(request)
            
            if not response.success or not response.frame:
                print(f"Capture failed: {response.message}")
                return None
            
            if as_image:
                # Convert BGRA to RGBA
                pixel_array = bytearray(response.frame)
                for i in range(0, len(pixel_array), 4):
                    # Swap B and R channels
                    pixel_array[i], pixel_array[i+2] = pixel_array[i+2], pixel_array[i]
                
                # Create PIL Image
                img = Image.frombytes("RGBA", (response.width, response.height), 
                                     bytes(pixel_array))
                return img
            else:
                return {
                    "success": True,
                    "pixels": response.frame,
                    "width": response.width,
                    "height": response.height,
                    "message": response.message
                }
        except grpc.RpcError as e:
            print(f"RPC failed: {e.details()}")
            return None
    
    def capture_and_save(self, filename: str) -> bool:
        """
        Capture frame and save to file.
        
        Args:
            filename: Output filename (format auto-detected)
        
        Returns:
            True if successful, False otherwise
        """
        frame_data = self.capture_frame(as_image=False)
        
        if not frame_data or not frame_data["success"]:
            return False
        
        return save_frame_image(frame_data["pixels"], frame_data["width"], 
                               frame_data["height"], filename)
    
    # Command Execution
    
    def execute_command(self, command: str, args: List[str] = None,
                       working_directory: str = "", timeout_seconds: int = 30,
                       capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute command on remote system.
        
        Args:
            command: Command to execute
            args: Command arguments
            working_directory: Working directory for command
            timeout_seconds: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            Dictionary with execution results
        """
        if args is None:
            args = []
        
        try:
            request = pb2.ExecuteCommandRequest()
            request.command = command
            request.args.extend(args)
            request.working_directory = working_directory
            request.timeout_seconds = timeout_seconds
            request.capture_output = capture_output
            
            response = self.stub.ExecuteCommand(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "exit_code": response.exit_code,
                "stdout": response.stdout_output,
                "stderr": response.stderr_output,
                "execution_time_ms": response.execution_time_ms
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "execution_time_ms": 0
            }
    
    # Recording Methods
    
    def start_recording(self, attribute_names: List[str], output_directory: str,
                       max_duration_seconds: int = 0) -> Dict[str, Any]:
        """
        Start recording session.
        
        Args:
            attribute_names: List of attributes to record
            output_directory: Directory to save recording
            max_duration_seconds: Max duration (0 = unlimited)
        
        Returns:
            Dictionary with success, message, and session_id
        """
        try:
            request = pb2.StartRecordingRequest()
            request.attribute_names.extend(attribute_names)
            request.output_directory = output_directory
            request.max_duration_seconds = max_duration_seconds
            
            response = self.stub.StartRecording(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "session_id": response.session_id
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "session_id": ""
            }
    
    def stop_recording(self, session_id: str) -> Dict[str, Any]:
        """
        Stop recording session.
        
        Args:
            session_id: Recording session ID
        
        Returns:
            Dictionary with recording statistics
        """
        try:
            request = pb2.StopRecordingRequest()
            request.session_id = session_id
            
            response = self.stub.StopRecording(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "total_frames": response.total_frames,
                "average_latency_ms": response.average_latency_ms,
                "dropped_frames": response.dropped_frames,
                "actual_duration_seconds": response.actual_duration_seconds,
                "actual_fps": response.actual_fps
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "total_frames": 0,
                "average_latency_ms": 0.0,
                "dropped_frames": 0,
                "actual_duration_seconds": 0.0,
                "actual_fps": 0.0
            }
    
    def get_recording_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get recording session status.
        
        Args:
            session_id: Recording session ID
        
        Returns:
            Dictionary with recording status
        """
        try:
            request = pb2.GetRecordingStatusRequest()
            request.session_id = session_id
            
            response = self.stub.GetRecordingStatus(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "is_recording": response.is_recording,
                "current_frame": response.current_frame,
                "elapsed_time_seconds": response.elapsed_time_seconds,
                "current_latency_ms": response.current_latency_ms,
                "dropped_frames": response.dropped_frames
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "is_recording": False,
                "current_frame": 0,
                "elapsed_time_seconds": 0.0,
                "current_latency_ms": 0.0,
                "dropped_frames": 0
            }
    
    def download_recording(self, session_id: str, output_dir: str, 
                          show_progress: bool = True) -> bool:
        """
        Download recording files from server to directory.
        
        This downloads all recording files (video, inputs, memory) to the specified directory.
        
        Args:
            session_id: Recording session ID
            output_dir: Local directory to save files
            show_progress: Whether to show progress
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from pathlib import Path
            
            request = pb2.DownloadRecordingRequest()
            request.session_id = session_id
            
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if show_progress:
                print(f"Downloading recording to: {output_path}")
            
            current_file = None
            current_filename = ""
            total_bytes_received = 0
            file_bytes_received = 0
            file_size = 0
            chunks_received = 0
            files_received = 0
            
            # Stream chunks
            for chunk in self.stub.DownloadRecording(request):
                # Check if we need to open a new file
                if chunk.filename != current_filename:
                    # Close previous file if open
                    if current_file is not None:
                        current_file.close()
                        if show_progress:
                            print(f"\n✓ Completed: {current_filename} ({file_bytes_received} bytes)")
                        files_received += 1
                    
                    # Open new file
                    current_filename = chunk.filename
                    file_bytes_received = 0
                    file_size = chunk.total_size
                    
                    file_path = output_path / current_filename
                    current_file = open(file_path, 'wb')
                    
                    if show_progress:
                        print(f"Downloading: {current_filename} ({file_size} bytes)")
                
                # Write chunk data to file
                current_file.write(chunk.data)
                
                total_bytes_received += len(chunk.data)
                file_bytes_received += len(chunk.data)
                chunks_received += 1
                
                # Show progress for large files
                if show_progress and file_size > 10 * 1024 * 1024 and (chunks_received % 10 == 0 or chunk.is_final):
                    progress = (file_bytes_received * 100.0) / file_size if file_size > 0 else 0
                    print(f"\r  Progress: {progress:.1f}% ({file_bytes_received}/{file_size} bytes)", 
                          end='', flush=True)
                
                if chunk.is_final:
                    if current_file is not None:
                        current_file.close()
                        current_file = None
                        if show_progress:
                            print(f"\n✓ Completed: {current_filename} ({file_bytes_received} bytes)")
                        files_received += 1
                    break
            
            # Close file if still open
            if current_file is not None:
                current_file.close()
            
            if show_progress:
                print(f"\n✓ Download complete!")
                print(f"  Files received: {files_received}")
                print(f"  Total size: {total_bytes_received} bytes")
                print(f"  Saved to: {output_path}")
            
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            if current_file is not None:
                current_file.close()
            return False
    
    # Streaming Methods
    
    def stream_frames(self, format: str = "jpeg", quality: int = 85, 
                     max_frames: int = 0, callback=None) -> Dict[str, Any]:
        """
        Stream frames from server (blocking).
        
        Args:
            format: Frame format ("jpeg" or "raw")
            quality: JPEG quality (1-100, only used for jpeg format)
            max_frames: Maximum frames to receive (0 = unlimited)
            callback: Optional callback function called for each frame
                     Signature: callback(frame_data: FrameData) -> bool
                     Return False to stop streaming
        
        Returns:
            Dictionary with streaming statistics
        """
        try:
            import time
            
            request = pb2.StreamFramesRequest()
            request.format = format
            request.quality = quality
            
            print(f"Starting frame stream ({format}, quality={quality})")
            if max_frames > 0:
                print(f"Max frames: {max_frames}")
            else:
                print("Press Ctrl+C to stop streaming")
            
            frames_received = 0
            start_time = time.time()
            last_print_time = start_time
            
            try:
                for frame_data in self.stub.StreamFrames(request):
                    frames_received += 1
                    
                    # Call user callback if provided
                    if callback is not None:
                        try:
                            if callback(frame_data) is False:
                                break
                        except Exception as e:
                            print(f"\nCallback error: {e}")
                            break
                    
                    # Print status every second
                    now = time.time()
                    elapsed_since_start = now - start_time
                    elapsed_since_print = now - last_print_time
                    
                    if elapsed_since_print >= 1.0:
                        avg_fps = frames_received / elapsed_since_start if elapsed_since_start > 0 else 0
                        data_size_kb = len(frame_data.data) / 1024.0
                        
                        print(f"\rFrames: {frames_received} | FPS: {avg_fps:.1f} | "
                              f"Size: {frame_data.width}x{frame_data.height} | "
                              f"Frame #{frame_data.frame_number} | "
                              f"Data: {data_size_kb:.1f} KB", end='', flush=True)
                        last_print_time = now
                    
                    # Stop after max frames if specified
                    if max_frames > 0 and frames_received >= max_frames:
                        print(f"\nReached max frames limit: {max_frames}")
                        break
            
            except KeyboardInterrupt:
                print("\n\nStreaming interrupted by user")
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_fps = frames_received / total_time if total_time > 0 else 0
            
            print("\n\n=== Streaming Complete ===")
            print(f"Total frames received: {frames_received}")
            print(f"Duration: {total_time:.2f}s")
            print(f"Average FPS: {avg_fps:.2f}")
            
            return {
                "success": True,
                "frames_received": frames_received,
                "duration_seconds": total_time,
                "average_fps": avg_fps
            }
        
        except grpc.RpcError as e:
            print(f"Streaming failed: {e.details()}")
            return {
                "success": False,
                "message": f"RPC failed: {e.details()}",
                "frames_received": 0,
                "duration_seconds": 0.0,
                "average_fps": 0.0
            }
    
    def stream_frames_to_callback(self, callback, format: str = "jpeg", 
                                  quality: int = 85, max_frames: int = 0) -> Dict[str, Any]:
        """
        Stream frames and call callback for each frame.
        
        This is a convenience wrapper around stream_frames() for simple callback usage.
        
        Args:
            callback: Callback function(frame_data) -> bool. Return False to stop.
            format: Frame format ("jpeg" or "raw")
            quality: JPEG quality (1-100)
            max_frames: Maximum frames (0 = unlimited)
        
        Returns:
            Dictionary with streaming statistics
        """
        return self.stream_frames(format=format, quality=quality, 
                                 max_frames=max_frames, callback=callback)
    
    # Non-Blocking Streaming with Polling
    
    class FrameStreamHandle:
        """Handle for non-blocking frame streaming with polling."""
        
        def __init__(self):
            self.is_running = True
            self.stream_thread: Optional[threading.Thread] = None
            self.frame_mutex = threading.Lock()
            self.latest_frame: Optional[pb2.FrameData] = None
            self.has_new_frame = False
            self.frames_received = 0
            self.start_time = time.time()
        
        def stop(self):
            """Stop the streaming thread."""
            self.is_running = False
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=5.0)
        
        def __del__(self):
            """Cleanup when handle is destroyed."""
            self.stop()
    
    def start_frame_stream(self, format: str = "jpeg", quality: int = 85) -> 'SiphonClient.FrameStreamHandle':
        """
        Start non-blocking frame stream in background thread.
        
        This starts a background thread that continuously receives frames from the server.
        Only the latest frame is kept - older frames are dropped. Use get_latest_frame()
        to poll for new frames in your control loop.
        
        Args:
            format: Frame format ("jpeg" or "raw")
            quality: JPEG quality (1-100, only used for jpeg format)
        
        Returns:
            FrameStreamHandle that can be polled for frames
        
        Example:
            ```python
            # Start non-blocking stream
            handle = client.start_frame_stream(format="jpeg", quality=85)
            
            # Control loop
            while your_condition:
                frame = client.get_latest_frame(handle)
                if frame:
                    # Process frame (run AI, computer vision, etc.)
                    process_frame(frame)
                    
                    # Send commands based on processing
                    client.input_key_tap(["w"], 50, 0)
                else:
                    time.sleep(0.005)  # Brief sleep if no new frame
            
            # Stop stream
            client.stop_frame_stream(handle)
            ```
        """
        handle = self.FrameStreamHandle()
        handle.start_time = time.time()
        
        def stream_worker():
            """Background thread that receives frames."""
            try:
                request = pb2.StreamFramesRequest()
                request.format = format
                request.quality = quality
                
                print(f"Frame stream started ({format}, quality={quality})")
                
                for frame_data in self.stub.StreamFrames(request):
                    if not handle.is_running:
                        break
                    
                    with handle.frame_mutex:
                        handle.latest_frame = frame_data
                        handle.has_new_frame = True
                        handle.frames_received += 1
                
            except grpc.RpcError as e:
                if e.code() != grpc.StatusCode.CANCELLED:
                    print(f"Stream error: {e.details()}")
            except Exception as e:
                print(f"Stream error: {e}")
        
        handle.stream_thread = threading.Thread(target=stream_worker, daemon=True)
        handle.stream_thread.start()
        
        return handle
    
    def get_latest_frame(self, handle: 'SiphonClient.FrameStreamHandle') -> Optional[pb2.FrameData]:
        """
        Get latest frame from non-blocking stream (non-blocking poll).
        
        Args:
            handle: FrameStreamHandle from start_frame_stream()
        
        Returns:
            Latest FrameData if a new frame is available, None otherwise.
            After returning a frame, it's marked as consumed until a new one arrives.
        """
        if not handle or not handle.has_new_frame:
            return None
        
        with handle.frame_mutex:
            if not handle.has_new_frame:
                return None
            
            frame = handle.latest_frame
            handle.has_new_frame = False  # Mark as consumed
            return frame
    
    def stop_frame_stream(self, handle: 'SiphonClient.FrameStreamHandle'):
        """
        Stop non-blocking frame stream.
        
        Args:
            handle: FrameStreamHandle from start_frame_stream()
        """
        if handle:
            handle.stop()

