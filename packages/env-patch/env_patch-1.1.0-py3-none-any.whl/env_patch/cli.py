"""
env-patch CLI - Environment file generator with template + override support.

Born from MochatAI team's production experience building cross-border e-commerce
and AI-powered applications.

Features:
- Industry-standard naming: .env.{environment} + .env.{environment}.local
- Aliases: dev -> development, prod -> production, stage -> staging
- Auto-detection when single env file exists
- Always regenerates output file for consistency
- Strict mode for key validation

https://github.com/upbrosai/env-patch
"""

import argparse
import difflib
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

from . import __version__

# Aliases for common environment names
ALIASES = {
    "dev": "development",
    "prod": "production",
    "stage": "staging",
}


# Terminal colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


# Status symbols
class Symbols:
    SUCCESS = "\u2713"
    ERROR = "\u2717"
    WARNING = "\u26a0"
    INFO = "\u2192"
    CHANGE = "\u2260"


def color_text(text: str, color: str) -> str:
    """Add color to text."""
    return f"{color}{text}{Colors.RESET}"


def show_version():
    """Show version information."""
    print(f"env-patch {__version__}")
    print("MochatAI Team")
    print("https://github.com/upbrosai/env-patch")


def show_help():
    """Show help message."""
    # NOTE: -p/--patch is intentionally hidden from public help.
    # It's kept for MochatAI internal backward compatibility with legacy .envpatch files.
    help_text = f"""
{color_text(f'env-patch {__version__} - Environment file generator', Colors.BOLD)}

{color_text('Usage:', Colors.BOLD)}
  env-patch [options]
  env-patch -e <env>           # Use .env.<env> + .env.<env>.local

{color_text('Options:', Colors.BOLD)}
  -e, --env ENV       Environment name (e.g., development, prod-uai)
  -t, --template FILE Template file (default: .env.example)
  -o, --output FILE   Output file (default: .env)
  -s, --strict        Error on unknown keys
  -h, --help          Show help
  -v, --version       Show version

{color_text('Aliases:', Colors.BOLD)}
  dev -> development, prod -> production, stage -> staging

{color_text('Examples:', Colors.BOLD)}
  env-patch                          # Auto-detect env file
  env-patch -e development           # Use .env.development
  env-patch -e dev                   # Same as above (alias)
  env-patch -e uai-prod              # Use .env.uai-prod

{color_text('Local Override:', Colors.BOLD)}
  Create .env.<env>.local for local overrides (git ignored).
  Example: .env.development + .env.development.local -> .env

{color_text('File Hierarchy:', Colors.BOLD)}
  1. .env.example          (template, git tracked)
  2. .env.development      (environment config, git tracked)
  3. .env.development.local (local override, git ignored)
  4. .env                  (output, git ignored)

{color_text('More Info:', Colors.BOLD)}
  https://github.com/upbrosai/env-patch
"""
    print(help_text)


def resolve_env_name(env_name: str) -> str:
    """
    Resolve environment name alias.

    dev -> development
    prod -> production
    stage -> staging
    """
    return ALIASES.get(env_name, env_name)


def resolve_env_file(env_name: str) -> str:
    """
    Resolve -e parameter to actual file path.

    -e development  -> .env.development
    -e dev          -> .env.development (alias)
    -e uai-prod     -> .env.uai-prod
    """
    resolved = resolve_env_name(env_name)
    return f".env.{resolved}"


def get_local_override_file(env_file: str) -> str:
    """
    Get the corresponding local override file path.

    .env.development  -> .env.development.local
    .env.uai-prod     -> .env.uai-prod.local
    """
    return f"{env_file}.local"


