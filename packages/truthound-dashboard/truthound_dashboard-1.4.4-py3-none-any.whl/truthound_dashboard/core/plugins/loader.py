"""Plugin Loader for loading and parsing plugin packages.

This module handles loading plugins from various sources:
- Local file system
- Remote URLs
- Plugin marketplace
"""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from .security import PluginSecurityManager

logger = logging.getLogger(__name__)


class PluginManifest:
    """Plugin manifest containing metadata and configuration.

    Attributes:
        name: Plugin name.
        version: Plugin version.
        display_name: Display name.
        description: Plugin description.
        plugin_type: Type of plugin.
        author: Author information.
        dependencies: Plugin dependencies.
        validators: List of validator definitions.
        reporters: List of reporter definitions.
        permissions: Required permissions.
        entry_point: Main entry point module.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize manifest from dictionary.

        Args:
            data: Manifest data dictionary.
        """
        self.name = data.get("name", "")
        self.version = data.get("version", "0.0.0")
        self.display_name = data.get("display_name", self.name)
        self.description = data.get("description", "")
        self.plugin_type = data.get("type", "validator")
        self.author = data.get("author", {})
        self.license = data.get("license")
        self.homepage = data.get("homepage")
        self.repository = data.get("repository")
        self.keywords = data.get("keywords", [])
        self.categories = data.get("categories", [])
        self.dependencies = data.get("dependencies", [])
        self.python_version = data.get("python_version")
        self.dashboard_version = data.get("dashboard_version")
        self.permissions = data.get("permissions", [])
        self.entry_point = data.get("entry_point")
        self.validators = data.get("validators", [])
        self.reporters = data.get("reporters", [])
        self.icon = data.get("icon")
        self.banner = data.get("banner")
        self.readme = data.get("readme")
        self.changelog = data.get("changelog")

    @classmethod
    def from_json(cls, json_str: str) -> "PluginManifest":
        """Create manifest from JSON string.

        Args:
            json_str: JSON string.

        Returns:
            PluginManifest instance.
        """
        return cls(json.loads(json_str))

    @classmethod
    def from_file(cls, path: Path) -> "PluginManifest":
        """Create manifest from file.

        Args:
            path: Path to manifest file.

        Returns:
            PluginManifest instance.
        """
        with open(path) as f:
            return cls(json.load(f))

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "name": self.name,
            "version": self.version,
            "display_name": self.display_name,
            "description": self.description,
            "type": self.plugin_type,
            "author": self.author,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "keywords": self.keywords,
            "categories": self.categories,
            "dependencies": self.dependencies,
            "python_version": self.python_version,
            "dashboard_version": self.dashboard_version,
            "permissions": self.permissions,
            "entry_point": self.entry_point,
            "validators": self.validators,
            "reporters": self.reporters,
            "icon": self.icon,
            "banner": self.banner,
        }


class PluginPackage:
    """Loaded plugin package ready for installation.

    Attributes:
        manifest: Plugin manifest.
        path: Path to extracted plugin files.
        checksum: Package checksum.
        signature: Package signature if available.
    """

    def __init__(
        self,
        manifest: PluginManifest,
        path: Path,
        checksum: str,
        signature: str | None = None,
    ) -> None:
        """Initialize plugin package.

        Args:
            manifest: Plugin manifest.
            path: Path to extracted files.
            checksum: Package checksum.
            signature: Optional package signature.
        """
        self.manifest = manifest
        self.path = path
        self.checksum = checksum
        self.signature = signature

    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.manifest.name

    @property
    def version(self) -> str:
        """Get plugin version."""
        return self.manifest.version

    def get_validator_code(self, validator_name: str) -> str | None:
        """Get code for a specific validator.

        Args:
            validator_name: Name of the validator.

        Returns:
            Validator code if found.
        """
        for v in self.manifest.validators:
            if v.get("name") == validator_name:
                code_file = v.get("code_file")
                if code_file:
                    code_path = self.path / code_file
                    if code_path.exists():
                        return code_path.read_text()
                return v.get("code")
        return None

    def get_reporter_code(self, reporter_name: str) -> str | None:
        """Get code for a specific reporter.

        Args:
            reporter_name: Name of the reporter.

        Returns:
            Reporter code if found.
        """
        for r in self.manifest.reporters:
            if r.get("name") == reporter_name:
                code_file = r.get("code_file")
                if code_file:
                    code_path = self.path / code_file
                    if code_path.exists():
                        return code_path.read_text()
                return r.get("code")
        return None

    def get_template(self, reporter_name: str) -> str | None:
        """Get template for a specific reporter.

        Args:
            reporter_name: Name of the reporter.

        Returns:
            Template content if found.
        """
        for r in self.manifest.reporters:
            if r.get("name") == reporter_name:
                template_file = r.get("template_file")
                if template_file:
                    template_path = self.path / template_file
                    if template_path.exists():
                        return template_path.read_text()
                return r.get("template")
        return None


