"""
maix.webrtc module
"""
from __future__ import annotations
import maix._maix.audio
import maix._maix.camera
import maix._maix.err
import maix._maix.image
import maix._maix.video
import typing
__all__: list[str] = ['Region', 'WebRTC', 'WebRTCRCType', 'WebRTCStreamType']
class Region:
    def __init__(self, x: int, y: int, width: int, height: int, format: maix._maix.image.Format, camera: maix._maix.camera.Camera) -> None:
        ...
    def get_canvas(self) -> maix._maix.image.Image:
        """
        Return an image object from region
        
        Returns: image object
        """
    def update_canvas(self) -> maix._maix.err.Err:
        """
        Update canvas
        
        Returns: error code
        """
class WebRTC:
    def __init__(self, ip: str = '', port: int = 8000, stream_type: WebRTCStreamType = ..., rc_type: WebRTCRCType = ..., bitrate: int = 3000000, gop: int = 60, signaling_ip: str = '', signaling_port: int = 8001, stun_server: str = 'stun:stun.l.google.com:19302', http_server: bool = True) -> None:
        ...
    def add_region(self, x: int, y: int, width: int, height: int, format: maix._maix.image.Format = ...) -> Region:
        """
        return a region object, you can draw image on the region.(This function will be removed in the future)
        
        Args:
          - x: region coordinate x
          - y: region coordinate y
          - width: region width
          - height: region height
          - format: region format, support Format::FMT_BGRA8888 only
        
        
        Returns: the reigon object
        """
    def bind_audio_recorder(self, recorder: maix._maix.audio.Recorder) -> maix._maix.err.Err:
        """
        Bind audio recorder
        
        Args:
          - recorder: audio recorder object
        
        
        Returns: error code
        """
    def bind_camera(self, camera: maix._maix.camera.Camera) -> maix._maix.err.Err:
        """
        Bind camera
        
        Args:
          - camera: camera object
        
        
        Returns: error code
        """
    def del_region(self, region: Region) -> maix._maix.err.Err:
        """
        del region(This function will be removed in the future)
        
        Returns: error code
        """
    def draw_rect(self, id: int, x: int, y: int, width: int, height: int, color: maix._maix.image.Color, thickness: int = 1) -> maix._maix.err.Err:
        """
        Draw a rectangle on the canvas(This function will be removed in the future)
        
        Args:
          - id: region id
          - x: rectangle coordinate x
          - y: rectangle coordinate y
          - width: rectangle width
          - height: rectangle height
          - color: rectangle color
          - thickness: rectangle thickness. If you set it to -1, the rectangle will be filled.
        
        
        Returns: error code
        """
    def draw_string(self, id: int, x: int, y: int, str: str, color: maix._maix.image.Color, size: int = 16, thickness: int = 1) -> maix._maix.err.Err:
        """
        Draw a string on the canvas(This function will be removed in the future)
        
        Args:
          - id: region id
          - x: string coordinate x
          - y: string coordinate y
          - str: string
          - color: string color
          - size: string size
          - thickness: string thickness
        
        
        Returns: error code
        """
    def get_url(self) -> str:
        """
        Get signaling or play url
        
        Returns: url
        """
    def get_urls(self) -> list[str]:
        """
        Get url list
        
        Returns: url list
        """
    def start(self) -> maix._maix.err.Err:
        """
        start webrtc
        
        Returns: error code
        """
    def stop(self) -> maix._maix.err.Err:
        """
        stop webrtc
        
        Returns: error code
        """
    def to_camera(self) -> maix._maix.camera.Camera:
        """
        Get camera object
        """
    def update_region(self, region: Region) -> maix._maix.err.Err:
        """
        update and show region(This function will be removed in the future)
        
        Returns: error code
        """
    def write(self, frame: maix._maix.video.Frame) -> maix._maix.err.Err:
        """
        Write encoded video (optional, reserved)
        """
class WebRTCRCType:
    """
    Members:
    
      WEBRTC_RC_NONE
    
      WEBRTC_RC_CBR
    
      WEBRTC_RC_VBR
    """
    WEBRTC_RC_CBR: typing.ClassVar[WebRTCRCType]  # value = <WebRTCRCType.WEBRTC_RC_CBR: 1>
    WEBRTC_RC_NONE: typing.ClassVar[WebRTCRCType]  # value = <WebRTCRCType.WEBRTC_RC_NONE: 0>
    WEBRTC_RC_VBR: typing.ClassVar[WebRTCRCType]  # value = <WebRTCRCType.WEBRTC_RC_VBR: 2>
    __members__: typing.ClassVar[dict[str, WebRTCRCType]]  # value = {'WEBRTC_RC_NONE': <WebRTCRCType.WEBRTC_RC_NONE: 0>, 'WEBRTC_RC_CBR': <WebRTCRCType.WEBRTC_RC_CBR: 1>, 'WEBRTC_RC_VBR': <WebRTCRCType.WEBRTC_RC_VBR: 2>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class WebRTCStreamType:
    """
    Members:
    
      WEBRTC_STREAM_NONE
    
      WEBRTC_STREAM_H264
    
      WEBRTC_STREAM_H265
    """
    WEBRTC_STREAM_H264: typing.ClassVar[WebRTCStreamType]  # value = <WebRTCStreamType.WEBRTC_STREAM_H264: 1>
    WEBRTC_STREAM_H265: typing.ClassVar[WebRTCStreamType]  # value = <WebRTCStreamType.WEBRTC_STREAM_H265: 2>
    WEBRTC_STREAM_NONE: typing.ClassVar[WebRTCStreamType]  # value = <WebRTCStreamType.WEBRTC_STREAM_NONE: 0>
    __members__: typing.ClassVar[dict[str, WebRTCStreamType]]  # value = {'WEBRTC_STREAM_NONE': <WebRTCStreamType.WEBRTC_STREAM_NONE: 0>, 'WEBRTC_STREAM_H264': <WebRTCStreamType.WEBRTC_STREAM_H264: 1>, 'WEBRTC_STREAM_H265': <WebRTCStreamType.WEBRTC_STREAM_H265: 2>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
