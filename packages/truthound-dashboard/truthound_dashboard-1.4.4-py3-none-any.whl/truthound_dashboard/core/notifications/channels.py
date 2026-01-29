"""Notification channel implementations.

This module provides concrete implementations of notification channels
for various notification services:

- Slack: Incoming webhooks
- Email: SMTP
- Webhook: Generic HTTP endpoints
- Discord: Discord webhooks
- Telegram: Telegram Bot API
- PagerDuty: Events API v2
- OpsGenie: Alert API
- Teams: Microsoft Teams webhooks
- GitHub: Issues/Discussions API

Each channel is registered with the ChannelRegistry and can be
instantiated dynamically based on channel type.
"""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from .base import (
    BaseNotificationChannel,
    ChannelRegistry,
    NotificationEvent,
)
from .events import (
    DriftDetectedEvent,
    SchemaChangedEvent,
    ScheduleFailedEvent,
    TestNotificationEvent,
    ValidationFailedEvent,
)


@ChannelRegistry.register("slack")
class SlackChannel(BaseNotificationChannel):
    """Slack notification channel using incoming webhooks.

    Configuration:
        webhook_url: Slack incoming webhook URL
        channel: Optional channel override
        username: Optional username override
        icon_emoji: Optional emoji icon (e.g., ":robot:")

    Example config:
        {
            "webhook_url": "https://hooks.slack.com/services/...",
            "username": "Truthound Bot",
            "icon_emoji": ":bar_chart:"
        }
    """

    channel_type = "slack"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Slack channel configuration schema."""
        return {
            "webhook_url": {
                "type": "string",
                "required": True,
                "description": "Slack incoming webhook URL",
            },
            "channel": {
                "type": "string",
                "required": False,
                "description": "Channel override (e.g., #alerts)",
            },
            "username": {
                "type": "string",
                "required": False,
                "description": "Bot username override",
            },
            "icon_emoji": {
                "type": "string",
                "required": False,
                "description": "Emoji icon (e.g., :robot:)",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to Slack.

        Args:
            message: Message text (supports Slack markdown).
            event: Optional triggering event.
            **kwargs: Additional Slack message options.

        Returns:
            True if message was sent successfully.
        """
        webhook_url = self.config["webhook_url"]

        # Build payload
        payload: dict[str, Any] = {
            "text": message,
        }

        # Add blocks for rich formatting
        blocks = self._build_blocks(message, event)
        if blocks:
            payload["blocks"] = blocks

        # Add optional overrides
        if self.config.get("channel"):
            payload["channel"] = self.config["channel"]
        if self.config.get("username"):
            payload["username"] = self.config["username"]
        if self.config.get("icon_emoji"):
            payload["icon_emoji"] = self.config["icon_emoji"]

        # Merge any additional kwargs
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            return response.status_code == 200

    def _build_blocks(
        self,
        message: str,
        event: NotificationEvent | None,
    ) -> list[dict[str, Any]]:
        """Build Slack blocks for rich message formatting."""
        blocks = []

        # Main message section
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            }
        )

        # Add context for specific event types
        if isinstance(event, ValidationFailedEvent):
            context_elements = [
                {"type": "mrkdwn", "text": f"*Severity:* {event.severity}"},
                {"type": "mrkdwn", "text": f"*Issues:* {event.total_issues}"},
            ]
            if event.validation_id:
                context_elements.append(
                    {"type": "mrkdwn", "text": f"*ID:* `{event.validation_id[:8]}...`"}
                )
            blocks.append({"type": "context", "elements": context_elements})

        elif isinstance(event, DriftDetectedEvent):
            context_elements = [
                {
                    "type": "mrkdwn",
                    "text": f"*Drift:* {event.drifted_columns}/{event.total_columns} columns",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Percentage:* {event.drift_percentage:.1f}%",
                },
            ]
            blocks.append({"type": "context", "elements": context_elements})

        return blocks

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for Slack with mrkdwn syntax."""
        if isinstance(event, ValidationFailedEvent):
            emoji = ":rotating_light:" if event.has_critical else ":warning:"
            return (
                f"{emoji} *Validation Failed*\n\n"
                f"*Source:* {event.source_name or 'Unknown'}\n"
                f"*Severity:* {event.severity}\n"
                f"*Total Issues:* {event.total_issues}"
            )

        elif isinstance(event, ScheduleFailedEvent):
            return (
                f":clock1: *Scheduled Validation Failed*\n\n"
                f"*Schedule:* {event.schedule_name}\n"
                f"*Source:* {event.source_name or 'Unknown'}\n"
                f"*Error:* {event.error_message or 'Validation failed'}"
            )

        elif isinstance(event, DriftDetectedEvent):
            emoji = ":chart_with_upwards_trend:" if event.has_high_drift else ":chart_with_downwards_trend:"
            return (
                f"{emoji} *Drift Detected*\n\n"
                f"*Baseline:* {event.baseline_source_name}\n"
                f"*Current:* {event.current_source_name}\n"
                f"*Drifted Columns:* {event.drifted_columns}/{event.total_columns} "
                f"({event.drift_percentage:.1f}%)"
            )

        elif isinstance(event, TestNotificationEvent):
            return (
                f":white_check_mark: *Test Notification*\n\n"
                f"This is a test from truthound-dashboard.\n"
                f"Channel: {event.channel_name}"
            )

        return self._default_format(event)


@ChannelRegistry.register("email")
class EmailChannel(BaseNotificationChannel):
    """Email notification channel using SMTP.

    Configuration:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port (default: 587)
        smtp_username: SMTP authentication username
        smtp_password: SMTP authentication password
        from_email: Sender email address
        recipients: List of recipient email addresses
        use_tls: Whether to use TLS (default: True)

    Example config:
        {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "user@gmail.com",
            "smtp_password": "app-password",
            "from_email": "alerts@example.com",
            "recipients": ["admin@example.com"],
            "use_tls": true
        }
    """

    channel_type = "email"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Email channel configuration schema."""
        return {
            "smtp_host": {
                "type": "string",
                "required": True,
                "description": "SMTP server hostname",
            },
            "smtp_port": {
                "type": "integer",
                "required": False,
                "default": 587,
                "description": "SMTP server port",
            },
            "smtp_username": {
                "type": "string",
                "required": False,
                "description": "SMTP authentication username",
            },
            "smtp_password": {
                "type": "string",
                "required": False,
                "secret": True,
                "description": "SMTP authentication password",
            },
            "from_email": {
                "type": "string",
                "required": True,
                "description": "Sender email address",
            },
            "recipients": {
                "type": "array",
                "required": True,
                "items": {"type": "string"},
                "description": "List of recipient email addresses",
            },
            "use_tls": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Use TLS encryption",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        subject: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification via email.

        Args:
            message: Email body text.
            event: Optional triggering event (used for subject).
            subject: Optional subject override.
            **kwargs: Additional options.

        Returns:
            True if email was sent successfully.
        """
        try:
            import aiosmtplib
        except ImportError:
            raise ImportError(
                "aiosmtplib is required for email notifications. "
                "Install with: pip install aiosmtplib"
            )

        # Build subject
        if subject is None:
            subject = self._build_subject(event)

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config["from_email"]
        msg["To"] = ", ".join(self.config["recipients"])

        # Plain text version
        text_part = MIMEText(message, "plain")
        msg.attach(text_part)

        # HTML version
        html_content = self._build_html(message, event)
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Send
        await aiosmtplib.send(
            msg,
            hostname=self.config["smtp_host"],
            port=self.config.get("smtp_port", 587),
            username=self.config.get("smtp_username"),
            password=self.config.get("smtp_password"),
            use_tls=self.config.get("use_tls", True),
        )

        return True

    def _build_subject(self, event: NotificationEvent | None) -> str:
        """Build email subject from event."""
        if event is None:
            return "[Truthound] Notification"

        if isinstance(event, ValidationFailedEvent):
            severity = event.severity
            return f"[Truthound] {severity} - Validation Failed: {event.source_name}"

        elif isinstance(event, ScheduleFailedEvent):
            return f"[Truthound] Schedule Failed: {event.schedule_name}"

        elif isinstance(event, DriftDetectedEvent):
            return f"[Truthound] Drift Detected: {event.baseline_source_name} → {event.current_source_name}"

        elif isinstance(event, TestNotificationEvent):
            return "[Truthound] Test Notification"

        return f"[Truthound] {event.event_type}"

    def _build_html(self, message: str, event: NotificationEvent | None) -> str:
        """Build HTML email body."""
        # Convert newlines to <br> for simple HTML
        html_message = message.replace("\n", "<br>")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #fd9e4b; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }}
                .footer {{ font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">Truthound Dashboard</h2>
                </div>
                <div class="content">
                    <p>{html_message}</p>
                </div>
                <div class="footer">
                    <p>This notification was sent by Truthound Dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for email (plain text)."""
        if isinstance(event, ValidationFailedEvent):
            return (
                f"Validation Failed\n\n"
                f"Source: {event.source_name or 'Unknown'}\n"
                f"Severity: {event.severity}\n"
                f"Total Issues: {event.total_issues}\n"
                f"Validation ID: {event.validation_id}\n\n"
                f"Please check the dashboard for details."
            )

        elif isinstance(event, ScheduleFailedEvent):
            return (
                f"Scheduled Validation Failed\n\n"
                f"Schedule: {event.schedule_name}\n"
                f"Source: {event.source_name or 'Unknown'}\n"
                f"Error: {event.error_message or 'Validation failed'}\n\n"
                f"Please check the dashboard for details."
            )

        elif isinstance(event, DriftDetectedEvent):
            return (
                f"Drift Detected\n\n"
                f"Baseline: {event.baseline_source_name}\n"
                f"Current: {event.current_source_name}\n"
                f"Drifted Columns: {event.drifted_columns}/{event.total_columns} "
                f"({event.drift_percentage:.1f}%)\n\n"
                f"Please check the dashboard for details."
            )

        elif isinstance(event, TestNotificationEvent):
            return (
                f"Test Notification\n\n"
                f"This is a test notification from truthound-dashboard.\n"
                f"Channel: {event.channel_name}\n\n"
                f"If you received this, your email channel is configured correctly."
            )

        return self._default_format(event)


@ChannelRegistry.register("webhook")
class WebhookChannel(BaseNotificationChannel):
    """Generic webhook notification channel.

    Sends JSON payloads to any HTTP endpoint.

    Configuration:
        url: Webhook endpoint URL
        method: HTTP method (default: POST)
        headers: Optional custom headers
        include_event_data: Whether to include full event data (default: True)

    Example config:
        {
            "url": "https://example.com/webhook",
            "method": "POST",
            "headers": {
                "Authorization": "Bearer token",
                "X-Custom-Header": "value"
            }
        }
    """

    channel_type = "webhook"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Webhook channel configuration schema."""
        return {
            "url": {
                "type": "string",
                "required": True,
                "description": "Webhook endpoint URL",
            },
            "method": {
                "type": "string",
                "required": False,
                "default": "POST",
                "description": "HTTP method (GET, POST, PUT)",
            },
            "headers": {
                "type": "object",
                "required": False,
                "description": "Custom HTTP headers",
            },
            "include_event_data": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Include full event data in payload",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification via webhook.

        Args:
            message: Message text.
            event: Optional triggering event.
            payload: Optional custom payload (overrides default).
            **kwargs: Additional options.

        Returns:
            True if webhook call was successful.
        """
        url = self.config["url"]
        method = self.config.get("method", "POST").upper()
        headers = self.config.get("headers", {})

        # Build payload
        if payload is None:
            payload = self._build_payload(message, event)

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=payload)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=payload)
            else:  # Default to POST
                response = await client.post(url, headers=headers, json=payload)

            # Consider 2xx responses as success
            return 200 <= response.status_code < 300

    def _build_payload(
        self,
        message: str,
        event: NotificationEvent | None,
    ) -> dict[str, Any]:
        """Build webhook payload."""
        payload: dict[str, Any] = {
            "message": message,
            "channel_id": self.channel_id,
            "channel_name": self.name,
        }

        if event and self.config.get("include_event_data", True):
            payload["event"] = event.to_dict()
            payload["event_type"] = event.event_type

        return payload

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for webhook (plain text)."""
        if isinstance(event, ValidationFailedEvent):
            return (
                f"Validation failed for {event.source_name or 'Unknown'}: "
                f"{event.total_issues} issues ({event.severity})"
            )

        elif isinstance(event, ScheduleFailedEvent):
            return (
                f"Schedule '{event.schedule_name}' failed for "
                f"{event.source_name or 'Unknown'}"
            )

        elif isinstance(event, DriftDetectedEvent):
            return (
                f"Drift detected: {event.drifted_columns}/{event.total_columns} columns "
                f"({event.drift_percentage:.1f}%)"
            )

        elif isinstance(event, TestNotificationEvent):
            return f"Test notification from truthound-dashboard"

        return self._default_format(event)


@ChannelRegistry.register("discord")
class DiscordChannel(BaseNotificationChannel):
    """Discord notification channel using webhooks.

    Configuration:
        webhook_url: Discord webhook URL
        username: Optional bot username override
        avatar_url: Optional avatar URL

    Example config:
        {
            "webhook_url": "https://discord.com/api/webhooks/...",
            "username": "Truthound Bot",
            "avatar_url": "https://example.com/avatar.png"
        }
    """

    channel_type = "discord"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Discord channel configuration schema."""
        return {
            "webhook_url": {
                "type": "string",
                "required": True,
                "description": "Discord webhook URL",
            },
            "username": {
                "type": "string",
                "required": False,
                "description": "Bot username override",
            },
            "avatar_url": {
                "type": "string",
                "required": False,
                "description": "Bot avatar URL",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to Discord.

        Args:
            message: Message text (supports Discord markdown).
            event: Optional triggering event.
            **kwargs: Additional Discord message options.

        Returns:
            True if message was sent successfully.
        """
        webhook_url = self.config["webhook_url"]

        # Build payload with embeds for rich formatting
        payload: dict[str, Any] = {"content": message}

        # Add embeds for specific events
        embeds = self._build_embeds(event)
        if embeds:
            payload["embeds"] = embeds

        # Add optional overrides
        if self.config.get("username"):
            payload["username"] = self.config["username"]
        if self.config.get("avatar_url"):
            payload["avatar_url"] = self.config["avatar_url"]

        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            # Discord returns 204 on success
            return response.status_code in (200, 204)

    def _build_embeds(
        self,
        event: NotificationEvent | None,
    ) -> list[dict[str, Any]]:
        """Build Discord embeds for rich message formatting."""
        if event is None:
            return []

        embed: dict[str, Any] = {
            "timestamp": event.timestamp.isoformat(),
            "footer": {"text": "Truthound Dashboard"},
        }

        if isinstance(event, ValidationFailedEvent):
            embed["title"] = "🚨 Validation Failed"
            embed["color"] = 0xFF0000 if event.has_critical else 0xFFA500
            embed["fields"] = [
                {"name": "Source", "value": event.source_name or "Unknown", "inline": True},
                {"name": "Severity", "value": event.severity, "inline": True},
                {"name": "Issues", "value": str(event.total_issues), "inline": True},
            ]
        elif isinstance(event, DriftDetectedEvent):
            embed["title"] = "📊 Drift Detected"
            embed["color"] = 0xFFA500
            embed["fields"] = [
                {"name": "Baseline", "value": event.baseline_source_name, "inline": True},
                {"name": "Current", "value": event.current_source_name, "inline": True},
                {"name": "Drift", "value": f"{event.drift_percentage:.1f}%", "inline": True},
            ]
        elif isinstance(event, ScheduleFailedEvent):
            embed["title"] = "⏰ Schedule Failed"
            embed["color"] = 0xFF6B6B
            embed["fields"] = [
                {"name": "Schedule", "value": event.schedule_name, "inline": True},
                {"name": "Source", "value": event.source_name or "Unknown", "inline": True},
            ]
            if event.error_message:
                embed["fields"].append({"name": "Error", "value": event.error_message[:1024], "inline": False})
        elif isinstance(event, TestNotificationEvent):
            embed["title"] = "✅ Test Notification"
            embed["color"] = 0x00FF00
            embed["description"] = f"Channel: {event.channel_name}"
        else:
            return []

        return [embed]

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for Discord."""
        if isinstance(event, ValidationFailedEvent):
            emoji = "🚨" if event.has_critical else "⚠️"
            return f"{emoji} **Validation Failed** for `{event.source_name or 'Unknown'}`"

        elif isinstance(event, ScheduleFailedEvent):
            return f"⏰ **Schedule Failed**: `{event.schedule_name}`"

        elif isinstance(event, DriftDetectedEvent):
            return f"📊 **Drift Detected**: {event.drift_percentage:.1f}% drift"

        elif isinstance(event, TestNotificationEvent):
            return f"✅ **Test Notification** from truthound-dashboard"

        return self._default_format(event)


@ChannelRegistry.register("telegram")
class TelegramChannel(BaseNotificationChannel):
    """Telegram notification channel using Bot API.

    Configuration:
        bot_token: Telegram Bot API token
        chat_id: Target chat/group/channel ID
        parse_mode: Message parse mode (HTML or MarkdownV2)
        disable_notification: Send silently (default: False)

    Example config:
        {
            "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            "chat_id": "-1001234567890",
            "parse_mode": "HTML"
        }
    """

    channel_type = "telegram"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Telegram channel configuration schema."""
        return {
            "bot_token": {
                "type": "string",
                "required": True,
                "secret": True,
                "description": "Telegram Bot API token",
            },
            "chat_id": {
                "type": "string",
                "required": True,
                "description": "Target chat/group/channel ID",
            },
            "parse_mode": {
                "type": "string",
                "required": False,
                "default": "HTML",
                "description": "Message parse mode (HTML or MarkdownV2)",
            },
            "disable_notification": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Send message silently",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification via Telegram Bot API.

        Args:
            message: Message text (supports HTML or Markdown).
            event: Optional triggering event.
            **kwargs: Additional Telegram API options.

        Returns:
            True if message was sent successfully.
        """
        bot_token = self.config["bot_token"]
        chat_id = self.config["chat_id"]
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": self.config.get("parse_mode", "HTML"),
        }

        if self.config.get("disable_notification"):
            payload["disable_notification"] = True

        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=payload)
            result = response.json()
            return result.get("ok", False)

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for Telegram with HTML."""
        if isinstance(event, ValidationFailedEvent):
            emoji = "🚨" if event.has_critical else "⚠️"
            return (
                f"{emoji} <b>Validation Failed</b>\n\n"
                f"<b>Source:</b> {event.source_name or 'Unknown'}\n"
                f"<b>Severity:</b> {event.severity}\n"
                f"<b>Issues:</b> {event.total_issues}"
            )

        elif isinstance(event, ScheduleFailedEvent):
            return (
                f"⏰ <b>Schedule Failed</b>\n\n"
                f"<b>Schedule:</b> {event.schedule_name}\n"
                f"<b>Source:</b> {event.source_name or 'Unknown'}\n"
                f"<b>Error:</b> {event.error_message or 'Validation failed'}"
            )

        elif isinstance(event, DriftDetectedEvent):
            return (
                f"📊 <b>Drift Detected</b>\n\n"
                f"<b>Baseline:</b> {event.baseline_source_name}\n"
                f"<b>Current:</b> {event.current_source_name}\n"
                f"<b>Drift:</b> {event.drifted_columns}/{event.total_columns} columns "
                f"({event.drift_percentage:.1f}%)"
            )

        elif isinstance(event, TestNotificationEvent):
            return (
                f"✅ <b>Test Notification</b>\n\n"
                f"This is a test from truthound-dashboard.\n"
                f"<b>Channel:</b> {event.channel_name}"
            )

        return self._default_format(event)


@ChannelRegistry.register("pagerduty")
class PagerDutyChannel(BaseNotificationChannel):
    """PagerDuty notification channel using Events API v2.

    Configuration:
        routing_key: PagerDuty Events API v2 routing/integration key
        severity: Default severity (critical, error, warning, info)
        component: Optional component name
        group: Optional logical grouping
        class_type: Optional class/type of event

    Example config:
        {
            "routing_key": "your-32-char-routing-key",
            "severity": "error",
            "component": "data-quality"
        }
    """

    channel_type = "pagerduty"

    EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get PagerDuty channel configuration schema."""
        return {
            "routing_key": {
                "type": "string",
                "required": True,
                "secret": True,
                "description": "PagerDuty Events API v2 routing key",
            },
            "severity": {
                "type": "string",
                "required": False,
                "default": "error",
                "description": "Default severity (critical, error, warning, info)",
            },
            "component": {
                "type": "string",
                "required": False,
                "description": "Component name",
            },
            "group": {
                "type": "string",
                "required": False,
                "description": "Logical grouping",
            },
            "class_type": {
                "type": "string",
                "required": False,
                "description": "Event class/type",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        action: str = "trigger",
        dedup_key: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send event to PagerDuty.

        Args:
            message: Alert summary.
            event: Optional triggering event.
            action: Event action (trigger, acknowledge, resolve).
            dedup_key: Optional deduplication key.
            **kwargs: Additional PagerDuty event options.

        Returns:
            True if event was accepted.
        """
        routing_key = self.config["routing_key"]

        # Determine severity from event
        severity = self._determine_severity(event)

        # Build payload
        payload: dict[str, Any] = {
            "routing_key": routing_key,
            "event_action": action,
            "payload": {
                "summary": message[:1024],  # PagerDuty limit
                "severity": severity,
                "source": "truthound-dashboard",
                "timestamp": event.timestamp.isoformat() if event else None,
            },
        }

        # Add optional fields
        if dedup_key:
            payload["dedup_key"] = dedup_key
        elif event:
            # Generate dedup key from event
            payload["dedup_key"] = f"truthound-{event.event_type}-{event.source_id or 'global'}"

        if self.config.get("component"):
            payload["payload"]["component"] = self.config["component"]
        if self.config.get("group"):
            payload["payload"]["group"] = self.config["group"]
        if self.config.get("class_type"):
            payload["payload"]["class"] = self.config["class_type"]

        # Add custom details
        if event:
            payload["payload"]["custom_details"] = event.to_dict()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.EVENTS_API_URL, json=payload)
            return response.status_code == 202

    def _determine_severity(self, event: NotificationEvent | None) -> str:
        """Determine PagerDuty severity from event."""
        default_severity = self.config.get("severity", "error")

        if event is None:
            return default_severity

        if isinstance(event, ValidationFailedEvent):
            if event.has_critical:
                return "critical"
            elif event.has_high:
                return "error"
            return "warning"

        elif isinstance(event, ScheduleFailedEvent):
            return "error"

        elif isinstance(event, DriftDetectedEvent):
            return "warning" if event.has_high_drift else "info"

        elif isinstance(event, TestNotificationEvent):
            return "info"

        return default_severity

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for PagerDuty alert summary."""
        if isinstance(event, ValidationFailedEvent):
            return (
                f"Validation failed for {event.source_name or 'Unknown'}: "
                f"{event.total_issues} {event.severity} issues"
            )

        elif isinstance(event, ScheduleFailedEvent):
            return f"Scheduled validation failed: {event.schedule_name}"

        elif isinstance(event, DriftDetectedEvent):
            return (
                f"Data drift detected: {event.drifted_columns}/{event.total_columns} columns "
                f"({event.drift_percentage:.1f}%)"
            )

        elif isinstance(event, TestNotificationEvent):
            return f"Test alert from truthound-dashboard ({event.channel_name})"

        return self._default_format(event)


@ChannelRegistry.register("opsgenie")
class OpsGenieChannel(BaseNotificationChannel):
    """OpsGenie notification channel using Alert API.

    Configuration:
        api_key: OpsGenie API key
        priority: Default priority (P1-P5)
        tags: Optional list of tags
        team: Optional team name
        responders: Optional list of responders

    Example config:
        {
            "api_key": "your-opsgenie-api-key",
            "priority": "P3",
            "tags": ["data-quality", "automated"],
            "team": "data-platform"
        }
    """

    channel_type = "opsgenie"

    API_URL = "https://api.opsgenie.com/v2/alerts"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get OpsGenie channel configuration schema."""
        return {
            "api_key": {
                "type": "string",
                "required": True,
                "secret": True,
                "description": "OpsGenie API key",
            },
            "priority": {
                "type": "string",
                "required": False,
                "default": "P3",
                "description": "Default priority (P1-P5)",
            },
            "tags": {
                "type": "array",
                "required": False,
                "items": {"type": "string"},
                "description": "Alert tags",
            },
            "team": {
                "type": "string",
                "required": False,
                "description": "Team name",
            },
            "responders": {
                "type": "array",
                "required": False,
                "items": {"type": "object"},
                "description": "List of responders",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        alias: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send alert to OpsGenie.

        Args:
            message: Alert message.
            event: Optional triggering event.
            alias: Optional unique alert identifier.
            **kwargs: Additional OpsGenie alert options.

        Returns:
            True if alert was created.
        """
        api_key = self.config["api_key"]

        # Determine priority from event
        priority = self._determine_priority(event)

        # Build payload
        payload: dict[str, Any] = {
            "message": message[:130],  # OpsGenie message limit
            "priority": priority,
            "source": "truthound-dashboard",
        }

        # Add alias for deduplication
        if alias:
            payload["alias"] = alias
        elif event:
            payload["alias"] = f"truthound-{event.event_type}-{event.source_id or 'global'}"

        # Add description with full details
        if event:
            payload["description"] = self._build_description(event)

        # Add optional fields
        tags = list(self.config.get("tags", [])) + ["truthound"]
        payload["tags"] = tags

        if self.config.get("team"):
            payload["responders"] = [{"type": "team", "name": self.config["team"]}]
        elif self.config.get("responders"):
            payload["responders"] = self.config["responders"]

        # Add details
        if event:
            payload["details"] = {
                "event_type": event.event_type,
                "source_id": event.source_id,
                "source_name": event.source_name,
                "timestamp": event.timestamp.isoformat(),
            }

        headers = {
            "Authorization": f"GenieKey {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.API_URL, json=payload, headers=headers)
            return response.status_code == 202

    def _determine_priority(self, event: NotificationEvent | None) -> str:
        """Determine OpsGenie priority from event."""
        default_priority = self.config.get("priority", "P3")

        if event is None:
            return default_priority

        if isinstance(event, ValidationFailedEvent):
            if event.has_critical:
                return "P1"
            elif event.has_high:
                return "P2"
            return "P3"

        elif isinstance(event, ScheduleFailedEvent):
            return "P2"

        elif isinstance(event, DriftDetectedEvent):
            return "P3" if event.has_high_drift else "P4"

        elif isinstance(event, TestNotificationEvent):
            return "P5"

        return default_priority

    def _build_description(self, event: NotificationEvent) -> str:
        """Build detailed description for OpsGenie alert."""
        if isinstance(event, ValidationFailedEvent):
            return (
                f"Validation failed for source: {event.source_name or 'Unknown'}\n\n"
                f"Severity: {event.severity}\n"
                f"Total Issues: {event.total_issues}\n"
                f"Critical Issues: {event.has_critical}\n"
                f"High Severity Issues: {event.has_high}\n"
                f"Validation ID: {event.validation_id}"
            )

        elif isinstance(event, ScheduleFailedEvent):
            return (
                f"Scheduled validation failed\n\n"
                f"Schedule: {event.schedule_name}\n"
                f"Source: {event.source_name or 'Unknown'}\n"
                f"Error: {event.error_message or 'Validation failed'}"
            )

        elif isinstance(event, DriftDetectedEvent):
            return (
                f"Data drift detected between datasets\n\n"
                f"Baseline: {event.baseline_source_name}\n"
                f"Current: {event.current_source_name}\n"
                f"Drifted Columns: {event.drifted_columns}/{event.total_columns}\n"
                f"Drift Percentage: {event.drift_percentage:.1f}%"
            )

        return f"Event type: {event.event_type}"

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for OpsGenie alert (short)."""
        if isinstance(event, ValidationFailedEvent):
            return f"Validation failed: {event.source_name or 'Unknown'} ({event.severity})"

        elif isinstance(event, ScheduleFailedEvent):
            return f"Schedule failed: {event.schedule_name}"

        elif isinstance(event, DriftDetectedEvent):
            return f"Drift detected: {event.drift_percentage:.1f}%"

        elif isinstance(event, TestNotificationEvent):
            return f"Test alert: {event.channel_name}"

        return self._default_format(event)


@ChannelRegistry.register("teams")
class TeamsChannel(BaseNotificationChannel):
    """Microsoft Teams notification channel using webhooks.

    Configuration:
        webhook_url: Teams incoming webhook URL
        theme_color: Optional accent color (hex without #)

    Example config:
        {
            "webhook_url": "https://outlook.office.com/webhook/...",
            "theme_color": "fd9e4b"
        }
    """

    channel_type = "teams"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Teams channel configuration schema."""
        return {
            "webhook_url": {
                "type": "string",
                "required": True,
                "description": "Teams incoming webhook URL",
            },
            "theme_color": {
                "type": "string",
                "required": False,
                "default": "fd9e4b",
                "description": "Accent color (hex without #)",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to Microsoft Teams.

        Args:
            message: Message text.
            event: Optional triggering event.
            **kwargs: Additional Teams message options.

        Returns:
            True if message was sent successfully.
        """
        webhook_url = self.config["webhook_url"]

        # Build Adaptive Card payload
        payload = self._build_card(message, event)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            return response.status_code == 200

    def _build_card(
        self,
        message: str,
        event: NotificationEvent | None,
    ) -> dict[str, Any]:
        """Build Teams Adaptive Card payload."""
        theme_color = self.config.get("theme_color", "fd9e4b")

        # Build card content
        card: dict[str, Any] = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": message[:150],
            "sections": [],
        }

        # Build sections based on event type
        if isinstance(event, ValidationFailedEvent):
            card["title"] = "🚨 Validation Failed"
            card["sections"].append({
                "activityTitle": event.source_name or "Unknown Source",
                "activitySubtitle": f"Severity: {event.severity}",
                "facts": [
                    {"name": "Total Issues", "value": str(event.total_issues)},
                    {"name": "Critical", "value": "Yes" if event.has_critical else "No"},
                    {"name": "High", "value": "Yes" if event.has_high else "No"},
                    {"name": "Validation ID", "value": event.validation_id[:8] + "..."},
                ],
                "markdown": True,
            })

        elif isinstance(event, ScheduleFailedEvent):
            card["title"] = "⏰ Schedule Failed"
            card["sections"].append({
                "activityTitle": event.schedule_name,
                "activitySubtitle": event.source_name or "Unknown Source",
                "facts": [
                    {"name": "Error", "value": event.error_message or "Validation failed"},
                ],
                "markdown": True,
            })

        elif isinstance(event, DriftDetectedEvent):
            card["title"] = "📊 Drift Detected"
            card["sections"].append({
                "activityTitle": "Data Drift Analysis",
                "facts": [
                    {"name": "Baseline", "value": event.baseline_source_name},
                    {"name": "Current", "value": event.current_source_name},
                    {"name": "Drifted Columns", "value": f"{event.drifted_columns}/{event.total_columns}"},
                    {"name": "Drift %", "value": f"{event.drift_percentage:.1f}%"},
                ],
                "markdown": True,
            })

        elif isinstance(event, TestNotificationEvent):
            card["title"] = "✅ Test Notification"
            card["sections"].append({
                "activityTitle": "truthound-dashboard",
                "activitySubtitle": f"Channel: {event.channel_name}",
                "text": "This is a test notification.",
                "markdown": True,
            })

        else:
            card["title"] = "Truthound Notification"
            card["sections"].append({
                "text": message,
                "markdown": True,
            })

        return card

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for Teams."""
        if isinstance(event, ValidationFailedEvent):
            return (
                f"Validation failed for {event.source_name or 'Unknown'}: "
                f"{event.total_issues} issues ({event.severity})"
            )

        elif isinstance(event, ScheduleFailedEvent):
            return f"Schedule '{event.schedule_name}' failed"

        elif isinstance(event, DriftDetectedEvent):
            return (
                f"Drift detected: {event.drifted_columns} columns "
                f"({event.drift_percentage:.1f}%)"
            )

        elif isinstance(event, TestNotificationEvent):
            return "Test notification from truthound-dashboard"

        return self._default_format(event)


@ChannelRegistry.register("github")
class GitHubChannel(BaseNotificationChannel):
    """GitHub notification channel for creating issues.

    Configuration:
        token: GitHub personal access token
        owner: Repository owner
        repo: Repository name
        labels: Optional list of labels to apply
        assignees: Optional list of assignees

    Example config:
        {
            "token": "ghp_xxxxxxxxxxxxxxxxxxxx",
            "owner": "myorg",
            "repo": "data-quality",
            "labels": ["data-quality", "automated"],
            "assignees": ["data-team-lead"]
        }
    """

    channel_type = "github"

    API_URL = "https://api.github.com"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get GitHub channel configuration schema."""
        return {
            "token": {
                "type": "string",
                "required": True,
                "secret": True,
                "description": "GitHub personal access token",
            },
            "owner": {
                "type": "string",
                "required": True,
                "description": "Repository owner",
            },
            "repo": {
                "type": "string",
                "required": True,
                "description": "Repository name",
            },
            "labels": {
                "type": "array",
                "required": False,
                "items": {"type": "string"},
                "description": "Labels to apply to issues",
            },
            "assignees": {
                "type": "array",
                "required": False,
                "items": {"type": "string"},
                "description": "Users to assign",
            },
        }

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        title: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """Create GitHub issue for notification.

        Args:
            message: Issue body.
            event: Optional triggering event.
            title: Optional title override.
            **kwargs: Additional issue options.

        Returns:
            True if issue was created.
        """
        token = self.config["token"]
        owner = self.config["owner"]
        repo = self.config["repo"]

        # Build issue title
        if title is None:
            title = self._build_title(event)

        # Build issue body
        body = self._build_body(message, event)

        # Build payload
        payload: dict[str, Any] = {
            "title": title,
            "body": body,
        }

        # Add optional fields
        labels = list(self.config.get("labels", [])) + ["truthound-alert"]
        payload["labels"] = labels

        if self.config.get("assignees"):
            payload["assignees"] = self.config["assignees"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        url = f"{self.API_URL}/repos/{owner}/{repo}/issues"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code == 201

    def _build_title(self, event: NotificationEvent | None) -> str:
        """Build issue title from event."""
        if event is None:
            return "[Truthound] Alert"

        if isinstance(event, ValidationFailedEvent):
            return f"[Truthound] Validation Failed: {event.source_name or 'Unknown'}"

        elif isinstance(event, ScheduleFailedEvent):
            return f"[Truthound] Schedule Failed: {event.schedule_name}"

        elif isinstance(event, DriftDetectedEvent):
            return f"[Truthound] Drift Detected: {event.baseline_source_name}"

        elif isinstance(event, TestNotificationEvent):
            return f"[Truthound] Test Issue: {event.channel_name}"

        return f"[Truthound] {event.event_type}"

    def _build_body(self, message: str, event: NotificationEvent | None) -> str:
        """Build issue body with markdown formatting."""
        body_parts = [
            "## Truthound Dashboard Alert",
            "",
            message,
            "",
        ]

        if event:
            body_parts.extend([
                "## Details",
                "",
                f"- **Event Type:** `{event.event_type}`",
                f"- **Timestamp:** {event.timestamp.isoformat()}",
            ])

            if event.source_id:
                body_parts.append(f"- **Source ID:** `{event.source_id}`")
            if event.source_name:
                body_parts.append(f"- **Source Name:** {event.source_name}")

            if isinstance(event, ValidationFailedEvent):
                body_parts.extend([
                    "",
                    "### Validation Summary",
                    "",
                    f"| Metric | Value |",
                    f"|--------|-------|",
                    f"| Severity | {event.severity} |",
                    f"| Total Issues | {event.total_issues} |",
                    f"| Critical | {'Yes' if event.has_critical else 'No'} |",
                    f"| High | {'Yes' if event.has_high else 'No'} |",
                    f"| Validation ID | `{event.validation_id}` |",
                ])

            elif isinstance(event, DriftDetectedEvent):
                body_parts.extend([
                    "",
                    "### Drift Summary",
                    "",
                    f"| Metric | Value |",
                    f"|--------|-------|",
                    f"| Baseline | {event.baseline_source_name} |",
                    f"| Current | {event.current_source_name} |",
                    f"| Drifted Columns | {event.drifted_columns}/{event.total_columns} |",
                    f"| Drift % | {event.drift_percentage:.1f}% |",
                ])

        body_parts.extend([
            "",
            "---",
            "_This issue was automatically created by truthound-dashboard._",
        ])

        return "\n".join(body_parts)

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for GitHub issue body."""
        if isinstance(event, ValidationFailedEvent):
            return (
                f"A validation failure has been detected.\n\n"
                f"**Source:** {event.source_name or 'Unknown'}\n"
                f"**Severity:** {event.severity}\n"
                f"**Total Issues:** {event.total_issues}"
            )

        elif isinstance(event, ScheduleFailedEvent):
            return (
                f"A scheduled validation has failed.\n\n"
                f"**Schedule:** {event.schedule_name}\n"
                f"**Source:** {event.source_name or 'Unknown'}\n"
                f"**Error:** {event.error_message or 'Validation failed'}"
            )

        elif isinstance(event, DriftDetectedEvent):
            return (
                f"Data drift has been detected between datasets.\n\n"
                f"**Baseline:** {event.baseline_source_name}\n"
                f"**Current:** {event.current_source_name}\n"
                f"**Drift:** {event.drift_percentage:.1f}%"
            )

        elif isinstance(event, TestNotificationEvent):
            return (
                f"This is a test issue created by truthound-dashboard.\n\n"
                f"**Channel:** {event.channel_name}"
            )

        return self._default_format(event)
