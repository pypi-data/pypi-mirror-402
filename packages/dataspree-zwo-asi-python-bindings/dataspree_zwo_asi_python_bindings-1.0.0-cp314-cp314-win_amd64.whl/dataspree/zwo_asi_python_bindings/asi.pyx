from typing import Optional

cimport dataspree.zwo_asi_python_bindings.casi as casi

# Declare the external C function and structs
cdef extern from "string.h":
    void memset(void *s, int c, size_t n)

from enum import IntEnum


class BayerPattern(IntEnum):
    BAYER_RG = 0
    BAYER_BG = 1
    BAYER_GR = 2
    BAYER_GB = 3


class ImgType(IntEnum):
    IMG_RAW8 = 0
    IMG_RGB24 = 1
    IMG_RAW16 = 2
    IMG_Y8 = 3
    IMG_END = -1


class ControlType(IntEnum):
    ASI_GAIN = 0
    ASI_EXPOSURE = 1
    ASI_GAMMA = 2
    ASI_WB_R = 3
    ASI_WB_B = 4
    ASI_OFFSET = 5
    ASI_BANDWIDTHOVERLOAD = 6
    ASI_OVERCLOCK = 7
    ASI_TEMPERATURE = 8
    ASI_FLIP = 9
    ASI_AUTO_MAX_GAIN = 10
    ASI_AUTO_MAX_EXP = 11
    ASI_AUTO_TARGET_BRIGHTNESS = 12
    ASI_HARDWARE_BIN = 13
    ASI_HIGH_SPEED_MODE = 14
    ASI_COOLER_POWER_PERC = 15
    ASI_TARGET_TEMP = 16
    ASI_COOLER_ON = 17
    ASI_MONO_BIN = 18
    ASI_FAN_ON = 19
    ASI_PATTERN_ADJUST = 20
    ASI_ANTI_DEW_HEATER = 21
    ASI_FAN_ADJUST = 22
    ASI_PWRLED_BRIGNT = 23
    ASI_USBHUB_RESET = 24
    ASI_GPS_SUPPORT = 25
    ASI_GPS_START_LINE = 26
    ASI_GPS_END_LINE = 27
    ASI_ROLLING_INTERVAL = 28


class CameraMode(IntEnum):
    ASI_MODE_NORMAL = 0
    ASI_MODE_TRIG_SOFT_EDGE = 1
    ASI_MODE_TRIG_RISE_EDGE = 2
    ASI_MODE_TRIG_FALL_EDGE = 3
    ASI_MODE_TRIG_SOFT_LEVEL = 4
    ASI_MODE_TRIG_HIGH_LEVEL = 5
    ASI_MODE_TRIG_LOW_LEVEL = 6
    ASI_MODE_END = -1


class GuideDirection(IntEnum):
    ASI_GUIDE_NORTH = 0
    ASI_GUIDE_SOUTH = 1
    ASI_GUIDE_EAST = 2
    ASI_GUIDE_WEST = 3


class FlipStatus(IntEnum):
    ASI_FLIP_NONE = 0  # original
    ASI_FLIP_HORIZ = 1  # horizontal flip
    ASI_FLIP_VERT = 2  #  vertical flip
    ASI_FLIP_BOTH = 3  # both horizontal and vertical flip


class TrigOutput(IntEnum):
    ASI_TRIG_OUTPUT_PINA = 0  # Only Pin A output
    ASI_TRIG_OUTPUT_PINB = 1  # Only Pin B output
    ASI_TRIG_OUTPUT_NONE = -1


class ExposureStatus(IntEnum):
    ASI_EXP_IDLE = 0  #idle states, you can start exposure now
    ASI_EXP_WORKING = 1  #exposing
    ASI_EXP_SUCCESS = 2  #exposure finished and waiting for download
    ASI_EXP_FAILED = 3  # failed, you need to start exposure again


class ASIError(Exception):
    """Base exception class for all ASI errors."""
    pass


class ASISuccess(ASIError):
    """ASI operation completed successfully."""
    pass


class ASIInvalidIndex(ASIError):
    """Invalid index: No camera connected or index value out of boundary."""
    pass


class ASIInvalidID(ASIError):
    """Invalid camera ID provided."""
    pass


class ASICameraClosed(ASIError):
    """Failed to open camera: Camera is closed."""
    pass


class ASICameraRemoved(ASIError):
    """Camera removed: Failed to find the camera, it might have been disconnected."""
    pass


