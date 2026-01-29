from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.framing_assistant_info_response_rectangle import FramingAssistantInfoResponseRectangle


T = TypeVar("T", bound="FramingAssistantInfoResponse")


@_attrs_define
class FramingAssistantInfoResponse:
    """
    Attributes:
        bound_height (int):
        bound_width (int):
        camera_height (int):
        camera_width (int):
        camera_pixel_size (int):
        dec_degrees (int):
        dec_minutes (int):
        dec_seconds (int):
        ra_hours (int):
        ra_minutes (int):
        ra_seconds (int):
        field_of_view (int):
        focal_length (int):
        horizontal_panels (int):
        vertical_panels (int):
        rectangle (FramingAssistantInfoResponseRectangle):
    """

    bound_height: int
    bound_width: int
    camera_height: int
    camera_width: int
    camera_pixel_size: int
    dec_degrees: int
    dec_minutes: int
    dec_seconds: int
    ra_hours: int
    ra_minutes: int
    ra_seconds: int
    field_of_view: int
    focal_length: int
    horizontal_panels: int
    vertical_panels: int
    rectangle: "FramingAssistantInfoResponseRectangle"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        bound_height = self.bound_height

        bound_width = self.bound_width

        camera_height = self.camera_height

        camera_width = self.camera_width

        camera_pixel_size = self.camera_pixel_size

        dec_degrees = self.dec_degrees

        dec_minutes = self.dec_minutes

        dec_seconds = self.dec_seconds

        ra_hours = self.ra_hours

        ra_minutes = self.ra_minutes

        ra_seconds = self.ra_seconds

        field_of_view = self.field_of_view

        focal_length = self.focal_length

        horizontal_panels = self.horizontal_panels

        vertical_panels = self.vertical_panels

        rectangle = self.rectangle.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "BoundHeight": bound_height,
                "BoundWidth": bound_width,
                "CameraHeight": camera_height,
                "CameraWidth": camera_width,
                "CameraPixelSize": camera_pixel_size,
                "DecDegrees": dec_degrees,
                "DecMinutes": dec_minutes,
                "DecSeconds": dec_seconds,
                "RAHours": ra_hours,
                "RAMinutes": ra_minutes,
                "RASeconds": ra_seconds,
                "FieldOfView": field_of_view,
                "FocalLength": focal_length,
                "HorizontalPanels": horizontal_panels,
                "VerticalPanels": vertical_panels,
                "Rectangle": rectangle,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.framing_assistant_info_response_rectangle import FramingAssistantInfoResponseRectangle

        d = src_dict.copy()
        bound_height = d.pop("BoundHeight")

        bound_width = d.pop("BoundWidth")

        camera_height = d.pop("CameraHeight")

        camera_width = d.pop("CameraWidth")

        camera_pixel_size = d.pop("CameraPixelSize")

        dec_degrees = d.pop("DecDegrees")

        dec_minutes = d.pop("DecMinutes")

        dec_seconds = d.pop("DecSeconds")

        ra_hours = d.pop("RAHours")

        ra_minutes = d.pop("RAMinutes")

        ra_seconds = d.pop("RASeconds")

        field_of_view = d.pop("FieldOfView")

        focal_length = d.pop("FocalLength")

        horizontal_panels = d.pop("HorizontalPanels")

        vertical_panels = d.pop("VerticalPanels")

        rectangle = FramingAssistantInfoResponseRectangle.from_dict(d.pop("Rectangle"))

        framing_assistant_info_response = cls(
            bound_height=bound_height,
            bound_width=bound_width,
            camera_height=camera_height,
            camera_width=camera_width,
            camera_pixel_size=camera_pixel_size,
            dec_degrees=dec_degrees,
            dec_minutes=dec_minutes,
            dec_seconds=dec_seconds,
            ra_hours=ra_hours,
            ra_minutes=ra_minutes,
            ra_seconds=ra_seconds,
            field_of_view=field_of_view,
            focal_length=focal_length,
            horizontal_panels=horizontal_panels,
            vertical_panels=vertical_panels,
            rectangle=rectangle,
        )

        framing_assistant_info_response.additional_properties = d
        return framing_assistant_info_response

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
