# XPlan-Tools

[![coverage report](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools/badges/main/coverage.svg)](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools/-/commits/main)
[![pipeline status](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools/badges/main/pipeline.svg)](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools/-/commits/main)
[![Latest Release](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools/-/badges/release.svg)](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools/-/releases)

**[Documentation](https://xplan-tools-xleitstelle-xplanung-8446a974e8119a851af45bf94e0717.usercontent.opencode.de/)** | **[Repository](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools)**


A Python library to provide some useful means when working with XPlanung, XTrasse and XWaermeplan data, e.g. format conversion, version migration and database setup. Relies on [Pydantic](https://pydantic.dev) for a Python representation of the XPlanung/XTrasse/XWaermeplan model as well as serialization/de-serialization and validation.

While it comes with a CLI, its modules are also meant to provide other applications a Python representation as well as an interface for XPlanung/XTrasse/XWaermeplan data.

## Features

* Conversion between GML, JSON-FG and DB encodings of XPlanung/XTrasse/XWaermeplan data.
* Migration from older versions of XPlanung to the latest one.
* Set up a database to store XPlanung data. Supports [PostgreSQL](https://www.postgresql.org)/[PostGIS](https://postgis.net) as well as [GeoPackage](https://www.geopackage.org) and [SpatiaLite](https://www.gaia-gis.it/fossil/libspatialite/index) SQLite databases.
* Transformation from XPlanung to [INSPIRE PLU](https://inspire-mif.github.io/uml-models/approved/fc/#_P5531) based on the [official mappings](https://xleitstelle.de/xplanung/transformation-inspire/releases).
* Adding style properties (stylesheetId, schriftinhalt) to XPlanung presentational objects based on [defined rules](https://xplan-tools-xleitstelle-xplanung-8446a974e8119a851af45bf94e0717.usercontent.opencode.de/style_defs/).

## Installation

### Pixi
This project uses [Pixi](https://pixi.sh) for package management. To install this repo with a self-contained environment, run

```shell
git clone https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools.git
cd xplan-tools
pixi install
```
### Python >= v3.10

[GDAL](https://gdal.org) and its Python bindings are required, so you need to make sure the GDAL system library and Python package versions match.

Download the repository:

```shell
git clone https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools.git
cd xplan-tools
pip install .
```
Or install from PyPI:
```shell
pip install xplan-tools
```

### Docker
Images are provided in the [container registry](https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools/container_registry) (see [docs](https://xplan-tools-xleitstelle-xplanung-8446a974e8119a851af45bf94e0717.usercontent.opencode.de/how-to-guides/#container-image-usage)).


## Development
Make sure [Pixi](https://pixi.sh) is installed and run

```shell
git clone https://gitlab.opencode.de/xleitstelle/xplanung/xplan-tools.git
cd xplan-tools
make dev
```

## License

The code in this repository is licensed under the [EUPL-1.2-or-later](https://joinup.ec.europa.eu/collection/eupl)

&copy; [XLeitstelle](https://xleitstelle.de), 2025