class ASITimeout(ASIError):
    """Operation timed out."""
    pass


class ASIGeneralError(ASIError):
    """General error: Value is out of valid range."""
    pass


class ASIInvalidControlType(ASIError):
    """Invalid control type provided."""
    pass


class ASIInvalidPath(ASIError):
    """Invalid file path provided."""
    pass


class ASIInvalidFileFormat(ASIError):
    """Invalid file format provided."""
    pass


class ASIInvalidSize(ASIError):
    """Invalid video format size."""
    pass


class ASIInvalidImageType(ASIError):
    """Unsupported image format."""
    pass


class ASIOutOfBoundary(ASIError):
    """The start position is out of boundary."""
    pass


class ASIInvalidSequence(ASIError):
    """Stop capture first: Invalid sequence of operations."""
    pass


class ASIBufferTooSmall(ASIError):
    """Buffer size is too small for the operation."""
    pass


class ASIVideoModeActive(ASIError):
    """Operation failed because video mode is currently active."""
    pass


class ASIExposureInProgress(ASIError):
    """Cannot perform operation while exposure is in progress."""
    pass


class ASIInvalidMode(ASIError):
    """The current mode is incorrect for this operation."""
    pass


class ASIGPSNotSupported(ASIError):
    """GPS is not supported by this camera."""
    pass


class ASIGPSVersionError(ASIError):
    """The FPGA GPS version is too low for the requested operation."""
    pass


class ASIGPSFPGAError(ASIError):
    """Failed to read or write data to FPGA for GPS."""
    pass


class ASIGPSParamOutOfRange(ASIError):
    """GPS parameter out of range: Start line or end line must be between 0 and MaxHeight-1."""
    pass


class ASIGPSDataInvalid(ASIError):
    """Invalid GPS data: GPS has not found satellites or FPGA cannot read GPS data."""
    pass


class ASIErrorEnd(ASIError):
    """End of ASI error codes."""
    pass


class ASIUnknownErrorCode(ASIError):
    """End of ASI error codes."""
    pass


ASI_ERROR_CODE_TO_EXCEPTION: dict[int, ASIError] = {
    0: ASISuccess,
    1: ASIInvalidIndex,
    2: ASIInvalidID,
    3: ASICameraClosed,
    4: ASICameraRemoved,
    5: ASITimeout,
    6: ASIGeneralError,
    7: ASIInvalidIndex,
    8: ASIInvalidID,
    9: ASIInvalidControlType,
    10: ASICameraClosed,
    11: ASICameraRemoved,
    12: ASIInvalidPath,
    13: ASIInvalidFileFormat,
    14: ASIInvalidSize,
    15: ASIInvalidImageType,
    16: ASIOutOfBoundary,
    17: ASITimeout,
    18: ASIInvalidSequence,
    19: ASIBufferTooSmall,
    20: ASIVideoModeActive,
    21: ASIExposureInProgress,
    22: ASIGeneralError,
    23: ASIInvalidMode,
    24: ASIGPSNotSupported,
    25: ASIGPSVersionError,
    26: ASIGPSFPGAError,
    27: ASIGPSParamOutOfRange,
    28: ASIGPSDataInvalid,
    29: ASIErrorEnd
}

def handle_error_code(asi_error_code: int) -> None:
    try:
        raise ASI_ERROR_CODE_TO_EXCEPTION[asi_error_code]()
    except KeyError:
        raise ASIUnknownErrorCode(f'Unknown error code {asi_error_code}. Update wrapper.')
    except ASISuccess:
        pass

cdef class ControlCaps:
    cdef casi.ASI_CONTROL_CAPS control_caps

    def __init__(self):
        memset(&self.control_caps, 0, sizeof(casi.ASI_CONTROL_CAPS))

    @property
    def name(self) -> str:
        return self.control_caps.Name.decode('utf-8')

    @property
    def description(self) -> str:
        return self.control_caps.Description.decode('utf-8')

    @property
    def max_value(self) -> int:
        return self.control_caps.MaxValue

    @property
    def min_value(self) -> int:
        return self.control_caps.MinValue

    @property
    def default_value(self) -> int:
        return self.control_caps.DefaultValue

    @property
    def is_auto_supported(self) -> bool:
        return bool(self.control_caps.IsAutoSupported)

    @property
    def is_writable(self) -> bool:
        return bool(self.control_caps.IsWritable)

    @property
    def control_type(self) -> ControlType:
        return ControlType(self.control_caps.ControlType)

