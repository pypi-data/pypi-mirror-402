#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
from mcp.server.fastmcp import FastMCP, Context
from typing import List, Dict, Any
from mcp_vms_config import vms_config

import vmspy # type: ignore

DATA_DIR = "./data"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

# Configure logging: first disable other loggers
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)

# Configure our logger
log_filename = os.path.join(DATA_DIR, datetime.now().strftime("%d-%m-%y.log"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create handlers
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(formatter)

# Set up our logger
logger = logging.getLogger("vms-mcp")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# Prevent double logging
logger.propagate = False

# Create a FastMCP server instance
mcp = FastMCP("image-service")

# Create vmspy instances
vms_live_video = vmspy.live_video()
vms_playback = vmspy.playback()
vms_utils = vmspy.utils()

@mcp.tool()
async def get_channels(ctx: Context) -> str:
    """
    Return a list of dictionaries containing video channel information.

    Each dictionary contains the following keys:
    - ch_no: The channel number.
    - title: The name or title of the channel.
    - is_connected: A boolean indicating whether the channel is currently connected.
    - is_recording: A boolean indicating whether the channel is currently recording.
    - is_ptz: A boolean indicating whether the channel is a PTZ (Pan-Tilt-Zoom) camera.
    - ptz_prestes: A list of PTZ presets, available only when is_ptz is True.
    - time_start: The earliest recording time of the channel
    - time_end: The latest recording time of the channel
    - sub_channel_count: The number of sub-channels associated with this channel.

    Args:
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the channel information.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
            channels = vms_utils.get_channel_list()
            logger.debug("Returning names: {}".format(channels))
            import json
            return json.dumps(channels)
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Failed to get channel list: {}".format(error_msg))
            logger.debug("Failed to get channel list: {}".format(error_msg))
            import json
            return json.dumps([])
    except Exception as e:
        logger.exception("Error in get_names")
        ctx.error("Failed to retrieve names: {}".format(str(e)))
        import json
        return json.dumps([])

@mcp.tool()
async def get_channel_groups(ctx: Context) -> str:
    """
    Return the list of channel groups along with their member channels.

    Each group contains the following keys:
    - title: The name of the group.
    - group_idx: The index of the group.
    - channels: A list of channels in the group, where each channel contains:
        - ch_no: The channel number.
        - title: The name or title of the channel.

    Args:
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the channel groups.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
            groups = vms_utils.get_group_list()
            logger.debug("Retrieved channel groups: {}".format(groups))
            import json
            return json.dumps(groups)
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Failed to retrieve channel groups: {}".format(error_msg))
            logger.error("Failed to retrieve channel groups: {}".format(error_msg))
            import json
            return json.dumps([])
    except Exception as e:
        logger.exception("Error in get_channel_groups")
        ctx.error("Failed to retrieve channel groups: {}".format(str(e)))
        import json
        return json.dumps([])

@mcp.tool()
async def get_recording_dates(year: int, month: int, ctx: Context) -> str:
    """
    Retrieve recording dates for video channels for a specific year and month.

    This function fetches the recording dates for all channels within the specified time range.

    Args:
        year: The year for which to retrieve recording dates.
        month: The month for which to retrieve recording dates.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the recording dates.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
            recording_dates = vms_utils.get_recording_dates(year, month)
            logger.debug("Retrieved recording dates for {}-{}: {}".format(year, month, recording_dates))
            import json
            return json.dumps(recording_dates)
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Fail to get recorind dates for {}-{}: {}".format(year, month, error_msg))
            logger.error(error_msg)
            import json
            return json.dumps([])
    except Exception as e:
        logger.exception("Error in get_recording_dates for {}-{}".format(year, month))
        ctx.error("Failed to retrieve recording dates for {}-{}: {}".format(year, month, str(e)))
        import json
        return json.dumps([])

@mcp.tool()
async def get_recording_times(ch_no: int, sub_idx: int, year: int, month: int, day: int, ctx: Context) -> str:
    """
    Retrieve recording times for a specific channel, sub-channel, and date.

    This function fetches the recording times for a given channel and sub-channel on a specific day.

    Args:
        ch_no: The channel number.
        sub_idx: The sub-channel index.
        year: The year for which to retrieve recording times.
        month: The month for which to retrieve recording times.
        day: The day for which to retrieve recording times.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the recording times.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
            recording_times = vms_utils.get_recording_times(ch_no, year, month, day, sub_idx)
            logger.debug("Retrieved recording times for channel {}, sub-channel {} on {}-{}-{}: {}".format(
                ch_no, sub_idx, year, month, day, recording_times))
            import json
            return json.dumps({
                "ch": ch_no,
                "sub": sub_idx,
                "title": "Channel {}".format(ch_no),
                "recordings": recording_times
            })
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Fail to get recording times for channel {}: {}".format(ch_no, error_msg))
            logger.error(error_msg)
            import json
            return json.dumps([])
    except Exception as e:
        logger.exception("Error in get_recording_times for channel {}, sub-channel {} on {}-{}-{}".format(
            ch_no, sub_idx, year, month, day))
        ctx.error("Failed to retrieve recording times for channel {}, sub-channel {} on {}-{}-{}: {}".format(
            ch_no, sub_idx, year, month, day, str(e)))
        import json
        return json.dumps([])

@mcp.tool()
async def get_events(ch_no: int, year: int, month: int, day: int, num_days: int = 1, ctx: Context = None) -> str:
    """
    Retrieve events for a specific date and channel.

    If the channel number is zero (0), events for all channels are retrieved.

    Args:
        ch_no: The channel number. Use 0 to retrieve events for all channels.
        year: The year of the events to retrieve.
        month: The month of the events to retrieve.
        day: The day of the events to retrieve.
        num_days: The number of days to retrieve events for (default: 1).
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the events.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
            events = vms_utils.get_events(ch_no, year, month, day, num_days)
            logger.debug("Retrieved events for channel {} on {}-{}-{} for {} day(s): {}".format(
                ch_no, year, month, day, num_days, events))
            import json
            return json.dumps(events)
        else:
            error_msg = vms_utils.get_error()
            if ctx:
                ctx.error("Failed to retrieve events for channel {}: {}".format(ch_no, error_msg))
            logger.error("Failed to retrieve events for channel {}: {}".format(ch_no, error_msg))
            import json
            return json.dumps([])
    except Exception as e:
        logger.exception("Error while retrieving events for channel {} on {}-{}-{}: {}".format(
            ch_no, year, month, day, str(e)))
        if ctx:
            ctx.error("An unexpected error occurred: {}".format(str(e)))
        import json
        return json.dumps([])


@mcp.tool()
def fetch_live_image(ch_no: int, sub_idx: int, ctx: Context) -> str:
    """
    Fetch a specific live frame image from a video channel.

    This function retrieves a frame image for a given channel, sub-channel, and timestamp.

    Args:
        ch_id: The channel ID.
        sub_idx: The sub-channel index.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the base64 encoded image or error message.
    """
    import base64
    if vms_live_video.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
        vms_live_video.set_image_size(vms_config['img_width'], vms_config['img_height'])
        vms_live_video.set_pixel_format(vms_config['pixel_format'])

        frame_image, frame_info = vms_live_video.get_image(ch_no, sub_idx)

        if frame_image is None:
            error_msg = "Failed to fetch live image for channel {}, sub-channel {}.".format(ch_no, sub_idx)
            ctx.error(error_msg)
            logger.error(error_msg)
            import json
            return json.dumps({"error": error_msg})

        # Convert the numpy array (frame_image) to a JPEG using PIL
        img = PILImage.fromarray(frame_image)
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="JPEG")
        image_data = img_byte_arr.getvalue()

        # with open("output_image.jpg", "wb") as f:
        #     f.write(image_data)
        logger.debug("Fetched live image for channel {}, sub-channel {}.".format(ch_no, sub_idx))
        import json
        return json.dumps({
            "image": base64.b64encode(image_data).decode('utf-8'),
            "format": "jpeg"
        })
    else:
        error_msg = "Failed to initialize connection to retrieve recording times for channel {}, sub-channel {}.".format(ch_no, sub_idx)
        ctx.error(error_msg)
        logger.error(error_msg)
        import json
        return json.dumps({"error": error_msg})

@mcp.tool()
async def fetch_recorded_image(ch_no: int, sub_idx: int, year: int, month: int, day: int, hour: int, minute: int, second: int, ctx: Context) -> str:
    """
    Fetch a specific recorded frame image from a video channel.

    This function retrieves a frame image for a given channel, sub-channel, and timestamp.

    Args:
        ch_id: The channel ID.
        sub_idx: The sub-channel index.
        year: The year of the frame to fetch.
        month: The month of the frame to fetch.
        day: The day of the frame to fetch.
        hour: The hour of the frame to fetch.
        minute: The minute of the frame to fetch.
        second: The second of the frame to fetch.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the base64 encoded image or error message.
    """
    import base64
    if vms_playback.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
        vms_playback.set_image_size(vms_config['img_width'], vms_config['img_height'])
        vms_playback.set_pixel_format(vms_config['pixel_format'])

        frame_image, frame_info = vms_playback.get_image(ch_no, year, month, day, hour, minute, second, sub_idx)

        if frame_image is None:
            error_msg = "Failed to fetch recorded image for channel {}, sub-channel {} at {}-{}-{} {}:{}:{}. ({})".format(
                ch_no, sub_idx, year, month, day, hour, minute, second, frame_info.get("error", "unknown error"))
            ctx.error(error_msg)
            logger.error(error_msg)
            import json
            return json.dumps({"error": error_msg})

        # Convert the numpy array (frame_image) to a JPEG using PIL
        img = PILImage.fromarray(frame_image)
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="JPEG")
        image_data = img_byte_arr.getvalue()

        logger.debug("Fetched recorded image for channel {}, sub-channel {} at {}-{}-{} {}:{}:.".format(
            ch_no, sub_idx, year, month, day, hour, minute, second))
        import json
        return json.dumps({
            "image": base64.b64encode(image_data).decode('utf-8'),
            "format": "jpeg"
        })
    else:
        error_msg = "Failed to initialize connection to retrieve recording times for channel {}, sub-channel {} on {}-{}-{}.".format(
            ch_no, sub_idx, year, month, day)
        ctx.error(error_msg)
        logger.error(error_msg)
        import json
        return json.dumps({"error": error_msg})

@mcp.tool()
async def move_ptz_to_preset(ch_no: int, preset_no: int, ctx: Context) -> str:
    """
    Move a PTZ camera to a specified preset position.

    Args:
        ch_no: The channel number of the PTZ camera.
        preset_no: The preset number to move the camera to.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string indicating success or failure.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']) \
            and vms_utils.ptz_preset_go(ch_no, preset_no):
            logger.debug("Moved PTZ camera on channel {} to preset {}.".format(ch_no, preset_no))
            import json
            return json.dumps({"success": True})
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Failed to move PTZ camera on channel {} to preset {}: {}".format(ch_no, preset_no, error_msg))
            logger.error(error_msg)
            import json
            return json.dumps({"success": False, "error": error_msg})

    except Exception as e:
        logger.exception("Error while moving PTZ camera on channel {} to preset {}: {}".format(ch_no, preset_no, str(e)))
        ctx.error("An unexpected error occurred: {}".format(str(e)))
        import json
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def get_ptz_preset(ch_no: int, ctx: Context) -> str:
    """
    Retrieve the PTZ preset position information for a specific channel.

    Args:
        ch_no: The channel number.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string containing the PTZ preset position.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']):
            preset = vms_utils.get_ptz_preset(ch_no)
            if preset and preset["status"] == "ok":
                logger.debug("Retrieved PTZ presets for channel {}: presetNo={}".format(ch_no, preset["no"]))
                import json
                return json.dumps(preset)
            else:
                error_msg = preset["status"]
                ctx.error(error_msg)
                logger.error(error_msg)
                import json
                return json.dumps([{"no": None, "title": None, "status": error_msg}])
        else:
            error_msg = "Failed to initialize connection to retrieve PTZ presets for channel {}.".format(ch_no)
            ctx.error(error_msg)
            logger.error(error_msg)
            import json
            return json.dumps([{"no": None, "title": None, "status": error_msg}])
    except Exception as e:
        logger.exception("Error while retrieving PTZ presets for channel {}: {}".format(ch_no, str(e)))
        ctx.error("An unexpected error occurred: {}".format(str(e)))
        import json
        return json.dumps([{"no": None, "title": None, "status": "Error: {}".format(str(e))}])

@mcp.tool()
async def show_live_video(ch_no: int, sub_idx: int, ctx: Context) -> str:
    """
    Show the live video stream of a specific channel in the VMS program.

    Args:
        ch_no: The channel number.
        sub_idx: The sub-channel index.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string indicating success or failure.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']) \
            and vms_utils.show_live(ch_no, sub_idx):
            logger.debug("Show live video for channel {}, sub-channel {}.".format(ch_no, sub_idx))
            import json
            return json.dumps({"success": True})
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Failed to show live video for channel {}, sub-channel {}: {}".format(ch_no, sub_idx, error_msg))
            logger.error("Failed to show live video for channel {}, sub-channel {}: {}".format(ch_no, sub_idx, error_msg))
            import json
            return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        logger.exception("Error while showing live video for channel {}, sub-channel {}: {}".format(ch_no, sub_idx, str(e)))
        ctx.error("An unexpected error occurred: {}".format(str(e)))
        import json
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def show_playback_video(ch_no: int, year: int, month: int, day: int, hour: int, minute: int, second: int, sub_idx: int, ctx: Context) -> str:
    """
    Show the playback video stream of a specific channel at a specific timestamp in the VMS program.

    Args:
        ch_no: The channel number.
        year: The year of the playback timestamp.
        month: The month of the playback timestamp.
        day: The day of the playback timestamp.
        hour: The hour of the playback timestamp.
        minute: The minute of the playback timestamp.
        second: The second of the playback timestamp.
        sub_idx: The sub-channel index.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string indicating success or failure.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']) \
            and vms_utils.show_playback(ch_no, year, month, day, hour, minute, second, sub_idx):
            logger.debug("Playback video started for channel {}, sub-channel {} at {}-{}-{} {}:{}:.".format(
                ch_no, sub_idx, year, month, day, hour, minute, second))
            import json
            return json.dumps({"success": True})
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Failed to show playback video for channel {}, sub-channel {} at {}-{}-{} {}:{}:{}: {}".format(
                ch_no, sub_idx, year, month, day, hour, minute, second, error_msg))
            logger.error(error_msg)
            import json
            return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        logger.exception("Error while showing playback video for channel {}, sub-channel {} at {}-{}-{} {}:{}:{}: {}".format(
            ch_no, sub_idx, year, month, day, hour, minute, second, str(e)))
        ctx.error("An unexpected error occurred: {}".format(str(e)))
        import json
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def show_group_live_video(group_idx: int, ctx: Context) -> str:
    """
    Show the live video streams of a specific group in the VMS program.

    Args:
        group_idx: The index of the group.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string indicating success or failure.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']) \
            and vms_utils.show_group_live(group_idx):
            logger.debug("Live video started for group {}.".format(group_idx))
            import json
            return json.dumps({"success": True})
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Failed to show live video for group {}: {}".format(group_idx, error_msg))
            logger.error("Failed to show live video for group {}: {}".format(group_idx, error_msg))
            import json
            return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        logger.exception("Error while showing live video for group {}: {}".format(group_idx, str(e)))
        ctx.error("An unexpected error occurred: {}".format(str(e)))
        import json
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def show_group_playback_video(group_idx: int, year: int, month: int, day: int, hour: int, minute: int, second: int, ctx: Context) -> str:
    """
    Show the playback video streams of a specific group at a specific timestamp in the VMS program.

    Args:
        group_idx: The index of the group.
        year: The year of the playback timestamp.
        month: The month of the playback timestamp.
        day: The day of the playback timestamp.
        hour: The hour of the playback timestamp.
        minute: The minute of the playback timestamp.
        second: The second of the playback timestamp.
        ctx: The context object for logging or error handling.

    Returns:
        A JSON string indicating success or failure.
    """
    try:
        if vms_utils.init(vms_config['url'], vms_config['port'], vms_config['access_id'], vms_config['access_pw']) \
            and vms_utils.show_group_playback(group_idx, year, month, day, hour, minute, second):
            logger.debug("Playback video started for group {} at {}-{}-{} {}:{}:.".format(
                group_idx, year, month, day, hour, minute, second))
            import json
            return json.dumps({"success": True})
        else:
            error_msg = vms_utils.get_error()
            ctx.error("Failed to show playback video for group {} at {}-{}-{} {}:{}:{}: {}".format(
                group_idx, year, month, day, hour, minute, second, error_msg))
            logger.error("Failed to show playback video for group {} at {}-{}-{} {}:{}:{}: {}".format(
                group_idx, year, month, day, hour, minute, second, error_msg))
            import json
            return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        logger.exception("Error while showing playback video for group {} at {}-{}-{} {}:{}:{}: {}".format(
            group_idx, year, month, day, hour, minute, second, str(e)))
        ctx.error("An unexpected error occurred: {}".format(str(e)))
        import json
        return json.dumps({"success": False, "error": str(e)})

# Run the async main function
if __name__ == "__main__":
    mcp.run(transport='stdio')

def main():
    """Main entry point for the MCP server."""
    mcp.run(transport='stdio')
