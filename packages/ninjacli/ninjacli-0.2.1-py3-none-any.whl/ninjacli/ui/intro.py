import os, time, readchar, random
from contextlib import contextmanager
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.rule import Rule
from rich import box
from ninjacli.ui.logo import get_logo_text

console = Console()

def is_dir_root():
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    return cwd == home

def header_display(console: Console | None = None):
    console = console or Console()
    logo_text = get_logo_text()
    info_text = Text("\nWelcome to Ninja CLI! Ready to code?\n", style="bold white", justify="center")
    author_text = Text.assemble(
        ("@yasasbanukaofficial", "bold cyan"),
        " - GitHub, NPM | ",
        ("@yasasbanukagunasena", "bold magenta"),
        " - LinkedIn | ",
        ("Yasas Banu", "bold red"),
        " - Google Me\n",
        style="bold white",
        justify="center"
    )
    header = Group(logo_text, info_text, author_text)
    rules_set = Group(
        Text("To get the best output:", style="bold white"),
        Text.assemble("1. Enter prompt in a", (" structured format.", "red"), style="bold white"),
        Text.assemble("2. Use", (" SHIFT + ENTER ", "blue"), "for a new line", style="bold white"),
        Text.assemble("3. For best performance of this CLI, use", (" Linux or Mac ", "magenta"), style="bold white"),
    )
    header_panel = Panel(
        rules_set,
        title="[bold #00FFAA]NINJA CLI[/bold #00FFAA]",
        border_style="#00FFAA",
        padding=(1, 2),
        box=box.DOUBLE,
    )
    console.clear()
    console.print("\n", header)
    console.print(header_panel)          
    progress = Progress(
        SpinnerColumn(spinner_name="bouncingBall", style="bold magenta", speed=0.1),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=None, complete_style="bold #00FFAA", finished_style="bold green"),
        console=console,
        transient=True,
    )
    task = progress.add_task("Checking directories...", total=100)
    def make_panel() -> RenderableType:
        return Panel(
            progress,  
            title="[bold #00FFAA]Loading[/bold #00FFAA]",
            border_style="#FF00AA",
            padding=(1, 2),
            box=box.ROUNDED
        )
    with Live(make_panel(), console=console, refresh_per_second=30, transient=True):
        while not progress.finished:
            progress.update(task, advance=1)
            time.sleep(0.02)
    if is_dir_root():
        dir_panel = Panel(
            Text("• You are running Ninja CLI in your root directory! Consider running it in a project directory for security.", style="bold white"),
            title="[bold red]CAUTION[/bold red]",
            border_style="#FF006F",
            padding=(1, 2)
        )
        console.print(dir_panel)
    else:
        dir_panel = Panel(
            Text("• Directory check passed!. It is recommended to run in a project based directory.", style="bold white"),
            border_style="#FF006F",
        )
        console.print(dir_panel)

def prompt_display(console: Console | None = None, prompt: str | Text = None):
    console = console or Console()
    sys_prompt = prompt or Text.assemble(("> ", "bold red"), ("Type your message", "bold white"))
    top = Rule(style="white")
    console.print(top)
    return Prompt.ask(sys_prompt)
    
def api_option_display(console: Console | None = None):
    console = console or Console()
    options = [("openai", "Use OpenAI API Key"), ("gemini", "Use Gemini API Key"), ("openrouter", "Use OpenRouter API Key")]
    selected = 0
    def render():
        text = Text()
        for i, (_, label) in enumerate(options):
            if i == selected:
                text.append(f"▶ {label}\n", style="bold black on #00FFAA")
            else:
                text.append(f"  {label}\n", style="white")
        return Panel(text, title="[bold #00FFAA]Choose API Provider[/bold #00FFAA]", border_style="#00FFAA", padding=(1, 2), box=box.ROUNDED)
    user_option = None
    with Live(render(), console=console, refresh_per_second=1, auto_refresh=False, transient=True) as live:
        while True:
            key = readchar.readkey()
            if key in (readchar.key.UP, "k"):
                selected = (selected - 1) % len(options)
                live.update(render(), refresh=True)
            elif key in (readchar.key.DOWN, "j"):
                selected = (selected + 1) % len(options)
                live.update(render(), refresh=True)
            elif key == readchar.key.ENTER:
                user_option = options[selected][0]
                break
            elif key in ("q", readchar.key.ESC):
                user_option = None
                break
    if user_option == None:
        return api_option_display(console)
    return [user_option, prompt_display(console, prompt=Text.assemble(("# ", "bold red"), ( "API_KEY:   ", "bold blue")))]

def display_plan(content: str):
    console.print(Panel(Text(content, style="white"), title="[bold green]Plan[/bold green]", border_style="green", box=box.ROUNDED, title_align="left"))

@contextmanager
def display_tool_call(tool_name: str, tool_input: any):
    playful_messages = [
        "Sharpening the ninja blades 🗡️",
        "Tickling the server octopus 🐙",
        "Bribing the syntax gremlins 🪙",
        "Teaching cats to type 🐱⌨️",
        "Stirring the binary soup 🍲",
        "Convincing bytes to behave 🤝",
        "Polishing pixels ✨",
        "Counting invisible semicolons ;",
        "Summoning coffee-fueled logic ☕️",
        "Warming up the robot brain 🤖",
    ]

    chosen = random.choice(playful_messages)
    status_message = f"[bold yellow]{chosen} — [cyan]{tool_name}[/cyan]"
    with console.status(status_message, spinner="aesthetic"):
        yield

def display_tool_result(tool_name: str, result: any):
    result_str = str(result)
    if len(result_str) > 1000:
        result_str = result_str[:1000] + "\n\n[bold red]... (output truncated) ...[/bold red]"
    console.print(Panel(Text(result_str, style="white"), title=f"[bold blue]Tool Output: {tool_name}[/bold blue]", border_style="blue", box=box.ROUNDED))

def display_output(content: str):
    console.print(Rule(style="dim"))
    console.print(Text("\n🤖 Assistant:", style="bold magenta"))
    console.print(content)
    console.print()

def ask_restriction_confirmation(command: str) -> bool:
    console.print(Panel(f"[bold red]⚠️  WARNING:[/bold red] The command [yellow]'{command}'[/yellow] is restricted.", border_style="red"))
    return Confirm.ask("Do you want to proceed?")