cdef class Id:
    cdef casi.ASI_ID c_id

    def __init__(self):
        memset(&self.c_id, 0, sizeof(casi.ASI_ID))

    @property
    def id(self) -> str:
        return self.c_id.id.decode('utf-8')

    @id.setter
    def id(self, identifier) -> None:
        self.c_id.id = identifier.encode('utf-8')

cdef class SupportedMode:
    cdef casi.ASI_SUPPORTED_MODE c_supported_mode

    def __init__(self):
        memset(&self.c_supported_mode, 0, sizeof(casi.ASI_SUPPORTED_MODE))

    @property
    def supported_camera_mode(self) -> list[CameraMode]:
        return [self.c_supported_mode.SupportedCamerMode[i] for i in range(16) if
                self.c_supported_mode.SupportedBins[i] != CameraMode.ASI_MODE_END.value]

cdef class GpsData:
    cdef casi.ASI_GPS_DATA c_gps_data

    def __init__(self):
        memset(&self.c_gps_data, 0, sizeof(casi.ASI_GPS_DATA))

    @property
    def latitude(self) -> float:
        return self.c_gps_data.Latitude

    @property
    def longitude(self) -> float:
        return self.c_gps_data.Longitude

    @property
    def altitude(self) -> int:
        return self.c_gps_data.Altitude

    @property
    def satellite_num(self) -> int:
        return self.c_gps_data.SatelliteNum

    @property
    def year(self) -> int:
        return self.c_gps_data.Datetime.Year

    @property
    def month(self) -> int:
        return self.c_gps_data.Datetime.Month

    @property
    def day(self) -> int:
        return self.c_gps_data.Datetime.Day

    @property
    def hour(self) -> int:
        return self.c_gps_data.Datetime.Hour

    @property
    def minute(self) -> int:
        return self.c_gps_data.Datetime.Minute

    @property
    def second(self) -> int:
        return self.c_gps_data.Datetime.Second

    @property
    def m_second(self) -> int:
        return self.c_gps_data.Datetime.Msecond

    @property
    def u_second(self) -> int:
        return self.c_gps_data.Datetime.Usecond

cdef class CameraInfo:
    cdef casi.ASI_CAMERA_INFO c_info

    def __init__(self):
        memset(&self.c_info, 0, sizeof(casi.ASI_CAMERA_INFO))

    @property
    def name(self) -> str:
        return self.c_info.Name.decode('utf-8')

    @name.setter
    def name(self, name) -> None:
        self.c_info.Name = name.encode('utf-8')

    @property
    def camera_id(self) -> int:
        return self.c_info.CameraID

    @property
    def max_height(self) -> int:
        return self.c_info.MaxHeight

    @property
    def max_width(self) -> int:
        return self.c_info.MaxWidth

    @property
    def is_color_camera(self) -> int:
        return bool(self.c_info.IsColorCam)

    @property
    def bayer_pattern(self) -> BayerPattern:
        return BayerPattern(self.c_info.BayerPattern)

    @property
    def supported_bins(self) -> list[int]:
        return [self.c_info.SupportedBins[i] for i in range(16) if self.c_info.SupportedBins[i] > 0]

    @property
    def supported_video_formats(self) -> list[ImgType]:
        return [ImgType(self.c_info.SupportedVideoFormat[i]) for i in range(8) if
                self.c_info.SupportedVideoFormat[i] != ImgType.IMG_END]

    @property
    def pixel_size(self) -> float:
        return self.c_info.PixelSize

    @property
    def mechanical_shutter(self) -> bool:
        return bool(self.c_info.MechanicalShutter)

    @property
    def st_4_port(self) -> bool:
        return bool(self.c_info.ST4Port)

    @property
    def is_cooler_cam(self) -> bool:
        return bool(self.c_info.IsCoolerCam)

    @property
    def is_usb3_host(self) -> bool:
        return bool(self.c_info.IsUSB3Host)

    @property
    def is_usb3_camera(self) -> bool:
        return bool(self.c_info.IsUSB3Camera)

    # new_patch
    @property
    def elec_per_adu(self) -> float:
        return float(self.c_info.ElecPerADU)

    @property
    def bit_depth(self) -> int:
        return int(self.c_info.BitDepth)

    """
    @property
    def elec_per_adu(self) -> bool:
        return bool(self.c_info.ElecPerADU)

    @property
    def bit_depth(self) -> bool:
        return bool(self.c_info.BitDepth)
    """

    @property
    def is_trigger_cam(self) -> bool:
        return bool(self.c_info.IsTriggerCam)

    def __repr__(self):
        # Custom string representation of the CameraInfo object
        return f"CameraInfo(Name={self.name}, CameraID={self.camera_id}, MaxHeight={self.max_height}, MaxWidth={self.max_width})"

