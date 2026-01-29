"""Tests for ProgressListener protocol and implementations."""

from __future__ import annotations

from unittest.mock import Mock, patch

from cat.experiments.runner.progress import NullProgressListener, ProgressListener


class TestNullProgressListener:
    """Test NullProgressListener no-op implementation."""

    def test_on_task_completed_is_noop(self):
        """Method does nothing, doesn't raise."""
        listener = NullProgressListener()
        listener.on_task_completed(0, 10, Mock())  # Should not raise

    def test_on_evaluation_completed_is_noop(self):
        """Method does nothing, doesn't raise."""
        listener = NullProgressListener()
        listener.on_evaluation_completed("eval", 0, 10)  # Should not raise

    def test_on_experiment_completed_is_noop(self):
        """Method does nothing, doesn't raise."""
        listener = NullProgressListener()
        listener.on_experiment_completed(Mock())  # Should not raise

    def test_implements_protocol(self):
        """NullProgressListener satisfies ProgressListener protocol."""
        listener = NullProgressListener()
        assert isinstance(listener, ProgressListener)


class TestTqdmProgressListener:
    """Test TqdmProgressListener adapter."""

    @patch("cat.experiments.runner.cli.progress.tqdm")
    def test_on_task_completed_updates_progress(self, mock_tqdm):
        """Progress bar updates on each task completion."""
        from cat.experiments.runner.cli.progress import TqdmProgressListener

        mock_bar = Mock()
        mock_tqdm.return_value = mock_bar

        listener = TqdmProgressListener()
        listener.on_task_completed(0, 10, Mock())

        mock_bar.update.assert_called_once_with(1)

    @patch("cat.experiments.runner.cli.progress.tqdm")
    def test_on_evaluation_completed_updates_progress(self, mock_tqdm):
        """Progress bar updates on each evaluation completion."""
        from cat.experiments.runner.cli.progress import TqdmProgressListener

        mock_bar = Mock()
        mock_tqdm.return_value = mock_bar

        listener = TqdmProgressListener()
        listener.on_evaluation_completed("accuracy", 0, 10)

        mock_bar.update.assert_called_once_with(1)

    @patch("cat.experiments.runner.cli.progress.tqdm")
    def test_on_experiment_completed_closes_bars(self, mock_tqdm):
        """Progress bars close when experiment completes."""
        from cat.experiments.runner.cli.progress import TqdmProgressListener

        mock_bar = Mock()
        mock_tqdm.return_value = mock_bar

        listener = TqdmProgressListener()
        listener.on_task_completed(0, 1, Mock())  # Create bar
        listener.on_experiment_completed(Mock())

        mock_bar.close.assert_called()

    def test_implements_protocol(self):
        """TqdmProgressListener satisfies ProgressListener protocol."""
        from cat.experiments.runner.cli.progress import TqdmProgressListener

        listener = TqdmProgressListener()
        assert isinstance(listener, ProgressListener)
