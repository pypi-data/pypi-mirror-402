"""Smart configuration setup for abersetz."""
# this_file: src/abersetz/setup.py

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass, field

import httpx
from loguru import logger
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .config import AbersetzConfig, Credential, EngineConfig, save_config
from .engine_catalog import (
    COMMUNITY_DEEP_TRANSLATOR_PROVIDERS,
    COMMUNITY_TRANSLATOR_PROVIDERS,
    DEEP_TRANSLATOR_FREE_PROVIDERS,
    FREE_TRANSLATOR_PROVIDERS,
    HYSF_DEFAULT_MODEL,
    HYSF_DEFAULT_TEMPERATURE,
    PAID_TRANSLATOR_PROVIDERS,
    collect_deep_translator_providers,
    collect_translator_providers,
    normalize_selector,
)
from .validation import ValidationResult, validate_engines

console = Console()


@dataclass
class DiscoveredProvider:
    """Information about a discovered API provider."""

    name: str
    api_key_env: str
    base_url: str | None = None
    is_available: bool = False
    model_count: int = 0
    error: str | None = None
    engine_names: list[str] = field(default_factory=list)
    pricing_hint: str = "Unknown"


# Provider configuration based on external/dump_models.py patterns
KNOWN_PROVIDERS = [
    # Major providers with translation capabilities
    ("openai", "OPENAI_API_KEY", "https://api.openai.com/v1"),
    ("anthropic", "ANTHROPIC_API_KEY", "https://api.anthropic.com/v1"),
    ("google", "GOOGLE_API_KEY", None),  # For Google Translate via translators
    ("deepl", "DEEPL_API_KEY", None),  # For DeepL via deep-translator
    ("microsoft", "MICROSOFT_TRANSLATOR_KEY", None),  # For Microsoft Translator
    # Alternative LLM providers
    ("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1"),
    ("mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1"),
    ("deepseek", "DEEPSEEK_API_KEY", "https://api.deepseek.com/v1"),
    ("togetherai", "TOGETHERAI_API_KEY", "https://api.together.xyz/v1"),
    ("siliconflow", "SILICONFLOW_API_KEY", "https://api.siliconflow.com/v1"),
    ("deepinfra", "DEEPINFRA_API_KEY", "https://api.deepinfra.com/v1/openai"),
    ("fireworks", "FIREWORKS_API_KEY", "https://api.fireworks.ai/inference/v1"),
    ("sambanova", "SAMBANOVA_API_KEY", "https://api.sambanova.ai/v1"),
    ("cerebras", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1"),
    ("hyperbolic", "HYPERBOLIC_API_KEY", "https://api.hyperbolic.xyz/v1"),
    ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
]

PROVIDER_METADATA: dict[str, dict[str, str]] = {
    # Pricing summaries sourced from provider documentation snapshots under external/
    "openai": {"pricing": "Usage-based billing"},
    "anthropic": {"pricing": "Usage-based billing"},
    "google": {"pricing": "Community/free via translators; Cloud API is paid"},
    "deepl": {"pricing": "Paid with limited free tier"},
    "microsoft": {"pricing": "Paid (Azure Cognitive Services)"},
    "groq": {"pricing": "Free tier available; paid for higher quotas"},
    "mistral": {"pricing": "Free community tier; paid enterprise plans"},
    "deepseek": {"pricing": "Free research access; usage caps apply"},
    "togetherai": {"pricing": "Usage-based aggregation"},
    "siliconflow": {"pricing": "Free tier available"},
    "deepinfra": {"pricing": "Usage-based aggregation"},
    "fireworks": {"pricing": "Usage-based billing"},
    "sambanova": {"pricing": "Paid enterprise plans"},
    "cerebras": {"pricing": "Free tier available"},
    "hyperbolic": {"pricing": "Usage-based with free tier"},
    "openrouter": {"pricing": "Usage-based marketplace"},
}


class SetupWizard:
    """Interactive setup wizard for abersetz configuration."""

    def __init__(
        self,
        non_interactive: bool = False,
        verbose: bool = False,
        include_community: bool = False,
    ):
        self.non_interactive = non_interactive
        self.verbose = verbose
        self.include_community = include_community
        self.discovered_providers: list[DiscoveredProvider] = []
        self.validation_results: list[ValidationResult] | None = None

    def run(self) -> bool:
        """Run the setup wizard."""
        if not self.non_interactive:
            console.print("\n[bold cyan]🔧 Abersetz Configuration Setup[/bold cyan]\n")
            console.print("Scanning environment for API keys and endpoints...\n")

        # Phase 1: Discover providers
        self._discover_providers()

        # Phase 2: Test endpoints
        if self.discovered_providers:
            self._test_endpoints()

        # Phase 3: Display results
        if not self.non_interactive:
            self._display_results()

        # Phase 4: Generate configuration
        config = self._generate_config()

        # Phase 5: Save configuration
        if config:
            save_config(config)
            self._validate_config(config)
            config_path = os.path.join(
                os.path.expanduser("~"), "Library", "Application Support", "abersetz", "config.toml"
            )
            if not self.non_interactive:
                console.print(f"\n[green]✓[/green] Configuration saved to: {config_path}")
                console.print("\n[bold]You can now use abersetz to translate files![/bold]")
                console.print("\nExample: [cyan]abersetz tr es document.txt[/cyan]")
            return True

        if not self.non_interactive:
            console.print("\n[yellow]⚠[/yellow] No API keys found in environment.")
            console.print("\nTo use abersetz, you need to set up at least one API key:")
            console.print("  • export OPENAI_API_KEY=your-key")
            console.print("  • export ANTHROPIC_API_KEY=your-key")
            console.print("  • export SILICONFLOW_API_KEY=your-key")
            console.print("  • export GOOGLE_API_KEY=your-key (for Google Translate)")
            console.print("  • export DEEPL_API_KEY=your-key (for DeepL)")

        return False

    def _validate_config(self, config: AbersetzConfig) -> None:
        """Run validation after configuration is saved."""

        results = validate_engines(config, include_defaults=True)
        self.validation_results = results

        if not results:
            return

        failures = [item for item in results if not item.success]

        if not self.non_interactive:
            console.print("\n[bold cyan]Validating configured engines...\n")
            table = Table(title="Validation Summary")
            table.add_column("Selector", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Latency (s)", justify="right")
            table.add_column("Error", style="red")

            for item in results:
                status = "✓" if item.success else "✗"
                latency = f"{item.latency:.2f}"
                error_message = item.error or ""
                table.add_row(item.selector, status, latency, error_message)

            console.print(table)

        for item in failures:
            logger.warning("Validation failed for %s: %s", item.selector, item.error)

    def _discover_providers(self) -> None:
        """Scan environment for API keys."""
        for name, env_key, base_url in KNOWN_PROVIDERS:
            api_key = os.environ.get(env_key)
            if api_key:
                provider = DiscoveredProvider(
                    name=name,
                    api_key_env=env_key,
                    base_url=base_url,
                    is_available=True,
                )
                metadata = PROVIDER_METADATA.get(name, {})
                provider.pricing_hint = metadata.get("pricing", "Unknown")

                # Map to available engines
                if name in ["google", "microsoft"]:
                    provider.engine_names.append(str(normalize_selector(f"translators/{name}")))
                if name == "deepl":
                    provider.engine_names.append(str(normalize_selector("deep-translator/deepl")))
                if name in ["openai", "anthropic"]:
                    provider.engine_names.append(str(normalize_selector("ullm/default")))
                if name == "siliconflow":
                    provider.engine_names.extend(
                        [
                            str(normalize_selector("hysf")),
                            str(normalize_selector("ullm/default")),
                        ]
                    )
                if base_url and "openai" in base_url:
                    # OpenAI-compatible endpoints
                    provider.engine_names.append(str(normalize_selector(f"ullm/{name}")))

                self.discovered_providers.append(provider)

                if self.verbose:
                    logger.debug(f"Found {name} API key in {env_key}")

    def _test_endpoints(self) -> None:
        """Test discovered endpoints with lightweight API calls."""
        if not self.non_interactive:
            console.print("Testing discovered services...\n")

        with Progress(transient=True, disable=self.non_interactive) as progress:
            task = progress.add_task(
                "[cyan]Validating endpoints...", total=len(self.discovered_providers)
            )

            for provider in self.discovered_providers:
                if provider.base_url:
                    self._test_single_endpoint(provider)
                else:
                    # Non-API providers (translators/deep-translator)
                    provider.is_available = True
                    provider.model_count = 1  # Placeholder

                progress.update(task, advance=1)

    def _test_single_endpoint(self, provider: DiscoveredProvider) -> None:
        """Test a single API endpoint."""
        if not provider.base_url:
            return

        api_key = os.environ.get(provider.api_key_env, "")

        try:
            # Test with a simple models endpoint
            models_url = f"{provider.base_url.rstrip('/')}/models"
            headers = {}

            if provider.name == "anthropic":
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                }
            else:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                }

            with httpx.Client(timeout=5.0) as client:
                response = client.get(models_url, headers=headers)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and "data" in data:
                            provider.model_count = len(data["data"])
                        elif isinstance(data, list):
                            provider.model_count = len(data)
                        else:
                            provider.model_count = 1
                        provider.is_available = True
                    except Exception:
                        # API works but response format unknown
                        provider.is_available = True
                        provider.model_count = 1
                else:
                    provider.is_available = False
                    provider.error = f"HTTP {response.status_code}"

        except httpx.ConnectError:
            provider.is_available = False
            provider.error = "Connection failed"
        except httpx.TimeoutException:
            provider.is_available = False
            provider.error = "Timeout"
        except Exception as e:
            provider.is_available = False
            provider.error = str(e)[:50]

        if self.verbose:
            if provider.is_available:
                logger.debug(f"✓ {provider.name}: {provider.model_count} models")
            else:
                logger.debug(f"✗ {provider.name}: {provider.error}")

    def _display_results(self) -> None:
        """Display discovered providers in a table."""
        if not self.discovered_providers:
            return

        table = Table(title="Discovered Translation Services")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Engines", style="yellow")
        table.add_column("Pricing", style="magenta")
        table.add_column("Models", justify="right")

        for provider in self.discovered_providers:
            status = (
                "[green]✓ Available[/green]"
                if provider.is_available
                else f"[red]✗ {provider.error or 'Failed'}[/red]"
            )
            engines = ", ".join(provider.engine_names) if provider.engine_names else "N/A"
            models = str(provider.model_count) if provider.model_count > 0 else "-"

            table.add_row(
                provider.name.capitalize(),
                status,
                engines,
                provider.pricing_hint,
                models,
            )

        console.print(table)

    def _generate_config(self) -> AbersetzConfig | None:
        """Generate configuration from discovered providers."""
        if not self.discovered_providers:
            return None

        config = AbersetzConfig()

        # Add credentials
        credentials = {}
        for provider in self.discovered_providers:
            if provider.is_available:
                credentials[provider.name] = Credential(
                    name=provider.name,
                    env=provider.api_key_env,
                )

        config.credentials = credentials

        # Set up engines based on discovered providers
        engines = {}

        # Configure translators engines with maximum free coverage
        translator_providers = collect_translator_providers(include_paid=False)
        if not translator_providers:
            translator_providers = list(FREE_TRANSLATOR_PROVIDERS)

        premium_translators: list[str] = []
        for provider in self.discovered_providers:
            if provider.is_available and provider.name in PAID_TRANSLATOR_PROVIDERS:
                premium_translators.append(provider.name)
        for item in premium_translators:
            if item not in translator_providers:
                translator_providers.append(item)

        if not self.include_community:
            translator_providers = [
                item
                for item in translator_providers
                if item not in COMMUNITY_TRANSLATOR_PROVIDERS
            ]

        if translator_providers:
            engines["translators"] = EngineConfig(
                name="translators",
                chunk_size=800,
                options={
                    "provider": translator_providers[0],
                    "providers": translator_providers,
                },
            )

        # Configure deep-translator engines (free first, add premium if keys present)
        deep_providers = collect_deep_translator_providers(include_paid=False)
        if not deep_providers:
            deep_providers = list(DEEP_TRANSLATOR_FREE_PROVIDERS)

        premium_deep_map = {
            "deepl": "deepl",
            "microsoft": "microsoft",
        }
        for provider in self.discovered_providers:
            alias = premium_deep_map.get(provider.name)
            if alias and provider.is_available and alias not in deep_providers:
                deep_providers.append(alias)

        if not self.include_community:
            deep_providers = [
                item
                for item in deep_providers
                if item not in COMMUNITY_DEEP_TRANSLATOR_PROVIDERS
            ]

        if deep_providers:
            engines["deep-translator"] = EngineConfig(
                name="deep-translator",
                chunk_size=800,
                options={
                    "provider": deep_providers[0],
                    "providers": deep_providers,
                },
            )

        # Configure LLM engines
        siliconflow_available = any(
            p.name == "siliconflow" and p.is_available for p in self.discovered_providers
        )

        if siliconflow_available:
            engines["hysf"] = EngineConfig(
                name="hysf",
                chunk_size=2400,
                credential=Credential(name="siliconflow"),
                options={
                    "base_url": "https://api.siliconflow.com/v1",
                    "model": HYSF_DEFAULT_MODEL,
                    "temperature": HYSF_DEFAULT_TEMPERATURE,
                },
            )

            engines["ullm"] = EngineConfig(
                name="ullm",
                chunk_size=2400,
                credential=Credential(name="siliconflow"),
                options={
                    "profiles": {
                        "default": {
                            "base_url": "https://api.siliconflow.com/v1",
                            "model": HYSF_DEFAULT_MODEL,
                            "temperature": HYSF_DEFAULT_TEMPERATURE,
                            "max_input_tokens": 32000,
                            "prolog": {},
                        }
                    }
                },
            )

        # Add OpenAI if available
        openai_available = any(
            p.name == "openai" and p.is_available for p in self.discovered_providers
        )
        if openai_available and "ullm" not in engines:
            engines["ullm"] = EngineConfig(
                name="ullm",
                chunk_size=2400,
                credential=Credential(name="openai"),
                options={
                    "profiles": {
                        "default": {
                            "base_url": "https://api.openai.com/v1",
                            "model": "gpt-4o-mini",
                            "temperature": 0.9,
                            "max_input_tokens": 16000,
                            "prolog": {},
                        }
                    }
                },
            )

        config.engines = engines

        # Set default engine based on priority
        default_engine = _select_default_engine(engines, self.discovered_providers)
        if default_engine:
            config.defaults.engine = default_engine

        return config


def _select_default_engine(
    engines: dict[str, EngineConfig],
    providers: Sequence[DiscoveredProvider],
) -> str | None:
    """Choose the default engine based on configured priorities."""
    if "deep-translator" in engines and any(
        provider.name == "deepl" and provider.is_available for provider in providers
    ):
        return "deep-translator/deepl"
    if "translators" in engines:
        return "tr/google"
    if "hysf" in engines:
        return "hysf"
    if "ullm" in engines:
        return "ullm/default"
    if engines:
        return next(iter(engines))
    return None


def setup_command(
    non_interactive: bool = False,
    verbose: bool = False,
    include_community: bool = False,
) -> None:
    """Run the abersetz setup wizard.

    Args:
        non_interactive: Run without user interaction (for CI/automation)
        verbose: Enable verbose output with detailed logging
        include_community: Include community/self-hosted providers in defaults
    """
    wizard = SetupWizard(
        non_interactive=non_interactive,
        verbose=verbose,
        include_community=include_community,
    )
    success = wizard.run()

    if not success and non_interactive:
        # Exit with error code in non-interactive mode
        import sys

        sys.exit(1)
