"""Tests for Plugin System (Phase 9).

This module tests the core plugin functionality including:
- Trust Store management
- Security Policy configuration
- Sandbox execution
- Custom Validator execution
- Custom Reporter execution
- Hot reload functionality
- Signature verification
"""

from __future__ import annotations

import asyncio
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from truthound_dashboard.db.models import (
    TrustedSigner,
    SecurityPolicy,
    PluginSignature,
    HotReloadConfig,
    PluginHook,
    SignatureAlgorithmType,
    TrustLevelType,
    IsolationLevelType,
)


class TestTrustedSignerModel:
    """Tests for TrustedSigner database model."""

    def test_trusted_signer_creation(self):
        """Test creating a TrustedSigner instance."""
        signer = TrustedSigner(
            signer_id="test@example.com",
            name="Test Signer",
            organization="Test Org",
            email="test@example.com",
            public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            algorithm=SignatureAlgorithmType.ED25519.value,
            fingerprint="abc123",
            trust_level=TrustLevelType.VERIFIED.value,
        )

        assert signer.signer_id == "test@example.com"
        assert signer.name == "Test Signer"
        assert signer.trust_level == "verified"
        assert signer.plugins_signed == 0

    def test_is_valid_active_signer(self):
        """Test is_valid returns True for active signer."""
        signer = TrustedSigner(
            signer_id="valid@example.com",
            name="Valid Signer",
            public_key="key",
            fingerprint="abc",
            trust_level=TrustLevelType.TRUSTED.value,
        )

        assert signer.is_valid() is True

    def test_is_valid_revoked_signer(self):
        """Test is_valid returns False for revoked signer."""
        signer = TrustedSigner(
            signer_id="revoked@example.com",
            name="Revoked Signer",
            public_key="key",
            fingerprint="abc",
            trust_level=TrustLevelType.REVOKED.value,
        )

        assert signer.is_valid() is False

    def test_is_valid_expired_signer(self):
        """Test is_valid returns False for expired signer."""
        signer = TrustedSigner(
            signer_id="expired@example.com",
            name="Expired Signer",
            public_key="key",
            fingerprint="abc",
            trust_level=TrustLevelType.TRUSTED.value,
            expires_at=datetime(2020, 1, 1),  # Expired
        )

        assert signer.is_valid() is False

    def test_revoke_signer(self):
        """Test revoking a signer."""
        signer = TrustedSigner(
            signer_id="to-revoke@example.com",
            name="To Revoke",
            public_key="key",
            fingerprint="abc",
            trust_level=TrustLevelType.TRUSTED.value,
        )

        signer.revoke("Security concern")

        assert signer.trust_level == TrustLevelType.REVOKED.value
        assert signer.revoked_at is not None
        assert signer.revocation_reason == "Security concern"

    def test_increment_signed_count(self):
        """Test incrementing plugins signed count."""
        signer = TrustedSigner(
            signer_id="counter@example.com",
            name="Counter",
            public_key="key",
            fingerprint="abc",
            trust_level=TrustLevelType.VERIFIED.value,
            plugins_signed=5,
        )

        signer.increment_signed_count()

        assert signer.plugins_signed == 6


class TestSecurityPolicyModel:
    """Tests for SecurityPolicy database model."""

    def test_security_policy_creation(self):
        """Test creating a SecurityPolicy instance."""
        policy = SecurityPolicy(
            name="test-policy",
            description="Test policy",
            isolation_level=IsolationLevelType.PROCESS.value,
            memory_limit_mb=256,
            cpu_time_limit_sec=30,
        )

        assert policy.name == "test-policy"
        assert policy.isolation_level == "process"
        assert policy.memory_limit_mb == 256
        assert policy.network_enabled is False  # Default

    def test_get_preset_development(self):
        """Test creating development preset."""
        policy = SecurityPolicy.get_preset("development")

        assert policy.name == "development"
        assert policy.isolation_level == "none"
        assert policy.network_enabled is True
        assert policy.file_write_enabled is True
        assert policy.require_signature is False

    def test_get_preset_standard(self):
        """Test creating standard preset."""
        policy = SecurityPolicy.get_preset("standard")

        assert policy.name == "standard"
        assert policy.isolation_level == "process"
        assert policy.network_enabled is False
        assert policy.file_write_enabled is False

    def test_get_preset_enterprise(self):
        """Test creating enterprise preset."""
        policy = SecurityPolicy.get_preset("enterprise")

        assert policy.name == "enterprise"
        assert policy.require_signature is True
        assert policy.min_trust_level == TrustLevelType.TRUSTED.value

    def test_get_preset_strict(self):
        """Test creating strict preset."""
        policy = SecurityPolicy.get_preset("strict")

        assert policy.name == "strict"
        assert policy.isolation_level == "container"
        assert policy.file_read_enabled is False
        assert policy.require_signature is True

    def test_get_preset_unknown_returns_standard(self):
        """Test unknown preset returns standard."""
        policy = SecurityPolicy.get_preset("unknown")

        assert policy.name == "unknown"
        assert policy.isolation_level == "process"  # Standard default


