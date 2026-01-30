"""
Mock vmspy module for testing purposes without actual VMS server.
"""

class VMSLiveVideo:
    """Mock live video class."""

    def init(self, url, port, access_id, access_pw):
        """Initialize connection to VMS server."""
        self.connected = True
        return True

    def set_image_size(self, width, height):
        """Set image size."""
        pass

    def set_pixel_format(self, pixel_format):
        """Set pixel format."""
        pass

    def get_image(self, ch_no, sub_idx):
        """Get image from channel."""
        import numpy as np
        # Return a dummy image
        return np.zeros((240, 320, 3), dtype=np.uint8), {"error": None}

class VMSPlayback:
    """Mock playback class."""

    def init(self, url, port, access_id, access_pw):
        """Initialize connection to VMS server."""
        self.connected = True
        return True

    def set_image_size(self, width, height):
        """Set image size."""
        pass

    def set_pixel_format(self, pixel_format):
        """Set pixel format."""
        pass

    def get_image(self, ch_no, year, month, day, hour, minute, second, sub_idx):
        """Get image from channel at specific time."""
        import numpy as np
        # Return a dummy image
        return np.zeros((240, 320, 3), dtype=np.uint8), {"error": None}

class VMSUtils:
    """Mock utils class."""

    def init(self, url, port, access_id, access_pw):
        """Initialize connection to VMS server."""
        self.connected = True
        self._error = None
        return True

    def get_error(self):
        """Get last error."""
        return self._error or "No error"

    def get_channel_list(self):
        """Get list of channels."""
        return [
            {
                "ch_no": 1,
                "title": "Camera 1",
                "is_connected": True,
                "is_recording": True,
                "is_ptz": True,
                "ptz_prestes": [{"no": 1, "title": "Preset 1"}, {"no": 2, "title": "Preset 2"}],
                "time_start": "2024-01-01T00:00:00",
                "time_end": "2024-12-31T23:59:59",
                "sub_channel_count": 1
            },
            {
                "ch_no": 2,
                "title": "Camera 2",
                "is_connected": True,
                "is_recording": False,
                "is_ptz": False,
                "ptz_prestes": [],
                "time_start": "2024-01-01T00:00:00",
                "time_end": "2024-12-31T23:59:59",
                "sub_channel_count": 1
            }
        ]

    def get_group_list(self):
        """Get list of channel groups."""
        return [
            {
                "title": "All Cameras",
                "group_idx": 0,
                "channels": [
                    {"ch_no": 1, "title": "Camera 1"},
                    {"ch_no": 2, "title": "Camera 2"}
                ]
            }
        ]

    def get_recording_dates(self, year, month):
        """Get recording dates for all channels."""
        return [
            {
                "ch_no": 1,
                "title": "Camera 1",
                "dates": [f"{year}-{month:02d}-{day:02d}" for day in range(1, 16)]
            },
            {
                "ch_no": 2,
                "title": "Camera 2",
                "dates": [f"{year}-{month:02d}-{day:02d}" for day in range(1, 16)]
            }
        ]

    def get_recording_times(self, ch_no, year, month, day, sub_idx):
        """Get recording times for a specific channel and date."""
        return [
            {"start": f"{year}-{month:02d}-{day:02d}T00:00:00", "duration": 3600},
            {"start": f"{year}-{month:02d}-{day:02d}T01:00:00", "duration": 3600},
            {"start": f"{year}-{month:02d}-{day:02d}T02:00:00", "duration": 3600}
        ]

    def get_events(self, ch_no, year, month, day, num_days=1):
        """Get events for a specific date and channel."""
        return [
            {
                "ch_no": ch_no if ch_no > 0 else 1,
                "type": "Motion",
                "time": f"{year}-{month:02d}-{day:02d}T10:00:00",
                "duration": 30
            },
            {
                "ch_no": ch_no if ch_no > 0 else 2,
                "type": "Sensor",
                "time": f"{year}-{month:02d}-{day:02d}T14:00:00",
                "duration": 60
            }
        ]

    def ptz_preset_go(self, ch_no, preset_no):
        """Move PTZ camera to preset position."""
        return True

    def get_ptz_preset(self, ch_no):
        """Get PTZ preset information."""
        return {
            "no": 1,
            "title": "Preset 1",
            "status": "ok"
        }

    def show_live(self, ch_no, sub_idx):
        """Show live video in VMS program."""
        return True

    def show_playback(self, ch_no, year, month, day, hour, minute, second, sub_idx):
        """Show playback video in VMS program."""
        return True

    def show_group_live(self, group_idx):
        """Show live video for group in VMS program."""
        return True

    def show_group_playback(self, group_idx, year, month, day, hour, minute, second):
        """Show playback video for group in VMS program."""
        return True

def live_video():
    """Create live video instance."""
    return VMSLiveVideo()

def playback():
    """Create playback instance."""
    return VMSPlayback()

def utils():
    """Create utils instance."""
    return VMSUtils()