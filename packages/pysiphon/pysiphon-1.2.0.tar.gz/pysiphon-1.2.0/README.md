# pysiphon

Python gRPC client for Siphon service - provides memory manipulation, input control, screen capture, and recording capabilities.

📚 **[Documentation](https://pysiphon.dhmnr.sh)**

## Features


- **Dual-Mode CLI**: Interactive REPL and single-command execution
- **Programmatic API**: Use as a Python library
- **Complete RPC Coverage**: All Siphon service methods supported
  - Memory manipulation (read/write attributes)
  - Input control (keyboard, mouse)
  - Screen capture
  - Command execution
  - Recording sessions with HDF5 output
  - Frame streaming (JPEG/raw) with real-time processing

## Installation

```bash
pip install pysiphon
```

## Usage

### CLI - Interactive Mode

Start an interactive session:

```bash
pysiphon interactive
```

Example session:
```
> init config.toml
> status
> get health
> set speed int 100
> capture screenshot.png
> input w,a,s,d 50 10
> rec-start ./output health,mana,position 30
> rec-stop <session-id>
> quit
```

### CLI - Single Command Mode

Execute individual commands:

```bash
# Initialize from config
pysiphon init config.toml

# Check server status
pysiphon status

# Get/set attributes
pysiphon get health
pysiphon set speed int 100
pysiphon set position array "6D DE AD BE EF"

# Input control
pysiphon input w,a,s,d 50 10
pysiphon toggle shift 1
pysiphon move 100 50 10

# Screen capture
pysiphon capture screenshot.png

# Execute remote commands
pysiphon exec notepad.exe

# Recording
pysiphon rec-start ./output health,mana 30
pysiphon rec-status <session-id>
pysiphon rec-stop <session-id>
pysiphon rec-download <session-id> ./recordings

# Frame streaming (blocking)
pysiphon stream --format jpeg --quality 85 --max-frames 100

# Non-blocking frame stream with control loop
pysiphon stream-loop --format jpeg --quality 85 --duration 10
```

### Custom Server Address

```bash
pysiphon --host 192.168.1.100:50051 interactive
pysiphon --host 192.168.1.100:50051 status
```

### Programmatic API

Use pysiphon as a Python library:

```python
from pysiphon import SiphonClient

# Create client
with SiphonClient("localhost:50051") as client:
    # Initialize all subsystems
    client.init_all("config.toml")
    
    # Get/set attributes
    result = client.get_attribute("health")
    print(f"Health: {result['value']}")
    
    client.set_attribute("speed", 100, "int")
    
    # Input control
    client.input_key_tap(["w", "a", "s", "d"], hold_ms=50, delay_ms=10)
    client.move_mouse(delta_x=100, delta_y=50, steps=10)
    
    # Capture frame
    image = client.capture_frame(as_image=True)  # Returns PIL Image
    image.save("screenshot.png")
    
    # Or save directly
    client.capture_and_save("screenshot.jpg")
    
    # Execute commands
    result = client.execute_command("notepad.exe")
    print(f"Exit code: {result['exit_code']}")
    
    # Recording
    result = client.start_recording(
        attribute_names=["health", "mana"],
        output_directory="./recordings",
        max_duration_seconds=30
    )
    session_id = result["session_id"]
    
    # Check status
    status = client.get_recording_status(session_id)
    print(f"Frames: {status['current_frame']}")
    
    # Stop and download
    stats = client.stop_recording(session_id)
    print(f"FPS: {stats['actual_fps']:.1f}")
    
    client.download_recording(session_id, "./recordings")
    
    # Frame streaming (blocking with callback)
    def process_frame(frame_data):
        print(f"Frame {frame_data.frame_number}: {frame_data.width}x{frame_data.height}")
        return True  # Return False to stop streaming
    
    result = client.stream_frames_to_callback(
        process_frame, 
        format="jpeg", 
        quality=85, 
        max_frames=100
    )
    print(f"Streamed {result['frames_received']} frames at {result['average_fps']:.1f} FPS")
    
    # Non-blocking frame streaming with polling (for control loops)
    # Start background stream
    handle = client.start_frame_stream(format="jpeg", quality=85)
    
    # Control loop - process frames and send commands
    import time
    start_time = time.time()
    frames_processed = 0
    
    while time.time() - start_time < 10:  # Run for 10 seconds
        # Poll for latest frame (non-blocking)
        frame = client.get_latest_frame(handle)
        
        if frame:
            frames_processed += 1
            
            # Process frame (run AI, computer vision, etc.)
            # Example: decode JPEG, analyze pixels, make decisions
            print(f"Processing frame {frame.frame_number}")
            
            # Send commands based on frame analysis
            if frames_processed % 30 == 0:  # Every ~2 seconds at 15fps
                client.input_key_tap(["w"], 50, 0)
        else:
            # No new frame yet, sleep briefly
            time.sleep(0.005)
    
    # Stop stream
    client.stop_frame_stream(handle)
    print(f"Processed {frames_processed} frames")
```

## Documentation

Full documentation is available with MkDocs:

```bash
# Install docs dependencies
uv sync --group docs

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```


## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- All features have corresponding CLI commands
- API methods return consistent dictionary structures
- Documentation is updated

<!-- See [Contributing Guide](docs/development/contributing.md) for details. -->

