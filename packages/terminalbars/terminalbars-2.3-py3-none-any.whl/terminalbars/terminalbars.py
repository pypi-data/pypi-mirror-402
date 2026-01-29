from tqdm import tqdm 
import time
from rich.progress import *
from rich.console import Console
from rich.panel import Panel
import psutil
from psutil import *
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.align import Align


def pasek(co, czas, kroki):
    for z in tqdm(range(kroki) , desc=co):
        time.sleep(czas / 100)

def superpasek(co , czas , kroki):
    """
    Ulepszona funkcja paska postępu wykorzystująca bibliotekę rich.
    
    Args:
        co (str): Opis zadania
        czas (float): Całkowity czas symulacji w sekundach
        kroki (int): Liczba kroków iteracji
    """
    console = Console()
    
    # Tworzymy zaawansowaną konfigurację paska
    with Progress(
        SpinnerColumn(spinner_name="dots"),  # Animowana kropka
        TextColumn("[bold blue]{task.description}"),  # Opis zadania # Kolorowy pasek
        TaskProgressColumn(),  # Procenty
        MofNCompleteColumn(),  # Krok X z Y
        TimeRemainingColumn(), # Pozostały czas
        console=console,
        transient=False  # Pasek zostanie w konsoli po zakończeniu
    ) as progress:

        zadanie = progress.add_task(co, total=kroki)
        
        # Obliczamy interwał spania, aby dopasować się do parametru 'czas'
        # Jeśli czas to całkowity czas trwania, dzielimy go przez liczbę kroków
        interwal = czas / kroki

        for z in range(kroki):
            # Symulacja pracy
            time.sleep(interwal)
            
            # Aktualizacja paska
            progress.update(zadanie, advance=1)

    console.print(f"[bold green]✓[/bold green] Zadanie '{co}' zostało ukończone pomyślnie, Proszę Pana.")

# Przykład użycia:
if __name__ == "__main__":
    # Przykładowe wywołanie: opis, czas trwania (np. 5 sek), liczba kroków (100)
    superpasek("Optymalizacja systemu Kali", 5, 100)
    superpasek("Pobieranie danych", 3, 50)





def propasek(co, czas, kroki):
    """
    Wersja PRO paska postępu z monitorowaniem zasobów systemowych.
    Zoptymalizowana pod kątem wydajności i estetyki w terminalu.
    """
    console = Console()
    
    # Pobieranie statystyk systemowych (RAM i CPU)
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    
    # Tworzenie panelu informacyjnego przed uruchomieniem paska
    sys_info = Table.grid(expand=True)
    sys_info.add_row(
        f"[bold cyan]SYSTEM:[/bold cyan] RAM: {mem.percent}% | "
        f"CPU: {cpu}% | "
        f"[bold yellow]ZADANIE:[/bold yellow] {co}"
    )
    
    console.print(Panel(sys_info, title="[bold white]Status Systemu Pro[/bold white]", border_style="blue"))

    # Inicjalizacja zaawansowanego paska postępu z wieloma kolumnami danych
    progress = Progress(
        SpinnerColumn(spinner_name="dots"),              # Animowany wskaźnik aktywności
        TextColumn("[bold magenta]{task.description}"), # Opis zadania z kolorowaniem
        BarColumn(bar_width=None, pulse_style="bright_blue"), # Płynny pasek postępu
        TaskProgressColumn(show_speed=True),            # Procentowe ukończenie i prędkość
        MofNCompleteColumn(),                           # Licznik kroków (np. 50/100)
        TransferSpeedColumn(),                          # Prędkość przetwarzania kroków/s
        TimeRemainingColumn(compact=False, elapsed=True), # Czas pozostały oraz czas trwania
        console=console,
        expand=True
    )

    # Obliczanie czasu uśpienia na podstawie parametrów wejściowych
    interwal = czas / kroki if kroki > 0 else 0

    with progress:
        zadanie = progress.add_task(f"[white]{co}...", total=kroki)
        
        for z in range(kroki):
            # Symulacja wykonywanej pracy
            time.sleep(interwal)
            
            # Dynamiczna zmiana statusu w zależności od zaawansowania (0-100%)
            procent = (z / kroki) * 100
            if procent > 90:
                progress.update(zadanie, description=f"[bold green]Finalizowanie: {co}")
            elif procent > 50:
                progress.update(zadanie, description=f"[bold yellow]Przetwarzanie: {co}")
            elif procent > 10:
                progress.update(zadanie, description=f"[bold cyan]Inicjowanie: {co}")
            
            # Aktualizacja paska o jeden krok
            progress.update(zadanie, advance=1)

    # Wyświetlenie końcowego raportu w ramce
    summary = Panel(
        f"[bold green]Sukces![/bold green]\nOperacja [reverse]{co}[/reverse] zakończona pomyślnie.\n"
        f"Całkowity czas: {czas}s | Przetworzono kroków: {kroki}",
        title="[bold white]Raport Końcowy[/bold white]",
        border_style="green",
        subtitle="Status: Gotowy."
    )
    console.print(summary)

