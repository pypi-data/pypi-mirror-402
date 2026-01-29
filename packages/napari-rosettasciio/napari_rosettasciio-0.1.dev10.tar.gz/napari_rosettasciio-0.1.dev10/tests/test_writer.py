"""Tests for the writer plugin."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from napari_rosettasciio._writer import (
    _layer_to_signal,
    write_multiple,
    write_single_image,
)


def test_layer_to_signal_basic():
    """Test conversion of napari layer data to RosettaSciIO signal format."""
    data = np.random.rand(10, 10)
    meta = {"name": "test_image"}

    signal_dict = _layer_to_signal(data, meta, "default")

    assert "data" in signal_dict
    assert "axes" in signal_dict
    assert "metadata" in signal_dict
    assert np.array_equal(signal_dict["data"], data)
    assert signal_dict["metadata"]["General"]["title"] == "test_image"
    assert len(signal_dict["axes"]) == 2


def test_layer_to_signal_with_scale():
    """Test that scale information is properly converted."""
    data = np.random.rand(5, 5)
    meta = {"name": "scaled_image", "scale": (2.0, 0.5)}

    signal_dict = _layer_to_signal(data, meta, "default")

    assert signal_dict["axes"][0]["scale"] == 2.0
    assert signal_dict["axes"][1]["scale"] == 0.5


def test_layer_to_signal_with_axis_labels():
    """Test that axis labels are properly converted."""
    data = np.random.rand(3, 4)
    meta = {"name": "labeled_image", "axis_labels": ["y", "x"]}

    signal_dict = _layer_to_signal(data, meta, "default")

    assert signal_dict["axes"][0]["name"] == "y"
    assert signal_dict["axes"][1]["name"] == "x"


def test_layer_to_signal_default_name():
    """Test that default name is used when no name is provided."""
    data = np.random.rand(5, 5)
    meta = {}

    signal_dict = _layer_to_signal(data, meta, "fallback_name")

    assert signal_dict["metadata"]["General"]["title"] == "fallback_name"


def test_write_single_image_hspy(tmp_path):
    """Test writing a single image to .hspy format."""
    output_file = tmp_path / "test_output.hspy"
    data = np.random.rand(10, 10).astype(np.float32)
    meta = {"name": "test_data", "scale": (1.0, 1.0)}

    result = write_single_image(str(output_file), data, meta)

    assert len(result) == 1
    assert Path(result[0]).exists()
    assert Path(result[0]).suffix == ".hspy"


def test_write_single_image_unsupported_format(tmp_path):
    """Test that unsupported formats return empty list."""
    output_file = tmp_path / "test.unsupported"
    data = np.random.rand(10, 10)
    meta = {"name": "test"}

    result = write_single_image(str(output_file), data, meta)

    assert result == []


def test_write_single_image_native_format_excluded(tmp_path):
    """Test that napari native formats are excluded."""
    output_file = tmp_path / "test.png"
    data = np.random.rand(10, 10)
    meta = {"name": "test"}

    result = write_single_image(str(output_file), data, meta)

    # PNG should not be handled by this plugin
    assert result == []


def test_write_multiple_hspy(tmp_path):
    """Test writing multiple layers to .hspy format."""
    output_file = tmp_path / "multi_layer.hspy"

    layer1_data = np.random.rand(10, 10).astype(np.float32)
    layer1_meta = {"name": "layer1"}

    layer2_data = np.random.rand(10, 10).astype(np.float32)
    layer2_meta = {"name": "layer2"}

    data_list = [
        (layer1_data, layer1_meta, "image"),
        (layer2_data, layer2_meta, "image"),
    ]

    result = write_multiple(str(output_file), data_list)

    # For hierarchical formats, should write to one file
    assert len(result) >= 1
    assert any(Path(p).exists() for p in result)


def test_write_multiple_non_hierarchical(tmp_path):
    """Test writing multiple layers to non-hierarchical format.

    Non-hierarchical formats like EMD and Ripple create separate files
    for each layer when multiple layers are provided.
    """
    output_file = tmp_path / "multi_layer.emd"

    layer1_data = np.random.rand(10, 10).astype(np.float32)
    layer1_meta = {"name": "layer1"}

    layer2_data = np.random.rand(10, 10).astype(np.float32)
    layer2_meta = {"name": "layer2"}

    data_list = [
        (layer1_data, layer1_meta, "image"),
        (layer2_data, layer2_meta, "image"),
    ]

    result = write_multiple(str(output_file), data_list)

    # Non-hierarchical formats should create separate files for each layer
    assert len(result) >= 2
    # Check that files were created with layer names
    assert any("layer1" in Path(p).name for p in result)
    assert any("layer2" in Path(p).name for p in result)
    # Verify all files exist
    assert all(Path(p).exists() for p in result)


def test_write_3d_data(tmp_path):
    """Test writing 3D volumetric data."""
    output_file = tmp_path / "volume.hspy"
    data = np.random.rand(5, 10, 10).astype(np.float32)
    meta = {"name": "volume_data", "scale": (2.0, 1.0, 1.0)}

    result = write_single_image(str(output_file), data, meta)

    assert len(result) == 1
    assert Path(result[0]).exists()


def test_write_with_metadata_preservation(tmp_path):
    """Test that metadata is preserved in signal dict."""
    output_file = tmp_path / "metadata_test.hspy"
    data = np.random.rand(10, 10).astype(np.float32)

    # Include some RosettaSciIO metadata
    meta = {
        "name": "test",
        "metadata": {
            "metadata": {
                "General": {"title": "original_title"},
                "Signal": {"signal_type": "EDS_TEM"},
            },
            "original_metadata": {"custom_field": "value"},
        },
    }

    signal_dict = _layer_to_signal(data, meta, "default")

    # Check that original metadata is preserved
    assert signal_dict["metadata"]["Signal"]["signal_type"] == "EDS_TEM"
    assert signal_dict["original_metadata"]["custom_field"] == "value"


def test_write_integer_data(tmp_path):
    """Test writing integer data (e.g., labels)."""
    output_file = tmp_path / "labels.hspy"
    data = np.random.randint(0, 5, (10, 10), dtype=np.uint8)
    meta = {"name": "label_data"}

    result = write_single_image(str(output_file), data, meta)

    assert len(result) == 1
    assert Path(result[0]).exists()