def auto_detect_env_file() -> Optional[str]:
    """
    Auto-detect available environment file.

    Excludes: .env, .env.example, .env.local, .env.*.local
    """
    excluded = {'.env', '.env.example', '.env.local'}

    candidates = []
    for f in os.listdir('.'):
        if f.startswith('.env.') and os.path.isfile(f):
            # Exclude .local files
            if f.endswith('.local'):
                continue
            # Exclude known files
            if f in excluded:
                continue
            candidates.append(f)

    candidates.sort()

    if len(candidates) == 0:
        return None
    if len(candidates) == 1:
        return candidates[0]
    else:
        print(color_text(f"{Symbols.ERROR} Multiple env files found:", Colors.RED))
        for c in candidates:
            print(f"  - {c}")
        print(f"\nUse -e to specify one:")
        print(f"  env-patch -e {candidates[0].replace('.env.', '')}")
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-e", "--env")
    # NOTE: -p/--patch is kept for MochatAI internal backward compatibility.
    # It supports legacy .envpatch file naming convention used in internal projects.
    # This option is intentionally hidden from public documentation.
    parser.add_argument("-p", "--patch")
    parser.add_argument("-t", "--template", default=".env.example")
    parser.add_argument("-o", "--output", default=".env")
    parser.add_argument("-s", "--strict", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-v", "--version", action="store_true")

    args = parser.parse_args()

    if args.help:
        show_help()
        sys.exit(0)

    if args.version:
        show_version()
        sys.exit(0)

    return args


def load_file(filename: str) -> List[str]:
    """Load a file and return its lines."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def parse_env_dict(lines: List[str]) -> Dict[str, str]:
    """Parse env file lines into a dictionary."""
    env_dict = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = re.match(r"^([^=]+)=(.*)$", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            env_dict[key] = value

    return env_dict


def get_patch_dict_with_local(env_file: str) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Load patch dict from env file and merge with .local override if exists.

    Returns:
        Tuple of (merged_dict, local_file_path or None)
    """
    # Load the base env file
    patch_lines = load_file(env_file)
    patch_dict = parse_env_dict(patch_lines)

    # Get corresponding local file
    local_file = get_local_override_file(env_file)
    local_file_used = None

    if os.path.isfile(local_file):
        local_lines = load_file(local_file)
        local_dict = parse_env_dict(local_lines)
        patch_dict.update(local_dict)  # Local overrides base
        local_file_used = local_file

    return patch_dict, local_file_used


def apply_patch(
    example_lines: List[str],
    patch_dict: Dict[str, str],
    strict: bool = False
) -> Tuple[List[str], Dict[str, int], List[str]]:
    """Apply patch to example lines and return result with stats and warnings."""
    result_lines = []
    example_dict = parse_env_dict(example_lines)
    applied_keys = set()
    warnings = []

    stats = {
        "total": len(example_dict),
        "patched": 0,
        "added": 0,
        "unknown": 0
    }

    # Process each line from example
    for line in example_lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            result_lines.append(line)
            continue

        match = re.match(r"^([^=]+)=(.*)$", stripped)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()

            if key in patch_dict:
                value = patch_dict[key]
                applied_keys.add(key)
                stats["patched"] += 1

            result_lines.append(f"{key}={value}\n")

    # Add unknown keys from patch (unless in strict mode)
    additional_keys = []
    for key, value in patch_dict.items():
        if key not in applied_keys:
            stats["unknown"] += 1
            if strict:
                raise ValueError(f"Key '{key}' not found in template file")
            else:
                # Add the key to the output
                additional_keys.append((key, value))
                warnings.append(f"Key '{key}' not found in template, adding anyway")
                stats["added"] += 1

    # Append additional keys at the end
    if additional_keys:
        result_lines.append("\n# Additional keys from env file\n")
        for key, value in additional_keys:
            result_lines.append(f"{key}={value}\n")

    return result_lines, stats, warnings


def show_diff(old_content: str, new_content: str, filename: str):
    """Display differences between old and new content."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"{filename} (before)",
        tofile=f"{filename} (after)",
        n=3
    ))

    if diff:
        print(f"\n{Symbols.CHANGE} Changes to {filename}:")
        for line in diff:
            line = line.rstrip()
            if line.startswith('+') and not line.startswith('+++'):
                print(color_text(line, Colors.GREEN))
            elif line.startswith('-') and not line.startswith('---'):
                print(color_text(line, Colors.RED))
            elif line.startswith('@'):
                print(color_text(line, Colors.CYAN))
            else:
                print(line)


def main():
    """Main entry point for the CLI."""
    args = parse_args()

    # Check if template file exists
    if not os.path.isfile(args.template):
        print(color_text(
            f"{Symbols.ERROR} Template file not found: {args.template}",
            Colors.RED
        ))
        print(f"\nRun 'env-patch -h' for help")
        sys.exit(1)

    # Determine env file to use
    env_file = None

    if args.patch:
        # -p flag: use specified file directly
        # NOTE: This is for MochatAI internal backward compatibility with legacy
        # .envpatch files. It allows direct file path specification without the
        # standard .env.{environment} naming convention.
        if not os.path.isfile(args.patch):
            print(color_text(
                f"{Symbols.ERROR} Patch file not found: {args.patch}",
                Colors.RED
            ))
            sys.exit(1)
        env_file = args.patch

    elif args.env:
        # -e flag: resolve environment name to file path
        env_file = resolve_env_file(args.env)
        if not os.path.isfile(env_file):
            print(color_text(
                f"{Symbols.ERROR} Env file not found: {env_file}",
                Colors.RED
            ))
            # Show helpful suggestion
            resolved = resolve_env_name(args.env)
            if resolved != args.env:
                print(f"  ('{args.env}' resolved to '{resolved}')")
            sys.exit(1)

    else:
        # No flag: auto-detect
        env_file = auto_detect_env_file()

    # Load template file
    template_lines = load_file(args.template)

    # If no env file, just copy template
    if not env_file:
        print(f"{Symbols.INFO} No env files found, copying {args.template} to {args.output}")

        current_content = ''.join(load_file(args.output))
        new_content = ''.join(template_lines)

        # Always write the file
        with open(args.output, "w", encoding="utf-8") as f:
            f.writelines(template_lines)

        if current_content == new_content:
            print(f"{Symbols.SUCCESS} {args.output} regenerated (no changes)")
        else:
            print(f"{Symbols.SUCCESS} Created {args.output}")
        return

    # Load and apply env file
    print(f"{Symbols.INFO} Using: {env_file}")
    patch_dict, local_file = get_patch_dict_with_local(env_file)

    if local_file:
        print(f"{Symbols.INFO} Local override: {local_file}")

    # Apply patch
    try:
        result_lines, stats, warnings = apply_patch(
            template_lines, patch_dict, args.strict
        )
    except ValueError as e:
        print(color_text(f"{Symbols.ERROR} {e}", Colors.RED))
        sys.exit(1)

    # Show warnings
    for warning in warnings:
        print(color_text(f"{Symbols.WARNING} {warning}", Colors.YELLOW))

    # Compare with existing file
    new_content = ''.join(result_lines)
    old_content = ''.join(load_file(args.output))
    content_changed = old_content != new_content

    # Always write new content
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Show diff if content changed
    if content_changed and old_content:
        show_diff(old_content, new_content, args.output)

    # Print summary
    print(f"\n{color_text('Summary', Colors.BOLD)}")
    print(f"  Total keys: {stats['total']}")
    print(f"  Patched: {color_text(str(stats['patched']), Colors.GREEN)}")

    if stats['added'] > 0:
        print(f"  Added: {color_text(str(stats['added']), Colors.YELLOW)}")

    if content_changed:
        print(f"\n{Symbols.SUCCESS} {color_text(args.output + ' updated', Colors.GREEN)}")
    else:
        print(f"\n{Symbols.SUCCESS} {color_text(args.output + ' regenerated (no changes)', Colors.GREEN)}")


if __name__ == "__main__":
    main()