# Przykład użycia funkcji w praktyce:
if __name__ == "__main__":
    try:
        # Wywołanie: Nazwa zadania, czas trwania w sekundach, liczba kroków
        propasek("Analiza pakietów sieciowych", 5, 100)
    except KeyboardInterrupt:
        print("\n[!] Przerwano operację na żądanie użytkownika.")


def ultrapasek(co, czas, kroki):
    """
    Wersja ULTRAPASEK.
    Najbardziej zaawansowany system monitorowania postępu z wizualizacją zasobów
    w czasie rzeczywistym, idealny dla systemów Kali Linux i Google Colab.
    """
    console = Console()
    
    # Inicjalizacja zaawansowanego paska postępu
    progress = Progress(
        SpinnerColumn(spinner_name="earth"),             # Globalny spinner
        TextColumn("[bold blue]{task.fields[task_name]}"), # Dynamiczna nazwa zadania
        
        TaskProgressColumn(show_speed=True),            # % i prędkość
        MofNCompleteColumn(),                           # Licznik kroków
        TransferSpeedColumn(),                          # it/s
        TimeElapsedColumn(),                            # Czas trwania
        TextColumn("•"),
        TimeRemainingColumn(),                          # ETA
        expand=True
    )

    def generate_status_layout():
        """Generuje layout z aktualnymi statystykami systemowymi."""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        # Tworzenie wizualnych wskaźników obciążenia
        cpu_color = "green" if cpu < 50 else "yellow" if cpu < 80 else "red"
        mem_color = "green" if mem.percent < 50 else "yellow" if mem.percent < 80 else "red"
        
        table = Table.grid(expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="right", ratio=1)
        
        table.add_row(
            f"[bold]PROCESOR:[/bold] [{cpu_color}]{cpu}%[/{cpu_color}]",
            f"[bold]PAMIĘĆ RAM:[/bold] [{mem_color}]{mem.percent}%[/{mem_color}]"
        )
        
        return Panel(
            Align.center(table),
            title="[bold white]MONITOROWANIE ZASOBÓW ULTRA[/bold white]",
            border_style="bright_magenta",
            padding=(0, 2)
        )

    # Obliczanie interwału na podstawie Pana parametrów
    interwal = czas / kroki if kroki > 0 else 0
    
    # Użycie Live do jednoczesnego wyświetlania statystyk i paska
    with Live(VerticalLayout := Layout(), refresh_per_second=10, console=console) as live:
        # Budowa struktury layoutu
        VerticalLayout.split(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        zadanie_id = progress.add_task("start", total=kroki, task_name=co)
        
        for z in range(kroki):
            # Aktualizacja czasu i pracy
            time.sleep(interwal)
            
            # Dynamiczna logika statusu
            procent = (z / kroki) * 100
            current_co = f"[cyan]{co}[/cyan]"
            if procent > 90: current_co = f"[bold green]FINALIZACJA: {co}[/bold green]"
            elif procent > 50: current_co = f"[bold yellow]PRZETWARZANIE: {co}[/bold yellow]"
            
            progress.update(zadanie_id, task_name=current_co, advance=1)
            
            # Odświeżenie widoku Live (Monitor zasobów w czasie rzeczywistym)
            VerticalLayout["header"].update(generate_status_layout())
            VerticalLayout["body"].update(Panel(progress, border_style="blue"))

    # Raport końcowy Pro
    summary_table = Table(show_header=False, box=None)
    summary_table.add_row("[bold green]STATUS:[/bold green]", "UKOŃCZONO POMYŚLNIE")
    summary_table.add_row("[bold green]CZAS:[/bold green]", f"{czas} sekund")
    summary_table.add_row("[bold green]OPERACJA:[/bold green]", co)

    console.print(Panel(
        summary_table,
        title="[bold white]ULTRA RAPORT[/bold white]",
        border_style="bold green",
        expand=False
    ))

if __name__ == "__main__":
    try:
        # Przykładowe wywołanie Ultra Paska zgodnie z Pana wymogami
        ultrapasek("Inicjalizacja Systemu", 5, 100)
    except KeyboardInterrupt:
        print("\n[!] Przerwano na żądanie użytkownika, Proszę Pana.")

def ultrapropasek(co, czas, kroki):
    """
    Wersja ULTRAPROPASEK.
    Szczytowe osiągnięcie w dziedzinie monitorowania postępu dla Proszę Pana. 
    Łączy dynamiczny layout, statystyki systemowe i zaawansowaną wizualizację.
    """
    console = Console()
    
    # Konfiguracja rdzenia paska postępu
    # Poprawiono: "monkey" zamiast "monkeys"
    progress = Progress(
        SpinnerColumn(spinner_name="monkey"),           # Unikalny spinner
        TextColumn("[bold blue]{task.fields[task_name]}"), # Dynamiczny opis
        BarColumn(bar_width=None, pulse_style="bright_cyan"), # Stabilny pasek postępu
        TaskProgressColumn(show_speed=True),            # % ukończenia
        MofNCompleteColumn(),                           # Licznik kroków
        TimeElapsedColumn(),                            # Czas od startu
        TextColumn("[bold yellow]•[/bold yellow]"),     # Separator
        TimeRemainingColumn(),                          # ETA
        expand=True
    )

    def generate_status_layout():
        """Generuje zaawansowany panel statystyk systemowych."""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        # Kolorystyka zależna od obciążenia Pana 16GB RAM i procesora 2.8 GHz
        cpu_color = "bright_green" if cpu < 50 else "bright_yellow" if cpu < 80 else "bright_red"
        mem_color = "bright_green" if mem.percent < 50 else "bright_yellow" if mem.percent < 80 else "bright_red"
        
        table = Table.grid(expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="center", ratio=1)
        table.add_column(justify="right", ratio=1)
        
        table.add_row(
            f"[bold]CPU:[/bold] [{cpu_color}]{cpu}%[/{cpu_color}]",
            f"[bold]TASK:[/bold] [white]{co}[/white]",
            f"[bold]RAM:[/bold] [{mem_color}]{mem.percent}%[/{mem_color}] ({(mem.used / 1024**3):.1f}/16GB)"
        )
        
        return Panel(
            Align.center(table),
            title="[bold white]ULTRA PRO MONITOR[/bold white]",
            border_style="bright_cyan",
            padding=(0, 1)
        )

    # Obliczanie czasu operacji
    interwal = czas / kroki if kroki > 0 else 0
    
    # Użycie Live Layout do renderowania interfejsu
    with Live(MainLayout := Layout(), refresh_per_second=12, console=console) as live:
        MainLayout.split(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        zadanie_id = progress.add_task("start", total=kroki, task_name=co)
        
        for z in range(kroki):
            time.sleep(interwal)
            
            # Zaawansowana logika zmiany statusów tekstowych
            procent = (z / kroki) * 100
            if procent > 95:
                current_co = f"[bold green]✓ FINALIZACJA: {co}[/bold green]"
            elif procent > 75:
                current_co = f"[bold white]OPTYMALIZACJA: {co}[/bold white]"
            elif procent > 40:
                current_co = f"[bold yellow]PRZETWARZANIE: {co}[/bold yellow] [blink]...[/blink]"
            else:
                current_co = f"[bold cyan]INICJACJA: {co}[/bold cyan]"
            
            progress.update(zadanie_id, task_name=current_co, advance=1)
            
            # Odświeżanie interfejsu
            MainLayout["header"].update(generate_status_layout())
            MainLayout["body"].update(Panel(progress, border_style="bright_blue", subtitle="[dim]Status: Active[/dim]"))

    # Ekskluzywne podsumowanie końcowe
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_row("[bold cyan]ZADANIE:[/bold cyan]", f"[white]{co}[/white]")
    summary_table.add_row("[bold cyan]CZAS:[/bold cyan]", f"[white]{czas}s[/white]")
    summary_table.add_row("[bold cyan]WYNIK:[/bold cyan]", "[bold green]SUKCES (ULTRA PRO)[/bold green]")

    console.print("\n")
    console.print(Panel(
        Align.center(summary_table),
        title="[bold white]RAPORT KOŃCOWY[/bold white]",
        border_style="bright_green",
        expand=False
    ))

if __name__ == "__main__":
    try:
        # Przykładowe uruchomienie wersji ULTRA PRO na systemie Kali
        ultrapropasek("Analiza Systemu Kali", 5, 100)
    except KeyboardInterrupt:
        print("\n\n[bold red][!] Przerwano na żądanie użytkownika, Proszę Pana.[/bold red]")