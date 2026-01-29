from .wrappers import cached, no_cache
from .namespace import CachingNamespace


# Alias, needed for backward compatibility
Namespace = CachingNamespace
