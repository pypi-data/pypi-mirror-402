# napari-rosettasciio

[![License MIT](https://img.shields.io/pypi/l/napari-rosettasciio.svg?color=green)](https://github.com/jules-vanaret/napari-rosettasciio/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-rosettasciio.svg?color=green)](https://pypi.org/project/napari-rosettasciio)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-rosettasciio.svg?color=green)](https://python.org)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-rosettasciio)](https://napari-hub.org/plugins/napari-rosettasciio)
[![npe2](https://img.shields.io/badge/plugin-npe2-blue?link=https://napari.org/stable/plugins/index.html)](https://napari.org/stable/plugins/index.html)

A napari plugin to read and write scientific data formats using [RosettaSciIO].

----------------------------------

## Overview

This plugin integrates [RosettaSciIO] with [napari], enabling napari to read and write a wide range of scientific data formats, particularly those used in electron microscopy and spectroscopy.

**Note:** This plugin focuses on scientific data formats not natively supported by napari. Standard image formats (PNG, JPEG, TIFF, BMP, GIF) and NumPy arrays are handled by napari's built-in readers and are excluded from this plugin to avoid conflicts.

### Supported File Formats

RosettaSciIO supports many scientific data formats including:

- **HDF5-based formats**: HyperSpy (`.hspy`), EMD (`.emd`), NeXus (`.nxs`), USID
- **Microscopy formats**: Digital Micrograph (`.dm3`, `.dm4`), MRC (`.mrc`), FEI/TIA (`.ser`, `.emi`)
- **Spectroscopy formats**: EDAX (`.spc`, `.spd`), Bruker (`.bcf`), Renishaw WiRE (`.wdf`)
- And many more specialized scientific formats...

For a complete list of supported formats, see the [RosettaSciIO documentation].

## Installation

You can install `napari-rosettasciio` via [pip]:

```bash
pip install napari-rosettasciio
```

### Optional Dependencies

To enable support for specific file formats, you can install with optional dependencies:

```bash
# For HDF5 formats (HyperSpy, EMD, NeXus, etc.)
pip install "napari-rosettasciio[hdf5]"

# For image formats (PNG, JPEG, etc.)
pip install "napari-rosettasciio[image]"

# For Zarr-based formats
pip install "napari-rosettasciio[zspy]"

# For all formats
pip install "napari-rosettasciio[all]"
```

## Usage

Once installed, the plugin will automatically register with napari. You can then:

1. **Open files**: Use `File > Open` or drag and drop files into napari
2. **Save files**: Use `File > Save` and select the desired format

The plugin will automatically detect and use the appropriate reader/writer based on the file extension.

### Preserving Metadata

The plugin preserves metadata from the original files, including:
- Axes scales and units
- Original metadata structures
- Custom attributes

This metadata is stored in the layer metadata and can be preserved when saving to formats that support it (e.g., HDF5, Zarr).

### Format Limitations

Some formats have specific requirements:
- **MRCZ** (`.mrcz`): Only supports 3D volumetric data. This format is currently excluded from the writer capabilities as it cannot handle 2D images.

## License

Distributed under the terms of the [MIT] license,
"napari-rosettasciio" is free and open source software.

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

## Acknowledgements

This plugin is built on top of [RosettaSciIO], which originated from the [HyperSpy] project. 
We are grateful to all contributors to these projects.

[napari]: https://github.com/napari/napari
[RosettaSciIO]: https://github.com/hyperspy/rosettasciio
[RosettaSciIO documentation]: https://hyperspy.org/rosettasciio/supported_formats/index.html
[HyperSpy]: https://hyperspy.org
[MIT]: http://opensource.org/licenses/MIT
[pip]: https://pypi.org/project/pip/
[file an issue]: https://github.com/jules-vanaret/napari-rosettasciio/issues
