"""
Reader plugin for napari using RosettaSciIO library.

This plugin enables napari to read scientific file formats supported by
RosettaSciIO, including microscopy data formats like Digital Micrograph,
TIFF, HDF5, and many others.
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np

import rsciio
from ._dialogs import ComplexDialog

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
    ".npy",
    ".npz",  # NumPy arrays
}

# Build a mapping of file extensions to rsciio plugins
_EXTENSION_TO_PLUGIN = {}
for plugin in rsciio.IO_PLUGINS:
    if "file_extensions" in plugin:
        for ext in plugin["file_extensions"]:
            if not ext.startswith("."):
                ext = f".{ext}"
            # Skip formats that napari handles natively
            if ext.lower() in _NAPARI_NATIVE_FORMATS:
                continue
            # Store plugin API path for each extension
            _EXTENSION_TO_PLUGIN[ext.lower()] = plugin["api"]


def napari_get_reader(path):
    """Return a reader function for files supported by RosettaSciIO.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # For image stacks, check the first file
        path = path[0]

    # Check if file extension is supported
    path_obj = Path(path)
    ext = path_obj.suffix.lower()

    if ext not in _EXTENSION_TO_PLUGIN:
        return None

    # Return the reader function
    return reader_function


def reader_function(path):
    """Read scientific data files using RosettaSciIO.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]).

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of
        layer.
    """
    # Handle both a string and a list of strings
    paths = [path] if isinstance(path, str) else path

    layer_data_list = []

    for file_path in paths:
        path_obj = Path(file_path)
        ext = path_obj.suffix.lower()

        # Get the appropriate plugin
        plugin_name = _EXTENSION_TO_PLUGIN.get(ext)
        if plugin_name is None:
            _logger.warning(f"No plugin found for extension {ext}")
            continue

        try:
            # Import the plugin module dynamically
            plugin_module = __import__(plugin_name, fromlist=["file_reader"])
            file_reader = getattr(plugin_module, "file_reader", None)

            if file_reader is None:
                _logger.warning(
                    f"Plugin {plugin_name} does not have file_reader"
                )
                continue

            # Read the file
            signal_dict_list = file_reader(str(file_path), lazy=False)

            # Convert each signal to napari layer
            for signal_dict in signal_dict_list:
                layer_data = _signal_to_layer(signal_dict, path_obj.stem)
                if layer_data is not None:
                    # _signal_to_layer may return a list of layers (for complex data)
                    # or a single layer tuple
                    if isinstance(layer_data, list):
                        layer_data_list.extend(layer_data)
                    else:
                        layer_data_list.append(layer_data)

        except Exception as e:
            _logger.error(f"Error reading {file_path} with {plugin_name}: {e}")
            continue

    return layer_data_list if layer_data_list else None


def _signal_to_layer(signal_dict, default_name="data"):
    """Convert a RosettaSciIO signal dictionary to napari layer data.

    Parameters
    ----------
    signal_dict : dict
        Dictionary containing 'data', 'axes', 'metadata', etc.
    default_name : str
        Default name if no title is found in metadata

    Returns
    -------
    tuple or list of tuples
        Single (data, add_kwargs, layer_type) tuple for napari, or
        a list of two tuples if the data is complex-valued.
    """
    data = signal_dict.get("data")
    if data is None:
        return None

    # Get name from metadata
    metadata = signal_dict.get("metadata", {})
    general = metadata.get("General", {})
    name = general.get("title", default_name)

    # Build base metadata for napari
    def _build_kwargs(data_array, layer_name):
        add_kwargs = {}
        add_kwargs["name"] = layer_name

        # Handle axes information
        axes = signal_dict.get("axes", [])
        if axes:
            scale = []
            axis_labels = []

            for axis in axes:
                # Get scale (pixel size)
                scale_value = axis.get("scale", 1.0)
                scale.append(scale_value)

                # Get axis name
                axis_name = axis.get("name", "")
                if not axis_name:
                    axis_name = axis.get("units", "")
                axis_labels.append(axis_name)

            if scale:
                add_kwargs["scale"] = tuple(scale)
            if any(axis_labels):
                add_kwargs["axis_labels"] = axis_labels

        # Store full metadata
        add_kwargs["metadata"] = signal_dict
        return add_kwargs

    # Handle complex data
    if np.iscomplexobj(data):
        _logger.info(f"Complex data detected in {name}, showing dialog...")
        display_mode = _show_complex_dialog()

        # Convert to two real-valued arrays
        components = _convert_complex_to_layers(data, name, display_mode)

        # Create layer tuples for both components
        layers = []
        for component_data, component_name in components:
            add_kwargs = _build_kwargs(component_data, component_name)
            layers.append((component_data, add_kwargs, "image"))

        return layers

    # For real-valued data, proceed normally
    add_kwargs = _build_kwargs(data, name)

    # Determine layer type based on data
    # Most scientific data will be image data
    layer_type = "image"

    # Check if data looks like labels (integer dtype with small range)
    if np.issubdtype(data.dtype, np.integer):
        unique_vals = np.unique(data)
        if len(unique_vals) < 1000:  # Heuristic for labels
            layer_type = "labels"

    return (data, add_kwargs, layer_type)


def _show_complex_dialog():
    """Show dialog to ask user how to display complex data.

    Returns
    -------
    str
        Either 'magnitude_phase' or 'real_imaginary'
    """
    try:
        from qtpy.QtWidgets import QApplication

        # Ensure QApplication exists
        app = QApplication.instance()
        if app is None:
            # Running in headless mode or outside napari
            return "magnitude_phase"  # Default

        dialog = ComplexDialog()
        dialog.exec_()
        return dialog.value_selected
    except Exception:
        # If dialog fails, return default
        return "magnitude_phase"


def _convert_complex_to_layers(data, name, display_mode):
    """Convert complex data to two real-valued arrays.

    Parameters
    ----------
    data : np.ndarray
        Complex-valued array
    name : str
        Base name for the layers
    display_mode : str
        Either 'magnitude_phase' or 'real_imaginary'

    Returns
    -------
    list of tuples
        List of (data, name) tuples for the two components
    """
    if display_mode == "magnitude_phase":
        magnitude = np.abs(data)
        phase = np.angle(data)
        return [(magnitude, f"{name} (magnitude)"), (phase, f"{name} (phase)")]
    else:  # real_imaginary
        real = np.real(data)
        imag = np.imag(data)
        return [(real, f"{name} (real)"), (imag, f"{name} (imaginary)")]
