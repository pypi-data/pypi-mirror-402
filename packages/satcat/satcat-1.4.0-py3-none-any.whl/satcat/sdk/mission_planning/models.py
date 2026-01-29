from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Union, Literal
from uuid import UUID

from satcat.sdk.models import Model
from typing_extensions import Annotated
from pydantic import Field

if TYPE_CHECKING:
    from satcat.sdk.client import Client


class VisibilityRequestEphemerisDataSource(Model):
    source_type: Literal["EPHEMERIS"] = "EPHEMERIS"
    ephemeris_id: str


class VisibilityRequestTLEDataSource(Model):
    source_type: Literal["TLE"] = "TLE"
    line1: str
    line2: str

    propagation_start_time: Optional[datetime] = None
    propagation_stop_time: Optional[datetime] = None


VisibilityRequestRSODataSource = Annotated[
    Union[VisibilityRequestTLEDataSource, VisibilityRequestEphemerisDataSource],
    Field(
        discriminator="source_type",
        description="Data source for the RSO state.",
    ),
]


class UDLGroundSensorLocation(Model):
    lat: float
    lon: float
    altitude: float


class UDLGroundSensorEntity(Model):
    location: UDLGroundSensorLocation


class UDLSensorCharacteristic(Model):
    minRangeLimit: Optional[float] = None
    maxRangeLimit: Optional[float] = None
    maxSunElevationAngle: Optional[float] = None


class UDLSensorAzElLimit(Model):
    upperLeftAzimuthLimit: Optional[float] = None
    upperRightAzimuthLimit: Optional[float] = None
    lowerLeftAzimuthLimit: Optional[float] = None
    lowerRightAzimuthLimit: Optional[float] = None
    upperLeftElevationLimit: Optional[float] = None
    upperRightElevationLimit: Optional[float] = None
    lowerLeftElevationLimit: Optional[float] = None
    lowerRightElevationLimit: Optional[float] = None


class UDLGroundSensor(Model):
    """
    Compatible with the UDL GroundSensor model.
    Can be used for both ground stations and ground sensors such as radar / EO.
    """

    sensorName: str
    idSensor: str
    source: str
    classificationMarking: str
    entity: UDLGroundSensorEntity
    sensorcharacteristics: Optional[List[UDLSensorCharacteristic]] = None
    sensorlimitsCollection: Optional[List[UDLSensorAzElLimit]] = None


class UDLGroundSensorDefinition(Model):
    source_type: Literal["UDL_GROUND_SENSOR"] = "UDL_GROUND_SENSOR"
    ground_sensor: UDLGroundSensor

class GroundStationDefinition(Model):
    source_type: Literal["GROUND_STATION"] = "GROUND_STATION"
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    min_elevation_deg: Optional[float] = None



VisibilityRequestObserverDefinition = Annotated[
    Union[UDLGroundSensorDefinition, GroundStationDefinition],
    Field(
        discriminator="source_type",
        description="Observer definition.",
    ),
]


class VisibilityRequestObserver(Model):
    id: str
    definition: VisibilityRequestObserverDefinition


class VisibilityWindowsRequest(Model):
    primary_rso_data_source: VisibilityRequestRSODataSource
    observers: List[VisibilityRequestObserver]


class VisibilityWindow(Model):
    aos_time: Optional[datetime] = None
    aos_el_deg: Optional[float] = None

    los_time: Optional[datetime] = None
    los_el_deg: Optional[float] = None

    max_el_time: Optional[datetime] = None
    max_el_deg: Optional[float] = None

    _aos_state = None
    _los_state = None

    observer_id: str


class VisibilityWindowsResult(Model):
    windows: List[VisibilityWindow]

