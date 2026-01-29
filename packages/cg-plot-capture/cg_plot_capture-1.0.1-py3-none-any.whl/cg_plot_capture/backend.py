"""
CodeGrade Plot Capture - Matplotlib backend for capturing plots.
For use with Matplotlib >= 3.6

**Thread Safety**: This backend is NOT thread-safe. Multiple threads calling
plt.show() or show() simultaneously may produce corrupted output or duplicate
filenames. This matches matplotlib's own threading limitations in which figures
should only be created and shown from the main thread. Multiprocessing, on the
other hand, IS safe.

Modes (via environment variable CG_PLOT_MODE):
  - display (default): Send plots to FD3 as SVG for display in UI
  - save: Save plots to disk in specified format
  - both: Display AND save

Configuration via environment variables:
  - CG_PLOT_MODE: 'display', 'save', or 'both' (default: 'display')
  - CG_PLOT_FILENAME: Template for filenames (default: 'plot_{i}.png')
    Placeholders:
      {i}: Counter (required)
    Examples:
      'plot_{i}.png'
      'figure_{i:03d}.svg'

    Format is auto-detected from extension.
    Parent directories are created automatically.

    WARNING: The {i} counter resets for each script block execution. When
    running multiple scripts with 'save' or 'both' mode, files may be
    overwritten unless you use different paths or filenames per script. Consider
    organizing plots into separate directories per script by updating the
    `CG_PLOT_FILENAME` in each script.

Display always uses SVG for optimal web rendering.
"""

import base64
import json
import logging
import os
import sys
from functools import cache
from io import BytesIO
from pathlib import Path
from typing import Iterator, Optional, TextIO, Type

from matplotlib.backend_bases import FigureManagerBase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

log = logging.getLogger(__name__)


@cache
def _get_plot_mode() -> str:
    """Gets the cached plot mode, reading from env on first call."""
    return os.environ.get('CG_PLOT_MODE', 'display').lower()


@cache
def _get_filename_template() -> str:
    """Gets the cached filename template, reading from env on first call."""
    template = os.environ.get('CG_PLOT_FILENAME', 'plot_{i}.png')
    _validate_filename_template(template)
    return template


def _reset_config() -> None:
    """Reset cached configuration. Call this in tests after modifying env vars."""
    _get_plot_mode.cache_clear()
    _get_filename_template.cache_clear()


def _validate_filename_template(template: str) -> None:
    """Validate that the filename template includes {i} placeholder."""
    try:
        test1 = template.format(i=1)
        test2 = template.format(i=2)
    except KeyError as e:
        msg = (
            f'ERROR: CG_PLOT_FILENAME contains unknown placeholder {e}.\n'
            f'Template: {template}\n'
            f'Only {{i}} is supported as a placeholder.'
        )
        print(msg, file=sys.stderr)
        sys.exit(1)

    if '{i' not in template:
        warning = (
            f'WARNING: CG_PLOT_FILENAME does not include {{i}} placeholder.\n'
            f'Template: {template}\n'
            f'If your script generates multiple plots, they will overwrite each other.\n'
            f'This is OK for single-plot scripts, but consider adding {{i}} for safety.'
        )
        print(warning, file=sys.stderr)
        return

    if test1 == test2:
        warning = (
            f'WARNING: CG_PLOT_FILENAME template produces identical filenames.\n'
            f'Template: {template}\n'
            f'If your script generates multiple plots, they will overwrite each other.\n'
            f'This is OK for single-plot scripts, but consider adding {{i}} for safety.'
        )
        print(warning, file=sys.stderr)


def _create_filename_generator() -> Iterator[str]:
    """
    Generator that yields sequential filenames.

    Format: Controlled by CG_PLOT_FILENAME template
    Default: plot_{i}.png
    Example: something_plot_1.png
    """
    counter = 0

    while True:
        counter += 1
        filename = _get_filename_template().format(i=counter)
        log.debug(f'Generated filename: {filename}')
        yield filename


def _open_fd3() -> Optional[TextIO]:
    """
    Attempt to open file descriptor 3 for writing.
    """
    try:
        fd3 = os.fdopen(3, 'w', closefd=False)
        log.debug('Successfully opened fd3 for writing')
        return fd3
    except OSError as e:
        log.warning('Cannot open fd3: %s', e)
        log.warning('Plots will not be sent to the AutoTest output')
        return None


