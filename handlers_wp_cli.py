"""Arbitrary and flexible WP-CLI command executor over SSH.

Enables full WP-CLI power for connected WordPress sites that have SSH credentials
configured via add_ssh. Validates against dangerous shell escapes and delegates
execution to wp_cli.run_wp_command.
"""
from __future__ import annotations

import re
from imperal_sdk import ActionResult

from app import chat
from models import RunWpCommandParams, WpCommandResult
import storage
import wp_cli

# Forbidden shell characters that could break out of the intended wp command
_SHELL_INJECTION_RE = re.compile(r"[;&|`$><]")


def _validate_command(cmd: str) -> str | None:
    """Check if the command string has dangerous shell metacharacters."""
    cleaned = cmd.strip()
    if cleaned.startswith("wp "):
        cleaned = cleaned[3:].strip()
    if not cleaned:
        return "Command cannot be empty."
    if _SHELL_INJECTION_RE.search(cleaned):
        return "Command contains disallowed shell metacharacters (;, &, |, `, $, >, <). Pass standard WP-CLI subcommands and arguments only."
    return None


@chat.function(
    "run_wp_command",
    description=(
        "Execute an arbitrary WP-CLI command over SSH on a connected WordPress site. "
        "Allows running any wp subcommand (e.g. 'plugin list --status=active', "
        "'post list --post_type=page', 'option get siteurl', 'transient delete --all', "
        "'user list --role=administrator'). Requires SSH configured via add_ssh."
    ),
    action_type="write",
    data_model=WpCommandResult,
    effects=["wp.cli_command"],
    event="wordpress-hub.run_wp_command",
)
async def run_wp_command(ctx, params: RunWpCommandParams) -> ActionResult:
    """Execute arbitrary WP-CLI subcommand over SSH."""
    val_err = _validate_command(params.command)
    if val_err:
        return ActionResult.error(val_err, retryable=False, code="INVALID_WP_COMMAND")

    record = await storage.get_site_record(ctx, params.site_id)
    if not record:
        return ActionResult.error(
            "No connected site with that id — run list_sites to see connected sites.",
            retryable=False,
            code="SITE_NOT_CONNECTED",
        )

    cred = await storage.get_ssh_cred(ctx, params.site_id)
    if not cred:
        return ActionResult.error(
            "SSH is not configured for this site. Use add_ssh to provide SSH credentials.",
            retryable=False,
            code="SSH_NOT_CONFIGURED",
        )

    cleaned_cmd = params.command.strip()
    if cleaned_cmd.startswith("wp "):
        cleaned_cmd = cleaned_cmd[3:].strip()

    timeout = params.timeout or 60
    try:
        stdout, err = await wp_cli.run_wp_command(
            cred,
            subcommand=cleaned_cmd,
            raw_args=params.raw_args,
            timeout=timeout,
        )
    except Exception as e:
        await ctx.log(f"run_wp_command exception: {e}", level="error")
        return ActionResult.error(f"Error executing WP-CLI command over SSH: {e}", retryable=True)

    if err:
        await ctx.log(f"run_wp_command error: {err}", level="error")
        return ActionResult.error(err, retryable=True, code="WP_CLI_ERROR")

    output = stdout or ""
    return ActionResult.success(
        WpCommandResult(
            id=params.site_id,
            title=f"wp {cleaned_cmd}",
            kind="wp_cli_command",
            output=output,
            command=f"wp {cleaned_cmd}",
        ),
        summary=output[:500] if len(output) > 500 else output,
    )
