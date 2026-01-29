# CV Stream Recorder

A Python tool to record video streams and save them into consecutive chunks using FFmpeg.

## Description

`cv-stream-recorder` connects to a video stream URL (e.g., HLS .m3u8) and records the content into segmented MP4 files. This is useful for capturing live streams for later processing or analysis.

## Features

- Records live video streams.
- Segments output into consecutive files (e.g., `chunk_000.mp4`, `chunk_001.mp4`).
- Stream copy mode (no transcoding) for minimal CPU usage.
- Configurable segment time and total duration.

## Requirements

- Python >= 3.11
- FFmpeg installed on your system
- `ffmpeg-python` library

## Installation

1.  **Install FFmpeg**:
    Ensure `ffmpeg` is installed and available in your system's PATH.

2.  **Install the package**:
    ```bash
    pip install cv-stream-recorder
    ```

## Usage

Import the module and use it in your code:

```python
import asyncio
import time
from cv_stream_recorder import record_stream, stop_recording


def done(path):
    print("Chunk saved to:", path)


async def main():
    url = "http://example.com/stream.m3u8"
    folder_path = "/path/to/output"

    pid = await record_stream(url, folder_path, done, segment_length=60)
    print("Recording started with PID:", pid)

    # Record for 3 minutes
    time.sleep(180)
    stop_recording(pid)


if __name__ == "__main__":
    asyncio.run(main())
```

By default, it will:
1.  Connect to the configured stream URL.
2.  Start recording.
3.  Save files as `chunk_000.mp4`, `chunk_001.mp4`, etc., in the target directory.
4.  Stop whenever the `stop_recording` function is called.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