class PluginLoader:
    """Loader for plugin packages.

    This class handles downloading, extracting, and parsing
    plugin packages from various sources.

    Attributes:
        plugins_dir: Directory to store plugin packages.
        security_manager: Optional security manager for verification.
    """

    def __init__(
        self,
        plugins_dir: Path | str | None = None,
        security_manager: "PluginSecurityManager | None" = None,
    ) -> None:
        """Initialize the plugin loader.

        Args:
            plugins_dir: Directory to store plugins.
            security_manager: Optional security manager.
        """
        if plugins_dir is None:
            plugins_dir = Path.home() / ".truthound" / "plugins"
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.security_manager = security_manager
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum of data.

        Args:
            data: Binary data.

        Returns:
            Hex-encoded checksum.
        """
        return hashlib.sha256(data).hexdigest()

    async def load_from_url(self, url: str) -> PluginPackage:
        """Load a plugin from a URL.

        Args:
            url: URL to plugin package (.zip).

        Returns:
            Loaded plugin package.

        Raises:
            ValueError: If download or extraction fails.
        """
        logger.info(f"Downloading plugin from: {url}")

        client = await self._get_http_client()
        response = await client.get(url)
        response.raise_for_status()

        package_data = response.content
        checksum = self._calculate_checksum(package_data)

        # Extract signature from headers if present
        signature = response.headers.get("X-Plugin-Signature")

        return await self._load_from_bytes(package_data, checksum, signature)

    async def load_from_file(self, path: Path | str) -> PluginPackage:
        """Load a plugin from a local file.

        Args:
            path: Path to plugin package (.zip).

        Returns:
            Loaded plugin package.

        Raises:
            ValueError: If file not found or extraction fails.
        """
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Plugin file not found: {path}")

        logger.info(f"Loading plugin from: {path}")

        package_data = path.read_bytes()
        checksum = self._calculate_checksum(package_data)

        # Check for signature file
        sig_path = path.with_suffix(".sig")
        signature = sig_path.read_text() if sig_path.exists() else None

        return await self._load_from_bytes(package_data, checksum, signature)

    async def load_from_directory(self, path: Path | str) -> PluginPackage:
        """Load a plugin from an extracted directory.

        Args:
            path: Path to extracted plugin directory.

        Returns:
            Loaded plugin package.

        Raises:
            ValueError: If manifest not found.
        """
        path = Path(path)
        manifest_path = path / "manifest.json"

        if not manifest_path.exists():
            raise ValueError(f"No manifest.json found in: {path}")

        manifest = PluginManifest.from_file(manifest_path)
        checksum = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

        logger.info(f"Loaded plugin from directory: {manifest.name} v{manifest.version}")

        return PluginPackage(
            manifest=manifest,
            path=path,
            checksum=checksum,
            signature=None,
        )

    async def _load_from_bytes(
        self,
        package_data: bytes,
        checksum: str,
        signature: str | None = None,
    ) -> PluginPackage:
        """Load plugin from raw bytes.

        Args:
            package_data: Package bytes.
            checksum: Package checksum.
            signature: Optional signature.

        Returns:
            Loaded plugin package.
        """
        # Create temp directory for extraction
        extract_dir = Path(tempfile.mkdtemp(prefix="truthound_plugin_"))

        try:
            # Write to temp file and extract
            temp_zip = extract_dir / "package.zip"
            temp_zip.write_bytes(package_data)

            with zipfile.ZipFile(temp_zip, "r") as zf:
                zf.extractall(extract_dir)

            temp_zip.unlink()

            # Find manifest
            manifest_path = extract_dir / "manifest.json"
            if not manifest_path.exists():
                # Check in subdirectory
                subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                if subdirs:
                    manifest_path = subdirs[0] / "manifest.json"
                    if manifest_path.exists():
                        # Move contents up
                        for item in subdirs[0].iterdir():
                            item.rename(extract_dir / item.name)
                        manifest_path = extract_dir / "manifest.json"

            if not manifest_path.exists():
                raise ValueError("No manifest.json found in package")

            manifest = PluginManifest.from_file(manifest_path)

            # Move to permanent location
            plugin_dir = self.plugins_dir / manifest.name / manifest.version
            if plugin_dir.exists():
                import shutil
                shutil.rmtree(plugin_dir)

            plugin_dir.parent.mkdir(parents=True, exist_ok=True)

            import shutil
            shutil.move(str(extract_dir), str(plugin_dir))

            logger.info(f"Loaded plugin: {manifest.name} v{manifest.version}")

            return PluginPackage(
                manifest=manifest,
                path=plugin_dir,
                checksum=checksum,
                signature=signature,
            )

        except Exception as e:
            # Clean up on error
            import shutil
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            raise ValueError(f"Failed to load plugin: {e}") from e

    async def list_local_plugins(self) -> list[PluginPackage]:
        """List all locally installed plugins.

        Returns:
            List of plugin packages.
        """
        packages = []

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            for version_dir in plugin_dir.iterdir():
                if not version_dir.is_dir():
                    continue

                manifest_path = version_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = PluginManifest.from_file(manifest_path)
                        checksum = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                        packages.append(
                            PluginPackage(
                                manifest=manifest,
                                path=version_dir,
                                checksum=checksum,
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Failed to load plugin from {version_dir}: {e}")

        return packages

    async def unload_plugin(self, name: str, version: str | None = None) -> None:
        """Remove a plugin from local storage.

        Args:
            name: Plugin name.
            version: Specific version to remove (all if None).
        """
        import shutil

        plugin_dir = self.plugins_dir / name

        if version:
            version_dir = plugin_dir / version
            if version_dir.exists():
                shutil.rmtree(version_dir)
                logger.info(f"Removed plugin: {name} v{version}")
        else:
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
                logger.info(f"Removed all versions of plugin: {name}")

        # Clean up empty parent directory
        if plugin_dir.exists() and not any(plugin_dir.iterdir()):
            plugin_dir.rmdir()

    def get_plugin_path(self, name: str, version: str) -> Path | None:
        """Get path to a specific plugin version.

        Args:
            name: Plugin name.
            version: Plugin version.

        Returns:
            Path to plugin directory if exists.
        """
        path = self.plugins_dir / name / version
        return path if path.exists() else None
