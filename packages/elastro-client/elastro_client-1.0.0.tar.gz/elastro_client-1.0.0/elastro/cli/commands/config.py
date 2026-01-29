"""
Configuration management commands for the CLI.
"""

import click
import json
import os
import yaml
from typing import Dict, Any
from elastro.config import get_config, save_config, default_config

CONFIG_PATH = os.path.expanduser("~/.elastic/config.yaml")

@click.command("get")
@click.argument("key", type=str)
@click.option("--profile", "-p", default="default", help="Configuration profile")
def get_config_value(key, profile):
    """Get a configuration value."""
    config = get_config(profile=profile)

    # Handle nested keys (e.g., "elasticsearch.hosts")
    parts = key.split(".")
    value = config
    try:
        for part in parts:
            value = value[part]

        if isinstance(value, (dict, list)):
            click.echo(json.dumps(value, indent=2))
        else:
            click.echo(value)
    except (KeyError, TypeError):
        click.echo(f"Configuration key '{key}' not found.", err=True)
        exit(1)

@click.command("set")
@click.argument("key", type=str)
@click.argument("value", type=str)
@click.option("--profile", "-p", default="default", help="Configuration profile")
def set_config_value(key, value, profile):
    """Set a configuration value."""
    config = get_config(profile=profile)

    # Parse the value if it looks like JSON
    if value.startswith("{") or value.startswith("["):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass

    # Handle nested keys (e.g., "elasticsearch.hosts")
    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]

    target[parts[-1]] = value

    # Save the updated config
    save_config(config, profile=profile)
    click.echo(f"Configuration key '{key}' set successfully.")

@click.command("list")
@click.option("--profile", "-p", default="default", help="Configuration profile")
def list_config(profile):
    """List all configuration values."""
    config = get_config(profile=profile)
    click.echo(yaml.dump(config, default_flow_style=False))

@click.command("init")
@click.option("--force", is_flag=True, help="Force initialization (overwrite existing)")
@click.option("--profile", "-p", default="default", help="Configuration profile")
def init_config(force, profile):
    """Initialize the configuration file."""
    config_dir = os.path.dirname(CONFIG_PATH)

    # Create config directory if it doesn't exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # Check if config file exists
    config_exists = os.path.exists(CONFIG_PATH)

    if config_exists and not force:
        click.echo("Configuration file already exists. Use --force to overwrite.")
        return

    # Initialize with default config
    config = default_config()

    # Add profile if specified
    if profile != "default":
        config["profiles"] = {profile: default_config()}

    # Save config
    save_config(config)

    click.echo(f"Configuration initialized at {CONFIG_PATH}")
    click.echo("Please update the configuration with your Elasticsearch connection details.")
