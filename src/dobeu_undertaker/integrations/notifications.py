"""
Notification service for Dobeu Undertaker.

Sends notifications via multiple channels:
- Slack webhooks
- Microsoft Teams webhooks
- Email (SMTP)
- SMS (via configured provider)
"""

import os
from pathlib import Path
from typing import Any

import httpx

from dobeu_undertaker.config.schema import NotificationConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Multi-channel notification service.

    Sends compliance alerts and reports via configured channels.
    """

    def __init__(self, config: NotificationConfig) -> None:
        """
        Initialize the notification service.

        Args:
            config: Notification configuration
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def send_compliance_alert(
        self,
        repo_path: Path,
        results: list[Any],
    ) -> None:
        """
        Send compliance alert via all configured channels.

        Args:
            repo_path: Repository that was scanned
            results: Scan results from agents
        """
        if not self.config.enabled:
            logger.debug("Notifications disabled, skipping alert")
            return

        # Calculate severity
        critical_count = sum(
            len([i for i in r.issues if i.get("severity") == "critical"])
            for r in results
        )
        high_count = sum(
            len([i for i in r.issues if i.get("severity") == "high"])
            for r in results
        )

        # Check notification thresholds
        should_notify = (
            (self.config.notify_on_critical and critical_count > 0)
            or (self.config.notify_on_high and high_count > 0)
        )

        if not should_notify:
            logger.debug("No notifications needed based on severity thresholds")
            return

        # Send to all configured channels
        tasks = []

        if self.config.slack_webhook_url:
            tasks.append(self._send_slack_alert(repo_path, results))

        if self.config.teams_webhook_url:
            tasks.append(self._send_teams_alert(repo_path, results))

        if self.config.email_recipients and self.config.smtp_host:
            tasks.append(self._send_email_alert(repo_path, results))

        import asyncio
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_slack_alert(
        self,
        repo_path: Path,
        results: list[Any],
    ) -> None:
        """Send alert to Slack webhook."""
        if not self.config.slack_webhook_url:
            return

        client = await self._get_client()

        # Build Slack message
        total_issues = sum(len(r.issues) for r in results)
        critical_count = sum(
            len([i for i in r.issues if i.get("severity") == "critical"])
            for r in results
        )

        # Determine color based on severity
        if critical_count > 0:
            color = "danger"
            emoji = "🚨"
        else:
            color = "warning"
            emoji = "⚠️"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Dobeu Undertaker Compliance Alert",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n{repo_path.name}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Issues:*\n{total_issues}",
                    },
                ],
            },
        ]

        # Add agent results
        for result in results:
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "warning": "⚠️",
            }.get(result.status, "❓")

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{status_emoji} *{result.agent_name}*: {len(result.issues)} issues",
                },
            })

        payload = {
            "channel": self.config.slack_channel,
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks,
                }
            ],
        }

        try:
            response = await client.post(self.config.slack_webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Slack notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def _send_teams_alert(
        self,
        repo_path: Path,
        results: list[Any],
    ) -> None:
        """Send alert to Microsoft Teams webhook."""
        if not self.config.teams_webhook_url:
            return

        client = await self._get_client()

        # Build Teams Adaptive Card
        total_issues = sum(len(r.issues) for r in results)
        critical_count = sum(
            len([i for i in r.issues if i.get("severity") == "critical"])
            for r in results
        )

        # Build facts for each agent
        facts = []
        for result in results:
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "warning": "⚠️",
            }.get(result.status, "❓")

            facts.append({
                "name": f"{status_emoji} {result.agent_name}",
                "value": f"{len(result.issues)} issues",
            })

        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000" if critical_count > 0 else "FFA500",
            "summary": f"Compliance Alert: {total_issues} issues in {repo_path.name}",
            "sections": [
                {
                    "activityTitle": "🔍 Dobeu Undertaker Compliance Alert",
                    "activitySubtitle": f"Repository: {repo_path.name}",
                    "facts": facts,
                    "markdown": True,
                }
            ],
        }

        try:
            response = await client.post(self.config.teams_webhook_url, json=card)
            response.raise_for_status()
            logger.info("Teams notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")

    async def _send_email_alert(
        self,
        repo_path: Path,
        results: list[Any],
    ) -> None:
        """Send alert via email (SMTP)."""
        if not self.config.smtp_host or not self.config.email_recipients:
            return

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Build email content
        total_issues = sum(len(r.issues) for r in results)

        html_content = f"""
<html>
<body>
<h2>🔍 Dobeu Undertaker Compliance Alert</h2>
<p><strong>Repository:</strong> {repo_path.name}</p>
<p><strong>Total Issues:</strong> {total_issues}</p>

<h3>Agent Results</h3>
<table border="1" cellpadding="5" cellspacing="0">
<tr><th>Agent</th><th>Status</th><th>Issues</th></tr>
"""

        for result in results:
            html_content += f"""
<tr>
    <td>{result.agent_name}</td>
    <td>{result.status.upper()}</td>
    <td>{len(result.issues)}</td>
</tr>
"""

        html_content += """
</table>
<p><em>Generated by Dobeu Undertaker</em></p>
</body>
</html>
"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Compliance Alert] {total_issues} issues in {repo_path.name}"
        msg["From"] = self.config.smtp_user or "dobeu-undertaker@dobeu.net"
        msg["To"] = ", ".join(self.config.email_recipients)

        msg.attach(MIMEText(html_content, "html"))

        try:
            password = os.environ.get(self.config.smtp_password_env_var)

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                if self.config.smtp_user and password:
                    server.login(self.config.smtp_user, password)
                server.send_message(msg)

            logger.info("Email notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    async def send_success_notification(
        self,
        repo_path: Path,
        message: str = "All compliance checks passed!",
    ) -> None:
        """
        Send a success notification.

        Args:
            repo_path: Repository that was scanned
            message: Success message
        """
        if not self.config.enabled:
            return

        if self.config.slack_webhook_url:
            client = await self._get_client()

            payload = {
                "channel": self.config.slack_channel,
                "attachments": [
                    {
                        "color": "good",
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"✅ *{repo_path.name}*: {message}",
                                },
                            }
                        ],
                    }
                ],
            }

            try:
                await client.post(self.config.slack_webhook_url, json=payload)
            except Exception as e:
                logger.error(f"Failed to send success notification: {e}")
