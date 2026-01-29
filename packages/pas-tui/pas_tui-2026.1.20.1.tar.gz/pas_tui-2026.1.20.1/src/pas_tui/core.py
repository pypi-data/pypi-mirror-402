import shutil
import subprocess
import sys
from typing import Optional, Dict, Any, List

from rich.console import Console
from rich.panel import Panel

# Shared console instance for all Rich output
console = Console()

def prompt_yes_no(message: str, default: bool = False) -> bool:
    """Standardize yes/no confirmation prompts."""
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        choice = input(f"{message} {suffix}: ").strip().lower()
        if choice == "":
            return default
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        console.print("[yellow]Please enter y or n.[/yellow]")

def copy_to_clipboard(text: str) -> bool:
    """Copy text to the system clipboard across different platforms."""
    try:
        if shutil.which("pbcopy"):
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return True
        elif shutil.which("xclip"):
            subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
            return True
        elif shutil.which("xsel"):
            subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, check=True)
            return True
    except Exception:
        pass
    return False

def prompt_toolkit_menu(choices, style=None, hotkeys=None, default_idx=0):
    """Interactive selection menu supporting arrow keys and immediate hotkeys."""
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.application import Application
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import Window, HSplit
    from prompt_toolkit.layout.controls import FormattedTextControl
    
    idx = max(0, min(default_idx, len(choices) - 1)) if choices else 0
    kb = KeyBindings()

    @kb.add('up')
    def _(event):
        nonlocal idx
        idx = (idx - 1) % len(choices)

    @kb.add('down')
    def _(event):
        nonlocal idx
        idx = (idx + 1) % len(choices)

    @kb.add('enter')
    def _(event):
        event.app.exit(result=choices[idx].value)

    @kb.add('escape')
    @kb.add('c-c')
    def _(event):
        event.app.exit(result=None)

    def make_hotkey_handler(h_val):
        keys = list(str(h_val))
        @kb.add(*keys)
        def _(event):
            for choice in choices:
                clean_title = choice.title.strip().lower()
                title_prefix = clean_title.split('.')[0].strip().lstrip('0')
                h_prefix = str(h_val).lstrip('0')
                
                if clean_title.startswith(f"{h_val}."):
                    event.app.exit(result=choice.value)
                    return
                if title_prefix == h_prefix and title_prefix != "":
                    event.app.exit(result=choice.value)
                    return
                if str(choice.value) == str(h_val):
                    event.app.exit(result=choice.value)
                    return
        return _

    if not hotkeys:
        hotkeys = []
        for choice in choices:
            title = choice.title.strip()
            if '.' in title:
                prefix = title.split('.')[0].strip().lower()
                if prefix:
                    hotkeys.append(prefix)
                    if prefix.isdigit() and prefix.startswith('0') and prefix != '0':
                        hotkeys.append(prefix.lstrip('0'))
        if not hotkeys:
            hotkeys = [str(i) for i in range(1, 10)] + ['q', 'b']
    
    seen = set()
    unique_hotkeys = []
    for h in hotkeys:
        if h not in seen:
            unique_hotkeys.append(h)
            seen.add(h)

    for h in unique_hotkeys:
        make_hotkey_handler(h)

    def get_text():
        result = []
        for i, choice in enumerate(choices):
            if i == idx:
                result.append(('class:selected', f" » {choice.title}\n"))
            else:
                result.append(('', f"   {choice.title}\n"))
        return result

    layout = Layout(HSplit([
        Window(content=FormattedTextControl(get_text)),
    ]))

    from prompt_toolkit.styles import Style
    if not style:
        style = Style([('selected', 'fg:#cc9900')])

    app = Application(layout=layout, key_bindings=kb, style=style, full_screen=False)
    return app.run()

def format_menu_choices(items: List[Any], title_field: Optional[str] = None, value_field: Optional[str] = None) -> List[Any]:
    """Prepare a list of items for `prompt_toolkit_menu` by adding index numbers and hotkeys."""
    import questionary
    
    special_keywords = {
        "quit": "q", "[quit]": "q", "(q) [quit]": "q", "q": "q",
        "back": "b", "[back]": "b", "(b) [back]": "b", "b": "b",
        "menu": "m", "[menu]": "m", "return to menu": "m"
    }
    
    regular_items = []
    special_items = []
    
    for item in items:
        title = ""
        if isinstance(item, dict):
            if title_field: title = str(item.get(title_field))
            elif "title" in item: title = str(item["title"])
            else: title = str(item)
        else:
            title = str(item)
            
        lower_title = title.strip().lower()
        if lower_title in special_keywords:
            special_items.append((item, special_keywords[lower_title]))
        else:
            regular_items.append(item)
            
    pad = len(str(len(regular_items)))
    choices = []
    
    for i, item in enumerate(regular_items, 1):
        idx_str = str(i).zfill(pad)
        if isinstance(item, dict):
            title = item.get(title_field) if title_field else item.get("title", str(item))
            value = item.get(value_field) if value_field else item.get("value", item)
        else:
            title = str(item)
            value = item
        choices.append(questionary.Choice(f"{idx_str}. {title}", value=value))
        
    for item, key in special_items:
        if isinstance(item, dict):
            title = item.get(title_field) if title_field else item.get("title", str(item))
            value = item.get(value_field) if value_field else item.get("value", item)
        else:
            title = str(item)
            value = item
        choices.append(questionary.Choice(f"{' ' * (pad - 1)}{key}. {title}", value=value))
        
    return choices
