from typing import Optional

import click
from click_option_group import RequiredMutuallyExclusiveOptionGroup, optgroup
from sifflet_sdk.config import SiffletConfig
from sifflet_sdk.configure.service import ConfigureService
from sifflet_sdk.constants import SIFFLET_CONFIG_CTX, TENANT_KEY, TOKEN_KEY


def default_from_context(default_key):
    class DefaultFromContext(click.Option):
        def get_default(self, ctx, call=True):
            sifflet_config: SiffletConfig = ctx.obj[SIFFLET_CONFIG_CTX]
            if default_key == TENANT_KEY:
                self.default = sifflet_config.tenant
            if default_key == TOKEN_KEY:
                self.default = sifflet_config.token
            return super().get_default(ctx)

        def __str__(self):
            print(default_key)
            return "*" * 8 if default_key == TOKEN_KEY else self.default

    return DefaultFromContext


@click.command()
@optgroup.group("Sifflet host configuration", cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option(
    "--tenant",
    help="For SaaS version, name of your tenant. Sifflet UI URL is https://<tenant_name>.siffletdata.com. Sifflet "
    "Backend URL is https://<tenant_name>api.siffletdata.com. For instance, if you access to Sifflet UI with "
    "https://mycompany.siffletdata.com, then your tenant would be mycompany",
)
@optgroup.option(
    "--backend-url",
    help="For self-hosted deployment, full URL to the Sifflet backend on your deployment including for instance: "
    "https://sifflet-backend.mycompany.com",
)
@click.option(
    "--token",
    prompt="API access token",
    help="The access token must be generated in the Web UI of Sifflet Settings > Access-Tokens",
)
def configure(
    token: Optional[str] = None,
    tenant: Optional[str] = None,
    backend_url: Optional[str] = None,
):
    """Configure sifflet variables"""
    service = ConfigureService()
    service.configure(tenant, backend_url, token)
