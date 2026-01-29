"""
SecureEnv-Pro - CLI Commands Module
Implements all command-line interface commands
"""

import os
import sys
import subprocess
import click
from pathlib import Path
from getpass import getpass
from tabulate import tabulate
from colorama import init, Fore, Style

from core.security import SecureVault, SecurityError, verify_password_strength
from core.storage import VaultStorage, StorageError, TeamVaultManager

# Initialize colorama for Windows support
init(autoreset=True)

# Initialize storage
storage = VaultStorage()
team_manager = TeamVaultManager(storage)


def print_success(message: str):
    """Print success message in green"""
    click.echo(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print error message in red"""
    click.echo(f"{Fore.RED}✗ {message}{Style.RESET_ALL}", err=True)


def print_info(message: str):
    """Print info message in cyan"""
    click.echo(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def print_warning(message: str):
    """Print warning message in yellow"""
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def get_password(prompt: str = "Enter Master Password", verify: bool = False) -> str:
    """
    Securely get password from user
    
    Args:
        prompt: Password prompt message
        verify: If True, ask for password confirmation
        
    Returns:
        Password string
    """
    password = getpass(f"{prompt}: ")
    
    if verify:
        confirm = getpass("Confirm Password: ")
        if password != confirm:
            print_error("Passwords don't match")
            sys.exit(1)
    
    return password


@click.group()
@click.version_option(version="1.0.0", prog_name="SecureEnv-Pro")
def cli():
    """
    🔐 SecureEnv-Pro - Enterprise Environment Variable Security
    
    Secure, encrypt, and manage your environment variables with military-grade encryption.
    """
    pass


@cli.command()
@click.argument('env_file', type=click.Path(exists=True))
@click.option('--name', '-n', required=True, help='Vault name identifier')
@click.option('--description', '-d', default='', help='Vault description')
@click.option('--output', '-o', help='Output vault file path')
def lock(env_file: str, name: str, description: str, output: str):
    """
    🔒 Lock (encrypt) an environment file into a vault
    
    Example: secureenv lock .env --name production --description "Production secrets"
    """
    try:
        # Get and verify password
        print_info("Creating new encrypted vault")
        password = get_password("Create Master Password", verify=True)
        
        is_strong, msg = verify_password_strength(password)
        if not is_strong:
            print_error(f"Weak password: {msg}")
            print_info("Recommendation: Use mix of uppercase, lowercase, digits, and symbols")
            if not click.confirm("Continue anyway?"):
                sys.exit(1)
        
        # Create vault
        vault = SecureVault(password)
        
        # Default output path
        if not output:
            output = str(Path(env_file).with_suffix('.vlt'))
        
        # Encrypt file
        output_path = vault.encrypt_file(env_file, output)
        
        # Register vault
        storage.register_vault(name, output_path, description)
        
        print_success(f"Vault created: {output_path}")
        print_success(f"Registered as: {name}")
        print_warning("⚠️  IMPORTANT: Remember your master password - it cannot be recovered!")
        
        # Ask to delete original
        if click.confirm(f"\nDelete original {env_file} for security?"):
            os.remove(env_file)
            print_success(f"Deleted {env_file}")
        
    except (SecurityError, StorageError) as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--name', '-n', required=True, help='Vault name to unlock')
@click.option('--output', '-o', help='Output file path (default: .env)')
def unlock(name: str, output: str):
    """
    🔓 Unlock (decrypt) a vault to an environment file
    
    Example: secureenv unlock --name production --output .env.local
    """
    try:
        # Get vault path
        vault_file = storage.get_vault_path(name)
        
        # Get password
        password = get_password()
        
        # Decrypt
        vault = SecureVault(password)
        decrypted_data = vault.decrypt_file(vault_file, password)
        
        # Write to output
        output_path = output or '.env'
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        storage.update_access_time(name)
        storage.log_audit("vault_unlocked", {"vault": name})
        
        print_success(f"Vault unlocked to: {output_path}")
        print_warning("⚠️  Remember to delete this file after use!")
        
    except (SecurityError, StorageError) as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--name', '-n', required=True, help='Vault name to use')
@click.argument('command', nargs=-1, required=True)
def run(name: str, command: tuple):
    """
    🚀 Run a command with decrypted environment variables (memory-only)
    
    Variables are injected into the command's environment without writing to disk.
    
    Examples:
      secureenv run --name production -- node app.js
      secureenv run --name dev -- python manage.py runserver
      secureenv run --name staging -- npm start
    """
    try:
        # Get vault path
        vault_file = storage.get_vault_path(name)
        
        # Get password
        password = get_password()
        
        # Decrypt to memory
        vault = SecureVault(password)
        decrypted_data = vault.decrypt_file(vault_file, password)
        
        # Parse environment variables
        env_content = decrypted_data.decode('utf-8')
        env_vars = storage.parse_env_content(env_content)
        
        # Prepare environment
        current_env = os.environ.copy()
        current_env.update(env_vars)
        
        # Run command
        command_str = ' '.join(command)
        print_info(f"Running: {command_str}")
        print_info(f"Loaded {len(env_vars)} environment variables")
        
        storage.update_access_time(name)
        storage.log_audit("command_executed", {
            "vault": name,
            "command": command_str
        })
        
        # Execute command with environment
        result = subprocess.run(
            command_str,
            env=current_env,
            shell=True
        )
        
        sys.exit(result.returncode)
        
    except (SecurityError, StorageError) as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
def list():
    """
    📋 List all registered vaults
    """
    try:
        vaults = storage.list_vaults()
        
        if not vaults:
            print_info("No vaults registered yet")
            print_info("Create one with: secureenv lock <file> --name <name>")
            return
        
        # Prepare table data
        table_data = []
        for vault in vaults:
            table_data.append([
                vault['name'],
                vault['description'] or '-',
                vault.get('created_at', 'Unknown')[:10],
                vault.get('last_accessed', 'Never')[:10] if vault.get('last_accessed') else 'Never',
                '✓' if os.path.exists(vault['file']) else '✗'
            ])
        
        headers = ['Name', 'Description', 'Created', 'Last Access', 'File Exists']
        click.echo("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo()
        
    except StorageError as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--name', '-n', required=True, help='Vault name to delete')
@click.option('--remove-file', is_flag=True, help='Also delete the .vlt file')
def delete(name: str, remove_file: bool):
    """
    🗑️  Delete a vault registration
    
    Example: secureenv delete --name old-project --remove-file
    """
    try:
        if not click.confirm(f"Delete vault '{name}'?"):
            print_info("Cancelled")
            return
        
        storage.delete_vault(name, remove_file)
        print_success(f"Vault '{name}' deleted")
        
    except StorageError as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', default=20, help='Number of entries to show')
def audit(limit: int):
    """
    📊 View audit logs
    
    Example: secureenv audit --limit 50
    """
    try:
        logs = storage.get_audit_logs(limit)
        
        if not logs:
            print_info("No audit logs found")
            return
        
        table_data = []
        for log in logs:
            table_data.append([
                log['timestamp'][:19],
                log['action'],
                str(log.get('details', {}))[:50]
            ])
        
        headers = ['Timestamp', 'Action', 'Details']
        click.echo("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo()
        
    except StorageError as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--name', '-n', required=True, help='Vault name')
@click.option('--email', '-e', required=True, help='Team member email')
@click.option('--role', '-r', type=click.Choice(['admin', 'developer', 'viewer']), 
              default='developer', help='Member role')
def add_member(name: str, email: str, role: str):
    """
    👥 Add team member to a vault
    
    Roles:
      - admin: Full access including team management
      - developer: Can read and deploy
      - viewer: Read-only access
    
    Example: secureenv add-member --name production --email dev@company.com --role developer
    """
    try:
        team_manager.add_team_member(name, email, role)
        print_success(f"Added {email} as {role} to vault '{name}'")
        
    except StorageError as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--name', '-n', required=True, help='Vault name')
def team(name: str):
    """
    👥 List team members for a vault
    
    Example: secureenv team --name production
    """
    try:
        members = team_manager.get_team_members(name)
        
        if not members:
            print_info(f"No team members for vault '{name}'")
            return
        
        table_data = [
            [email, info['role'], info.get('added_at', 'Unknown')[:10]]
            for email, info in members.items()
        ]
        
        headers = ['Email', 'Role', 'Added']
        click.echo(f"\n{Fore.CYAN}Team members for '{name}':{Style.RESET_ALL}")
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo()
        
    except StorageError as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == '__main__':
    cli()
