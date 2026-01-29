"""Tests for hook loader and coercion."""

from unittest.mock import MagicMock, patch

import pytest

from hooks.interfaces import CursorHooks
from hooks.loader import _coerce_to_hooks, load_hooks


class TestCursorHooksSubclass(CursorHooks):
    """A test hooks implementation."""


class TestCoerceToHooks:
    """Test _coerce_to_hooks handles different input types."""

    def test_accepts_cursor_hooks_instance(self) -> None:
        instance = TestCursorHooksSubclass()
        result = _coerce_to_hooks(instance)
        assert result is instance

    def test_accepts_cursor_hooks_subclass(self) -> None:
        result = _coerce_to_hooks(TestCursorHooksSubclass)
        assert isinstance(result, TestCursorHooksSubclass)

    def test_rejects_non_cursor_hooks(self) -> None:
        with pytest.raises(TypeError, match="CursorHooks instance"):
            _coerce_to_hooks("not a hooks object")


class TestLoadHooks:
    """Test load_hooks entry point resolution."""

    def test_raises_when_no_implementation_found(self) -> None:
        """Error when no entry point is registered."""
        with patch("hooks.loader.entry_points") as mock_ep:
            mock_ep.return_value.select.return_value = []
            with pytest.raises(RuntimeError, match="No hook implementation found"):
                load_hooks()

    def test_raises_when_multiple_entry_points(self) -> None:
        """Error when multiple entry points exist."""
        with patch("hooks.loader.entry_points") as mock_ep:
            mock_ep.return_value.select.return_value = [MagicMock(), MagicMock()]
            with pytest.raises(RuntimeError, match="Multiple hook implementations"):
                load_hooks()

    def test_uses_single_entry_point(self) -> None:
        """Single entry point is used automatically."""
        with patch("hooks.loader.entry_points") as mock_ep:
            mock_entry = MagicMock()
            mock_entry.load.return_value = TestCursorHooksSubclass()
            mock_ep.return_value.select.return_value = [mock_entry]

            result = load_hooks()
            assert isinstance(result, CursorHooks)
            mock_entry.load.assert_called_once()