#
# Open, close cameras
#

def get_number_of_connected_cameras() -> int:
    """Get the count of connected ASI cameras.

    Returns:
        int: Count of connected cameras.
    """
    return casi.ASIGetNumOfConnectedCameras()

def camera_check(i_vid: int, i_pid: int) -> int:
    """Get the count of connected ASI cameras.

    Usage: Check if the device is ASI Camera

    Args:
        i_vid (int): VID (vendor id) of the device.
                     This is a unique identifier assigned to ZWO (the company that makes
                     ASI cameras). ZWO's USB Vendor ID is 0x03C3
        i_pid (int): PID (product id) of the device.
                     This is a unique identifier for each specific product or model from ZWO.
                     Each ASI camera model will have a different PID.
                     For example, the ZWO ASI120MM camera might have a specific PID different
                     from the ASI294MC model

    Return:
        Whether the device is an ASI Camera.
    """
    return bool(casi.ASICameraCheck(i_vid, i_pid))

def get_camera_property(camera_index: int) -> CameraInfo:
    """
    Get camera properties by camera index.

    Args:
        camera_index (int): Index of the camera.

    Raises:
        AsiException

    Returns CameraInfo: the camera info.

    """
    camera_info = CameraInfo()
    handle_error_code(casi.ASIGetCameraProperty(&camera_info.c_info, camera_index))
    return camera_info

def get_sdk_version() -> str:
    """Get the SDK version of the ZWO ASI camera.

    Returns:
        str: The SDK version string.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    return casi.ASIGetSDKVersion().decode('utf-8')

def get_camera_property_by_id(camera_id: int) -> CameraInfo:
    """
    Get camera properties by camera ID.

    Args:
        camera_id (int): The camera ID from the CameraInfo object.

    Raises:
        AsiException


    Returns CameraInfo: the camera info.

    """
    camera_info = CameraInfo()
    handle_error_code(casi.ASIGetCameraPropertyByID(camera_id, &camera_info.c_info, ))
    return camera_info

def open_camera(camera_id: int) -> None:
    """
    Open a camera for use.

    Raises:
        AsiException

    Args:
        camera_id (int): The camera ID.
    """
    handle_error_code(casi.ASIOpenCamera(camera_id))

def init_camera(camera_id: int) -> None:
    """
    Initialize the camera for capturing images.

    Raises:
        AsiException

    Args:
        camera_id (int): The camera ID.
    """
    handle_error_code(casi.ASIInitCamera(camera_id))

def close_camera(camera_id: int) -> None:
    """
    Close the camera.

    Raises:
        AsiException

    Args:
        camera_id (int): The camera ID.
    """
    handle_error_code(casi.ASICloseCamera(camera_id))

#
# Basic properties
#

def get_id(i_camera_id: int) -> Id:
    """Retrieve the camera ID from the camera's flash memory.

    Args:
        i_camera_id (int): The camera ID.

    Returns:
        Id: The camera ID.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cam_id: Id = Id()
    handle_error_code(casi.ASIGetID(i_camera_id, &cam_id.c_id))
    return cam_id

def set_id(camera_id: int, serial_number: Id) -> None:
    """Write a new camera ID to the camera's flash memory.

    Args:
        camera_id (int): The camera ID.

        serial_number (Id): The camera serial number

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASISetID(camera_id, serial_number.c_id))

def get_serial_number(camera_id: int) -> Id:
    """Get the serial number of the camera.

    Args:
        camera_id (int): The camera ID.

    Returns:
        Id: The camera serial number id.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    serial_number = Id()
    handle_error_code(casi.ASIGetSerialNumber(camera_id, &serial_number.c_id))
    return serial_number

#
# Data acquisition modes
#

