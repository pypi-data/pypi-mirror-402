import os
import json
import subprocess
from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Log, Button, SelectionList, Label, Select, Static
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.message import Message

class SearchResult(Message):
    def __init__(self, url: str, fmt: str) -> None:
        self.url = url
        self.fmt = fmt 
        super().__init__()

class PathSetupScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="setup_dialog"):
            yield Label("YT-NEBULA SETUP", id="setup_title")
            yield Label("folder to save files:")
            yield Input(placeholder="/home/user/music", id="path_input", value=os.path.expanduser("~/Music"))
            yield Button("enter nebula", id="start_btn", variant="success")

    @on(Button.Pressed, "#start_btn")
    def finish_setup(self) -> None:
        path = self.query_one("#path_input", Input).value.strip()
        self.app.download_path = path if path else os.path.expanduser("~/Music")
        os.makedirs(self.app.download_path, exist_ok=True)
        self.app.pop_screen()

class SearchScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="search_container"):
            yield Label("NEBULA SEARCH", id="section_subtitle")
            with Horizontal(id="search_bar"):
                yield Input(placeholder="search for music or video...", id="search_input")
                yield Button("FIND", id="search_button", variant="primary")
            yield SelectionList[str](id="results_list")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "enter":
            if self.focused is self.query_one("#results_list"):
                self.action_select_and_go()

    def action_select_and_go(self) -> None:
        sel = self.query_one("#results_list", SelectionList)
        if sel.highlighted_option:
            url = sel.highlighted_option.value
            main_app = self.app
            # capturamos el valor del selector antes de cerrar
            fmt = main_app.query_one("#fmt_selector", Select).value
            self.app.post_message(SearchResult(url, fmt))
            self.app.pop_screen()

    @on(Input.Submitted, "#search_input")
    @on(Button.Pressed, "#search_button")
    def start_search(self) -> None:
        btn = self.query_one("#search_button", Button)
        btn.loading = True
        query = self.query_one("#search_input", Input).value.strip()
        if query: self.run_search(query)

    @work(exclusive=True, thread=True)
    def run_search(self, query: str) -> None:
        cmd = ["yt-dlp", "--dump-json", "--flat-playlist", f"ytsearch10:{query}"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        options = []
        for line in proc.stdout.strip().split('\n'):
            if not line.strip(): continue
            try:
                v = json.loads(line)
                title = v.get('title', 'unknown')[:55]
                url = v.get('url') or v.get('webpage_url')
                if url: options.append((f"󰎈 {title}", url))
            except: continue
        self.app.call_from_thread(self.finish_search, options)

    def finish_search(self, options):
        self.query_one("#search_button", Button).loading = False
        res_list = self.query_one("#results_list", SelectionList)
        res_list.clear_options()
        res_list.add_options(options)
        res_list.focus()

class YTNebula(App):
    TITLE = "yt-nebula"
    CSS = """
    Screen { background: #0b0214; }
    #setup_dialog { align: center middle; padding: 2 4; border: tall #7b2cbf; margin: 8 20; background: #10002b; }
    #setup_title { text-style: bold; color: #c77dff; margin-bottom: 1; }
    
    #main_grid { padding: 1; }
    
    /* AQUI ESTA EL ARREGLO: quitamos el align center y usamos flex vertical */
    #header_card { 
        border: round #5a189a; 
        padding: 1 2; 
        background: #1a0a2e; 
        height: auto; 
        margin-bottom: 1;
    }

    #fmt_label {
        color: #e0aaff;
        margin-bottom: 1;
        text-style: bold;
    }

    #fmt_selector { 
        width: 100%; 
        border: solid #7b2cbf; 
        background: #240046;
    }

    #status_log { border: vkey #3c096c; background: #050010; color: #e0aaff; height: 1fr; }
    
    #search_container { padding: 1; }
    #search_bar { height: auto; margin-bottom: 1; }
    #search_input { width: 1fr; border: solid #5a189a; background: #10002b; }
    #search_button { width: 12; background: #7b2cbf; }
    #section_subtitle { color: #9d4edd; text-style: bold; margin-bottom: 1; }
    SelectionList { border: solid #3c096c; background: #0b0214; }
    """

    BINDINGS = [("d", "push_screen('search_screen')", "search"), ("q", "quit", "exit")]
    SCREENS = {"search_screen": SearchScreen}

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_grid"):
            # UI SIMPLIFICADA: Vertical puro, sin cosas raras
            with Vertical(id="header_card"):
                yield Label("YT-NEBULA COMMAND CENTER", id="setup_title")
                yield Label("OUTPUT FORMAT:", id="fmt_label")
                yield Select([("MP3 (Audio Only)", "mp3"), ("MP4 (Video + Audio)", "mp4")], value="mp3", id="fmt_selector", allow_blank=False)
            yield Log(id="status_log")
        yield Footer()

    async def on_mount(self) -> None:
        self.push_screen(PathSetupScreen())

    @on(SearchResult)
    def prepare_download(self, message: SearchResult):
        self.do_download(message.url, message.fmt)

    @work(exclusive=False, thread=True)
    def do_download(self, url: str, fmt: str) -> None:
        log = self.query_one("#status_log", Log)
        self.app.call_from_thread(log.write_line, f"󰋋 nebula: syncing [{fmt}] mode...")
        
        template = os.path.join(self.download_path, "%(title)s.%(ext)s")
        
        cmd = [
            "yt-dlp",
            "--extractor-args", "youtube:player-client=web,android",
            "--add-metadata",
            "--embed-thumbnail",
            "-o", template,
            url
        ]
        
        if fmt == "mp3": 
            cmd.extend(["-x", "--audio-format", "mp3"])
        else: 
            cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"])

        proc = subprocess.run(cmd, capture_output=True, text=True)
        
        if proc.returncode == 0:
            self.app.call_from_thread(log.write_line, f" DONE: {fmt} sync complete")
            self.notify(f"nebula: {fmt} downloaded")
        else:
            self.app.call_from_thread(log.write_line, " RAW ERROR FROM YOUTUBE:")
            for line in proc.stderr.split('\n'):
                if line.strip():
                    self.app.call_from_thread(log.write_line, f" > {line}")

def check_dependencies():
    import shutil
    if not shutil.which("ffmpeg"):
        print("󱔎 ERROR: ffmpeg not found! Please install it to use nebula.")
        exit(1)

def run():
    check_dependencies()
    app = YTNebula()
    app.run()

if __name__ == "__main__":
    run()