class TestPluginSignatureModel:
    """Tests for PluginSignature database model."""

    def test_plugin_signature_creation(self):
        """Test creating a PluginSignature instance."""
        sig = PluginSignature(
            plugin_id="plugin-123",
            signer_id="signer-456",
            algorithm=SignatureAlgorithmType.ED25519.value,
            signature="base64_signature_here",
            signed_hash="sha256_hash_here",
            signed_at=datetime.utcnow(),
        )

        assert sig.plugin_id == "plugin-123"
        assert sig.algorithm == "ed25519"
        assert sig.is_valid is True

    def test_mark_verified(self):
        """Test marking signature as verified."""
        sig = PluginSignature(
            plugin_id="plugin-123",
            signature="sig",
            signed_hash="hash",
            signed_at=datetime.utcnow(),
        )

        sig.mark_verified()

        assert sig.verified_at is not None
        assert sig.is_valid is True

    def test_invalidate(self):
        """Test invalidating a signature."""
        sig = PluginSignature(
            plugin_id="plugin-123",
            signature="sig",
            signed_hash="hash",
            signed_at=datetime.utcnow(),
            is_valid=True,
        )

        sig.invalidate()

        assert sig.is_valid is False


class TestHotReloadConfigModel:
    """Tests for HotReloadConfig database model."""

    def test_hot_reload_config_creation(self):
        """Test creating a HotReloadConfig instance."""
        config = HotReloadConfig(
            plugin_id="plugin-123",
            enabled=True,
            watch_paths=["/path/to/plugin"],
            debounce_ms=500,
            reload_strategy="graceful",
        )

        assert config.plugin_id == "plugin-123"
        assert config.enabled is True
        assert config.debounce_ms == 500

    def test_record_reload_success(self):
        """Test recording successful reload."""
        config = HotReloadConfig(
            plugin_id="plugin-123",
            reload_count=5,
        )

        config.record_reload(success=True)

        assert config.reload_count == 6
        assert config.last_reload_at is not None
        assert config.last_error is None

    def test_record_reload_failure(self):
        """Test recording failed reload."""
        config = HotReloadConfig(
            plugin_id="plugin-123",
            reload_count=5,
        )

        config.record_reload(success=False, error="Module not found")

        assert config.reload_count == 6
        assert config.last_error == "Module not found"


class TestPluginHookModel:
    """Tests for PluginHook database model."""

    def test_plugin_hook_creation(self):
        """Test creating a PluginHook instance."""
        hook = PluginHook(
            plugin_id="plugin-123",
            hook_type="pre_validation",
            callback_name="my_callback",
            priority=50,
        )

        assert hook.plugin_id == "plugin-123"
        assert hook.hook_type == "pre_validation"
        assert hook.enabled is True

    def test_average_execution_ms_zero_triggers(self):
        """Test average execution returns 0 when no triggers."""
        hook = PluginHook(
            plugin_id="plugin-123",
            hook_type="post_validation",
            callback_name="cb",
            trigger_count=0,
        )

        assert hook.average_execution_ms == 0

    def test_average_execution_ms_with_triggers(self):
        """Test average execution calculation."""
        hook = PluginHook(
            plugin_id="plugin-123",
            hook_type="post_validation",
            callback_name="cb",
            trigger_count=5,
            total_execution_ms=250,
        )

        assert hook.average_execution_ms == 50

    def test_record_trigger(self):
        """Test recording a hook trigger."""
        hook = PluginHook(
            plugin_id="plugin-123",
            hook_type="on_error",
            callback_name="error_handler",
            trigger_count=10,
            total_execution_ms=500,
        )

        hook.record_trigger(execution_ms=25.5)

        assert hook.trigger_count == 11
        assert hook.total_execution_ms == 525.5
        assert hook.last_triggered_at is not None

    def test_record_trigger_with_error(self):
        """Test recording a hook trigger with error."""
        hook = PluginHook(
            plugin_id="plugin-123",
            hook_type="on_error",
            callback_name="error_handler",
        )

        hook.record_trigger(execution_ms=10, error="Timeout")

        assert hook.last_error == "Timeout"


