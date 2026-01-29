"""
Configuration loader for Joblet SDK.

This module handles loading configuration from various sources:
1. Default location: ~/.rnx/rnx-config.yml
2. Custom config file specified by RNX_CONFIG_PATH environment variable
3. Direct parameters passed to the client
4. Environment variables (JOBLET_CA_CERT, JOBLET_CLIENT_CERT, JOBLET_CLIENT_KEY)
5. AWS Secrets Manager
6. AWS Parameter Store (SSM)

The configuration file supports multiple nodes/profiles and includes
connection details and mTLS certificates.
"""

import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import yaml

# Default gRPC port for Joblet server
DEFAULT_PORT = 50051

# Environment variable names for certificate content
ENV_CA_CERT = "JOBLET_CA_CERT"
ENV_CLIENT_CERT = "JOBLET_CLIENT_CERT"
ENV_CLIENT_KEY = "JOBLET_CLIENT_KEY"
ENV_HOST = "JOBLET_HOST"
ENV_PORT = "JOBLET_PORT"


class ConfigLoader:
    """Handles loading and parsing Joblet configuration files."""

    DEFAULT_CONFIG_PATH = Path.home() / ".rnx" / "rnx-config.yml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to configuration file. If not provided,
                        checks RNX_CONFIG_PATH env var, then uses default location.
        """
        if config_path:
            self.config_path = Path(config_path)
        elif os.environ.get("RNX_CONFIG_PATH"):
            self.config_path = Path(os.environ["RNX_CONFIG_PATH"])
        else:
            self.config_path = self.DEFAULT_CONFIG_PATH

        self.config: Optional[Dict] = None
        self._temp_files: List[str] = []

    def load(self) -> bool:
        """
        Load the configuration file.

        Returns:
            bool: True if config was loaded successfully, False otherwise.
        """
        if not self.config_path.exists():
            return False

        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            return True
        except (yaml.YAMLError, IOError):
            return False

    def get_node_config(self, node_name: str = "default") -> Optional[Dict]:
        """
        Get configuration for a specific node.

        Args:
            node_name: Name of the node/profile to retrieve. Defaults to "default".

        Returns:
            Dict containing node configuration or None if not found.
        """
        if not self.config or "nodes" not in self.config:
            return None

        result = self.config["nodes"].get(node_name)
        return cast(Optional[Dict], result)

    def extract_connection_info(self, node_name: str = "default") -> Optional[Dict]:
        """
        Extract connection information from node configuration.

        Args:
            node_name: Name of the node/profile to use.

        Returns:
            Dict with host, port, node_id, and certificate paths, or None if not found.

        Raises:
            ValueError: If required field 'address' is missing.
        """
        node_config = self.get_node_config(node_name)
        if not node_config:
            return None

        # Validate required fields
        if "address" not in node_config:
            raise ValueError(f"Missing required field 'address' in node '{node_name}'")

        # Parse address (host:port)
        address = node_config.get("address", "")
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = DEFAULT_PORT
        else:
            host = address
            port = 50051

        # Get nodeId if present
        node_id = node_config.get("nodeId", "")

        # Create temporary files for certificates if they're embedded
        cert_paths = self._create_cert_files(node_config)
        if not cert_paths:
            return None

        ca_cert_path, client_cert_path, client_key_path = cert_paths

        return {
            "host": host,
            "port": port,
            "node_id": node_id,
            "ca_cert_path": ca_cert_path,
            "client_cert_path": client_cert_path,
            "client_key_path": client_key_path,
        }

    def _create_cert_files(self, node_config: Dict) -> Optional[Tuple[str, str, str]]:
        """
        Create temporary certificate files from embedded certificate strings.

        Args:
            node_config: Node configuration containing certificates.

        Returns:
            Tuple of (ca_cert_path, client_cert_path, client_key_path) or None.
        """
        # Check if we have cert and key in the config
        cert_content = node_config.get("cert")
        key_content = node_config.get("key")

        if not cert_content or not key_content:
            return None

        # Get CA certificate from parent directory or config
        ca_cert_path = None

        # First try to find ca.crt or ca.pem in ~/.rnx/
        rnx_dir = Path.home() / ".rnx"
        for ca_file in ["ca.crt", "ca.pem"]:
            ca_path = rnx_dir / ca_file
            if ca_path.exists():
                ca_cert_path = str(ca_path)
                break

        # If not found, check if it's in the config
        if not ca_cert_path and "ca" in node_config:
            ca_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
            ca_temp.write(node_config["ca"])
            ca_temp.close()
            # Set restrictive permissions (owner read/write only)
            os.chmod(ca_temp.name, stat.S_IRUSR | stat.S_IWUSR)
            ca_cert_path = ca_temp.name
            self._temp_files.append(ca_cert_path)

        if not ca_cert_path:
            return None

        # Create temp files for client cert and key with restrictive permissions
        cert_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        cert_temp.write(cert_content)
        cert_temp.close()
        os.chmod(cert_temp.name, stat.S_IRUSR | stat.S_IWUSR)
        self._temp_files.append(cert_temp.name)

        key_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        key_temp.write(key_content)
        key_temp.close()
        # Private key should be even more restrictive (owner read only)
        os.chmod(key_temp.name, stat.S_IRUSR)
        self._temp_files.append(key_temp.name)

        return ca_cert_path, cert_temp.name, key_temp.name

    def cleanup(self):
        """Clean up temporary certificate files created during configuration loading.

        This method removes temporary files created when certificates were embedded
        in the configuration file. It's automatically called when the client is closed
        or when the object is deleted.
        """
        for temp_file in self._temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        self._temp_files.clear()

    def __del__(self):
        """Cleanup temporary files on deletion."""
        self.cleanup()


class EnvironmentCertProvider:
    """Load certificates from environment variables.

    Environment variables:
        JOBLET_CA_CERT: CA certificate content (PEM format)
        JOBLET_CLIENT_CERT: Client certificate content (PEM format)
        JOBLET_CLIENT_KEY: Client private key content (PEM format)
        JOBLET_HOST: Server hostname (optional)
        JOBLET_PORT: Server port (optional)

    Example:
        export JOBLET_CA_CERT="-----BEGIN CERTIFICATE-----
        ...
        -----END CERTIFICATE-----"
        export JOBLET_CLIENT_CERT="-----BEGIN CERTIFICATE-----
        ...
        -----END CERTIFICATE-----"
        export JOBLET_CLIENT_KEY="-----BEGIN PRIVATE KEY-----
        ...
        -----END PRIVATE KEY-----"
    """

    def __init__(self) -> None:
        self._temp_files: List[str] = []

    def load(self) -> Optional[Dict[str, Any]]:
        """Load certificates from environment variables.

        Returns:
            Dict with host, port, and certificate paths, or None if not configured.
        """
        ca_cert = os.environ.get(ENV_CA_CERT)
        client_cert = os.environ.get(ENV_CLIENT_CERT)
        client_key = os.environ.get(ENV_CLIENT_KEY)

        if not all([ca_cert, client_cert, client_key]):
            return None

        # Type narrowing: after the check above, these are guaranteed to be str
        assert ca_cert is not None
        assert client_cert is not None
        assert client_key is not None

        # Create temporary files for certificates
        ca_path = self._write_temp_cert(ca_cert, "ca")
        cert_path = self._write_temp_cert(client_cert, "cert")
        key_path = self._write_temp_cert(client_key, "key", restricted=True)

        result: Dict[str, Any] = {
            "ca_cert_path": ca_path,
            "client_cert_path": cert_path,
            "client_key_path": key_path,
        }

        # Optionally load host/port from environment
        if os.environ.get(ENV_HOST):
            result["host"] = os.environ.get(ENV_HOST)
        if os.environ.get(ENV_PORT):
            try:
                result["port"] = int(os.environ.get(ENV_PORT, ""))
            except ValueError:
                pass

        return result

    def _write_temp_cert(
        self, content: str, name: str, restricted: bool = False
    ) -> str:
        """Write certificate content to a temporary file."""
        temp = tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{name}.pem", delete=False
        )
        temp.write(content)
        temp.close()

        # Set permissions: restricted (0400) for keys, normal (0600) for certs
        if restricted:
            os.chmod(temp.name, stat.S_IRUSR)
        else:
            os.chmod(temp.name, stat.S_IRUSR | stat.S_IWUSR)

        self._temp_files.append(temp.name)
        return temp.name

    def cleanup(self) -> None:
        """Clean up temporary certificate files."""
        for temp_file in self._temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        self._temp_files.clear()

    def __del__(self) -> None:
        self.cleanup()


class AWSSecretsManagerProvider:
    """Load certificates from AWS Secrets Manager.

    Supports two modes:
    1. Single secret containing JSON with ca, cert, key fields
    2. Separate secrets for each certificate component

    Example (single secret):
        Secret value (JSON):
        {
            "ca": "-----BEGIN CERTIFICATE-----...",
            "cert": "-----BEGIN CERTIFICATE-----...",
            "key": "-----BEGIN PRIVATE KEY-----...",
            "host": "joblet-server.example.com",  # optional
            "port": 50051  # optional
        }

    Example (separate secrets):
        joblet/ca   -> CA certificate content
        joblet/cert -> Client certificate content
        joblet/key  -> Client private key content

    Requires boto3: pip install boto3
    """

    def __init__(
        self,
        secret_name: Optional[str] = None,
        secret_prefix: Optional[str] = None,
        region_name: Optional[str] = None,
    ) -> None:
        """Initialize AWS Secrets Manager provider.

        Args:
            secret_name: Single secret name containing JSON with ca/cert/key
            secret_prefix: Prefix for separate secrets (e.g., "joblet/" for
                          joblet/ca, joblet/cert, joblet/key)
            region_name: AWS region (uses default if not specified)
        """
        self.secret_name = secret_name
        self.secret_prefix = secret_prefix
        self.region_name = region_name
        self._temp_files: List[str] = []
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create boto3 Secrets Manager client."""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for AWS Secrets Manager support. "
                    "Install it with: pip install joblet-sdk-python[aws]"
                )

            if self.region_name:
                self._client = boto3.client(
                    "secretsmanager", region_name=self.region_name
                )
            else:
                self._client = boto3.client("secretsmanager")

        return self._client

    def load(self) -> Optional[Dict[str, Any]]:
        """Load certificates from AWS Secrets Manager.

        Returns:
            Dict with host, port, and certificate paths, or None if not configured.

        Raises:
            ImportError: If boto3 is not installed
            Exception: If secrets cannot be retrieved
        """
        import json

        client = self._get_client()

        if self.secret_name:
            # Single secret mode
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_data = json.loads(response["SecretString"])

            ca_cert = secret_data.get("ca")
            client_cert = secret_data.get("cert")
            client_key = secret_data.get("key")
            host = secret_data.get("host")
            port = secret_data.get("port")

        elif self.secret_prefix:
            # Separate secrets mode
            prefix = self.secret_prefix.rstrip("/")

            ca_response = client.get_secret_value(SecretId=f"{prefix}/ca")
            cert_response = client.get_secret_value(SecretId=f"{prefix}/cert")
            key_response = client.get_secret_value(SecretId=f"{prefix}/key")

            ca_cert = ca_response["SecretString"]
            client_cert = cert_response["SecretString"]
            client_key = key_response["SecretString"]
            host = None
            port = None

            # Try to get optional host/port
            try:
                host_response = client.get_secret_value(SecretId=f"{prefix}/host")
                host = host_response["SecretString"]
            except Exception:
                pass

            try:
                port_response = client.get_secret_value(SecretId=f"{prefix}/port")
                port = int(port_response["SecretString"])
            except Exception:
                pass
        else:
            return None

        if not all([ca_cert, client_cert, client_key]):
            return None

        # Create temporary files for certificates
        ca_path = self._write_temp_cert(ca_cert, "ca")
        cert_path = self._write_temp_cert(client_cert, "cert")
        key_path = self._write_temp_cert(client_key, "key", restricted=True)

        result: Dict[str, Any] = {
            "ca_cert_path": ca_path,
            "client_cert_path": cert_path,
            "client_key_path": key_path,
        }

        if host:
            result["host"] = host
        if port:
            result["port"] = int(port)

        return result

    def _write_temp_cert(
        self, content: str, name: str, restricted: bool = False
    ) -> str:
        """Write certificate content to a temporary file."""
        temp = tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{name}.pem", delete=False
        )
        temp.write(content)
        temp.close()

        if restricted:
            os.chmod(temp.name, stat.S_IRUSR)
        else:
            os.chmod(temp.name, stat.S_IRUSR | stat.S_IWUSR)

        self._temp_files.append(temp.name)
        return temp.name

    def cleanup(self) -> None:
        """Clean up temporary certificate files."""
        for temp_file in self._temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        self._temp_files.clear()

    def __del__(self) -> None:
        self.cleanup()


