from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label, ProgressBar
from textual.containers import Grid, Vertical, Center
from textual.screen import Screen
import datetime
import random

DEV_CHALLENGES = {
    1: ("Setup", "Environment", "Install Python & setup venv"),
    2: ("Git", "Version Control", "Create GitHub repo"),
    3: ("CLI", "Terminal", "Learn basic shell commands"),
    4: ("Functions", "Python", "Refactor code"),
    5: ("Loops", "Python", "Practice loops"),
    6: ("Files", "IO", "Read/write files"),
    7: ("Errors", "Debugging", "Fix bugs"),
    8: ("Modules", "Imports", "Create modules"),
    9: ("Textual", "TUI", "Build a TUI"),
    10: ("Styling", "CSS", "Style Textual"),
    11: ("Events", "UI", "Handle events"),
    12: ("State", "Logic", "Manage app state"),
    13: ("Dates", "Time", "Work with datetime"),
    14: ("Testing", "QA", "Write tests"),
    15: ("Docs", "Docs", "Write README"),
    16: ("Packaging", "PyPI", "Create package"),
    17: ("APIs", "Web", "Call API"),
    18: ("JSON", "Data", "Parse JSON"),
    19: ("Performance", "Optimize", "Speed code"),
    20: ("Security", "Safety", "Secure code"),
    21: ("Refactor", "Clean", "Clean code"),
    22: ("UX", "Design", "Improve UX"),
    23: ("Review", "Learn", "Review progress"),
    24: ("Celebrate", "Congrats", "You made it!")
}

QUOTES = [
    "Progress > perfection.",
    "Every expert was once a beginner.",
    "One step a day.",
    "You are doing great."
]

class DayScreen(Screen):

    CSS = """
    DayScreen {
        align: center middle;
    }

    #dialog {
        width: 70;
        border: round $accent;
        background: $panel;
        padding: 2;
    }
    """

    def __init__(self, day: int):
        self.day = day
        super().__init__()

    def compose(self):
        title, desc, task = DEV_CHALLENGES[self.day]
        quote = random.choice(QUOTES)

        with Vertical(id="dialog"):
            yield Label(f"[bold]{title}[/bold]")
            yield Label(desc)
            yield Label(task)
            yield Label(f"[italic]{quote}[/italic]")
            with Center():
                yield Button("Close")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()
        event.stop()

class DeveloperAdventApp(App):

    CSS = """
    Grid {
        grid-size: 6 4;
        grid-gutter: 1 1;
    }

    Button {
        width: 100%;
        height: 100%;
        border: round white;
        background: $boost;
    }

    Button:hover {
        background: $secondary;
    }

    Button.opened {
        background: $success;
    }

    Button.locked {
        background: $error;
    }
    """

    BINDINGS = [
        ("r", "reset", "Reset"),
        ("c", "count", "Count"),
        ("h", "help", "Help"),
        ("n", "next", "Next"),
        ("q", "quit", "Quit"),
    ]

    START_DATE = datetime.date(2025, 12, 1)

    def compose(self):
        yield Header()
        self.progress = ProgressBar(total=24)
        yield self.progress

        with Grid():
            for day in range(1, 25):
                unlock = self.START_DATE + datetime.timedelta(days=day - 1)
                if datetime.date.today() < unlock:
                    yield Button("Closed", id=f"locked-{day}", classes="locked")
                else:
                    yield Button(str(day), id=f"day-{day}")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if not event.button.id:
            return
        
        if event.button.has_class("locked"):
            return
        
        day = int(str(event.button.label))  # convert Content to str

        if not event.button.has_class("opened"):
            event.button.add_class("opened")
            self.progress.advance(1)

        self.push_screen(DayScreen(day))

    def action_count(self):
        opened = len(self.query("Button.opened"))
        self.notify(f"Opened {opened}/24")

    def action_reset(self):
        for b in self.query("Button.opened"):
            b.remove_class("opened")
        self.progress.progress = 0
        self.progress.refresh()


    def action_help(self):
        self.notify("r reset | c count | h help | n next")

    def action_next(self):
        for b in self.query("Button"):
            if b.id and not b.has_class("opened"):
                self.on_button_pressed(Button.Pressed(b))
                break
    
    def action_quit(self):
        self.exit()

def main():
    DeveloperAdventApp().run()

if __name__ == "__main__":
    main()
