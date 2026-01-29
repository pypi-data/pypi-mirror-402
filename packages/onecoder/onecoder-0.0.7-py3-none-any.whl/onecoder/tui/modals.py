from textual.screen import ModalScreen
from textual.widgets import Label, Button, ListView, ListItem
from textual.containers import Vertical, Grid
from textual.binding import Binding

class ModelSelectionModal(ModalScreen[str]):
    """Modal screen for selecting an LLM model."""

    CSS = """
    ModelSelectionModal {
        align: center middle;
    }

    #dialog {
        padding: 0 1;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    Label {
        padding: 1 2;
        width: 100%;
        text-align: center;
        text-style: bold;
    }
    
    ListView {
        height: auto;
        max-height: 20;
        margin: 1 0;
        border: solid $accent;
    }

    ListItem {
        padding: 1 2;
    }

    #buttons {
        width: 100%;
        align: center bottom;
        padding-top: 1;
        height: auto;
    }
    
    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, models: list[str], current_model: str):
        super().__init__()
        self.models = models
        self.current_model = current_model

    def compose(self):
        yield Vertical(
            Label("Select AI Model", id="title"),
            ListView(
                *[ListItem(Label(f"{'● ' if m == self.current_model else '  '}{m}"), id=m) for m in self.models],
                id="model-list"
            ),
            Grid(
                Button("Select", variant="primary", id="select"),
                Button("Cancel", variant="error", id="cancel"),
                id="buttons",
                column_gutter=1,
                grid_size=(2, 1)
            ),
            id="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select":
            self._select_current()
        elif event.button.id == "cancel":
            self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Double click or enter on list item
        selected_model = event.item.id
        self.dismiss(selected_model)

    def _select_current(self):
        list_view = self.query_one("#model-list", ListView)
        if list_view.highlighted_child:
            self.dismiss(list_view.highlighted_child.id)
        else:
            self.dismiss(None)

    def action_cancel(self):
        self.dismiss(None)
