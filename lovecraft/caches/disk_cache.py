import hashlib
import json
import logging
from typing import Any, Optional, Sequence

import diskcache as dc
from langchain_core.caches import BaseCache
from langchain_core.outputs import Generation
from tenacity import retry, stop_after_attempt

# Configure logging to output to stderr
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[logging.StreamHandler()],  # Specify that logs should be sent to stderr
)
logger = logging.getLogger(__name__)


class DiskCache(BaseCache):
    """Cache that stores things to disk using diskcache."""

    def __init__(self, cache_path="/tmp/openai_cache", retries=3) -> None:
        """Initialize with empty cache."""
        self.cache_path = cache_path
        self.retries = retries
        self._cache: dc.Cache = dc.Cache(self.cache_path)

    @staticmethod
    def get_cache_key(prompt, llm_string, **kwargs):
        """Create a cache key from the prompt + LLM configuration + any additional arguments."""
        request_data = {"prompt": prompt, "llm_string": llm_string, **kwargs}
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()

    @retry(stop=stop_after_attempt(3))  # type: ignore
    def lookup(self, prompt: str, llm_string: str) -> Optional[Sequence[Generation]]:
        """Look up based on prompt."""
        cache_key = self.get_cache_key(prompt, llm_string)
        logger.debug(f"Looking up cache_key: {cache_key}")

        if cache_key in self._cache:
            logger.debug(f"Found cache key: {cache_key}")

            # We need to return a Sequence[Generation]
            gen = Generation(text=self._cache[cache_key])
            return [gen]
        return None

    def update(self, prompt: str, llm_string: str, return_val: Sequence[Generation]) -> None:
        """Update cache based on prompt and llm_string."""
        cache_key = self.get_cache_key(prompt, llm_string)
        self._cache[cache_key] = return_val
        logger.debug(f"Set cache key: {cache_key}")

    def clear(self, **kwargs: Any) -> None:
        """Clear cache."""
        self._cache.clear()
        logger.debug("Cleared cache.")

    async def alookup(self, prompt: str, llm_string: str) -> Optional[Sequence[Generation]]:
        """Look up based on prompt and llm_string."""
        return self.lookup(prompt, llm_string)

    async def aupdate(self, prompt: str, llm_string: str, return_val: Sequence[Generation]) -> None:
        """Update cache based on prompt and llm_string."""
        self.update(prompt, llm_string, return_val)

    async def aclear(self, **kwargs: Any) -> None:
        """Clear cache."""
        self.clear()