def get_camera_support_mode(camera_id: int) -> list[CameraMode]:
    """Get the supported camera modes for the camera.

    Args:
        camera_id (int): The camera ID.

    Returns:
        SupportedMode: The supported mode that contains a list of supported camera modes.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    supported_mode = SupportedMode()
    handle_error_code(casi.ASIGetCameraSupportMode(camera_id, &supported_mode.c_supported_mode))
    return supported_mode.supported_camera_mode

def get_camera_mode(camera_id: int) -> CameraMode:
    """Get the current camera mode.

    Args:
        camera_id (int): The camera ID.

    Returns:
        CameraMode: The current camera mode.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef int camera_mode
    handle_error_code(casi.ASIGetCameraMode(camera_id, &camera_mode))
    return CameraMode(camera_mode)

def set_camera_mode(camera_id: int, mode: CameraMode) -> None:
    """Set the camera mode.

    Args:
        camera_id (int): The camera ID.
        mode (CameraMode): The camera mode to set.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASISetCameraMode(camera_id, mode.value))

#
# Snap mode data acquisition
#

def start_exposure(camera_id: int, is_dark: bool) -> None:
    """Start a camera exposure.

    Args:
        camera_id (int): The camera ID.
        is_dark (bool): True for a dark frame exposure, False otherwise.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIStartExposure(camera_id, is_dark))

def stop_exposure(camera_id: int) -> None:
    """Stop the ongoing camera exposure.

    Args:
        camera_id (int): The camera ID.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIStopExposure(camera_id))

def get_exp_status(camera_id: int) -> int:
    """Get the status of the camera exposure.

    Args:
        camera_id (int): The camera ID.

    Returns:
        ExposureStatus: The exposure status.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef int exp_status
    handle_error_code(casi.ASIGetExpStatus(camera_id, &exp_status))
    return ExposureStatus(exp_status)

def get_data_after_exp(camera_id: int, buffer_size: int) -> bytes:
    """Get the image data after an exposure has completed.

    Args:
        camera_id (int): The camera ID.
        buffer_size (int): The size of the buffer to store the image data.

    Returns:
        bytes: The captured image data.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    buffer = bytearray(buffer_size)
    handle_error_code(casi.ASIGetDataAfterExp(camera_id, buffer, buffer_size))
    return bytes(buffer)

def get_data_after_exp_gps(camera_id: int, buffer_size: int) -> tuple[bytes, GpsData]:
    """Get the image data after an exposure has completed.

    Args:
        camera_id (int): The camera ID.
        buffer_size (int): The size of the buffer to store the image data.

    Returns:
        tuple(bytes, GpsData): The captured image data and the gps data.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    gps_data = GpsData()
    buffer = bytearray(buffer_size)
    handle_error_code(casi.ASIGetDataAfterExpGPS(camera_id, buffer, buffer_size,
                                                 &gps_data.c_gps_data))
    return bytes(buffer), gps_data

#
# Video mode data acquisition
#

def start_video_capture(camera_id: int) -> None:
    """Start video capture.

    Args:
        camera_id (int): The camera ID.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIStartVideoCapture(camera_id))

def stop_video_capture(camera_id: int) -> None:
    """Stop video capture.

    Args:
        camera_id (int): The camera ID.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIStopVideoCapture(camera_id))

def get_video_data(camera_id: int, buffer_size: int, wait_ms: int) -> bytes:
    """Get video data from the camera.

    Args:
        camera_id (int): The camera ID.
        buffer_size (int): The size of the buffer to store the image data.
        wait_ms (int): Time to wait for an image in milliseconds (-1 for infinite wait).

    Returns:
        bytes: The captured image data.

    Raises:
        AsiException: Raised if the operation is unsuccessful or timeout occurs.
    """
    buffer = bytearray(buffer_size)
    handle_error_code(casi.ASIGetVideoData(camera_id, buffer, buffer_size, wait_ms))
    return bytes(buffer)

def get_video_data_gps(camera_id: int, buffer_size: int, wait_ms: int) -> tuple[bytes, GpsData]:
    """Get video data from the camera.

    Args:
        camera_id (int): The camera ID.
        buffer_size (int): The size of the buffer to store the image data.
        wait_ms (int): Time to wait for an image in milliseconds (-1 for infinite wait).

    Returns:
        tuple(bytes, GpsData): The captured image data and the gps data.

    Raises:
        AsiException: Raised if the operation is unsuccessful or timeout occurs.
    """
    gps_data = GpsData()
    buffer = bytearray(buffer_size)
    handle_error_code(casi.ASIGetVideoDataGPS(camera_id, buffer, buffer_size, wait_ms,
                                              &gps_data.c_gps_data))
    return bytes(buffer), gps_data

