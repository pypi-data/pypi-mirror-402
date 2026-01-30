from dataclasses import dataclass
@dataclass
class MonitorCaptureConfig:
    monitor_index: int = 1
    output_file: str = 'screenshot.png'
    target_text: str = 'html'
    functions: str = None
    target_image: str = None
