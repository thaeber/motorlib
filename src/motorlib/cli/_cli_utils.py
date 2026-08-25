from rich.table import Table


def format_status_table(status: dict[str, bool], title: None | str = None) -> Table:
    table = Table(title=title)
    for key in status:
        table.add_column(str(key), style='cyan', no_wrap=True)

    table.add_row(
        *(
            '[bold][green]✓[/green][/bold]' if value else ''
            for value in status.values()
        ),
        style='magenta',
    )
    return table
