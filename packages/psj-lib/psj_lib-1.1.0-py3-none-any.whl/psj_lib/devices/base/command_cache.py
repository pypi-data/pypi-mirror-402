"""
Command cache for piezo devices to reduce redundant read operations.
"""

import logging
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class CommandCache:
    """Cache for device command results to minimize redundant communication.
    
    The CommandCache stores results from device read operations and serves cached
    values for subsequent identical queries. This significantly reduces latency in
    applications that repeatedly query device parameters (e.g., GUI monitoring).
    
    Caching Mechanism:
        - Only commands marked as cacheable in the cacheable_commands set are cached
        - Command results are stored by full command string (including parameters)
        - Base command matching allows commands with parameters to match cacheable base commands
          when using a device with multiple channels
        - Cache entries are invalidated on write operations to maintain consistency
    
    When to Use Caching:
        - Single application accessing the device
        - GUI applications with frequent parameter queries
        - Read-heavy operations (monitoring, data visualization)
        - Parameters that change infrequently (configuration values)
    
    When to Disable Caching:
        - Multiple applications accessing the same device simultaneously
        - External software may modify device state (e.g., serial + Telnet access)
        - Real-time monitoring requiring immediate hardware state reflection
        - Debugging scenarios where stale data could mislead
    
    Warning:
        Caching assumes exclusive device access. If other applications can modify
        device state concurrently, disable caching to prevent stale data issues.
    
    Example:
        >>> cache = CommandCache({'notchon', 'monsrc'}, enabled=True)
        >>> cache.set('notchon', ['1'])  # Cache notch filter enable
        >>> result = cache.get('notchon')  # Retrieve from cache
        >>> cache.invalidate('notchon')  # Invalidate after writing
    
    Attributes:
        _cache: Internal dictionary storing command results
        _cacheable_commands: Set of command patterns eligible for caching
        _enabled: Flag controlling whether caching is active
    """
    
    def __init__(self, cacheable_commands: Set[str], enabled: bool = True):
        """Initialize the command cache.

        Args:
            cacheable_commands: Set of base command names eligible for caching.
                Commands are matched against this set both exactly and by base
                name (before the first comma). For example, 'voltage' in this
                set will match both 'voltage' and 'voltage,0,100'.
            enabled: Whether caching is enabled on initialization (default: True).
                Caching can be toggled later via the enabled property.
        
        Example:
            >>> cache = CommandCache({'voltage', 'position', 'status'})
            >>> cache.is_cacheable('voltage')  # True
            >>> cache.is_cacheable('voltage,0')  # True (base command matches)
            >>> cache.is_cacheable('frequency')  # False
        """
        self._cache: Dict[str, list[str]] = {}
        self._cacheable_commands = cacheable_commands
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Returns whether caching is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable caching and clear cache when disabled.
        
        Setting enabled to False automatically clears all cached entries to
        prevent stale data from being served if caching is later re-enabled.
        
        Args:
            value: True to enable caching, False to disable and clear cache
        
        Example:
            >>> cache.enabled = False  # Disables caching and clears all entries
            >>> cache.enabled = True   # Re-enables caching with empty cache
        """
        self._enabled = value
        if not value:
            self.clear()

    def is_cacheable(self, cmd: str) -> bool:
        """Check if a command is eligible for caching.
        
        Commands are cacheable if either:
        1. The exact command string is in the cacheable_commands set, or
        2. The base command (before the first comma) is in the set
        
        This allows parameterized commands to match their base command pattern.
        For example, if 'voltage' is cacheable, then 'voltage,0,100' is also
        cacheable because its base command 'voltage' matches.

        Args:
            cmd: The complete command string to check

        Returns:
            True if the command or its base is in the cacheable commands set
        
        Example:
            >>> cache = CommandCache({'voltage', 'position'})
            >>> cache.is_cacheable('voltage')  # True (exact match)
            >>> cache.is_cacheable('voltage,0')  # True (base command matches)
            >>> cache.is_cacheable('voltage,0,100')  # True (base command matches)
            >>> cache.is_cacheable('frequency')  # False
        """
        # Check exact match
        if cmd in self._cacheable_commands:
            return True

        # Check for base command match (before any commas)
        base_cmd = cmd.split(",")[0]
        return base_cmd in self._cacheable_commands

    def get(self, cmd: str) -> Optional[list[str]]:
        """Retrieve cached response for a command.
        
        Returns the cached result if:
        1. Caching is enabled, and
        2. The command exists in the cache
        
        Otherwise returns None, which signals that the command must be
        executed against the device hardware.
        
        Args:
            cmd: The complete command string (including parameters)
            
        Returns:
            Cached response values as a list of strings if cache hit,
            None if cache miss or caching disabled
        
        Example:
            >>> cache.set('voltage,0', ['12.5', 'V'])
            >>> result = cache.get('voltage,0')  # ['12.5', 'V']
            >>> result = cache.get('voltage,1')  # None (not in cache)
        
        Note:
            Cache hits are logged at DEBUG level for troubleshooting.
        """
        if not self._enabled:
            return None

        if cmd in self._cache:
            logger.debug(f"Cache hit for command: {cmd} -> {self._cache[cmd]}")
            return self._cache[cmd]

        return None

    def set(self, cmd: str, values: list[str]) -> None:
        """Store command response in cache.
        
        Stores the provided values only if:
        1. Caching is enabled, and
        2. The command is marked as cacheable (via is_cacheable check)
        
        Non-cacheable commands are silently ignored to simplify calling code.
        
        Args:
            cmd: The complete command string (including parameters)
            values: The response values returned by the device
        
        Example:
            >>> cache.set('voltage,0', ['12.5', 'V'])  # Stored if voltage is cacheable
            >>> cache.set('trigger,0', ['1'])  # Ignored if trigger not cacheable
        
        Note:
            Cache storage is logged at DEBUG level for troubleshooting.
        """
        if not self._enabled:
            return
            
        if not self.is_cacheable(cmd):
            logger.debug(f"Command {cmd} is not cacheable, skipping cache")
            return
        
        self._cache[cmd] = values
        logger.debug(f"Cached values for {cmd}: {values}")
    
    
    def invalidate(self, cmd: str) -> None:
        """Remove a specific command from the cache.
        
        Invalidation is typically performed after write operations that modify
        device state, ensuring that subsequent reads return fresh hardware values
        rather than stale cached data.
        
        Args:
            cmd: The complete command string to remove from cache
        
        Example:
            >>> cache.set('voltage,0', ['10.0'])
            >>> # ... later, after writing new voltage ...
            >>> cache.invalidate('voltage,0')  # Force re-read on next access
        
        Note:
            If the command is not in the cache, this is a no-op.
        """
        if cmd in self._cache:
            del self._cache[cmd]
            logger.debug(f"Invalidated cache for command: {cmd}")
    
    
    def invalidate_pattern(self, prefix: str) -> None:
        """Invalidate all cached commands matching a prefix pattern.
        
        This is useful when a write operation affects multiple related parameters.
        For example, changing a device mode might invalidate all settings commands
        starting with a common prefix.
        
        Args:
            prefix: Command prefix to match (e.g., 'voltage' matches 'voltage,0',
                'voltage,1', 'voltage,0,max', etc.)
        
        Example:
            >>> # Cache contains: 'voltage,0', 'voltage,1', 'current,0'
            >>> cache.invalidate_pattern('voltage')  # Removes voltage,0 and voltage,1
            >>> cache.invalidate_pattern('voltage,0')  # More specific: removes voltage,0,*
        
        Note:
            Prefix matching is simple string-based (startswith). Invalidated
            commands are logged at DEBUG level.
        """
        invalidated = [cmd for cmd in self._cache.keys() if cmd.startswith(prefix)]
        for cmd in invalidated:
            del self._cache[cmd]
        
        if invalidated:
            logger.debug(f"Invalidated {len(invalidated)} commands with prefix '{prefix}'")
    
    
    def clear(self) -> None:
        """Remove all entries from the cache.
        
        Clearing is performed automatically when caching is disabled, and can
        be called manually when:
        - Device is reset or reconfigured
        - Switching device operation modes
        - Recovering from errors that may have corrupted state
        - Testing scenarios requiring fresh reads
        
        Example:
            >>> cache.clear()  # Empty the cache
            >>> len(cache)  # 0
        """
        self._cache.clear()
        logger.debug("Command cache cleared")
    
    
    def __len__(self) -> int:
        """Return the number of cached command entries.
        
        Returns:
            Number of commands currently stored in the cache
        
        Example:
            >>> cache.set('voltage,0', ['10.0'])
            >>> len(cache)  # 1
        """
        return len(self._cache)
    
    
    def __contains__(self, cmd: str) -> bool:
        """Check if a command has a cached entry.
        
        Args:
            cmd: The command string to check
        
        Returns:
            True if the command is in the cache, False otherwise
        
        Example:
            >>> 'voltage,0' in cache  # True if cached, False otherwise
        """
        return cmd in self._cache
    
    
    def __repr__(self) -> str:
        """Return string representation of cache state.
        
        Returns:
            String showing enabled status and cache size
        
        Example:
            >>> repr(cache)  # 'CommandCache(enabled=True, size=5)'
        """
        return f"CommandCache(enabled={self._enabled}, size={len(self._cache)})"