#
# Controls
#

def get_num_of_controls(camera_id: int) -> int:
    """
    Get the number of control settings available on the camera.

    Args:
        camera_id (int): The camera ID.

    Raises:
        AsiException

    Returns:
        int: Number of controls.
    """
    cdef int num_of_controls
    handle_error_code(casi.ASIGetNumOfControls(camera_id, &num_of_controls))
    return num_of_controls

def get_control_caps(camera_id: int, control_index: int) -> ControlCaps:
    """
    Get the capabilities of a specific control on the camera.

    Args:
        camera_id (int): The camera ID.

        control_index (int): The control index.

    Raises:
        AsiException

    Returns:
        Controlaps: THe control caps
    """
    c = ControlCaps()
    handle_error_code(casi.ASIGetControlCaps(camera_id, control_index, &c.control_caps))
    return c

def get_control_value(camera_id: int, control_type: ControlType) -> tuple[int, bool]:
    """
    Get the value of a control setting on the camera.

    Args:
        camera_id (int): The camera ID.
        control_type (int): The control type.

    Raises:
        AsiException

    Returns:
        tuple[int, bool]: The value of the control and whether it's in auto mode.
    """
    cdef long value
    cdef bint auto_mode
    handle_error_code(casi.ASIGetControlValue(camera_id, control_type.value, &value, &auto_mode))
    return value, bool(auto_mode)

def set_control_value(camera_id: int, control_type: ControlType, value: int, auto_mode: bool) -> None:
    """
    Set the value of a control setting on the camera.

    Args:
        camera_id (int): The camera ID.
        control_type (int): The control type.
        value (long): The new control value.
        auto_mode (bool): Whether to enable auto mode.

    Raises:
        AsiException

    """
    handle_error_code(casi.ASISetControlValue(camera_id, control_type.value, value, auto_mode))

#
# ROI
#

def set_roi_format(camera_id: int, width: int, height: int, bin: int, img_type: ImgType) -> None:
    """Set the Region of Interest (ROI) format before starting capture.

    Args:
        camera_id (int): The camera ID.
        width (int): The width of the ROI area (must be a multiple of 8).
        height (int): The height of the ROI area (must be a multiple of 2).
        bin (int): The binning method (e.g., bin1=1, bin2=2).
        img_type (ImgType): The output format type.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASISetROIFormat(camera_id, width, height, bin, img_type.value))

def get_roi_format(camera_id: int) -> tuple[int, int, int, ImgType]:
    """Get the Region of Interest (ROI) format.

    Args:
        camera_id (int): The camera ID.

    Returns: tuple[int, int, int, ImgType]
        - width (int): The width of the ROI area (must be a multiple of 8).
        - height (int): The height of the ROI area (must be a multiple of 2).
        - bin (int): The binning method (e.g., bin1=1, bin2=2).
        - img_type (ImgType): The output format type.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef int width
    cdef int height
    cdef int bin
    cdef int img_type
    handle_error_code(casi.ASIGetROIFormat(camera_id, &width, &height, &bin, &img_type))
    return width, height, bin, ImgType(img_type)

def set_start_pos(camera_id: int, start_x: int, start_y: int) -> None:
    """Set the start position of the ROI area.

    Args:
        camera_id (int): The camera ID.
        start_x (int): Start X coordinate.
        start_y (int): Start Y coordinate.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASISetStartPos(camera_id, start_x, start_y))

def get_start_pos(camera_id: int) -> tuple[int, int]:
    """Get the start position of the current ROI area.

    Args:
        camera_id (int): The camera ID.

    Returns:
        tuple[int, int]: Start X and Start Y coordinates.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef int start_x, start_y
    handle_error_code(casi.ASIGetStartPos(camera_id, &start_x, &start_y))
    return start_x, start_y

def get_dropped_frames(camera_id: int) -> int:
    """Get the number of dropped frames during video capture.

    Args:
        camera_id (int): The camera ID.

    Returns:
        int: The number of dropped frames.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef int dropped_frames
    handle_error_code(casi.ASIGetDroppedFrames(camera_id, &dropped_frames))
    return dropped_frames

def enable_dark_subtract(camera_id: int, bmp_path: str) -> None:
    """Enable dark subtract using a dark frame BMP file.

    Args:
        camera_id (int): The camera ID.
        bmp_path (str): Path to the dark frame BMP file.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIEnableDarkSubtract(camera_id, bmp_path.encode('utf-8')))

