import json
import os
import secrets
import string
import subprocess
from dataclasses import dataclass

import git
from rich import print

from btpy.configuration.config import KeyVaultInfo, get_config_value, get_config
from btpy.core.azure_utility import (
    assign_subscription_role,
    create_service_principal,
    get_keyvault_secret,
    query_keyvault_secrets,
    upload_keyvault_secret,
    upload_keyvault_secret_file,
)


@dataclass
class AzureServicePrincipal:
    client_id: str
    client_secret: str


def generate_keys_ed25519(private_key_path, public_key_path, comment):
    if os.path.exists(private_key_path) or os.path.exists(public_key_path):
        print("[blue]Key file(s) already exist")
        return

    subprocess.run(
        [
            "ssh-keygen",
            "-t",
            "ed25519",
            "-C",
            comment,
            "-f",
            private_key_path,
            "-N",
            "",
        ],
        check=True,
    )
    os.chmod(private_key_path, 0o600)
    os.chmod(public_key_path, 0o644)


def setup_ssh_keys(keyvault_name, secrets_path, comment, regen_ssh=False):
    ssh_path = os.path.join(secrets_path, "id_ed25519")
    ssh_pub_path = os.path.join(secrets_path, "id_ed25519.pub")

    existing_ssh_key = get_keyvault_secret(keyvault_name, "repo-ssh-key")
    existing_ssh_pub_key = get_keyvault_secret(keyvault_name, "repo-ssh-key-pub")

    if existing_ssh_key and existing_ssh_pub_key and not regen_ssh:
        return

    generate_keys_ed25519(ssh_path, ssh_pub_path, comment)
    upload_keyvault_secret_file(keyvault_name, "repo-ssh-key", ssh_path)
    upload_keyvault_secret_file(keyvault_name, "repo-ssh-key-pub", ssh_pub_path)
    os.remove(ssh_path)
    os.remove(ssh_pub_path)


def init_git_repo(folder, repo_kind_message):
    print(f"[blue]Set up local {repo_kind_message} git repo...", end=" ")

    # Initialize or open existing repo
    try:
        repo = git.Repo.init(folder)
    except git.exc.GitCommandError as e:
        if "already exists" not in str(e):
            print(f"[red]Failed (git init - {e})")
            return False
        repo = git.Repo(folder)

    # If the repo is already initialized, fetch and pull before committing
    try:
        if repo.remotes:
            origin = repo.remotes.origin
            origin.fetch()
            origin.pull()
    except git.exc.GitCommandError as e:
        if "There is no tracking information for the current branch" not in str(e):
            print(f"[red]Failed (git fetch/pull - {e})")
            return False

    # Stage and commit changes
    try:
        # Check if there are changes to commit BEFORE staging
        if not repo.head.is_valid():
            # No commits yet - check for any files
            has_changes = len(repo.untracked_files) > 0
        else:
            # Has commits - check for changes
            has_changes = (
                len(repo.index.diff(None)) > 0  # Working tree changes
                or len(repo.index.diff("HEAD")) > 0  # Staged changes
                or len(repo.untracked_files) > 0  # Untracked files
            )

        if has_changes:
            repo.git.add(
                "."
            )  # Use git.add() to properly respect .gitignore and exclude .git/
            repo.index.commit(
                f"{repo_kind_message.capitalize()} repo bootstrap commit by btpy"
            )
        # else: nothing to commit, silently skip (matches original behavior)

    except git.exc.GitCommandError as e:
        print(f"[red]Failed (git commit - {e})")
        return False

    print("[green]Complete")
    return True


def get_azure_tenant_sps():
    global_kv_info = KeyVaultInfo(**get_config_value("global_keyvault"))

    if not global_kv_info:
        print("[red]Failed to read config for global keyvault")
        return []

    sps = query_keyvault_secrets(
        global_kv_info.name, "[?starts_with(name,'az-tenant-sp')]"
    )
    return [sp["name"] for sp in sps]


def get_or_create_azure_tenant_sp(
    tenant_id, subscription_id=None
) -> AzureServicePrincipal:
    kv_info = KeyVaultInfo(**get_config_value("global_keyvault"))
    kv_name = kv_info.name
    sps = get_azure_tenant_sps()
    sp_name = next((sp for sp in sps if tenant_id in sp), None)

    if not sp_name:
        sp = create_azure_tenant_sp(kv_name, tenant_id, subscription_id)["value"]
    else:
        sp = get_keyvault_secret(kv_name, sp_name)

    sp_obj = AzureServicePrincipal(**json.loads(sp))

    if subscription_id:
        assign_subscription_role(subscription_id, sp_obj.client_id, "Contributor")

    return sp_obj


def create_azure_tenant_sp(keyvault_name, tenant_id, subscription_id=None):
    sp_name = f"az-tenant-sp-{tenant_id}"
    sp = create_service_principal(sp_name, tenant_id)

    sp_secret = {"client_id": sp["appId"], "client_secret": sp["password"]}
    return upload_keyvault_secret(
        keyvault_name, sp_name, json.dumps(sp_secret, separators=(",", ":"))
    )


@dataclass
class GitHubAuthInfo:
    private_key: str
    app_id: str
    installation_id: str


def get_gh_btenvs_app_info():
    kv_info = KeyVaultInfo(**get_config_value("global_keyvault"))
    return GitHubAuthInfo(
        private_key=get_keyvault_secret(kv_info.name, "btenvs-private-key"),
        app_id="2251489",  # App ID taken from GitHub website on the app's page
        installation_id="93545915",  # Installation ID taken from the URL in the btenvs repo -> settings -> github apps -> configure the installed app
    )


def create_domain(subdomain):
    btpy_config = get_config()
    base_domain = btpy_config.domain
    return f"{subdomain}.{base_domain}"


def generate_password(
    length: int = 20,
    lowercase: bool = True,
    uppercase: bool = True,
    digits: bool = True,
    symbols: str | None = "_",
) -> str:
    """
    Generate a secure password with guaranteed character type representation.

    Args:
        length: Total password length (must be >= number of enabled types)
        lowercase: Include lowercase letters (a-z)
        uppercase: Include uppercase letters (A-Z)
        digits: Include digits (0-9)
        symbols: String of allowed symbols, or None to disable

    Returns:
        Generated password with at least one of each enabled type
    """
    pools = []
    if lowercase:
        pools.append(string.ascii_lowercase)
    if uppercase:
        pools.append(string.ascii_uppercase)
    if digits:
        pools.append(string.digits)
    if symbols:
        pools.append(symbols)

    if not pools:
        raise ValueError("At least one character type must be enabled")

    if length < len(pools):
        raise ValueError(
            f"Length must be at least {len(pools)} to include one of each type"
        )

    # Guarantee at least one from each pool
    password_chars = [secrets.choice(pool) for pool in pools]

    # Fill remaining length from combined pool
    all_chars = "".join(pools)
    password_chars.extend(secrets.choice(all_chars) for _ in range(length - len(pools)))

    # Shuffle to avoid predictable positions
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)