def _send_file_message(fd3: TextIO, filename: str, data: bytes) -> None:
    """
    Send a file message to fd3 in JSON format.
    """

    encoded_data = base64.b64encode(data).decode('ascii')
    message = {
        'messageType': 'file',
        'filename': filename,
        'data': encoded_data,
        'size': len(data),
    }

    json.dump(message, fd3)
    fd3.write('\n')
    fd3.flush()

    log.info('Sent plot: %s (%d bytes)', filename, len(data))


def _render_figure_to_svg(fig: Figure) -> bytes:
    """
    Render a matplotlib figure to SVG bytes.
    Used for display via FD3.
    """
    buffer = BytesIO()
    fig.savefig(buffer, format='svg')
    buffer.seek(0)
    svg_data = buffer.read()
    log.debug(f'Rendered figure to SVG: {len(svg_data)} bytes')
    return svg_data


def _display(fd3: Optional[TextIO], fig: Figure, filename: str) -> None:
    """
    Send the image to be displayed.
    """
    if fd3 is None:
        log.error(f'Cannot open connection to render file {filename}')
        return None

    try:
        svg_data = _render_figure_to_svg(fig)
        svg_filename = Path(filename).with_suffix('.svg').name
        _send_file_message(fd3, svg_filename, svg_data)
    except Exception as e:
        log.error(f'Failed to display plot: {e}', exc_info=True)


def _save(fig: Figure, filename: str) -> None:
    """
    Save figure to the configured output folder.

    Args:
        fig: The matplotlib figure to save
        filename: Full filename/path like "something_plot_1.png" or "./output/plot_1.pdf"

    Matplotlib auto-detects format from the file extension.
    Creates parent directories if needed.
    """
    try:
        filepath = Path(filename)
        if filepath.exists():
            log.warning(
                f'Overwriting existing file: {filepath}. '
                f'Consider using unique filenames across scripts by changing the `CG_PLOT_FILENAME` environment variable for individual scripts.'
            )
        filepath.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(filepath)
        log.info(f'Saved plot to: {filepath}')
    except Exception as e:
        log.error(f'Failed to save plot: {e}', exc_info=True)


class CGPlotCaptureFigureManager(FigureManagerBase):
    """
    Figure manager for CodeGrade plot capture.
    Handles streaming plots to fd3.
    """

    _filename_gen: Optional[Iterator[str]] = None

    @classmethod
    def _get_next_filename(cls) -> str:
        if cls._filename_gen is None:
            cls._filename_gen = _create_filename_generator()
        return next(cls._filename_gen)

    @classmethod
    def _reset_filename_generator(cls) -> None:
        cls._filename_gen = None

    def show(self) -> None:
        """
        Called when individual figures are shown (plotnine uses this).
        """
        fig = self.canvas.figure
        filename = self._get_next_filename()
        fd3 = None

        if _get_plot_mode() in ('display', 'both'):
            fd3 = _open_fd3()
            _display(fd3, fig, filename)
        if _get_plot_mode() in ('save', 'both'):
            _save(fig, filename)

        if fd3 is not None:
            try:
                fd3.close()
                log.debug('Closed fd3 wrapper - underlying fd3 is still open')
            except Exception as e:
                log.error('Error closing fd3 wrapper: %s', e, exc_info=True)

    @classmethod
    def pyplot_show(cls, *, block: Optional[bool] = None) -> None:
        """
        Called by pyplot.show() to display all figures.
        Streams all active figures to fd3 instead of displaying.

        Args:
            block: Kept for API compatibility.
        """
        from matplotlib._pylab_helpers import Gcf

        managers: list[FigureManagerBase] = Gcf.get_all_fig_managers()

        if not managers:
            return

        fd3 = None
        if _get_plot_mode() in ('display', 'both'):
            fd3 = _open_fd3()

        for manager in managers:
            fig = manager.canvas.figure
            filename = cls._get_next_filename()

            if _get_plot_mode() in ('display', 'both'):
                _display(fd3, fig, filename)
            if _get_plot_mode() in ('save', 'both'):
                _save(fig, filename)

        if fd3 is not None:
            try:
                fd3.close()
                log.debug('Closed fd3 wrapper - underlying fd3 is still open')
            except Exception as e:
                log.error('Error closing fd3 wrapper: %s', e, exc_info=True)


class CGPlotCaptureFigureCanvas(FigureCanvasAgg):
    """
    Links to our custom manager class.
    """

    manager_class: Type[FigureManagerBase] = CGPlotCaptureFigureManager


# Export for matplotlib backend interface
FigureCanvas: Type[FigureCanvasAgg] = CGPlotCaptureFigureCanvas


def draw_if_interactive() -> None:
    """
    Noop for non-interactive backend.
    Required by matplotlib backend interface.
    """
    pass
