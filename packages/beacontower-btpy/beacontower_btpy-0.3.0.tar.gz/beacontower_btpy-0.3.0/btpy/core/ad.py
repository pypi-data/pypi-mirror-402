from rich import print
from btpy.core.azure_utility import (
    create_azure_ad,
    get_azure_ad,
    get_azure_ad_app_by_name,
    create_azure_ad_app,
    create_azure_ad_app_secret,
    get_azure_ad_app_secret_by_name,
)


async def create_ad(
    id,
    name,
    resource_group,
    location,
    country_code,
    subscription_id,
    redirect_uris=None,
):
    """Create Azure AD B2C tenant with app registration. User flows must be created manually."""
    if redirect_uris is None:
        redirect_uris = []

    tenant_domain = f"{id}.onmicrosoft.com"
    ad_info = get_azure_ad(tenant_domain, resource_group, subscription_id)
    if not ad_info:
        print(f"[blue]Creating Azure AD {id}...", end=" ")
        ad_info = create_azure_ad(
            id, name, resource_group, location, country_code, subscription_id
        )
        print("[green]Complete")
    else:
        print(f"[blue]Azure AD {id} already exists")

    app_name = "beacontower"
    app = await get_azure_ad_app_by_name(app_name, ad_info.tenant_id)
    if not app:
        print(f"[blue]Creating Azure AD app registration {app_name}...", end=" ")
        app = await create_azure_ad_app(app_name, redirect_uris, ad_info.tenant_id)
        print("[green]Complete")
    else:
        print(f"[blue]Azure AD app registration {app_name} already exists")

    secret_name = "btpy-secret"
    secret = await get_azure_ad_app_secret_by_name(
        app.id, secret_name, ad_info.tenant_id
    )
    if not secret:
        print(
            f"[blue]Creating Azure AD app registration secret {secret_name}...", end=" "
        )
        secret = await create_azure_ad_app_secret(
            app.id, secret_name, ad_info.tenant_id
        )
        print("[green]Complete")
        print(f"[yellow]Secret value (save this!):[/yellow] {secret.secret_text}")
    else:
        print(f"[blue]Azure AD app registration secret {secret_name} already exists")

    print()
    print("[yellow]Manual step required:[/yellow] Create user flow in Azure Portal:")
    print("  1. Go to: https://portal.azure.com")
    print(f"  2. Switch to directory: [cyan]{tenant_domain}[/cyan]")
    print("  3. Search for 'Azure AD B2C' -> User flows -> New user flow")
    print("  4. Select 'Sign up and sign in' -> Recommended -> Create")

    return ad_info