class AWSParameterStoreProvider:
    """Load certificates from AWS Systems Manager Parameter Store.

    Parameters should be stored as SecureString type for security.

    Example:
        /joblet/certs/ca   -> CA certificate content (SecureString)
        /joblet/certs/cert -> Client certificate content (SecureString)
        /joblet/certs/key  -> Client private key content (SecureString)
        /joblet/certs/host -> Server hostname (optional, String)
        /joblet/certs/port -> Server port (optional, String)

    Requires boto3: pip install boto3
    """

    def __init__(
        self,
        parameter_prefix: str,
        region_name: Optional[str] = None,
    ) -> None:
        """Initialize AWS Parameter Store provider.

        Args:
            parameter_prefix: Prefix for parameters (e.g., "/joblet/certs")
            region_name: AWS region (uses default if not specified)
        """
        self.parameter_prefix = parameter_prefix.rstrip("/")
        self.region_name = region_name
        self._temp_files: List[str] = []
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create boto3 SSM client."""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for AWS Parameter Store support. "
                    "Install it with: pip install joblet-sdk-python[aws]"
                )

            if self.region_name:
                self._client = boto3.client("ssm", region_name=self.region_name)
            else:
                self._client = boto3.client("ssm")

        return self._client

    def load(self) -> Optional[Dict[str, Any]]:
        """Load certificates from AWS Parameter Store.

        Returns:
            Dict with host, port, and certificate paths, or None if not configured.

        Raises:
            ImportError: If boto3 is not installed
            Exception: If parameters cannot be retrieved
        """
        client = self._get_client()

        # Get required parameters
        try:
            ca_response = client.get_parameter(
                Name=f"{self.parameter_prefix}/ca", WithDecryption=True
            )
            cert_response = client.get_parameter(
                Name=f"{self.parameter_prefix}/cert", WithDecryption=True
            )
            key_response = client.get_parameter(
                Name=f"{self.parameter_prefix}/key", WithDecryption=True
            )

            ca_cert = ca_response["Parameter"]["Value"]
            client_cert = cert_response["Parameter"]["Value"]
            client_key = key_response["Parameter"]["Value"]
        except Exception:
            return None

        if not all([ca_cert, client_cert, client_key]):
            return None

        # Get optional host/port
        host = None
        port = None

        try:
            host_response = client.get_parameter(
                Name=f"{self.parameter_prefix}/host", WithDecryption=False
            )
            host = host_response["Parameter"]["Value"]
        except Exception:
            pass

        try:
            port_response = client.get_parameter(
                Name=f"{self.parameter_prefix}/port", WithDecryption=False
            )
            port = int(port_response["Parameter"]["Value"])
        except Exception:
            pass

        # Create temporary files for certificates
        ca_path = self._write_temp_cert(ca_cert, "ca")
        cert_path = self._write_temp_cert(client_cert, "cert")
        key_path = self._write_temp_cert(client_key, "key", restricted=True)

        result: Dict[str, Any] = {
            "ca_cert_path": ca_path,
            "client_cert_path": cert_path,
            "client_key_path": key_path,
        }

        if host:
            result["host"] = host
        if port:
            result["port"] = port

        return result

    def _write_temp_cert(
        self, content: str, name: str, restricted: bool = False
    ) -> str:
        """Write certificate content to a temporary file."""
        temp = tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{name}.pem", delete=False
        )
        temp.write(content)
        temp.close()

        if restricted:
            os.chmod(temp.name, stat.S_IRUSR)
        else:
            os.chmod(temp.name, stat.S_IRUSR | stat.S_IWUSR)

        self._temp_files.append(temp.name)
        return temp.name

    def cleanup(self) -> None:
        """Clean up temporary certificate files."""
        for temp_file in self._temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        self._temp_files.clear()

    def __del__(self) -> None:
        self.cleanup()
