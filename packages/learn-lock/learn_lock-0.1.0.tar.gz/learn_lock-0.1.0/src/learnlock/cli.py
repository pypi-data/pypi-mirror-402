"""learn-lock CLI - Interactive learning system with adversarial spaced repetition."""

import sys
import os
import select
import warnings
import logging

# Suppress all warnings and litellm logging noise
warnings.filterwarnings("ignore")
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
logging.getLogger("litellm").setLevel(logging.CRITICAL)

from typing import Optional, Callable

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich import box

from . import config
from . import storage
from . import scheduler
from . import llm
from .tools import extract_youtube, extract_article, extract_pdf, extract_github


def _flush_stdin():
    """Flush any buffered stdin input."""
    if sys.platform == "win32":
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except:
            pass
    else:
        try:
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except:
            try:
                while select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.readline()
            except:
                pass

# ============ CONSTANTS ============
VERSION = "0.1.0"
BANNER = """[bold cyan]
██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗
██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝
██║     █████╗  ███████║██████╔╝██╔██╗ ██║██║     ██║   ██║██║     █████╔╝ 
██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗ 
███████╗███████╗██║  ██║██║  ██║██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗
╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝[/bold cyan]
"""

HELP_TEXT = """
[bold]Commands:[/bold]
  [cyan]/add[/cyan] <source>     Add YouTube, article, GitHub, or PDF
  [cyan]/study[/cyan]            Start adversarial study session
  [cyan]/stats[/cyan]            Show your progress
  [cyan]/list[/cyan]             List all concepts
  [cyan]/due[/cyan]              Show what's due
  [cyan]/skip[/cyan] <name>      Skip a concept
  [cyan]/unskip[/cyan] <name>    Restore skipped concept
  [cyan]/config[/cyan]           Show configuration
  [cyan]/clear[/cyan]            Clear screen
  [cyan]/help[/cyan]             Show this help
  [cyan]/quit[/cyan]             Exit

[bold]How It Works:[/bold]
  1. You explain a concept
  2. I find holes in your understanding
  3. I challenge you with follow-up questions
  4. Your score drops for each gap exposed
  5. No bullshitting allowed

[bold]Supported Sources:[/bold]
  • YouTube videos • GitHub repos • PDFs • Web articles

[bold]Tips:[/bold]
  • Paste a URL to add content
  • Press Enter to start studying
  • Be specific — vague answers get challenged
"""

console = Console()
app = typer.Typer(no_args_is_help=False)


# ============ UTILITIES ============

def _spinner(msg: str):
    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn(f"[dim]{msg}[/dim]"),
        transient=True,
        console=console,
    )


def _is_url(text: str) -> bool:
    return text.startswith(("http://", "https://", "www."))


def _is_local_file(text: str) -> bool:
    return os.path.exists(text)


def _is_image_path(text: str) -> bool:
    """Check if text is a path to an image file."""
    if not os.path.exists(text):
        return False
    from pathlib import Path
    return Path(text).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")


def _is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def _is_github(url: str) -> bool:
    return "github.com" in url


def _is_pdf(path: str) -> bool:
    return path.endswith(".pdf") or "/pdf/" in path


def _print_banner():
    console.print(BANNER)


def _print_status():
    """Print current status line."""
    try:
        summary = scheduler.get_study_summary()
        parts = []
        if summary["due_now"] > 0:
            parts.append(f"[cyan]{summary['due_now']} due[/cyan]")
        if summary["total_concepts"] > 0:
            parts.append(f"[dim]{summary['total_concepts']} concepts[/dim]")
        if summary["mastered"] > 0:
            parts.append(f"[green]{summary['mastered']} mastered[/green]")
        if parts:
            console.print(" • ".join(parts))
    except:
        pass


