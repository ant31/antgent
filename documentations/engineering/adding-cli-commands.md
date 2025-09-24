# How to Add a New CLI Command

Our project uses the [`typer`](https://typer.tiangolo.com/) library to build powerful and user-friendly command-line interfaces. This guide will walk you through adding a new command to the `antgent` CLI tool.

## Step 1: Create the Command File

First, create a new Python file for your command in the `antgent/cmd/` directory. This file will contain the `typer` application and the command's logic. For this example, we'll create a `hello` command.

**File:** `antgent/cmd/hello.py`
```python
from typing import Annotated
import typer

# It's common to create a typer "sub-application" for a group of related commands
app = typer.Typer()

@app.command()
def hello(
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="The name to greet."),
    ] = "World",
) -> None:
    """
    A simple command that greets the user.
    """
    typer.echo(f"Hello, {name}!")

```
- `@app.command()`: This decorator turns the `hello` function into a command-line command.
- `typer.Option(...)`: This defines a command-line option (`--name`). Using `Annotated` is the recommended modern style.
- The function's docstring is automatically used as the help text for the command.

## Step 2: Register the New Command

After creating the command file, you must register it with the main CLI application, which is located in `antgent/cmd/main.py`.

**File:** `antgent/cmd/main.py`
```python
#!/usr/bin/env python3
import typer
# ... other imports

from .hello import app as hello_app  # Import your new command app
from .server import app as server_app

app = typer.Typer(no_args_is_help=True)

# ... add other commands
app.add_typer(server_app)
app.add_typer(hello_app)  # Add your new command here


def main() -> None:
    app()


if __name__ == "__main__":
    main()

```
- We import the `app` object from our `hello.py` file.
- `app.add_typer(hello_app)` registers all commands from `hello_app`.

## Step 3: Testing the Command

CLI commands should be tested. You can use `typer.testing.CliRunner` to invoke commands in your tests.

**File:** `tests/cmd/test_hello.py`
```python
from typer.testing import CliRunner

from antgent.cmd.main import app  # Test through the main app entry point

runner = CliRunner()


def test_hello_help():
    """Test the help output of the hello command."""
    result = runner.invoke(app, ["hello", "--help"])
    assert result.exit_code == 0
    assert "A simple command that greets the user." in result.stdout
    assert "--name" in result.stdout

def test_hello_default_name():
    """Test the command with the default name."""
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.stdout

def test_hello_with_name():
    """Test the command with a specific name."""
    result = runner.invoke(app, ["hello", "--name", "Engineer"])
    assert result.exit_code == 0
    assert "Hello, Engineer!" in result.stdout
```

## Step 4: Verify Your Command

You can now verify your command from your terminal.

```bash
# See the new "hello" command listed
antgent --help

# Run the command
antgent hello --name "Engineer"
```

Output:
```
Hello, Engineer!
```
