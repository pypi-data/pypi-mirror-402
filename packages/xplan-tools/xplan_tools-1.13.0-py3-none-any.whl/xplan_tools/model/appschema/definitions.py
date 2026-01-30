# generated from JSON Schema


from __future__ import annotations

from datetime import date as date_aliased
from typing import Annotated, Any

from pydantic import AnyUrl, Field, RootModel

from ..base import BaseFeature


class Model(RootModel[Any]):
    root: Any


class GeometryBase(BaseFeature):
    srid: int


class Polygon(GeometryBase):
    wkt: Annotated[str, Field(pattern="^((CURVE)?POLYGON|SURFACE).*$")]


class MultiPolygon(GeometryBase):
    wkt: Annotated[str, Field(pattern="^(MULTIPOLYGON|MULTISURFACE).*$")]


class Line(GeometryBase):
    wkt: Annotated[str, Field(pattern="^((LINE|CIRCULAR)STRING|COMPOUNDCURVE).*$")]


class MultiLine(GeometryBase):
    wkt: Annotated[str, Field(pattern="^(MULTI(LINESTRING|CURVE)).*$")]


class Point(GeometryBase):
    wkt: Annotated[str, Field(pattern="^(POINT).*$")]


class MultiPoint(GeometryBase):
    wkt: Annotated[str, Field(pattern="^(MULTIPOINT).*$")]


class Measure(BaseFeature):
    """Basisklasse für Maße"""

    value: Annotated[float, Field(description="Wert des Maßes")]


class Length(Measure):
    """Angabe einer Länge in Metern"""

    uom: Annotated[str | None, Field(description="Maßeinheit")] = "m"


class Area(Measure):
    """Angabe einer Fläche in Quadratmetern"""

    uom: Annotated[str | None, Field(description="Maßeinheit")] = "m2"


class Angle(Measure):
    """Angabe eines Winkels in Grad"""

    uom: Annotated[str | None, Field(description="Maßeinheit")] = "grad"


class Volume(Measure):
    """Angabe eines Volumens in Kubikmetern"""

    uom: Annotated[str | None, Field(description="Maßeinheit")] = "m3"


class Velocity(Measure):
    """Angabe einer Geschwindigkeit in km/h"""

    uom: Annotated[str | None, Field(description="Maßeinheit")] = "km/h"


class Scale(Measure):
    """Angabe einer Skala in Prozent"""

    uom: Annotated[str | None, Field(description="Maßeinheit")] = "vH"


class GenericMeasure(Measure):
    """Nicht näher konkretisiertes Maß"""

    uom: Annotated[str | None, Field(description="Maßeinheit")] = "unknown"


class VoidReasonValue(BaseFeature):
    """Reasons for void values."""

    nilReason: Annotated[AnyUrl, Field(description="Reason")]


class CIDate(BaseFeature):
    date: Annotated[date_aliased, Field(description="Date")]
    dateType: Annotated[AnyUrl, Field(description="Date Type")]
