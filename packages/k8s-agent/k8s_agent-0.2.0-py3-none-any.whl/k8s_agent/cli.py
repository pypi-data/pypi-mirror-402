"""Main CLI entry point for k8s-agent."""

import click

from .commands.auth import auth_commands
from .commands.vm import vm_commands


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="0.1.0", prog_name="k8s-agent")
def main():
    """k8s-agent: CLI for K8sVMgr backend (no LLM)."""
    pass


# Register command groups
main.add_command(auth_commands.commands["login"])
main.add_command(auth_commands.commands["logout"])
main.add_command(auth_commands.commands["whoami"])
main.add_command(vm_commands.commands["list"], name="list")
main.add_command(vm_commands.commands["create"], name="create")
main.add_command(vm_commands.commands["delete"], name="delete")
main.add_command(vm_commands.commands["ssh"], name="ssh")
main.add_command(vm_commands.commands["events"], name="events")
main.add_command(vm_commands.commands["logs"], name="logs")
main.add_command(vm_commands.commands["dashboard"], name="dashboard")
main.add_command(vm_commands.commands["interconnect"], name="interconnect")
main.add_command(vm_commands.commands["saves"], name="saves")
main.add_command(vm_commands.commands["keys"], name="keys")


if __name__ == "__main__":
    main()
