"""
Progress Indicators for NetworkDoctor CLI
"""
from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

console = Console()


class ProgressManager:
    """Manages progress indicators for scans"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize progress manager.
        
        Args:
            verbose: Enable verbose progress output
        """
        self.verbose = verbose
        self.progress: Optional[Progress] = None
    
    def __enter__(self):
        """Context manager entry"""
        if self.verbose:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            )
            self.progress.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.progress:
            self.progress.stop()
    
    def add_task(self, description: str, total: int = 100) -> int:
        """
        Add a progress task.
        
        Args:
            description: Task description
            total: Total number of items
            
        Returns:
            Task ID
        """
        if self.progress:
            return self.progress.add_task(description, total=total)
        return 0
    
    def update(self, task_id: int, advance: int = 1, description: Optional[str] = None):
        """
        Update progress for a task.
        
        Args:
            task_id: Task ID
            advance: Amount to advance
            description: Optional new description
        """
        if self.progress:
            self.progress.update(task_id, advance=advance, description=description)
    
    def print(self, message: str, style: str = ""):
        """
        Print a message.
        
        Args:
            message: Message to print
            style: Rich style string
        """
        console.print(message, style=style)







