"""Live Duel HUD - Exposes the Duel Engine's mind."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Global mode flag
_gentle_mode = False

def set_gentle_mode(enabled: bool):
    global _gentle_mode
    _gentle_mode = enabled

def is_gentle() -> bool:
    return _gentle_mode


def _claim_status(claim_idx: int, errors: list) -> tuple[str, str]:
    """Determine claim status: green/yellow/red based on errors."""
    for e in errors:
        if e.claim_index == claim_idx:
            if e.severity >= 2:
                return "red", "✗"
            return "yellow", "~"
    return "green", "✓"


def render_duel_state(duel, console: Console = None):
    """Render live HUD showing claims, belief, and attack target."""
    console = console or Console()
    state = duel.state
    claims = state.claims
    errors = state.errors
    belief = state.belief
    
    if _gentle_mode:
        # Gentle: just show progress dots
        dots = ""
        for c in claims:
            color, _ = _claim_status(c.index, errors)
            dot = {"green": "[green]●[/green]", "yellow": "[yellow]●[/yellow]", "red": "[red]●[/red]"}[color]
            dots += dot + " "
        console.print(f"[dim]Progress:[/dim] {dots}")
        return
    
    # === CLAIMS PANEL ===
    claims_table = Table(box=None, show_header=False, padding=(0, 1))
    claims_table.add_column("", width=3)
    claims_table.add_column("", width=60)
    
    for c in claims:
        color, icon = _claim_status(c.index, errors)
        claims_table.add_row(
            Text(icon, style=color),
            Text(f"[{c.index+1}] {c.statement}", style=color)
        )
    
    console.print(Panel(claims_table, title="[bold]CLAIMS[/bold]", border_style="cyan", box=box.ROUNDED))
    
    # === BELIEF PANEL ===
    if belief:
        console.print(Panel(
            Text(f'"{belief}"', style="italic"),
            title="[bold]CURRENT BELIEF[/bold]",
            border_style="magenta",
            box=box.ROUNDED
        ))
    
    # === ATTACK TARGET PANEL ===
    if errors:
        target = max(errors, key=lambda e: e.severity)
        sev_label = {1: "minor", 2: "significant", 3: "critical"}.get(target.severity, "")
        sev_color = {1: "dim", 2: "yellow", 3: "red"}.get(target.severity, "red")
        
        target_text = Text()
        target_text.append(f"Claim {target.claim_index+1}: ", style="bold")
        target_text.append(f'"{target.violated_claim}"\n', style="white")
        target_text.append("Error: ", style="dim")
        target_text.append(f"{target.type} ", style=sev_color)
        target_text.append(f"({sev_label})", style="dim")
        
        console.print(Panel(
            target_text,
            title="[bold red]ATTACK TARGET[/bold red]",
            border_style="red",
            box=box.ROUNDED
        ))


def render_attack(question: str, console: Console = None):
    """Render the attack question in a panel."""
    console = console or Console()
    
    if _gentle_mode:
        console.print(f"[cyan]{question}[/cyan]")
        return
    
    console.print(Panel(
        Text(question, style="yellow bold"),
        title="[bold yellow]INTERROGATION[/bold yellow]",
        border_style="yellow",
        box=box.HEAVY
    ))


def render_reveal(reveal: dict, console: Console = None):
    """Render final reveal with claim satisfaction, trajectory, verdict."""
    console = console or Console()
    claims = reveal.get("claims", [])
    errors = reveal.get("errors", [])
    history = reveal.get("history", [])
    belief = reveal.get("belief", "")
    
    if _gentle_mode:
        # Gentle reveal: supportive, not clinical
        console.print()
        if not errors:
            console.print("[green]Nice work![/green] You covered the key points.")
        else:
            console.print("[cyan]Here's what to focus on:[/cyan]")
            for e in errors[:2]:
                # Reframe errors as learning opportunities
                console.print(f"  [dim]•[/dim] {e.violated_claim}")
        
        # Simple score bar
        max_sev = max((e.severity for e in errors), default=0)
        bars = {0: "[green]●●●●●[/green]", 1: "[green]●●●●[/green][dim]○[/dim]", 
                2: "[yellow]●●●[/yellow][dim]○○[/dim]", 3: "[red]●[/red][dim]○○○○[/dim]"}
        console.print(f"\n{bars.get(max_sev, bars[3])}")
        return
    
    console.print()
    console.print("[bold cyan]═══ DUEL COMPLETE ═══[/bold cyan]")
    
    # === CLAIM SATISFACTION TABLE ===
    if claims:
        table = Table(title="Claim Satisfaction", box=box.ROUNDED, border_style="cyan")
        table.add_column("#", width=3)
        table.add_column("Type", width=12)
        table.add_column("Claim", width=50)
        table.add_column("Status", width=8)
        
        for c in claims:
            color, icon = _claim_status(c.index, errors)
            status = {"green": "PASS", "yellow": "PARTIAL", "red": "FAIL"}.get(color, "?")
            table.add_row(
                str(c.index + 1),
                c.claim_type,
                c.statement,
                Text(f"{icon} {status}", style=color)
            )
        console.print(table)
    
    # === BELIEF TRAJECTORY TIMELINE ===
    if history:
        console.print()
        console.print(Panel.fit("[bold]BELIEF TRAJECTORY[/bold]", border_style="magenta"))
        for i, snap in enumerate(history):
            prefix = "→" if i > 0 else "○"
            label = "Initial" if snap.trigger == "initial" else f"After Q{i}"
            console.print(f"  [magenta]{prefix}[/magenta] [dim]{label}:[/dim] \"{snap.belief}\"")
            for e in snap.errors_at_time[:2]:
                sev_color = {1: "dim", 2: "yellow", 3: "red"}.get(e.severity, "red")
                console.print(f"      [{sev_color}]└─ {e.type} → claim {e.claim_index+1}[/{sev_color}]")
    elif belief:
        console.print()
        console.print(f"[dim]Final belief:[/dim] \"{belief}\"")
    
    # === FINAL ERRORS ===
    if errors:
        console.print()
        err_table = Table(title="Errors Detected", box=box.ROUNDED, border_style="red")
        err_table.add_column("Type", width=18)
        err_table.add_column("Severity", width=10)
        err_table.add_column("Violated Claim", width=40)
        
        for e in errors:
            sev = {1: "minor", 2: "significant", 3: "critical"}.get(e.severity, "")
            sev_color = {1: "dim", 2: "yellow", 3: "red"}.get(e.severity, "red")
            err_table.add_row(
                e.type,
                Text(sev, style=sev_color),
                f"[{e.claim_index+1}] {e.violated_claim[:40]}"
            )
        console.print(err_table)
    
    # === VERDICT PANEL ===
    console.print()
    max_sev = max((e.severity for e in errors), default=0)
    verdicts = {
        0: ("[green]█████[/green]", "SOLID", "green"),
        1: ("[green]████░[/green]", "MINOR GAPS", "green"),
        2: ("[yellow]███░░[/yellow]", "SIGNIFICANT GAPS", "yellow"),
        3: ("[red]█░░░░[/red]", "CRITICAL ERRORS", "red"),
    }
    bar, label, color = verdicts.get(max_sev, verdicts[3])
    from rich.text import Text as RichText
    verdict_text = RichText.from_markup(f"{bar}  {label}")
    verdict_text.justify = "center"
    console.print(Panel(
        verdict_text,
        title="[bold]VERDICT[/bold]",
        border_style=color,
        box=box.DOUBLE
    ))
