import logging

import rich_click as click
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from pymodbus.exceptions import ModbusIOException
from reactivex import Subject

from ..controller import BaseController, ContinuousMode
from .cli import main


@main.command()
@click.pass_context
def adjust(ctx: click.Context) -> None:
    """Adjust the motor position using the keyboard."""
    logger = logging.getLogger(__name__)

    device: BaseController = ctx.obj['device']
    key_pressed: Subject[ContinuousMode] = Subject()
    try:
        kb = KeyBindings()
        app = Application(key_bindings=kb, full_screen=False)

        @kb.add('right')
        def move_forward(event):
            """Move the motor forward."""
            key_pressed.on_next(ContinuousMode.FORWARD)

        @kb.add('left')
        def move_backward(event):
            """Move the motor backward."""
            key_pressed.on_next(ContinuousMode.BACKWARD)

        @kb.add('c-right')
        def crawl_forward(event):
            """Move the motor forward at crawl speed."""
            key_pressed.on_next(ContinuousMode.CRAWL_FORWARD)

        @kb.add('c-left')
        def crawl_backward(event):
            """Move the motor backward at crawl speed."""
            key_pressed.on_next(ContinuousMode.CRAWL_BACKWARD)

        @kb.add('s-right')
        def fast_forward(event):
            """Move the motor forward at fast speed."""
            key_pressed.on_next(ContinuousMode.FAST_FORWARD)

        @kb.add('s-left')
        def fast_backward(event):
            """Move the motor backward at fast speed."""
            key_pressed.on_next(ContinuousMode.FAST_BACKWARD)

        @kb.add('c-c')
        @kb.add('escape')
        def _(event):
            event.app.exit()

        def _on_error(e):
            if isinstance(e, (ModbusIOException, RuntimeError)):
                logger.error(f'Error during continuous operation: {e}')
            app.exit()

        stream_position = device.continuous(commands=key_pressed).subscribe(
            on_next=lambda position: logger.info(f'Current position: {position:.3f~P}'),
            on_error=_on_error,
        )
        assert stream_position  # to avoid "unused variable" warning

        app.run()
        key_pressed.on_completed()
    except (ModbusIOException, RuntimeError) as e:
        logger.error(e)
