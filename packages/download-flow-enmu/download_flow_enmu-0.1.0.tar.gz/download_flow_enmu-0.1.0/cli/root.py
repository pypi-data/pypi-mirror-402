import typer

app = typer.Typer(help="demail")


def version_callback(value: bool):
    if value:
        print("Awesome CLI Version: 1.0.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
):
    if verbose:
        print("Verbose mode is ON")
