import math

import pytest

from geomet.screen.models import PanelSpec
from geomet.screen.models import PanelLayoutCalculator


def make_basic_panel_spec(**overrides) -> PanelSpec:
    """Helper to create a reasonable PanelSpec for tests."""
    base_kwargs = dict(
        name="TestPanel",
        panel_width=1000.0,     # mm
        panel_height=500.0,     # mm
        aperture_short=10.0,    # mm
        aperture_long=30.0,     # mm
        radius=2.0,             # mm
        min_border=20.0,        # mm
        min_ligament=5.0,       # mm
        orientation="with-flow",
        material="PU",
        duro_hardness=80,
    )
    base_kwargs.update(overrides)
    return PanelSpec(**base_kwargs)


def test_compute_grid_with_flow_orientation():
    panel = make_basic_panel_spec(orientation="with-flow")

    grid = PanelLayoutCalculator.compute_grid(panel)

    assert grid["cols"] > 0
    assert grid["rows"] > 0
    assert grid["panel_w"] > 0
    assert grid["panel_h"] > 0
    # With\-flow: short side is width, long side is height.
    assert grid["ap_w"] <= grid["ap_h"]
    # Borders respected
    assert grid["border"] > 0
    # Ligatures are non\-negative
    assert grid["lig_x"] >= 0
    assert grid["lig_y"] >= 0


def test_compute_grid_cross_flow_orientation():
    panel = make_basic_panel_spec(orientation="cross-flow")

    grid = PanelLayoutCalculator.compute_grid(panel)

    # Cross\-flow: long side is width, short side is height.
    assert grid["ap_w"] >= grid["ap_h"]
    assert grid["cols"] > 0
    assert grid["rows"] > 0


def test_compute_grid_invalid_orientation_raises():

    with pytest.raises(ValueError):
        panel = make_basic_panel_spec(orientation="invalid")
        PanelLayoutCalculator.compute_grid(panel)


def test_compute_open_area_basic_properties():
    panel = make_basic_panel_spec()

    result = PanelLayoutCalculator.compute_open_area(panel)

    assert result["aperture_area_mm2"] > 0
    assert result["total_open_area_mm2"] > 0
    assert result["panel_area_mm2"] == pytest.approx(
        panel.panel_width * panel.panel_height
    )
    # Percent should be between 0 and 100
    assert 0.0 < result["open_area_percent"] < 100.0


def test_open_area_changes_with_aperture_size():
    small_panel = make_basic_panel_spec(aperture_short=5.0, aperture_long=10.0)
    large_panel = make_basic_panel_spec(aperture_short=20.0, aperture_long=40.0)

    small_open = PanelLayoutCalculator.compute_open_area(small_panel)["open_area_percent"]
    large_open = PanelLayoutCalculator.compute_open_area(large_panel)["open_area_percent"]

    assert large_open > small_open


def test_open_area_uses_radius_correction():
    no_radius = make_basic_panel_spec(radius=0.0)
    with_radius = make_basic_panel_spec(radius=5.0)

    no_radius_area = PanelLayoutCalculator.compute_open_area(no_radius)["aperture_area_mm2"]
    with_radius_area = PanelLayoutCalculator.compute_open_area(with_radius)["aperture_area_mm2"]

    # Corner radii reduce effective area
    assert with_radius_area < no_radius_area
    # Check formula qualitatively matches (rect \- corner\-cutout)
    rect_area = with_radius.aperture_short * with_radius.aperture_long
    expected_cutout = (4 - math.pi) * (with_radius.radius ** 2)
    assert with_radius_area == pytest.approx(rect_area - expected_cutout)
