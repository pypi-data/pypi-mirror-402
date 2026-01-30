from geomet.screen.models.panel import PanelSpec, Orientation
from geomet.screen.render.panel_colors import PanelColorMapper


def make_spec(name: str, aperture_long: float, aperture_short: float,
              orientation: Orientation = Orientation.WITH_FLOW,
              radius: float = 0.0) -> PanelSpec:
    return PanelSpec(
        name=name,
        panel_width=300,
        panel_height=300,
        aperture_long=aperture_long,
        aperture_short=aperture_short,
        orientation=orientation,
        radius=radius,
        px_per_mm=1.0,  # simplify
    )


def test_panel_color_mapper_from_specs_basic():
    # Small, medium, large open areas
    s_small = make_spec("P_small", aperture_long=20, aperture_short=10)
    s_medium = make_spec("P_medium", aperture_long=40, aperture_short=20)
    s_large = make_spec("P_large", aperture_long=60, aperture_short=30)

    # Impact panel: orientation BLANK (treated as zero area)
    s_impact = make_spec("P_impact", aperture_long=0, aperture_short=0,
                         orientation=Orientation.BLANK)

    specs = {
        "P_small": s_small,
        "P_medium": s_medium,
        "P_large": s_large,
        "P_impact": s_impact,
    }

    mapper = PanelColorMapper.from_specs(specs)
    cmap = mapper.generate_colormap()

    # All panels should have colors
    assert set(cmap.keys()) == set(specs.keys())

    # Impact panel must be grey
    assert cmap["P_impact"] == "#808080"

    # Non-impact colors should be valid hex strings
    for name in ["P_small", "P_medium", "P_large"]:
        color = cmap[name]
        assert isinstance(color, str)
        assert color.startswith("#")
        assert len(color) == 7  # \#RRGGBB


def test_panel_color_mapper_monotonicity():
    # Two non-impact panels with clearly different open areas
    s_small = make_spec("P_small", aperture_long=20, aperture_short=10)
    s_large = make_spec("P_large", aperture_long=80, aperture_short=40)

    mapper = PanelColorMapper.from_specs(
        {"P_small": s_small, "P_large": s_large}
    )
    cmap = mapper.generate_colormap()

    c_small = cmap["P_small"]
    c_large = cmap["P_large"]

    # Colors differ because normalization sees different values
    assert c_small != c_large