def _check_api_keys():
    """Check for required API keys."""
    if not os.environ.get("GROQ_API_KEY"):
        console.print("[red]Error: GROQ_API_KEY not set[/red]")
        console.print()
        console.print("[dim]Get your free API key:[/dim]")
        console.print("  1. Go to [cyan]https://console.groq.com[/cyan]")
        console.print("  2. Create account and get API key")
        console.print()
        if sys.platform == "win32":
            console.print("[dim]Set it (PowerShell):[/dim]")
            console.print('  [white]$env:GROQ_API_KEY="your_key"[/white]')
            console.print()
            console.print("[dim]Or permanent (CMD):[/dim]")
            console.print('  [white]setx GROQ_API_KEY "your_key"[/white]')
        else:
            console.print("[dim]Set it:[/dim]")
            console.print("  [white]export GROQ_API_KEY=your_key[/white]")
            console.print()
            console.print("[dim]Or add to ~/.bashrc for persistence[/dim]")
        return False
    return True


# ============ COMMANDS ============

def cmd_add(url: str) -> bool:
    """Add content from URL."""
    url = url.strip()
    if not url:
        console.print("[yellow]Usage: /add <url>[/yellow]")
        return True
    
    # Check if exists
    existing = storage.get_source_by_url(url)
    if existing:
        console.print(f"[yellow]Already added:[/yellow] {existing['title']}")
        concepts = storage.get_concepts_for_source(existing["id"])
        console.print(f"[dim]{len(concepts)} concepts[/dim]")
        return True
    
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    
    with Progress(
        SpinnerColumn(style="cyan"),
        BarColumn(bar_width=20, complete_style="cyan", finished_style="green"),
        TextColumn("[bold]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching content...", total=4)
        
        # Step 1: Fetch based on URL type
        if _is_youtube(url):
            result = extract_youtube(url)
        elif _is_github(url):
            result = extract_github(url)
        elif _is_pdf(url):
            result = extract_pdf(url)
        else:
            result = extract_article(url)
        
        if "error" in result:
            progress.stop()
            console.print(f"[red]Error: {result['error']}[/red]")
            return True
        
        progress.update(task, advance=1, description="Generating title...")
        
        # Step 2: Title
        title = llm.generate_title(result["content"], result["title"])
        progress.update(task, advance=1, description="Extracting concepts...")
        
        # Step 3: Concepts
        try:
            concepts = llm.extract_concepts(result["content"], title)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Error: Failed to extract concepts: {e}[/red]")
            return True
        
        if not concepts:
            progress.stop()
            console.print("[red]Error: No concepts found[/red]")
            return True
        
        progress.update(task, advance=1, description="Saving...")
        
        # Step 4: Store (with segments if available for YouTube)
        segments_json = None
        if result.get("segments"):
            import json
            segments_json = json.dumps(result["segments"])
        
        source_id = storage.add_source(
            url=result["url"],
            title=title,
            source_type=result["source_type"],
            raw_content=result["content"],
            segments=segments_json
        )
        
        for c in concepts:
            storage.add_concept(source_id, c["name"], c["source_quote"], c.get("question"))
        
        progress.update(task, advance=1, description="Done!")
    
    console.print(f"[green]OK[/green] {title}")
    console.print(f"[green]OK[/green] Added {len(concepts)} concepts:")
    for c in concepts:
        console.print(f"  [dim]•[/dim] {c['name']}")
    
    console.print()
    console.print(f"[cyan]{len(concepts)} concepts ready to study![/cyan]")
    console.print("[dim]Run /study to start, or press Enter[/dim]")
    
    return True


def cmd_study() -> bool:
    """Interactive study session with Duel Engine - adversarial Socratic interrogation."""
    from .duel import create_duel, belief_to_score, save_duel_data
    from .hud import render_duel_state, render_attack, render_reveal
    
    due = scheduler.get_next_due()
    
    if not due:
        summary = scheduler.get_study_summary()
        if summary["total_concepts"] == 0:
            console.print("[dim]No concepts yet. Add some content first:[/dim]")
            console.print("  [cyan]/add[/cyan] <youtube-url>")
        else:
            console.print("[green]OK[/green] All caught up! Nothing due for review.")
        return True
    
    total_due = len(scheduler.get_all_due())
    studied = 0
    
    console.print()
    console.print(f"[bold cyan]DUEL SESSION[/bold cyan] - {total_due} concepts")
    console.print("[dim]I will find what you don't know. Type 'skip' or 'q' anytime.[/dim]")
    console.print("[dim]Double Enter to send your answer.[/dim]")
    
    while due:
        studied += 1
        
        # Create Duel Engine
        duel = create_duel(
            concept=due["name"],
            ground_truth=due["source_quote"],
            question=due.get("question")
        )
        
        # Header
        console.print()
        console.print(f"[bold]--- {studied}/{total_due}: {due['name']} ---[/bold]")
        console.print(f"[dim]{due['source_title']}[/dim]")
        
        # Show memory from last duel (if exists)
        memory = storage.get_duel_memory(due["id"])
        if memory and memory.get("last_belief"):
            console.print()
            console.print("[dim]Last time you believed:[/dim]")
            console.print(f"  \"{memory['last_belief']}\"")
            if memory.get("last_errors"):
                console.print(f"[dim]It failed because:[/dim] {memory['last_errors']}")
            console.print("[dim]Let's see if you still believe it.[/dim]")
        
        # Initial HUD - show claims panel
        console.print()
        render_duel_state(duel, console)
        
        # Initial challenge
        console.print()
        render_attack(duel.get_challenge(), console)
        
        skipped = False
        
        # Duel loop
        while not duel.finished:
            console.print()
            
            _flush_stdin()
            lines = []
            try:
                while True:
                    line = console.input("[bold]> [/bold]" if not lines else "[bold]  [/bold]")
                    if not line and lines:
                        break
                    if line:
                        lines.append(line)
                    elif not lines:
                        console.print("[yellow]Explain yourself, or 'skip'.[/yellow]")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Session ended.[/dim]")
                return True
            
            _flush_stdin()
            answer = " ".join(lines).strip()
            
            if answer.lower() in ("q", "quit", "/quit", "exit"):
                console.print("[dim]Session ended.[/dim]")
                return True
            
            if answer.lower() in ("skip", "s", "/skip"):
                storage.skip_concept(due["id"])
                console.print("[yellow]Skipped[/yellow]")
                skipped = True
                break
            
            if not answer:
                continue
            
            # OCR support
            if _is_image_path(answer):
                with _spinner("Reading image..."):
                    from .ocr import extract_text_from_image
                    ocr = extract_text_from_image(answer)
                if "error" in ocr or not ocr["text"].strip():
                    console.print("[yellow]Couldn't read image.[/yellow]")
                    continue
                answer = ocr["text"]
                console.print(f"[dim]OCR: \"{answer[:80]}...\"[/dim]")
            
            # Process
            with _spinner(""):
                result = duel.process(answer)
            
            if result["type"] == "attack":
                # Update HUD after processing
                console.print()
                render_duel_state(duel, console)
                console.print()
                render_attack(result["message"], console)
        
        if skipped:
            due = scheduler.get_next_due()
            total_due = len(scheduler.get_all_due()) + studied
            continue
        
        # REVEAL with HUD
        reveal = duel.get_reveal()
        render_reveal(reveal, console)
        _show_source_help(due, reveal["ground_truth"])
        
        # Score
        score = belief_to_score(duel.state)
        
        # Save duel memory
        errors_str = "; ".join(e.description for e in reveal["errors"][:2]) if reveal["errors"] else ""
        last_attack = reveal["attacks"][-1] if reveal.get("attacks") else ""
        storage.save_duel_memory(due["id"], reveal["belief"], errors_str, last_attack)
        
        # Save duel data for research
        try:
            save_duel_data(duel.state, due["name"])
        except:
            pass
        
        # Store explanation
        storage.add_explanation(
            concept_id=due["id"],
            text=" | ".join(reveal["evidence"]),
            score=score,
            covered=None,
            missed=errors_str,
            feedback=reveal["belief"]
        )
        
        # Update scheduler
        sched_result = scheduler.update_after_review(due["id"], score)
        console.print()
        console.print(f"[dim]Next review: {sched_result['next_review']}[/dim]")
        
        # Next
        due = scheduler.get_next_due()
        
        if due:
            remaining = len(scheduler.get_all_due())
            console.print()
            try:
                cont = console.input(f"[dim]({remaining} more) Enter to continue, 'q' to quit: [/dim]").strip()
                if cont.lower() in ("q", "quit", "n"):
                    console.print("[dim]Session ended.[/dim]")
                    return True
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Session ended.[/dim]")
                return True
    
    console.print()
    console.print(f"[green]Done.[/green] Dueled {studied} concepts.")
    return True


def _show_reveal(reveal: dict, due: dict = None):
    """Display the final reveal - claims, belief trajectory, typed errors."""
    console.print()
    console.print("[bold]--- REVEAL ---[/bold]")
    
    # A) Show claims
    claims = reveal.get("claims", [])
    if claims:
        console.print()
        console.print("[bold]Ground Truth Claims:[/bold]")
        for c in claims:
            console.print(f"  [{c.index+1}] [dim]{c.claim_type}:[/dim] {c.statement}")
    
    # B) Show belief trajectory
    history = reveal.get("history", [])
    if history:
        console.print()
        console.print("[bold]Belief Trajectory:[/bold]")
        for i, snap in enumerate(history):
            label = "Initial" if snap.trigger == "initial" else f"After Q{i}"
            console.print(f"  [dim]{label}:[/dim]")
            console.print(f"    \"{snap.belief}\"")
            if snap.errors_at_time:
                for e in snap.errors_at_time[:2]:
                    sev_color = "red" if e.severity == 3 else "yellow" if e.severity == 2 else "dim"
                    console.print(f"    [{sev_color}]-> {e.type}: violates claim {e.claim_index+1}[/{sev_color}]")
    elif reveal.get("belief"):
        console.print()
        console.print("[dim]Final belief:[/dim]")
        console.print(f"  \"{reveal['belief']}\"")
    
    # C) Show final errors with claim references
    errors = reveal.get("errors", [])
    if errors:
        console.print()
        console.print("[red]Errors:[/red]")
        for e in errors:
            sev = {1: "minor", 2: "significant", 3: "critical"}.get(e.severity, "")
            console.print(f"  [red]Error:[/red] {e.type} [dim]({sev})[/dim]")
            console.print(f"  [red]Violates:[/red] Claim {e.claim_index+1} - \"{e.violated_claim}\"")
            console.print(f"  [red]Because:[/red] {e.description}")
            console.print()
    else:
        console.print()
        console.print("[green]All claims satisfied.[/green]")
    
    # YouTube timestamp help
    if errors and due:
        _show_source_help(due, reveal["ground_truth"])
    
    # Score bar
    max_sev = max((e.severity for e in errors), default=0) if errors else 0
    console.print()
    bars = {0: ("[green]█████[/green]", "Solid"), 1: ("[green]████░[/green]", "Minor gaps"),
            2: ("[yellow]███░░[/yellow]", "Significant gaps"), 3: ("[red]█░░░░[/red]", "Critical errors")}
    bar, label = bars.get(max_sev, bars[3])
    console.print(f"{bar} [bold]{label}[/bold]")


def _show_source_help(due: dict, source_quote: str):
    """Show timestamp link and visual content for failed concepts (YouTube only)."""
    source = storage.get_source(due["source_id"])
    if not source or source["source_type"] != "youtube":
        return
    
    # Get segments
    segments = None
    if source.get("segments"):
        import json
        try:
            segments = json.loads(source["segments"])
        except:
            pass
    
    if not segments:
        return
    
    # Find timestamp for this concept
    from .tools.youtube import find_timestamp_for_text, get_video_link_at_time, extract_frame_at_timestamp
    
    timestamp = find_timestamp_for_text(segments, source_quote)
    if timestamp is None:
        return
    
    # Format timestamp as MM:SS
    mins = int(timestamp) // 60
    secs = int(timestamp) % 60
    time_str = f"{mins}:{secs:02d}"
    
    # Show link to video at timestamp
    link = get_video_link_at_time(source["url"], timestamp)
    console.print()
    console.print(f"[dim]Review at[/dim] [yellow]{time_str}[/yellow][dim]:[/dim] [cyan]{link}[/cyan]")
    
    # Try to extract visual content at that timestamp
    with _spinner("Extracting visual content..."):
        visual = extract_frame_at_timestamp(source["url"], timestamp)
    
    if visual:
        console.print()
        console.print("[dim]What was shown on screen:[/dim]")
        visual_short = visual[:300] + "..." if len(visual) > 300 else visual
        console.print(f"  [white]{visual_short}[/white]")




def _show_evaluation_result(result: dict):
    """Display evaluation result with visual score bar."""
    score = result["score"]
    
    # Visual score bar (█ filled, ░ empty)
    stars = "█" * score + "░" * (5 - score)
    
    # Score display with color and label
    labels = {1: "Needs Work", 2: "Getting There", 3: "Good", 4: "Great", 5: "Perfect"}
    label = labels.get(score, "")
    
    if score >= 4:
        console.print(f"[green]{stars}[/green] [bold green]{label}[/bold green]")
    elif score >= 3:
        console.print(f"[yellow]{stars}[/yellow] [bold yellow]{label}[/bold yellow]")
    else:
        console.print(f"[red]{stars}[/red] [bold red]{label}[/bold red]")
    
    # Feedback
    if result["feedback"]:
        console.print(f"[dim]{result['feedback']}[/dim]")
    
    # Covered/Missed as bullet points
    if result["covered"]:
        console.print("[green]You got:[/green]")
        for item in result["covered"][:3]:
            console.print(f"  [green]•[/green] {item}")
    
    if result["missed"]:
        console.print("[red]You missed:[/red]")
        for item in result["missed"][:3]:
            console.print(f"  [red]•[/red] {item}")


def cmd_stats() -> bool:
    """Show statistics."""
    stats = storage.get_stats()
    summary = scheduler.get_study_summary()
    
    if stats["total_sources"] == 0:
        console.print("[dim]No data yet. Start by adding content:[/dim]")
        console.print("  [cyan]/add[/cyan] <url>")
        return True
    
    table = Table(box=box.ROUNDED, show_header=False, border_style="cyan")
    table.add_column("", style="dim", width=15)
    table.add_column("", style="bold")
    
    table.add_row("Sources", str(stats["total_sources"]))
    table.add_row("Concepts", str(stats["total_concepts"]))
    table.add_row("Due now", f"[cyan]{summary['due_now']}[/cyan]" if summary["due_now"] > 0 else "[dim]0[/dim]")
    table.add_row("Reviews", str(stats["total_reviews"]))
    
    if stats["avg_score"] > 0:
        score_color = "green" if stats["avg_score"] >= 4 else "yellow" if stats["avg_score"] >= 3 else "red"
        table.add_row("Avg score", f"[{score_color}]{stats['avg_score']}/5[/{score_color}]")
    
    table.add_row("Mastered", f"[green]{summary['mastered']}[/green]" if summary["mastered"] > 0 else "[dim]0[/dim]")
    
    if stats["skipped_concepts"] > 0:
        table.add_row("Skipped", f"[dim]{stats['skipped_concepts']}[/dim]")
    
    console.print(Panel(table, title="[bold]Your Progress[/bold]", border_style="cyan"))
    return True


def cmd_list(args: str = "") -> bool:
    """List sources and concepts."""
    if args.strip() in ("-s", "--sources", "sources"):
        sources = storage.get_all_sources()
        if not sources:
            console.print("[dim]No sources yet.[/dim]")
            return True
        
        for s in sources:
            concepts = storage.get_concepts_for_source(s["id"])
            console.print(f"[bold]{s['title']}[/bold] [dim]({len(concepts)} concepts)[/dim]")
            console.print(f"  [dim]{s['url']}[/dim]")
        return True
    
    concepts = storage.get_all_concepts()
    if not concepts:
        console.print("[dim]No concepts yet. Add some content:[/dim]")
        console.print("  [cyan]/add[/cyan] <url>")
        return True
    
    # Group by source
    by_source = {}
    for c in concepts:
        src = c["source_title"]
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(c)
    
    for src_title, src_concepts in by_source.items():
        console.print(f"\n[bold]{src_title}[/bold]")
        for c in src_concepts:
            progress = storage.get_progress(c["id"])
            if progress and progress["review_count"] > 0:
                score = progress.get("last_score")
                score_str = f"[dim]({progress['review_count']}x"
                if score:
                    score_str += f", last: {score}/5"
                score_str += ")[/dim]"
                console.print(f"  • {c['name']} {score_str}")
            else:
                console.print(f"  • {c['name']} [dim](new)[/dim]")
    
    return True


def cmd_due() -> bool:
    """Show due concepts."""
    due = scheduler.get_all_due()
    
    if not due:
        console.print("[green]OK[/green] Nothing due! All caught up.")
        return True
    
    console.print(f"[bold]{len(due)} concepts due for review:[/bold]")
    console.print()
    
    for d in due:
        console.print(f"  • {d['name']}")
        console.print(f"    [dim]{d['source_title']}[/dim]")
    
    console.print()
    console.print("[dim]Run /study to start reviewing[/dim]")
    return True


def cmd_skip(name: str) -> bool:
    """Skip a concept."""
    name = name.strip()
    if not name:
        console.print("[yellow]Usage: /skip <concept-name>[/yellow]")
        return True
    
    concepts = storage.get_all_concepts()
    matches = [c for c in concepts if name.lower() in c["name"].lower()]
    
    if not matches:
        console.print(f"[red]No concept matching '{name}'[/red]")
        return True
    
    if len(matches) > 1:
        console.print("[yellow]Multiple matches:[/yellow]")
        for m in matches:
            console.print(f"  • {m['name']}")
        console.print("[dim]Be more specific.[/dim]")
        return True
    
    storage.skip_concept(matches[0]["id"])
    console.print(f"[green]OK[/green] Skipped: {matches[0]['name']}")
    return True


def cmd_unskip(name: str) -> bool:
    """Unskip a concept."""
    name = name.strip()
    if not name:
        # Show all skipped
        with storage.get_db() as conn:
            rows = conn.execute("""
                SELECT c.*, s.title as source_title
                FROM concepts c JOIN sources s ON c.source_id = s.id
                WHERE c.skipped = 1
            """).fetchall()
            skipped = [dict(r) for r in rows]
        
        if not skipped:
            console.print("[dim]No skipped concepts.[/dim]")
            return True
        
        console.print("[bold]Skipped concepts:[/bold]")
        for s in skipped:
            console.print(f"  • {s['name']}")
        console.print()
        console.print("[dim]Usage: /unskip <name>[/dim]")
        return True
    
    with storage.get_db() as conn:
        rows = conn.execute("""
            SELECT c.*, s.title as source_title
            FROM concepts c JOIN sources s ON c.source_id = s.id
            WHERE c.skipped = 1
        """).fetchall()
        skipped = [dict(r) for r in rows]
    
    matches = [c for c in skipped if name.lower() in c["name"].lower()]
    
    if not matches:
        console.print(f"[red]No skipped concept matching '{name}'[/red]")
        return True
    
    if len(matches) > 1:
        console.print("[yellow]Multiple matches:[/yellow]")
        for m in matches:
            console.print(f"  • {m['name']}")
        return True
    
    storage.unskip_concept(matches[0]["id"])
    console.print(f"[green]OK[/green] Restored: {matches[0]['name']}")
    return True


def cmd_config() -> bool:
    """Show configuration."""
    console.print("[bold]Configuration:[/bold]")
    console.print()
    console.print(f"  Data directory: [cyan]{config.DATA_DIR}[/cyan]")
    console.print(f"  Database: [cyan]{config.DB_PATH}[/cyan]")
    console.print()
    console.print(f"  Groq model: [dim]{config.GROQ_MODEL}[/dim]")
    console.print(f"  Gemini model: [dim]{config.GEMINI_MODEL}[/dim]")
    console.print()
    console.print("  GROQ_API_KEY: [green]set[/green]" if os.environ.get("GROQ_API_KEY") else "  GROQ_API_KEY: [red]not set[/red]")
    console.print("  GEMINI_API_KEY: [green]set[/green]" if os.environ.get("GEMINI_API_KEY") else "  GEMINI_API_KEY: [dim]not set (optional)[/dim]")
    return True


def cmd_help() -> bool:
    """Show help."""
    console.print(HELP_TEXT)
    return True


def cmd_clear() -> bool:
    """Clear screen."""
    console.clear()
    _print_banner()
    return True


# ============ COMMAND ROUTER ============

COMMANDS: dict[str, Callable] = {
    "add": lambda args: cmd_add(args),
    "study": lambda args: cmd_study(),
    "stats": lambda args: cmd_stats(),
    "list": lambda args: cmd_list(args),
    "ls": lambda args: cmd_list(args),
    "due": lambda args: cmd_due(),
    "skip": lambda args: cmd_skip(args),
    "unskip": lambda args: cmd_unskip(args),
    "config": lambda args: cmd_config(),
    "help": lambda args: cmd_help(),
    "h": lambda args: cmd_help(),
    "?": lambda args: cmd_help(),
    "clear": lambda args: cmd_clear(),
    "cls": lambda args: cmd_clear(),
    "quit": lambda args: False,
    "exit": lambda args: False,
    "q": lambda args: False,
}


def handle_input(user_input: str) -> bool:
    """Handle user input. Returns False to exit."""
    user_input = user_input.strip()
    
    if not user_input:
        # Empty input = start study
        return cmd_study()
    
    # Slash command
    if user_input.startswith("/"):
        parts = user_input[1:].split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in COMMANDS:
            result = COMMANDS[cmd](args)
            return result if result is not None else True
        else:
            console.print(f"[red]Unknown command: /{cmd}[/red]")
            console.print("[dim]Type /help for available commands[/dim]")
            return True
    
    # URL or local file detection
    if _is_url(user_input) or _is_local_file(user_input):
        return cmd_add(user_input)
    
    # Unknown input
    console.print("[dim]Unknown input. Type /help for commands.[/dim]")
    return True


# ============ MAIN LOOP ============

def interactive_mode():
    """Run interactive REPL."""
    console.clear()
    _print_banner()
    console.print()
    _print_status()
    console.print()
    console.print("[dim]Type /help for commands, or paste a URL to add content[/dim]")
    console.print("[dim]Press Enter to start studying[/dim]")
    console.print()
    
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]learnlock[/bold cyan]", console=console)
            console.print()
            
            if not handle_input(user_input):
                console.print("[dim]Goodbye![/dim]")
                break
                
            console.print()
        except (EOFError, KeyboardInterrupt):
            console.print()
            console.print("[dim]Goodbye![/dim]")
            break


# ============ CLI ENTRY POINTS ============

@app.command()
def cli(
    prompt: Optional[str] = typer.Argument(None, help="Command or URL to process"),
    print_mode: bool = typer.Option(False, "-p", "--print", help="Print output and exit (non-interactive)"),
    gentle: bool = typer.Option(False, "-g", "--gentle", help="Gentle UI mode (less aggressive feedback)"),
    version: bool = typer.Option(False, "-v", "--version", help="Show version"),
):
    """
    learn-lock - Stop consuming. Start retaining.
    
    Run without arguments for interactive mode.
    """
    if version:
        console.print(f"learnlock {VERSION}")
        return
    
    # Ensure data directory
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check API keys
    if not _check_api_keys():
        raise typer.Exit(1)
    
    # Set gentle mode
    if gentle:
        from .hud import set_gentle_mode
        set_gentle_mode(True)
    
    if print_mode and prompt:
        # Non-interactive mode
        handle_input(prompt)
    elif prompt:
        # Single command then interactive
        console.clear()
        _print_banner()
        console.print()
        handle_input(prompt)
        console.print()
        interactive_mode()
    else:
        # Interactive mode
        interactive_mode()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
