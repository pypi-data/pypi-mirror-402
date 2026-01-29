from .generate_provider import ColorfulTableProvider, WordTableProvider, AddTableProvider
from .template_provider import (
    ProxyModelProvider,
    TableProvider,
    TemplateProvider,
    MergedTableProvider,
    SingleMergedTableProvider,
    ProxyPDFModelProvider,
)
from .providers_config import ProviderRegistry, provider_registration
