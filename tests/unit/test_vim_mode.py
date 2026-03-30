"""
Unit Tests for Vim Mode
========================
Tests for the Vim mode functionality.
"""

import unittest

from core.editor.vim_mode import VimMode, VimState, VimEngineSignals, VimEngine


class TestVimMode(unittest.TestCase):
    """Test VimMode enum."""
    
    def test_modes_defined(self):
        """Test all Vim modes are defined."""
        self.assertEqual(VimMode.NORMAL.name, "NORMAL")
        self.assertEqual(VimMode.INSERT.name, "INSERT")
        self.assertEqual(VimMode.VISUAL.name, "VISUAL")
        self.assertEqual(VimMode.COMMAND.name, "COMMAND")


class TestVimState(unittest.TestCase):
    """Test VimState class."""
    
    def test_initial_state(self):
        """Test initial state values."""
        state = VimState()
        
        self.assertEqual(state.mode, VimMode.NORMAL)
        self.assertEqual(state.register, "")
        self.assertEqual(state.count, 1)
        self.assertEqual(state.last_command, "")
        self.assertEqual(state.command_buffer, "")
        self.assertIsNone(state.visual_start)
    
    def test_state_modification(self):
        """Test modifying state values."""
        state = VimState()
        
        state.mode = VimMode.INSERT
        state.register = "a"
        state.count = 5
        state.last_command = "dd"
        
        self.assertEqual(state.mode, VimMode.INSERT)
        self.assertEqual(state.register, "a")
        self.assertEqual(state.count, 5)
        self.assertEqual(state.last_command, "dd")


class TestVimEngineSignals(unittest.TestCase):
    """Test VimEngineSignals."""
    
    def test_signals_defined(self):
        """Test all signals are defined."""
        signals = VimEngineSignals()
        
        self.assertTrue(hasattr(signals, 'mode_changed'))
        self.assertTrue(hasattr(signals, 'status_changed'))


class TestVimEngine(unittest.TestCase):
    """Test VimEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = VimEngine()
    
    def test_initial_state(self):
        """Test initial engine state."""
        self.assertFalse(self.engine.enabled)
        self.assertEqual(self.engine.mode, VimMode.NORMAL)
    
    def test_set_enabled(self):
        """Test enabling Vim mode."""
        self.engine.set_enabled(True)
        
        self.assertTrue(self.engine.enabled)
        self.assertEqual(self.engine.mode, VimMode.NORMAL)
    
    def test_set_enabled_false(self):
        """Test disabling Vim mode."""
        self.engine.set_enabled(True)
        self.engine.set_enabled(False)
        
        self.assertFalse(self.engine.enabled)
        self.assertEqual(self.engine.mode, VimMode.INSERT)
    
    def test_signals_exist(self):
        """Test signals property exists."""
        signals = self.engine.signals
        
        self.assertIsInstance(signals, VimEngineSignals)
        self.assertTrue(hasattr(signals, 'mode_changed'))
        self.assertTrue(hasattr(signals, 'status_changed'))
    
    def test_set_editor(self):
        """Test setting editor reference - skip in headless."""
        # Skip in headless mode - just verify the method exists
        self.assertTrue(hasattr(self.engine, 'set_editor'))
    
    def test_mode_change_emits_signal(self):
        """Test mode change emits signal."""
        from PyQt6.QtCore import QObject
        
        received_modes = []
        
        class Receiver(QObject):
            def receive_mode(self, mode):
                received_modes.append(mode)
        
        receiver = Receiver()
        self.engine.signals.mode_changed.connect(receiver.receive_mode)
        
        self.engine.set_enabled(True)
        
        self.assertIn("NORMAL", received_modes)


if __name__ == '__main__':
    unittest.main()