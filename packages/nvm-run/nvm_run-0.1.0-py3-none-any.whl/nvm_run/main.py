#!/usr/bin/env python3
"""
nvm-run: Just *run* a particular version of node using nvm.
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path

NVM_DIR = Path(os.environ.get("NVM_DIR", Path.home() / ".nvm"))
VERSIONS_DIR = NVM_DIR / "versions" / "node"


def get_installed_versions():
    """Get list of installed node versions."""
    if not VERSIONS_DIR.exists():
        return []
    
    versions = []
    for d in VERSIONS_DIR.iterdir():
        if d.is_dir() and d.name.startswith("v"):
            versions.append(d.name)
    
    return sorted(versions, key=parse_version, reverse=True)


def parse_version(v):
    """Parse version string like 'v22.0.0' into tuple for sorting."""
    v = v.lstrip("v")
    parts = v.split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    return tuple(result)


def resolve_version(requested):
    """Resolve a version request to an installed version.
    
    '22' -> 'v22.x.x' (latest matching)
    'v22.0.0' -> 'v22.0.0' (exact)
    '22.0' -> 'v22.0.x' (latest patch)
    """
    installed = get_installed_versions()
    if not installed:
        return None
    
    # Normalize: remove leading 'v' for matching
    requested = requested.lstrip("v")
    
    # Try exact match first
    if f"v{requested}" in installed:
        return f"v{requested}"
    
    # Try prefix match
    for v in installed:
        if v.lstrip("v").startswith(requested):
            return v
    
    return None


def get_node_bin(version):
    """Get path to node binary directory for a version."""
    return VERSIONS_DIR / version / "bin"


def list_versions():
    """List installed node versions."""
    versions = get_installed_versions()
    if not versions:
        print("No node versions installed in", VERSIONS_DIR)
        return
    
    print("Installed versions:")
    for v in versions:
        bin_path = get_node_bin(v)
        node_path = bin_path / "node"
        status = "✓" if node_path.exists() else "✗"
        print(f"  {status} {v}")


def install_version(version):
    """Install a node version via nvm."""
    # We need to source nvm and run install
    nvm_sh = NVM_DIR / "nvm.sh"
    if not nvm_sh.exists():
        print(f"Error: nvm.sh not found at {nvm_sh}")
        sys.exit(1)
    
    cmd = f'source "{nvm_sh}" && nvm install {version}'
    result = subprocess.run(["bash", "-c", cmd])
    sys.exit(result.returncode)


def run_with_version(version, command):
    """Run a command with a specific node version."""
    resolved = resolve_version(version)
    if not resolved:
        print(f"Error: No installed version matching '{version}'")
        print(f"Installed: {', '.join(get_installed_versions()) or 'none'}")
        print(f"\nInstall with: nvm-run --install {version}")
        sys.exit(1)
    
    bin_path = get_node_bin(resolved)
    if not bin_path.exists():
        print(f"Error: bin directory not found: {bin_path}")
        sys.exit(1)
    
    # Prepend to PATH
    env = os.environ.copy()
    env["PATH"] = f"{bin_path}:{env.get('PATH', '')}"
    
    # Exec the command
    os.execvpe(command[0], command, env)


def main():
    parser = argparse.ArgumentParser(
        description="Run commands with a specific node version from nvm",
        usage="%(prog)s [--list] [--install VERSION] [VERSION COMMAND...]"
    )
    parser.add_argument("--list", "-l", action="store_true",
                        help="List installed node versions")
    parser.add_argument("--install", "-i", metavar="VERSION",
                        help="Install a node version")
    parser.add_argument("--path", "-p", metavar="VERSION",
                        help="Print the bin path for a version")
    parser.add_argument("args", nargs="*",
                        help="VERSION followed by COMMAND to run")
    
    args = parser.parse_args()
    
    if args.list:
        list_versions()
        return
    
    if args.install:
        install_version(args.install)
        return
    
    if args.path:
        resolved = resolve_version(args.path)
        if not resolved:
            print(f"Error: No installed version matching '{args.path}'")
            sys.exit(1)
        print(get_node_bin(resolved))
        return
    
    if len(args.args) < 2:
        parser.print_help()
        sys.exit(1)
    
    version = args.args[0]
    command = args.args[1:]
    run_with_version(version, command)


if __name__ == "__main__":
    main()