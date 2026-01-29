import os
import shutil
from typing import Optional

from .const import ALLUXIO_REQUEST_MAX_RETRIES
from .const import ALLUXIO_REQUEST_MAX_TIMEOUT_SECONDS
from .const import ALLUXIO_WORKER_HTTP_SERVER_PORT_DEFAULT_VALUE
from .const import ALLUXIO_WORKER_S3_SERVER_PORT_DEFAULT_VALUE


class AlluxioClientConfig:
    """
    Class responsible for creating the configuration for Alluxio Client.
    """

    def __init__(
        self,
        load_balance_domain: str = "localhost",
        worker_hosts: Optional[str] = None,
        worker_http_port: int = ALLUXIO_WORKER_HTTP_SERVER_PORT_DEFAULT_VALUE,
        worker_data_port: int = ALLUXIO_WORKER_S3_SERVER_PORT_DEFAULT_VALUE,
        fallback_to_ufs_enabled: bool = True,
        ufs_info_refresh_interval_minutes: (float, int) = 2,
        log_level: str = "INFO",
        log_dir: str = None,
        log_tag_allowlist: str = None,
        local_cache_dir: str = "/tmp/local_cache/",
        local_cache_enabled: bool = False,
        local_cache_prefetch_ahead_blocks: int = 2,
        local_cache_prefetch_concurrency: int = 32,
        local_cache_size_gb: (float, int) = 64,
        local_cache_block_size_mb: (float, int) = 4,
        local_cache_eviction_high_watermark: float = 0.8,
        local_cache_eviction_low_watermark: float = 0.7,
        local_cache_max_prefetch_blocks: int = 16,
        local_cache_prefetch_policy: str = "adaptive_window",
        local_cache_eviction_scan_interval_minutes: (float, int) = 0.5,
        local_cache_ttl_time_minutes: (float, int) = 10,
        local_cache_metrics_enabled: bool = False,
        use_memory_cache: bool = False,
        memory_cache_size_mb: (float, int) = 256,
        http_max_retries: int = ALLUXIO_REQUEST_MAX_RETRIES,
        http_timeouts: int = ALLUXIO_REQUEST_MAX_TIMEOUT_SECONDS,
        buffered_io_enabled: bool = True,
        read_buffer_size_mb: (float, int) = 0.008,
        **kwargs,
    ):
        """
        Initializes Alluxio client configuration.
        Args:
            worker_hosts (Optional[str], optional): The worker hostnames in 'host1,host2,host3' format.
            concurrency (int, optional): The maximum number of concurrent operations for HTTP requests, default to 64.
            worker_http_port (int, optional): The port of the HTTP server on each Alluxio worker node.
        """
        # Validate that no invalid configuration keys are provided
        valid_config_keys = {
            "load_balance_domain",
            "worker_hosts",
            "worker_http_port",
            "worker_data_port",
            "fallback_to_ufs_enabled",
            "ufs_info_refresh_interval_minutes",
            "log_level",
            "log_dir",
            "log_tag_allowlist",
            "local_cache_dir",
            "local_cache_enabled",
            "local_cache_prefetch_ahead_blocks",
            "local_cache_prefetch_concurrency",
            "local_cache_size_gb",
            "local_cache_block_size_mb",
            "local_cache_eviction_high_watermark",
            "local_cache_eviction_low_watermark",
            "local_cache_max_prefetch_blocks",
            "local_cache_prefetch_policy",
            "local_cache_eviction_scan_interval_minutes",
            "local_cache_ttl_time_minutes",
            "local_cache_metrics_enabled",
            "use_memory_cache",
            "memory_cache_size_mb",
            "http_max_retries",
            "http_timeouts",
            "buffered_io_enabled",
            "read_buffer_size_mb",
            "ufs_config",
            "skip_alluxio",
            "fallback_to_ufs_enabled",
            "test_options",
        }

        if kwargs:
            invalid_keys = set(kwargs.keys()) - valid_config_keys
            if invalid_keys:
                raise ValueError(
                    f"Invalid configuration key(s) provided: {', '.join(sorted(invalid_keys))}. "
                    f"Valid configuration keys are: {', '.join(sorted(valid_config_keys))}"
                )
        assert (
            isinstance(load_balance_domain, str) or load_balance_domain is None
        ), "'load_balance_domain' should be string"

        assert (
            isinstance(worker_hosts, str) or worker_hosts is None
        ), "'worker_hosts' should be string or None"

        assert isinstance(worker_http_port, int) and (
            1 <= worker_http_port <= 65535
        ), "'worker_http_port' should be an integer in the range 1-65535"

        assert isinstance(worker_data_port, int) and (
            1 <= worker_data_port <= 65535
        ), "'worker_data_port' should be an integer in the range 1-65535"

        assert isinstance(
            fallback_to_ufs_enabled, bool
        ), "'fallback_to_ufs_enabled' should be a boolean"

        assert isinstance(log_level, str) and log_level in [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ], "'log_level' should be one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'"

        assert (
            isinstance(log_dir, str) or log_dir is None
        ), "'log_dir' should be a string or None"

        # Create log directory if specified and doesn't exist
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            # Validate write permissions
            test_file = os.path.join(log_dir, f".test_write_{os.getpid()}")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                raise ValueError(
                    f"Log directory '{log_dir}' is not writable: {str(e)}"
                ) from e

        assert (
            isinstance(log_tag_allowlist, str) or log_tag_allowlist is None
        ), "'log_tag_allowlist' should be a string"

        assert isinstance(
            local_cache_enabled, bool
        ), "'local_cache_enabled' should be a boolean"

        assert isinstance(
            local_cache_dir, str
        ), "'local_cache_dir' should be a string"

        assert (
            isinstance(local_cache_prefetch_ahead_blocks, int)
            and 0 <= local_cache_prefetch_ahead_blocks <= 10000
        ), "'local_cache_prefetch_ahead_blocks' should be an integer between 0 and 10000"

        assert (
            isinstance(local_cache_prefetch_concurrency, int)
            and 1 <= local_cache_prefetch_concurrency <= 1000
        ), "'local_cache_prefetch_concurrency' should be an integer between 1 and 1000"

        assert (
            (
                isinstance(local_cache_size_gb, int)
                or isinstance(local_cache_size_gb, float)
            )
            and local_cache_size_gb > 0
            or isinstance(local_cache_size_gb, str)
        ), "'local_cache_size_gb' should be a positive integer or float"

        assert (
            isinstance(local_cache_block_size_mb, int)
            or isinstance(local_cache_block_size_mb, float)
        ) and local_cache_block_size_mb > 0, (
            "'local_cache_block_size_mb' should be a positive integer or float"
        )

        assert isinstance(
            use_memory_cache, bool
        ), "'use_memory_range_cache' should be a boolean"

        assert (
            isinstance(memory_cache_size_mb, int)
            or isinstance(memory_cache_size_mb, float)
        ) and memory_cache_size_mb > 0, "'memory_range_cache_size_mb' should be a positive integer or float"

        assert (
            isinstance(http_max_retries, int) and 0 <= http_max_retries <= 100
        ), "'http_max_retries' should be an integer between 0 and 100"

        assert (
            isinstance(http_timeouts, int) and 0 < http_timeouts <= 3600
        ), "'http_timeouts' should be an integer between 0 and 3600 seconds (1 hour)"

        assert (
            isinstance(read_buffer_size_mb, int)
            or isinstance(read_buffer_size_mb, float)
        ) and 0 < read_buffer_size_mb <= 1024, "'read_buffer_size_mb' should be a positive integer or float between 0 and 1024 (1GB)"

        assert (
            isinstance(local_cache_max_prefetch_blocks, int)
            and local_cache_max_prefetch_blocks >= 0
        ), "'local_cache_max_prefetch_blocks' should be an a non-negative integer"

        assert isinstance(
            local_cache_prefetch_policy, str
        ), "'local_cache_prefetch_policy' should be a string"

        assert (
            isinstance(ufs_info_refresh_interval_minutes, float)
            or isinstance(ufs_info_refresh_interval_minutes, int)
        ) and ufs_info_refresh_interval_minutes > 0, "'ufs_info_refresh_interval_minutes' should be a positive float or integer"

        assert (
            isinstance(local_cache_eviction_high_watermark, float)
            and 0.0 < local_cache_eviction_high_watermark < 1.0
        ), "'local_cache_eviction_high_watermark' should be a float between 1.0 and 1.0"

        assert (
            isinstance(local_cache_eviction_low_watermark, float)
            and 0.0 < local_cache_eviction_low_watermark < 1.0
        ), "'local_cache_eviction_low_watermark' should be a float between 0.0 and 1.0"

        assert (
            local_cache_eviction_high_watermark
            > local_cache_eviction_low_watermark
        ), "'local_cache_eviction_high_watermark' must be greater than 'local_cache_eviction_low_watermark'"

        assert (
            isinstance(
                local_cache_eviction_scan_interval_minutes, (int, float)
            )
            and local_cache_eviction_scan_interval_minutes > 0
        ), "'local_cache_eviction_scan_interval_minutes' should be a positive integer or float"

        assert isinstance(local_cache_ttl_time_minutes, (int, float)) and (
            local_cache_ttl_time_minutes == -1
            or local_cache_ttl_time_minutes > 0
        ), "'local_cache_ttl_time_minutes' should be -1 or a positive integer or float"

        assert isinstance(
            local_cache_metrics_enabled, bool
        ), "'local_cache_metrics_enabled' should be a boolean"

        # Validate disk space for local cache if local cache is enabled
        if local_cache_enabled and not isinstance(local_cache_size_gb, str):
            self._validate_local_cache_disk_space(
                local_cache_dir, local_cache_size_gb
            )

        assert isinstance(
            buffered_io_enabled, bool
        ), "'buffered_io_enabled' should be a boolean"

        assert (
            isinstance(read_buffer_size_mb, int)
            or isinstance(read_buffer_size_mb, float)
        ) and read_buffer_size_mb > 0, (
            "'read_buffer_size_mb' should be a positive integer or float"
        )

        self.load_balance_domain = load_balance_domain
        self.worker_hosts = worker_hosts
        self.worker_http_port = worker_http_port
        self.worker_data_port = worker_data_port
        self.log_level = log_level
        self.log_dir = log_dir
        self.log_tag_allowlist = log_tag_allowlist
        self.local_cache_enabled = local_cache_enabled
        self.local_cache_dir = local_cache_dir
        self.local_cache_prefetch_ahead_blocks = (
            local_cache_prefetch_ahead_blocks
        )
        self.local_cache_prefetch_concurrency = (
            local_cache_prefetch_concurrency
        )
        self.local_cache_size_gb = local_cache_size_gb
        self.local_cache_block_size_mb = local_cache_block_size_mb
        self.local_cache_eviction_high_watermark = (
            local_cache_eviction_high_watermark
        )
        self.local_cache_eviction_low_watermark = (
            local_cache_eviction_low_watermark
        )
        self.local_cache_eviction_scan_interval_minutes = (
            local_cache_eviction_scan_interval_minutes
        )
        self.local_cache_ttl_time_minutes = local_cache_ttl_time_minutes
        self.local_cache_metrics_enabled = local_cache_metrics_enabled
        self.use_memory_cache = use_memory_cache
        self.memory_cache_size_mb = memory_cache_size_mb
        self.http_max_retries = http_max_retries
        self.http_timeouts = http_timeouts
        self.local_cache_max_prefetch_blocks = local_cache_max_prefetch_blocks
        self.local_cache_prefetch_policy = local_cache_prefetch_policy
        self.fallback_to_ufs_enabled = fallback_to_ufs_enabled
        self.ufs_info_refresh_interval_minutes = (
            ufs_info_refresh_interval_minutes
        )
        self.buffered_io_enabled = buffered_io_enabled
        self.read_buffer_size_mb = read_buffer_size_mb

    def _validate_local_cache_disk_space(
        self, cache_dir: str, cache_size_gb: float
    ) -> None:
        """
        Validates that the specified local cache size does not exceed available disk space.

        Args:
            cache_dir (str): The local cache directory path
            cache_size_gb (float): The requested cache size in GB

        Raises:
            ValueError: If cache size exceeds available disk space
        """
        try:
            # Create cache directory if it doesn't exist to check disk space
            os.makedirs(cache_dir, exist_ok=True)

            # Get disk usage statistics
            total, used, free = shutil.disk_usage(cache_dir)

            # Convert bytes to GB
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)

            # Check if requested cache size exceeds free space
            if cache_size_gb > free_gb:
                raise ValueError(
                    f"Local cache size ({cache_size_gb} GB) exceeds available disk space "
                    f"({free_gb:.2f} GB free out of {total_gb:.2f} GB total) in directory '{cache_dir}'. "
                    f"Please reduce 'local_cache_size_gb' to a value less than or equal to {free_gb:.2f} GB."
                )

        except OSError as e:
            raise ValueError(
                f"Unable to validate disk space for local cache directory '{cache_dir}': {str(e)}. "
                f"Please ensure the directory path is valid and accessible."
            ) from e

    def to_dict(self) -> dict:
        """
        Converts the Alluxio client configuration to a dictionary.
        Returns:
            dict: A dictionary representation of the Alluxio client configuration.
        """
        return {
            "load_balance_domain": self.load_balance_domain,
            "worker_hosts": self.worker_hosts,
            "worker_http_port": self.worker_http_port,
            "worker_data_port": self.worker_data_port,
            "fallback_to_ufs_enabled": self.fallback_to_ufs_enabled,
            "ufs_info_refresh_interval_minutes": self.ufs_info_refresh_interval_minutes,
            "log_level": self.log_level,
            "log_dir": self.log_dir,
            "log_tag_allowlist": self.log_tag_allowlist,
            "local_cache_enabled": self.local_cache_enabled,
            "local_cache_dir": self.local_cache_dir,
            "local_cache_prefetch_ahead_blocks": self.local_cache_prefetch_ahead_blocks,
            "local_cache_prefetch_concurrency": self.local_cache_prefetch_concurrency,
            "local_cache_size_gb": self.local_cache_size_gb,
            "local_cache_block_size_mb": self.local_cache_block_size_mb,
            "local_cache_eviction_high_watermark": self.local_cache_eviction_high_watermark,
            "local_cache_eviction_low_watermark": self.local_cache_eviction_low_watermark,
            "local_cache_eviction_scan_interval_minutes": self.local_cache_eviction_scan_interval_minutes,
            "local_cache_ttl_time_minutes": self.local_cache_ttl_time_minutes,
            "local_cache_metrics_enabled": self.local_cache_metrics_enabled,
            "use_memory_cache": self.use_memory_cache,
            "memory_cache_size_mb": self.memory_cache_size_mb,
            "http_max_retries": self.http_max_retries,
            "http_timeouts": self.http_timeouts,
            "local_cache_max_prefetch_blocks": self.local_cache_max_prefetch_blocks,
            "local_cache_prefetch_policy": self.local_cache_prefetch_policy,
            "buffered_io_enabled": self.buffered_io_enabled,
            "read_buffer_size_mb": self.read_buffer_size_mb,
        }