def disable_dark_subtract(camera_id: int) -> None:
    """Disable the dark subtract feature.

    Args:
        camera_id (int): The camera ID.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIDisableDarkSubtract(camera_id))

def pulse_guide_on(camera_id: int, direction: GuideDirection) -> None:
    """Activate guiding in the specified direction using the ST4 port.

    Args:
        camera_id (int): The camera ID.
        direction (GuideDirection): The guiding direction (e.g., NORTH, SOUTH, etc.).

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIPulseGuideOn(camera_id, direction.value))

def pulse_guide_off(camera_id: int, direction: GuideDirection) -> None:
    """Deactivate guiding in the specified direction using the ST4 port.

    Args:
        camera_id (int): The camera ID.
        direction (GuideDirection): The guiding direction (e.g., NORTH, SOUTH, etc.).

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASIPulseGuideOff(camera_id, direction.value))

def get_gain_offset(camera_id: int) -> tuple[int, int, int, int]:
    """Get preset gain and offset values for the camera.

    Args:
        camera_id (int): The camera ID.

    Returns:
        tuple[int, int, int, int]: Offset at highest dynamic range, offset at unity gain,
                                   gain at lowest read noise, and offset at lowest read noise.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef int offset_highest_dr, offset_unity_gain, gain_lowest_rn, offset_lowest_rn
    handle_error_code(casi.ASIGetGainOffset(camera_id, &offset_highest_dr, &offset_unity_gain,
                                            &gain_lowest_rn, &offset_lowest_rn))
    return offset_highest_dr, offset_unity_gain, gain_lowest_rn, offset_lowest_rn

def get_lmh_gain_offset(camera_id: int) -> tuple[int, int, int, int]:
    """Get low, medium, and high gain and offset settings for the camera.

    Args:
        camera_id (int): The camera ID.

    Returns:
        tuple[int, int, int, int]: Low gain, medium gain, high gain, and high offset values.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef int l_gain, m_gain, h_gain, h_offset
    handle_error_code(casi.ASIGetLMHGainOffset(camera_id, &l_gain, &m_gain, &h_gain, &h_offset))
    return l_gain, m_gain, h_gain, h_offset

def send_soft_trigger(camera_id: int, start: bool) -> None:
    """Send a soft trigger to the camera to start or stop exposure.

    Args:
        camera_id (int): The camera ID.
        start (bool): True to start exposure, False to stop.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASISendSoftTrigger(camera_id, start))

def set_trigger_output_io_conf(camera_id: int, pin: TrigOutput, pin_high: bool, delay: int, duration: int) -> None:
    """Configure the trigger output IO.

    Args:
        camera_id (int): The camera ID.
        pin (int): Trigger output pin (e.g., PINA or PINB).
        pin_high (bool): True to output a high signal, False for a low signal.
        delay (int): Delay time in microseconds.
        duration (int): Duration time in microseconds.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    handle_error_code(casi.ASISetTriggerOutputIOConf(camera_id, pin.value, pin_high, delay, duration))

def get_trigger_output_io_conf(camera_id: int, pin: int) -> tuple[bool, int, int]:
    """Get the trigger output IO configuration.

    Args:
        camera_id (int): The camera ID.
        pin (int): Trigger output pin (e.g., PINA or PINB).

    Returns:
        tuple[bool, int, int]: Pin high status, delay, and duration.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    cdef bint pin_high
    cdef long delay, duration
    handle_error_code(casi.ASIGetTriggerOutputIOConf(camera_id, pin, &pin_high, &delay, &duration))
    return bool(pin_high), delay, duration

def gps_get_data(camera_id: int) -> tuple[GpsData, GpsData]:
    """Get GPS data for the start and end lines.

    Args:
        camera_id (int): The camera ID.

    Returns:
        tuple[DateTime, DateTime]: GPS data for the start and end lines.

    Raises:
        AsiException: Raised if the operation is unsuccessful.
    """
    start_line_gps_data = GpsData()
    end_line_gps_data = GpsData()

    handle_error_code(casi.ASIGPSGetData(camera_id, &start_line_gps_data.c_gps_data,
                                         &end_line_gps_data.c_gps_data))
    return start_line_gps_data, end_line_gps_data
