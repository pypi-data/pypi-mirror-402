
from geomet.screen.models.panel import PanelSpec
from geomet.screen.render.panel_renderer import PanelRenderer
from geomet.screen.models.panel_layout import PanelLayoutCalculator


def make_basic_panel_spec(**overrides) -> PanelSpec:
    base_kwargs = dict(
        name="TestPanel",
        panel_width=200.0,
        panel_height=100.0,
        aperture_short=10.0,
        aperture_long=20.0,
        radius=2.0,
        min_border=10.0,
        min_ligament=5.0,
        orientation="with-flow",
        material="PU",
        duro_hardness=80,
        panel_color_rgba=(200, 200, 200, 255),
        aperture_rgba=(0, 0, 0, 255),
    )
    base_kwargs.update(overrides)
    return PanelSpec(**base_kwargs)


def test_render_plotly_returns_figure():
    panel = make_basic_panel_spec()

    fig = PanelRenderer.render(panel, mode="plotly")

    assert fig is not None
    assert len(fig.data) == 1
    heatmap = fig.data[0]
    assert heatmap.z is not None


def test_render_plotly_grid_dimensions_match_layout():
    panel = make_basic_panel_spec()

    grid = PanelLayoutCalculator.compute_grid(panel)
    expected_rows = grid["rows"]
    expected_cols = grid["cols"]

    fig = PanelRenderer.render(panel, mode="plotly")
    heatmap = fig.data[0]

    # Plotly stores z as a list of rows
    assert len(heatmap.z) == expected_rows
    if expected_rows > 0:
        assert len(heatmap.z[0]) == expected_cols
