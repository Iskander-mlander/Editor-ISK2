"""
Splash Screen Module
====================
Provides a startup splash screen for the application.
"""

import os
from typing import Optional, List

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtWidgets import QSplashScreen, QLabel, QProgressBar, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QPen, QBrush


class SplashScreen(QSplashScreen):
    """
    Custom splash screen with progress indicator.
    """
    
    loading_progress = pyqtSignal(int, str)  # progress, message
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        # Splash settings
        self._width = 450
        self._height = 300
        
        # Create pixmap
        pixmap = QPixmap(self._width, self._height)
        self.setPixmap(pixmap)
        
        # Progress tracking
        self._current_progress = 0
        self._current_message = "Initializing..."
        self._steps: List[tuple] = []  # (progress, message)
        
        # Set flags
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        
        # Auto close settings
        self._auto_close = True
        self._close_on_complete = True
    
    def drawContents(self, painter: QPainter) -> None:
        """Draw splash screen contents."""
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        
        # Background gradient
        gradient = QLinearGradient(0, 0, 0, self._height)
        gradient.setColorAt(0, QColor(40, 42, 54))  # Dark blue-gray
        gradient.setColorAt(1, QColor(30, 32, 44))
        painter.fillRect(QRect(0, 0, self._width, self._height), gradient)
        
        # Draw border
        pen = QPen(QColor(98, 114, 164))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(1, 1, self._width - 2, self._height - 2)
        
        # Title
        title_font = QFont("Sans Serif", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(139, 233, 253))  # Cyan
        title_rect = QRect(0, 40, self._width, 40)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "Editor ISK")
        
        # Version
        version_font = QFont("Sans Serif", 10)
        painter.setFont(version_font)
        painter.setPen(QColor(139, 148, 151))  # Gray
        version_rect = QRect(0, 75, self._width, 20)
        painter.drawText(version_rect, Qt.AlignmentFlag.AlignCenter, "Version 2.0.0")
        
        # Divider line
        pen = QPen(QColor(98, 114, 164, 100))
        painter.setPen(pen)
        painter.drawLine(50, 95, self._width - 50, 95)
        
        # Progress bar background
        bar_x = 50
        bar_y = 130
        bar_width = self._width - 100
        bar_height = 20
        
        # Bar background
        painter.fillRect(bar_x, bar_y, bar_width, bar_height, QColor(50, 52, 64))
        
        # Bar fill
        if self._current_progress > 0:
            fill_width = int(bar_width * self._current_progress / 100)
            gradient = QLinearGradient(bar_x, 0, bar_x + fill_width, 0)
            gradient.setColorAt(0, QColor(80, 250, 123))  # Green
            gradient.setColorAt(1, QColor(139, 233, 253))  # Cyan
            painter.fillRect(bar_x, bar_y, fill_width, bar_height, gradient)
        
        # Bar border
        pen = QPen(QColor(98, 114, 164))
        painter.setPen(pen)
        painter.drawRect(bar_x, bar_y, bar_width, bar_height)
        
        # Status text
        status_font = QFont("Sans Serif", 10)
        painter.setFont(status_font)
        painter.setPen(QColor(248, 248, 242))  # White
        status_rect = QRect(0, 160, self._width, 20)
        painter.drawText(status_rect, Qt.AlignmentFlag.AlignCenter, self._current_message)
        
        # Progress text
        progress_font = QFont("Sans Serif", 9)
        painter.setFont(progress_font)
        painter.setPen(QColor(139, 148, 151))
        progress_rect = QRect(0, 185, self._width, 15)
        painter.drawText(progress_rect, Qt.AlignmentFlag.AlignCenter, f"{self._current_progress}%")
        
        # Loading steps indicator
        step_y = 220
        step_height = 15
        step_font = QFont("Sans Serif", 8)
        painter.setFont(step_font)
        
        for i, (progress, message) in enumerate(self._steps):
            y = step_y + i * step_height
            
            # Draw checkmark or dot
            color = QColor(80, 250, 123) if progress <= self._current_progress else QColor(98, 114, 164)
            painter.setPen(color)
            
            prefix = "✓ " if progress <= self._current_progress else "  "
            painter.drawText(QRect(50, y, self._width - 100, step_height), 
                          Qt.AlignmentFlag.AlignLeft, f"{prefix}{message}")
    
    def set_progress(self, progress: int, message: str = "") -> None:
        """Set current progress and message."""
        self._current_progress = min(100, max(0, progress))
        if message:
            self._current_message = message
        self.loading_progress.emit(self._current_progress, self._current_message)
        self.repaint()
    
    def add_step(self, progress: int, message: str) -> None:
        """Add a loading step."""
        self._steps.append((progress, message))
    
    def set_steps(self, steps: List[tuple]) -> None:
        """Set all loading steps."""
        self._steps = steps
    
    def complete(self) -> None:
        """Mark loading as complete."""
        self.set_progress(100, "Ready!")
        
        if self._close_on_complete:
            QTimer.singleShot(500, self.close)
    
    def set_auto_close(self, enabled: bool) -> None:
        """Enable or disable auto-close on complete."""
        self._close_on_complete = enabled


class SplashScreenManager:
    """
    Manages the splash screen display during application startup.
    """
    
    DEFAULT_STEPS = [
        (10, "Loading configuration..."),
        (20, "Initializing UI components..."),
        (40, "Loading themes and translations..."),
        (60, "Setting up editor core..."),
        (80, "Connecting features..."),
        (90, "Preparing workspace..."),
        (100, "Ready!"),
    ]
    
    def __init__(self) -> None:
        self._splash: Optional[SplashScreen] = None
        self._app = None
    
    def show_splash(self, app) -> Optional[SplashScreen]:
        """Show the splash screen."""
        self._app = app
        self._splash = SplashScreen()
        self._splash.show()
        app.processEvents()
        return self._splash
    
    def set_steps(self, steps: List[tuple]) -> None:
        """Set loading steps."""
        if self._splash:
            self._splash.set_steps(steps)
    
    def set_progress(self, progress: int, message: str = "") -> None:
        """Update progress."""
        if self._splash:
            self._splash.set_progress(progress, message)
            if self._app:
                self._app.processEvents()
    
    def finish(self) -> None:
        """Finish and close splash."""
        if self._splash:
            self._splash.complete()
            if self._app:
                self._app.processEvents()
            # Give time for user to see completion
            QTimer.singleShot(300, self._splash.close)
            self._splash = None


def create_splash_screen(app) -> tuple:
    """
    Create and show splash screen.
    
    Returns:
        tuple: (splash_screen, manager)
    """
    manager = SplashScreenManager()
    splash = manager.show_splash(app)
    splash.set_steps(SplashScreenManager.DEFAULT_STEPS)
    
    return splash, manager