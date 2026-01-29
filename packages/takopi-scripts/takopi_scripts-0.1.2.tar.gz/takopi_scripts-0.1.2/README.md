# takopi-scripts

A dynamic script runner plugin for [takopi](https://github.com/banteg/takopi).

## Installation

```bash
uv tool install takopi-scripts
```

## Usage

The plugin provides a `/run` command to execute Python scripts from a scripts directory.

```
/run <script> [args]   - Run a script with optional arguments
/run list              - List available scripts
/run reload            - Clear cached script modules
```

By default, scripts are loaded from `~/.takopi/scripts/`. You can customize this in your takopi config:

```yaml
plugins:
  takopi-scripts:
    scripts_dir: ~/my-scripts
```

## Writing Scripts

Create `.py` files in your scripts directory. Each script must define an async `handle` function:

```python
"""My example script - this docstring becomes the description."""

from takopi.api import CommandContext, CommandResult

async def handle(ctx: CommandContext) -> CommandResult:
    return CommandResult(text=f"Hello! Args: {ctx.args}")
```

The first line of the module docstring is shown when running `/run list`.