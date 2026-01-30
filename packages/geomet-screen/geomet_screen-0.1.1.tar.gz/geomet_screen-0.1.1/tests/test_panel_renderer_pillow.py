import tempfile
from pathlib import Path

from PIL import Image

from geomet.screen.models.panel import PanelSpec
from geomet.screen.render.panel_renderer import PanelRenderer


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


def test_render_pillow_creates_image_file():
    panel = make_basic_panel_spec()

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "panel.png"

        PanelRenderer.render(panel, mode="pillow", output_path=out_path)

        assert out_path.exists()
        with Image.open(out_path) as img:
            assert img.width > 0
            assert img.height > 0



def test_render_pillow_requires_output_path():
    panel = make_basic_panel_spec()

    # No output_path should raise
    from pytest import raises

    with raises(ValueError):
        PanelRenderer.render(panel, mode="pillow", output_path=None)
