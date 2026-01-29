"""Joblet client for running jobs on a server."""

from typing import Any, Dict, Optional

import grpc

from .config import (
    AWSParameterStoreProvider,
    AWSSecretsManagerProvider,
    ConfigLoader,
    EnvironmentCertProvider,
)
from .exceptions import JobletConnectionError
from .services import (
    JobService,
    MonitoringService,
    NetworkService,
    RuntimeService,
    VolumeService,
)


class JobletClient:
    """Client for connecting to a Joblet server.

    Loads config from various sources (in order of precedence):
    1. Explicit parameters passed to constructor
    2. AWS Secrets Manager (if aws_secret_name or aws_secret_prefix specified)
    3. AWS Parameter Store (if aws_ssm_prefix specified)
    4. Environment variables (JOBLET_CA_CERT, JOBLET_CLIENT_CERT, JOBLET_CLIENT_KEY)
    5. Config file (~/.rnx/rnx-config.yml)

    Use with 'with' statement for automatic cleanup.
    """

    def __init__(
        self,
        ca_cert_path: Optional[str] = None,
        client_cert_path: Optional[str] = None,
        client_key_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        node_name: str = "default",
        # AWS Secrets Manager options
        aws_secret_name: Optional[str] = None,
        aws_secret_prefix: Optional[str] = None,
        # AWS Parameter Store options
        aws_ssm_prefix: Optional[str] = None,
        # AWS common options
        aws_region: Optional[str] = None,
    ):
        """Connect to Joblet server with mTLS.

        Joblet always requires mTLS authentication. Certificates can be provided
        from multiple sources (checked in order):

        1. Explicit file paths (ca_cert_path, client_cert_path, client_key_path)
        2. AWS Secrets Manager (aws_secret_name or aws_secret_prefix)
        3. AWS Parameter Store (aws_ssm_prefix)
        4. Environment variables (JOBLET_CA_CERT, JOBLET_CLIENT_CERT, JOBLET_CLIENT_KEY)
        5. Config file (~/.rnx/rnx-config.yml)

        Args:
            host: Server hostname (optional if using config/AWS/env)
            port: Server port (optional if using config/AWS/env)
            ca_cert_path: CA certificate path
            client_cert_path: Client certificate path
            client_key_path: Client private key path
            options: Extra gRPC options
            config_path: Config file path (default: ~/.rnx/rnx-config.yml)
            node_name: Config node to use (default: "default")
            aws_secret_name: AWS Secrets Manager secret name (JSON with ca/cert/key)
            aws_secret_prefix: AWS Secrets Manager prefix for separate secrets
            aws_ssm_prefix: AWS Parameter Store prefix (e.g., "/joblet/certs")
            aws_region: AWS region (uses default if not specified)

        Examples:
            # Direct file paths (VM/on-premise)
            client = JobletClient(
                host="server", port=50051,
                ca_cert_path="/path/to/ca.pem",
                client_cert_path="/path/to/client.pem",
                client_key_path="/path/to/client.key"
            )

            # AWS Secrets Manager (single secret with JSON)
            client = JobletClient(
                host="server", port=50051,
                aws_secret_name="joblet/certs",
                aws_region="us-east-1"
            )

            # AWS Secrets Manager (separate secrets)
            client = JobletClient(
                host="server", port=50051,
                aws_secret_prefix="joblet/",  # Uses joblet/ca, joblet/cert, joblet/key
                aws_region="us-east-1"
            )

            # AWS Parameter Store
            client = JobletClient(
                host="server", port=50051,
                aws_ssm_prefix="/joblet/certs",
                aws_region="us-east-1"
            )

            # Environment variables
            # (set JOBLET_CA_CERT, JOBLET_CLIENT_CERT, JOBLET_CLIENT_KEY)
            client = JobletClient(host="server", port=50051)

            # Config file (default: ~/.rnx/rnx-config.yml)
            client = JobletClient()
        """
        self._config_loader: Optional[ConfigLoader] = None
        self._env_provider: Optional[EnvironmentCertProvider] = None
        self._aws_secrets_provider: Optional[AWSSecretsManagerProvider] = None
        self._aws_ssm_provider: Optional[AWSParameterStoreProvider] = None
        self._aws_secrets_error: Optional[str] = None
        self._aws_ssm_error: Optional[str] = None
        node_id = None

        # Try to load certificates from various sources if not all provided explicitly
        if not all([host, port, ca_cert_path, client_cert_path, client_key_path]):

            # Source 1: AWS Secrets Manager
            if (aws_secret_name or aws_secret_prefix) and not all(
                [ca_cert_path, client_cert_path, client_key_path]
            ):
                self._aws_secrets_provider = AWSSecretsManagerProvider(
                    secret_name=aws_secret_name,
                    secret_prefix=aws_secret_prefix,
                    region_name=aws_region,
                )
                try:
                    aws_info = self._aws_secrets_provider.load()
                    if aws_info:
                        host = host or aws_info.get("host")
                        port = port or aws_info.get("port")
                        ca_cert_path = ca_cert_path or aws_info.get("ca_cert_path")
                        client_cert_path = client_cert_path or aws_info.get(
                            "client_cert_path"
                        )
                        client_key_path = client_key_path or aws_info.get(
                            "client_key_path"
                        )
                except ImportError:
                    raise  # Re-raise ImportError so user knows boto3 is missing
                except Exception as e:
                    # Store error for better final error message
                    self._aws_secrets_error = str(e)

            # Source 2: AWS Parameter Store
            if aws_ssm_prefix and not all(
                [ca_cert_path, client_cert_path, client_key_path]
            ):
                self._aws_ssm_provider = AWSParameterStoreProvider(
                    parameter_prefix=aws_ssm_prefix,
                    region_name=aws_region,
                )
                try:
                    ssm_info = self._aws_ssm_provider.load()
                    if ssm_info:
                        host = host or ssm_info.get("host")
                        port = port or ssm_info.get("port")
                        ca_cert_path = ca_cert_path or ssm_info.get("ca_cert_path")
                        client_cert_path = client_cert_path or ssm_info.get(
                            "client_cert_path"
                        )
                        client_key_path = client_key_path or ssm_info.get(
                            "client_key_path"
                        )
                except ImportError:
                    raise  # Re-raise ImportError so user knows boto3 is missing
                except Exception as e:
                    # Store error for better final error message
                    self._aws_ssm_error = str(e)

            # Source 3: Environment variables
            if not all([ca_cert_path, client_cert_path, client_key_path]):
                self._env_provider = EnvironmentCertProvider()
                env_info = self._env_provider.load()
                if env_info:
                    host = host or env_info.get("host")
                    port = port or env_info.get("port")
                    ca_cert_path = ca_cert_path or env_info.get("ca_cert_path")
                    client_cert_path = client_cert_path or env_info.get(
                        "client_cert_path"
                    )
                    client_key_path = client_key_path or env_info.get("client_key_path")

            # Source 4: Config file
            if not all([ca_cert_path, client_cert_path, client_key_path]):
                self._config_loader = ConfigLoader(config_path)
                if self._config_loader.load():
                    config_info = self._config_loader.extract_connection_info(node_name)
                    if config_info:
                        host = host or config_info.get("host")
                        port = port or config_info.get("port")
                        ca_cert_path = ca_cert_path or config_info.get("ca_cert_path")
                        client_cert_path = client_cert_path or config_info.get(
                            "client_cert_path"
                        )
                        client_key_path = client_key_path or config_info.get(
                            "client_key_path"
                        )
                        node_id = config_info.get("node_id")

        # Validate that we have all required parameters
        if not all([host, port, ca_cert_path, client_cert_path, client_key_path]):
            missing = []
            if not host:
                missing.append("host")
            if not port:
                missing.append("port")
            if not ca_cert_path:
                missing.append("ca_cert_path")
            if not client_cert_path:
                missing.append("client_cert_path")
            if not client_key_path:
                missing.append("client_key_path")
            # Build detailed error message with source-specific errors
            error_details = []
            if self._aws_secrets_error:
                error_details.append(
                    f"AWS Secrets Manager failed: {self._aws_secrets_error}"
                )
            if self._aws_ssm_error:
                error_details.append(
                    f"AWS Parameter Store failed: {self._aws_ssm_error}"
                )

            error_msg = (
                f"Missing required parameters: {', '.join(missing)}. "
                f"Provide certificates via one of: "
                f"(1) explicit paths, "
                f"(2) aws_secret_name/aws_secret_prefix, "
                f"(3) aws_ssm_prefix, "
                f"(4) environment variables (JOBLET_*_CERT, JOBLET_*_KEY), "
                f"(5) config file (~/.rnx/rnx-config.yml)."
            )

            if error_details:
                error_msg += "\n\nSource errors:\n- " + "\n- ".join(error_details)

            raise ValueError(error_msg)

        # Store connection parameters
        self.host = host
        self.port = port
        self.ca_cert_path = ca_cert_path
        self.client_cert_path = client_cert_path
        self.client_key_path = client_key_path
        self._channel: Optional[grpc.Channel] = None
        self._options = options or {}

        # Services - created when first used
        self._job_service: Optional[JobService] = None
        self._network_service: Optional[NetworkService] = None
        self._volume_service: Optional[VolumeService] = None
        self._monitoring_service: Optional[MonitoringService] = None
        self._runtime_service: Optional[RuntimeService] = None
        self._node_id = node_id

        # Connect now
        self._connect()

    def _connect(self) -> None:
        """Connect to server with mTLS authentication."""
        target = f"{self.host}:{self.port}"

        try:
            # Add default gRPC options
            default_options = [
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 5000),
                ("grpc.keepalive_permit_without_calls", True),
                ("grpc.http2.max_pings_without_data", 0),
                ("grpc.http2.min_ping_interval_without_data_ms", 300000),
                ("grpc.http2.min_time_between_pings_ms", 10000),
            ]

            # Merge with user options
            all_options = default_options + list(self._options.items())

            # Load certificates - validate paths are set
            # These should always be set after __init__ validation, but we check
            # defensively since assertions can be disabled with -O flag
            if self.ca_cert_path is None:
                raise ValueError("ca_cert_path must be set before connecting")
            if self.client_cert_path is None:
                raise ValueError("client_cert_path must be set before connecting")
            if self.client_key_path is None:
                raise ValueError("client_key_path must be set before connecting")

            try:
                with open(self.ca_cert_path, "rb") as f:
                    ca_cert = f.read()
                with open(self.client_cert_path, "rb") as f:
                    client_cert = f.read()
                with open(self.client_key_path, "rb") as f:
                    client_key = f.read()
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Certificate file not found: {e.filename}")
            except Exception as e:
                raise ValueError(f"Failed to read certificates: {e}")

            # Validate certificates are not empty
            if not ca_cert:
                raise ValueError(f"Empty CA certificate: {self.ca_cert_path}")
            if not client_cert:
                raise ValueError(f"Empty client certificate: {self.client_cert_path}")
            if not client_key:
                raise ValueError(f"Empty client key: {self.client_key_path}")

            # Validate certificate format
            if b"BEGIN CERTIFICATE" not in ca_cert:
                raise ValueError(f"Invalid CA certificate format: {self.ca_cert_path}")
            if b"BEGIN CERTIFICATE" not in client_cert:
                raise ValueError(
                    f"Invalid client certificate format: {self.client_cert_path}"
                )
            if b"BEGIN" not in client_key or b"PRIVATE KEY" not in client_key:
                raise ValueError(f"Invalid client key format: {self.client_key_path}")

            # Setup mTLS with custom root certificate
            # Trust only our CA, not system CAs
            credentials = grpc.ssl_channel_credentials(
                root_certificates=ca_cert,  # Use ONLY our CA cert
                private_key=client_key,
                certificate_chain=client_cert,
            )

            self._channel = grpc.secure_channel(
                target, credentials, options=all_options
            )

        except (FileNotFoundError, ValueError) as e:
            raise e
        except Exception as e:
            raise JobletConnectionError(f"Can't connect to {target}: {e}")

    def close(self) -> None:
        """
        Close the connection to the Joblet server and clean up resources.

        This method should be called when you're done using the client to
        ensure proper cleanup of network resources. If using the client as
        a context manager, this is called automatically.

        Note:
            After calling close(), the client should not be used for further
            operations. Create a new client instance if needed.
        """
        if self._channel:
            self._channel.close()
            self._channel = None

        # Clean up all certificate providers and temporary files
        if self._config_loader:
            self._config_loader.cleanup()
        if self._env_provider:
            self._env_provider.cleanup()
        if self._aws_secrets_provider:
            self._aws_secrets_provider.cleanup()
        if self._aws_ssm_provider:
            self._aws_ssm_provider.cleanup()

    def __enter__(self) -> "JobletClient":
        """
        Context manager entry point.

        Returns:
            JobletClient: Self, to allow usage in 'with' statements.
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Context manager exit point.

        Automatically closes the connection when exiting the 'with' block,
        ensuring proper cleanup regardless of how the block exits.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        self.close()

    @property
    def jobs(self) -> JobService:
        """
        Access the Job Service for managing jobs.

        The JobService provides methods for running jobs, monitoring execution
        status, streaming logs, and handling job lifecycle operations like
        stopping and deletion.

        Returns:
            JobService: A service instance for job operations.

        Example:
            >>> with JobletClient() as client:
            ...     # Run a simple job
            ...     job = client.jobs.run_job(command="echo", args=["Hello"])
            ...
            ...     # Monitor the job
            ...     status = client.jobs.get_job_status(job['job_uuid'])
            ...     print(f"Job status: {status['status']}")
        """
        if not self._job_service:
            if self._channel is None:
                raise JobletConnectionError("Client is not connected to server")
            self._job_service = JobService(self._channel)
        return self._job_service

    @property
    def networks(self) -> NetworkService:
        """
        Access the Network Service for managing isolated networks.

        The NetworkService allows you to create, list, and remove virtual networks
        that provide isolated communication environments for your jobs. This is
        useful for multi-container applications or when you need network isolation.

        Returns:
            NetworkService: A service instance for network operations.

        Example:
            >>> with JobletClient() as client:
            ...     # Create a new network
            ...     network = client.networks.create_network(
            ...         name="my-app-network",
            ...         cidr="10.0.1.0/24"
            ...     )
            ...     print(f"Created network: {network['name']}")
        """
        if not self._network_service:
            if self._channel is None:
                raise JobletConnectionError("Client is not connected to server")
            self._network_service = NetworkService(self._channel)
        return self._network_service

    @property
    def volumes(self) -> VolumeService:
        """
        Access the Volume Service for managing persistent storage.

        The VolumeService enables creation and management of storage volumes
        that can be mounted into jobs for persistent data storage. Supports
        both filesystem and memory-based volumes with configurable sizes.

        Returns:
            VolumeService: A service instance for volume operations.

        Example:
            >>> with JobletClient() as client:
            ...     # Create a persistent volume
            ...     volume = client.volumes.create_volume(
            ...         name="data-storage",
            ...         size="5GB",
            ...         volume_type="filesystem"
            ...     )
            ...     print(f"Volume path: {volume['path']}")
        """
        if not self._volume_service:
            if self._channel is None:
                raise JobletConnectionError("Client is not connected to server")
            self._volume_service = VolumeService(self._channel)
        return self._volume_service

    @property
    def monitoring(self) -> MonitoringService:
        """
        Access the Monitoring Service for system health and metrics.

        The MonitoringService provides real-time system status information,
        streaming metrics for CPU, memory, disk, and network usage, and overall
        system health monitoring capabilities.

        Returns:
            MonitoringService: A service instance for monitoring operations.

        Example:
            >>> with JobletClient() as client:
            ...     # Get current system status
            ...     status = client.monitoring.get_system_status()
            ...     print(f"CPU usage: {status['cpu']['usage_percent']:.1f}%")
            ...
            ...     # Stream real-time metrics
            ...     for metrics in client.monitoring.stream_system_metrics():
            ...         print(f"Memory: {metrics['memory']['usage_percent']:.1f}%")
        """
        if not self._monitoring_service:
            if self._channel is None:
                raise JobletConnectionError("Client is not connected to server")
            self._monitoring_service = MonitoringService(self._channel)
        return self._monitoring_service

    @property
    def runtimes(self) -> RuntimeService:
        """
        Access the Runtime Service for managing execution environments.

        The RuntimeService handles installation, testing, and management of
        runtime environments (like Python, Node.js, Go, etc.) that jobs can
        execute within. Supports installation from GitHub repositories and
        local sources.

        Returns:
            RuntimeService: A service instance for runtime operations.

        Example:
            >>> with JobletClient() as client:
            ...     # List available runtimes
            ...     runtimes = client.runtimes.list_runtimes()
            ...     for runtime in runtimes:
            ...         print(f"- {runtime['name']}: {runtime['language']}")
            ...
            ...     # Test a specific runtime
            ...     result = client.runtimes.test_runtime("python:3.11")
            ...     print(
            ...         f"Runtime test: {'passed' if result['success'] else 'failed'}"
            ...     )
        """
        if not self._runtime_service:
            if self._channel is None:
                raise JobletConnectionError("Client is not connected to server")
            self._runtime_service = RuntimeService(self._channel)
        return self._runtime_service

    @property
    def node_id(self) -> Optional[str]:
        """
        Get the node ID from configuration.

        Returns:
            Optional[str]: The node ID if configured, None otherwise.

        Example:
            >>> with JobletClient() as client:
            ...     if client.node_id:
            ...         print(f"Connected to node: {client.node_id}")
        """
        return self._node_id

    def health_check(self) -> bool:
        """
        Perform a health check to verify server connectivity and availability.

        This method attempts to connect to the Joblet server and retrieve basic
        system status information. It's useful for verifying that the server is
        running and accessible before performing other operations.

        Returns:
            bool: True if the server is healthy and responsive, False otherwise.
                  A False return could indicate network issues, server downtime,
                  authentication problems, or server overload.

        Example:
            >>> client = JobletClient(host="joblet-server.com")
            >>> if client.health_check():
            ...     print("Server is healthy, proceeding with operations")
            ...     jobs = client.jobs.list_jobs()
            ... else:
            ...     print("Server is not available, check connection settings")

        Note:
            This method catches all exceptions and returns False rather than
            raising them, making it safe to use for conditional logic without
            needing exception handling.
        """
        try:
            # Attempt to get system status from the monitoring service
            # This verifies both connectivity and basic server functionality
            status = self.monitoring.get_system_status()
            return bool(status.get("available", False))
        except Exception:
            # Any exception (network, auth, server error) means unhealthy
            return False
