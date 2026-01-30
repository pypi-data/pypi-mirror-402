from geomet.screen.models import PanelSpec, DeckSpec
from geomet.screen.models.screen import ScreenSpec
from geomet.screen.render.screen_renderer import ScreenRenderer

def _build_dummy_panels():
    return {
        "P1": PanelSpec(
            name="Panel 1",
            aperture_short=10,
            aperture_long=20,
            material="TestMat",
            duro_hardness=60,
            panel_width=100,
            panel_height=50,
            px_per_mm=1.0,
        ),
        "P2": PanelSpec(
            name="Panel 2",
            aperture_short=15,
            aperture_long=25,
            material="TestMat",
            duro_hardness=70,
            panel_width=100,
            panel_height=50,
            px_per_mm=1.0,
        ),
    }

def _build_dummy_screen():
    deck_a = DeckSpec(
        name="Deck A",
        layout=[["P1", "P1"],
                ["P2", "P2"]],
        rows=2,
        cols=2,
    )
    deck_b = DeckSpec(
        name="Deck B",
        layout=[["P2", "P2"],
                ["P1", "P1"]],
        rows=2,
        cols=2,
    )

    return ScreenSpec(
        name="Test Screen",
        metadata={},
        decks={
            "Deck A": deck_a,
            "Deck B": deck_b,
        },
    )

if __name__ == "__main__":
    panels = _build_dummy_panels()
    screen = _build_dummy_screen()
    fig = ScreenRenderer.render(screen, panels, mode="plotly")
    fig.show(renderer="browser")