class TestCustomValidatorExecutor:
    """Tests for CustomValidatorExecutor."""

    def test_validate_validator_code_valid(self):
        """Test validating valid validator code."""
        from truthound_dashboard.core.plugins.validator_executor import (
            CustomValidatorExecutor,
        )

        executor = CustomValidatorExecutor(log_executions=False)

        code = '''
def validate(column_name, values, params, schema, row_count):
    return {"passed": True, "issues": [], "message": "OK", "details": {}}
'''

        is_valid, issues = executor.validate_validator_code(code)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_validator_code_missing_function(self):
        """Test validating code missing required function."""
        from truthound_dashboard.core.plugins.validator_executor import (
            CustomValidatorExecutor,
        )

        executor = CustomValidatorExecutor(log_executions=False)

        code = '''
def some_other_function():
    pass
'''

        is_valid, issues = executor.validate_validator_code(code)

        assert is_valid is False
        assert "Missing required 'validate' function" in issues

    def test_validate_validator_code_dangerous_pattern(self):
        """Test validating code with dangerous patterns."""
        from truthound_dashboard.core.plugins.validator_executor import (
            CustomValidatorExecutor,
        )

        executor = CustomValidatorExecutor(log_executions=False)

        code = '''
import os
def validate(column_name, values, params, schema, row_count):
    os.system("rm -rf /")
    return True
'''

        is_valid, issues = executor.validate_validator_code(code)

        assert is_valid is False
        assert any("os.system" in issue for issue in issues)

    def test_get_validator_template(self):
        """Test getting validator template."""
        from truthound_dashboard.core.plugins.validator_executor import (
            CustomValidatorExecutor,
        )

        executor = CustomValidatorExecutor(log_executions=False)
        template = executor.get_validator_template()

        assert "def validate(" in template
        assert "column_name" in template
        assert "values" in template


class TestCustomReporterExecutor:
    """Tests for CustomReporterExecutor."""

    def test_validate_reporter_code_valid(self):
        """Test validating valid reporter code."""
        from truthound_dashboard.core.plugins.reporter_executor import (
            CustomReporterExecutor,
        )

        executor = CustomReporterExecutor(log_executions=False)

        code = '''
def generate_report(data, config, format, metadata):
    return {"content": "<html></html>", "content_type": "text/html", "filename": "report.html"}
'''

        is_valid, issues = executor.validate_reporter_code(code)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_reporter_code_missing_function(self):
        """Test validating code missing required function."""
        from truthound_dashboard.core.plugins.reporter_executor import (
            CustomReporterExecutor,
        )

        executor = CustomReporterExecutor(log_executions=False)

        code = '''
def other_function():
    pass
'''

        is_valid, issues = executor.validate_reporter_code(code)

        assert is_valid is False
        assert "Missing required 'generate_report' function" in issues

    def test_validate_template_valid(self):
        """Test validating valid Jinja2 template."""
        from truthound_dashboard.core.plugins.reporter_executor import (
            CustomReporterExecutor,
        )

        executor = CustomReporterExecutor(log_executions=False)

        template = '''
<html>
<body>
    <h1>{{ title }}</h1>
    <p>{{ summary }}</p>
</body>
</html>
'''

        is_valid, issues = executor.validate_template(template)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_template_dangerous(self):
        """Test validating template with dangerous patterns."""
        from truthound_dashboard.core.plugins.reporter_executor import (
            CustomReporterExecutor,
        )

        executor = CustomReporterExecutor(log_executions=False)

        template = '''
<html>
{% import os %}
{{ self.__class__ }}
</html>
'''

        is_valid, issues = executor.validate_template(template)

        assert is_valid is False
        assert len(issues) > 0

    def test_get_reporter_template(self):
        """Test getting reporter template."""
        from truthound_dashboard.core.plugins.reporter_executor import (
            CustomReporterExecutor,
        )

        executor = CustomReporterExecutor(log_executions=False)
        template = executor.get_reporter_template()

        assert "def generate_report(" in template
        assert "content" in template

    def test_get_jinja2_template(self):
        """Test getting Jinja2 template example."""
        from truthound_dashboard.core.plugins.reporter_executor import (
            CustomReporterExecutor,
        )

        executor = CustomReporterExecutor(log_executions=False)
        template = executor.get_jinja2_template()

        assert "{{ title }}" in template
        assert "{{ metadata.generated_at }}" in template


