"""
Writer plugin for napari using RosettaSciIO library.

This plugin enables napari to write scientific file formats supported by
RosettaSciIO, including microscopy data formats like Digital Micrograph,
TIFF, HDF5, and many others.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import numpy as np

import rsciio

if TYPE_CHECKING:
    DataType = Union[Any, Sequence[Any]]
    FullLayerData = tuple[DataType, dict, str]

_logger = logging.getLogger(__name__)

# Formats that napari handles natively - we exclude these to avoid conflicts
_NAPARI_NATIVE_FORMATS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",  # Standard images
    ".tif",
    ".tiff",  # TIFF images
    ".npy",  # NumPy arrays
}

# Formats with special requirements that we don't support
_UNSUPPORTED_FORMATS = {
    ".mrcz",  # MRCZ only supports 3D data, too limiting for general use
}

# Build a mapping of file extensions to rsciio plugins that support writing
_EXTENSION_TO_WRITER = {}
for plugin in rsciio.IO_PLUGINS:
    if plugin.get("writes", False) and "file_extensions" in plugin:
        for ext in plugin["file_extensions"]:
            if not ext.startswith("."):
                ext = f".{ext}"
            # Skip formats that napari handles natively or we don't support
            if (
                ext.lower() in _NAPARI_NATIVE_FORMATS
                or ext.lower() in _UNSUPPORTED_FORMATS
            ):
                continue
            # Store plugin API path for each extension
            _EXTENSION_TO_WRITER[ext.lower()] = plugin["api"]


def write_single_image(path: str, data: Any, meta: dict) -> list[str]:
    """Write a single image layer using RosettaSciIO.

    Parameters
    ----------
    path : str
        A string path indicating where to save the image file.
    data : The layer data
        The `.data` attribute from the napari layer.
    meta : dict
        A dictionary containing all other attributes from the napari layer
        (excluding the `.data` layer attribute).

    Returns
    -------
    [path] : A list containing the string path to the saved file.
    """
    path_obj = Path(path)
    ext = path_obj.suffix.lower()

    # Check if this extension is supported for writing
    plugin_name = _EXTENSION_TO_WRITER.get(ext)
    if plugin_name is None:
        _logger.error(f"No writer plugin found for extension {ext}")
        return []

    try:
        # Import the plugin module dynamically
        plugin_module = __import__(plugin_name, fromlist=["file_writer"])
        file_writer = getattr(plugin_module, "file_writer", None)

        if file_writer is None:
            _logger.error(f"Plugin {plugin_name} does not have file_writer")
            return []

        # Convert napari layer to RosettaSciIO signal format
        signal_dict = _layer_to_signal(data, meta, path_obj.stem)

        # Write the file
        file_writer(str(path), signal_dict)

        return [path]

    except Exception as e:
        _logger.error(f"Error writing {path} with {plugin_name}: {e}")
        return []


def write_multiple(path: str, data: list[FullLayerData]) -> list[str]:
    """Write multiple layers of different types using RosettaSciIO.

    Parameters
    ----------
    path : str
        A string path indicating where to save the data file(s).
    data : A list of layer tuples.
        Tuples contain three elements: (data, meta, layer_type)
        `data` is the layer data
        `meta` is a dictionary containing all other metadata attributes
        from the napari layer (excluding the `.data` layer attribute).
        `layer_type` is a string, eg: "image", "labels", "surface", etc.

    Returns
    -------
    [path] : A list containing (potentially multiple) string paths to the saved file(s).
    """
    path_obj = Path(path)
    ext = path_obj.suffix.lower()

    # Check if this extension is supported for writing
    plugin_name = _EXTENSION_TO_WRITER.get(ext)
    if plugin_name is None:
        _logger.error(f"No writer plugin found for extension {ext}")
        return []

    # For formats that support multiple signals (like HDF5/hspy),
    # we can write all layers to one file
    # For other formats, we need to write each layer to a separate file
    is_hierarchical = plugin_name in ["rsciio.hspy", "rsciio.zspy"]

    saved_paths = []

    if is_hierarchical:
        # Write all layers to a single hierarchical file
        # This would require a more complex implementation
        # For now, write only the first layer
        if len(data) > 0:
            layer_data, meta, layer_type = data[0]
            result = write_single_image(path, layer_data, meta)
            saved_paths.extend(result)
    else:
        # Write each layer to a separate file
        for i, (layer_data, meta, layer_type) in enumerate(data):
            # Create a unique filename for each layer
            if len(data) > 1:
                layer_name = meta.get("name", f"layer_{i}")
                layer_path = (
                    path_obj.parent
                    / f"{path_obj.stem}_{layer_name}{path_obj.suffix}"
                )
            else:
                layer_path = path_obj

            result = write_single_image(str(layer_path), layer_data, meta)
            saved_paths.extend(result)

    return saved_paths


def _layer_to_signal(data: np.ndarray, meta: dict, default_name: str = "data"):
    """Convert napari layer data to RosettaSciIO signal dictionary.

    Parameters
    ----------
    data : np.ndarray
        The layer data array
    meta : dict
        The layer metadata from napari
    default_name : str
        Default name if no name is found in metadata

    Returns
    -------
    dict
        RosettaSciIO signal dictionary with 'data', 'axes', 'metadata', etc.
    """
    signal_dict = {
        "data": data,
        "axes": [],
        "metadata": {
            "General": {"title": meta.get("name", default_name)},
            "Signal": {"signal_type": ""},
        },
        "original_metadata": {},
        "attributes": {
            "_lazy": False,  # Data is already loaded in napari
        },
        "tmp_parameters": {},  # Required by RosettaSciIO writers
        "package_info": {  # Package information for file metadata
            "name": "napari-rosettasciio",
            "version": "0.1.0",
        },
        "learning_results": {},  # Required by some formats
        "models": {},  # Required by some formats
    }

    # Convert napari scale and axis information to RosettaSciIO axes
    scale = meta.get("scale", None)
    axis_labels = meta.get("axis_labels", None)

    for i in range(data.ndim):
        axis_dict = {
            "size": data.shape[i],
            "index_in_array": i,
            "name": "",
            "scale": 1.0,
            "offset": 0.0,
            "units": "",
            "navigate": False,
        }

        # Set scale if available
        if scale is not None and i < len(scale):
            axis_dict["scale"] = float(scale[i])

        # Set axis label/name if available
        if axis_labels is not None and i < len(axis_labels):
            axis_dict["name"] = axis_labels[i]

        # Determine navigation vs signal axes
        # Convention: first axes are navigation, last 2 are signal for 3D+ data
        if data.ndim > 2 and i < data.ndim - 2:
            axis_dict["navigate"] = True

        signal_dict["axes"].append(axis_dict)

    # If there's stored RosettaSciIO metadata, use it
    if "metadata" in meta and isinstance(meta["metadata"], dict):
        stored_metadata = meta["metadata"]
        if "metadata" in stored_metadata:
            signal_dict["metadata"].update(stored_metadata["metadata"])
        if "original_metadata" in stored_metadata:
            signal_dict["original_metadata"] = stored_metadata[
                "original_metadata"
            ]
        if "attributes" in stored_metadata:
            signal_dict["attributes"] = stored_metadata["attributes"]

    return signal_dict
