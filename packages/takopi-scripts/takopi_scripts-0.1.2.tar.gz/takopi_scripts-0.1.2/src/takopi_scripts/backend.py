"""Script runner command backend for takopi."""

import importlib.util
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

from takopi.api import CommandContext, CommandResult

DEFAULT_SCRIPTS_DIR = Path.home() / ".takopi" / "scripts"


def get_scripts_dir(ctx: CommandContext) -> Path:
    """Get the scripts directory from config or use default."""
    scripts_dir = ctx.plugin_config.get("scripts_dir")
    if scripts_dir:
        return Path(scripts_dir).expanduser()
    return DEFAULT_SCRIPTS_DIR


def get_script_description(script_path: Path) -> str:
    """Extract the first line of the module docstring as description."""
    try:
        source = script_path.read_text()
        # Compile and extract docstring without executing
        code = compile(source, script_path, "exec")
        if code.co_consts and isinstance(code.co_consts[0], str):
            docstring = code.co_consts[0]
            # Return first non-empty line
            for line in docstring.strip().split("\n"):
                line = line.strip()
                if line:
                    return line
    except Exception:
        pass
    return ""


def list_scripts(scripts_dir: Path) -> str:
    """List available scripts with descriptions."""
    if not scripts_dir.exists():
        return f"Scripts directory does not exist: {scripts_dir}"

    scripts = sorted(scripts_dir.glob("*.py"))
    if not scripts:
        return f"No scripts found in {scripts_dir}"

    lines = []
    for script in scripts:
        name = script.stem
        desc = get_script_description(script)
        if desc:
            lines.append(f"  {name} - {desc}")
        else:
            lines.append(f"  {name}")

    return "Available scripts:\n" + "\n".join(lines)


def clear_script_cache(scripts_dir: Path) -> str:
    """Clear cached script modules from sys.modules."""
    cleared = []
    scripts_dir_str = str(scripts_dir.resolve())

    to_remove = []
    for name, module in sys.modules.items():
        if hasattr(module, "__file__") and module.__file__:
            try:
                if str(Path(module.__file__).resolve()).startswith(scripts_dir_str):
                    to_remove.append(name)
            except Exception:
                pass

    for name in to_remove:
        del sys.modules[name]
        cleared.append(name)

    if cleared:
        return f"Cleared {len(cleared)} cached module(s): {', '.join(cleared)}"
    return "No cached scripts to clear."


async def load_and_run_script(
    script_name: str, args_text: str, ctx: CommandContext, scripts_dir: Path
) -> CommandResult:
    """Load a script module and execute its handle function."""
    script_path = scripts_dir / f"{script_name}.py"

    if not script_path.exists():
        return CommandResult(text=f"Script not found: {script_name}")

    # Create a unique module name to allow reloading
    module_name = f"takopi_script_{script_name}"

    # Remove from cache if exists (for reload behavior)
    if module_name in sys.modules:
        del sys.modules[module_name]

    try:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            return CommandResult(text=f"Failed to load script: {script_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception:
        tb = traceback.format_exc()
        return CommandResult(text=f"Import error in {script_name}:\n```\n{tb}```")

    if not hasattr(module, "handle"):
        return CommandResult(
            text=f"Script {script_name} missing required 'handle' function"
        )

    handle = module.handle
    if not callable(handle):
        return CommandResult(text=f"Script {script_name} 'handle' is not callable")

    # Build a new context with script-specific args
    script_args = tuple(args_text.split()) if args_text else ()
    script_ctx = CommandContext(
        command=script_name,
        text=ctx.text,
        args_text=args_text,
        args=script_args,
        message=ctx.message,
        reply_to=ctx.reply_to,
        reply_text=ctx.reply_text,
        config_path=ctx.config_path,
        plugin_config=ctx.plugin_config,
        runtime=ctx.runtime,
        executor=ctx.executor,
    )

    try:
        result = await handle(script_ctx)
        if result is None:
            return CommandResult(text=f"Script {script_name} completed (no output)")
        return result
    except Exception:
        tb = traceback.format_exc()
        return CommandResult(text=f"Runtime error in {script_name}:\n```\n{tb}```")


@dataclass
class RunCommandBackend:
    id: str = "run"
    description: str = "Run scripts from ~/.takopi/scripts/"

    async def handle(self, ctx: CommandContext) -> CommandResult:
        scripts_dir = get_scripts_dir(ctx)
        args = ctx.args

        if not args:
            return CommandResult(
                text="Usage: /run <script> [args] | /run list | /run reload"
            )

        subcommand = args[0]

        if subcommand == "list":
            return CommandResult(text=list_scripts(scripts_dir))

        if subcommand == "reload":
            return CommandResult(text=clear_script_cache(scripts_dir))

        # Run the script
        script_name = subcommand
        args_text = " ".join(args[1:]) if len(args) > 1 else ""
        return await load_and_run_script(script_name, args_text, ctx, scripts_dir)


BACKEND = RunCommandBackend()