class TestFileWatcher:
    """Tests for FileWatcher in hot reload system."""

    @pytest.mark.asyncio
    async def test_file_watcher_detect_new_file(self):
        """Test detecting new file creation."""
        from truthound_dashboard.core.plugins.lifecycle.hot_reload import (
            FileWatcher,
            FileChange,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create initial file
            (tmppath / "initial.py").write_text("# initial")

            watcher = FileWatcher([tmppath], poll_interval=0.1)

            changes: list[FileChange] = []
            watcher.on_change(lambda c: changes.append(c))

            await watcher.start()

            # Create new file
            (tmppath / "new.py").write_text("# new file")

            # Wait for detection
            await asyncio.sleep(0.3)

            await watcher.stop()

            # Check that new file was detected
            created_changes = [c for c in changes if c.event_type == "created"]
            assert any("new.py" in c.path for c in created_changes)

    @pytest.mark.asyncio
    async def test_file_watcher_detect_modification(self):
        """Test detecting file modification."""
        from truthound_dashboard.core.plugins.lifecycle.hot_reload import (
            FileWatcher,
            FileChange,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create initial file
            test_file = tmppath / "test.py"
            test_file.write_text("# initial content")

            watcher = FileWatcher([tmppath], poll_interval=0.1)

            changes: list[FileChange] = []
            watcher.on_change(lambda c: changes.append(c))

            await watcher.start()

            # Wait for initial scan
            await asyncio.sleep(0.15)

            # Modify file
            test_file.write_text("# modified content")

            # Wait for detection
            await asyncio.sleep(0.3)

            await watcher.stop()

            # Check that modification was detected
            modified_changes = [c for c in changes if c.event_type == "modified"]
            assert any("test.py" in c.path for c in modified_changes)

    @pytest.mark.asyncio
    async def test_file_watcher_detect_deletion(self):
        """Test detecting file deletion."""
        from truthound_dashboard.core.plugins.lifecycle.hot_reload import (
            FileWatcher,
            FileChange,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create initial file
            test_file = tmppath / "to_delete.py"
            test_file.write_text("# will be deleted")

            watcher = FileWatcher([tmppath], poll_interval=0.1)

            changes: list[FileChange] = []
            watcher.on_change(lambda c: changes.append(c))

            await watcher.start()

            # Wait for initial scan
            await asyncio.sleep(0.15)

            # Delete file
            test_file.unlink()

            # Wait for detection
            await asyncio.sleep(0.3)

            await watcher.stop()

            # Check that deletion was detected
            deleted_changes = [c for c in changes if c.event_type == "deleted"]
            assert any("to_delete.py" in c.path for c in deleted_changes)


class TestHotReloadManager:
    """Tests for HotReloadManager."""

    def test_hot_reload_manager_register_plugin(self):
        """Test registering a plugin for hot reload."""
        from truthound_dashboard.core.plugins.lifecycle.hot_reload import (
            HotReloadManager,
            ReloadStrategy,
        )
        from truthound_dashboard.core.plugins.lifecycle.machine import (
            PluginStateMachine,
        )

        manager = HotReloadManager(strategy=ReloadStrategy.MANUAL)
        state_machine = MagicMock(spec=PluginStateMachine)

        manager.register_plugin("test-plugin", state_machine)

        status = manager.get_status("test-plugin")
        assert status["registered"] is True
        assert status["strategy"] == "manual"

    def test_hot_reload_manager_unregister_plugin(self):
        """Test unregistering a plugin from hot reload."""
        from truthound_dashboard.core.plugins.lifecycle.hot_reload import (
            HotReloadManager,
            ReloadStrategy,
        )

        manager = HotReloadManager(strategy=ReloadStrategy.MANUAL)
        state_machine = MagicMock()

        manager.register_plugin("test-plugin", state_machine)
        manager.unregister_plugin("test-plugin")

        status = manager.get_status("test-plugin")
        assert status["registered"] is False


class TestPluginSandbox:
    """Tests for PluginSandbox execution."""

    def test_sandbox_analyze_safe_code(self):
        """Test analyzing safe code."""
        from truthound_dashboard.core.plugins.sandbox import PluginSandbox, SandboxConfig

        sandbox = PluginSandbox(SandboxConfig())

        code = '''
import math
def calculate(x):
    return math.sqrt(x)
'''

        issues, warnings = sandbox.analyze_code(code)

        # Safe code should have minimal issues
        assert "math" not in str(issues).lower() or len(issues) == 0

    def test_sandbox_analyze_dangerous_code(self):
        """Test analyzing dangerous code."""
        from truthound_dashboard.core.plugins.sandbox import PluginSandbox, SandboxConfig

        sandbox = PluginSandbox(SandboxConfig())

        code = '''
import os
import subprocess
def dangerous():
    os.system("rm -rf /")
    subprocess.run(["ls"])
'''

        issues, warnings = sandbox.analyze_code(code)

        # Should detect dangerous patterns
        assert len(issues) > 0 or len(warnings) > 0

    def test_sandbox_execute_simple_function(self):
        """Test executing simple function in sandbox."""
        from truthound_dashboard.core.plugins.sandbox import PluginSandbox, SandboxConfig

        sandbox = PluginSandbox(SandboxConfig())

        code = '''
def add_numbers(a, b):
    return a + b
'''

        result = sandbox.execute(
            code=code,
            entry_point="add_numbers",
            entry_args={"a": 5, "b": 3},
        )

        assert result.success is True
        assert result.result == 8

    def test_sandbox_execute_with_timeout(self):
        """Test sandbox enforces timeout."""
        from truthound_dashboard.core.plugins.sandbox import PluginSandbox, SandboxConfig

        sandbox = PluginSandbox(SandboxConfig(timeout_seconds=0.1))

        code = '''
import time
def slow_function():
    time.sleep(10)
    return "done"
'''

        result = sandbox.execute(
            code=code,
            entry_point="slow_function",
            entry_args={},
        )

        # Should timeout
        assert result.success is False
        assert "timeout" in result.error.lower() or result.execution_time_ms > 100


class TestSignatureVerification:
    """Tests for plugin signature verification."""

    def test_compute_plugin_hash(self):
        """Test computing hash of plugin content."""
        from truthound_dashboard.core.plugins.security.signing import (
            SigningService,
        )

        service = SigningService()

        content = b"test plugin content"
        hash1 = service.compute_hash(content)
        hash2 = service.compute_hash(content)

        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_sign_and_verify_hmac(self):
        """Test signing and verifying with HMAC."""
        from truthound_dashboard.core.plugins.security.signing import (
            SigningService,
            SignatureAlgorithm,
        )

        service = SigningService(algorithm=SignatureAlgorithm.HMAC_SHA256)

        content = b"plugin content to sign"
        secret_key = b"super_secret_key"

        signature = service.sign(content, secret_key)
        is_valid = service.verify(content, signature, secret_key)

        assert is_valid is True

    def test_verify_fails_with_wrong_key(self):
        """Test verification fails with wrong key."""
        from truthound_dashboard.core.plugins.security.signing import (
            SigningService,
            SignatureAlgorithm,
        )

        service = SigningService(algorithm=SignatureAlgorithm.HMAC_SHA256)

        content = b"plugin content"
        correct_key = b"correct_key"
        wrong_key = b"wrong_key"

        signature = service.sign(content, correct_key)
        is_valid = service.verify(content, signature, wrong_key)

        assert is_valid is False

    def test_verify_fails_with_tampered_content(self):
        """Test verification fails with tampered content."""
        from truthound_dashboard.core.plugins.security.signing import (
            SigningService,
            SignatureAlgorithm,
        )

        service = SigningService(algorithm=SignatureAlgorithm.HMAC_SHA256)

        original_content = b"original content"
        tampered_content = b"tampered content"
        key = b"secret_key"

        signature = service.sign(original_content, key)
        is_valid = service.verify(tampered_content, signature, key)

        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
