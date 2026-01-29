from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import emails
import jinja2
import keble_exceptions
import mjml

from .schemas import EmailSettingABC


class AsyncEmailSender:
    @classmethod
    async def use_template(
        cls,
        mjml_template: Optional[Union[str, Path]] = None,
        html_template: Optional[Union[str, Path]] = None,
        environment: Optional[Dict[str, Any]] = None,
    ) -> str:
        assert html_template is not None or mjml_template is not None
        assert not (html_template and mjml_template)

        jinja_env = jinja2.Environment()
        if html_template:
            template_str = Path(html_template).read_text()
        else:
            if not mjml_template:
                raise keble_exceptions.ServerSideMissingParams(
                    admin_note="mjml_template is None and html_template is None",
                    alert_admin=True,
                    missing_params="mjml_template or html_template (at least one is required)",
                )
            template_str = Path(mjml_template).read_text()

        compiled = jinja_env.from_string(template_str)
        rendered = compiled.render(environment or {})

        return rendered if html_template else mjml.mjml_to_html(rendered).html

    @classmethod
    async def _asend_with_smtp(
        cls,
        *,
        subject: str,
        recipient_email: str,
        sender_email: str,
        sender_name: str,
        smtp_user: str,
        smtp_password: str,
        smtp_host: str,
        smtp_port: int,
        smtp_tls: bool,
        smtp_ssl: bool,
        html: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachment_path: Optional[Union[str, Path]] = None,
        attachment_paths: Optional[List[Union[str, Path]]] = None,
    ) -> Dict[str, Any]:
        """Send an email using SMTP with the provided settings.

        This method handles the actual email sending logic using the emails library.
        """
        message = emails.Message(
            subject=subject,
            html=html,
            mail_from=(sender_name, sender_email),
            cc=cc,
            bcc=bcc,
        )

        # Attach files
        for path in ([attachment_path] if attachment_path else []) + (
            attachment_paths or []
        ):
            data = Path(path).read_bytes()
            filename = Path(path).name
            message.attach(data=data, filename=filename)

        # Set up SMTP options
        smtp_options = {
            "host": smtp_host,
            "port": smtp_port,
            "user": smtp_user,
            "password": smtp_password,
            "tls": smtp_tls,
            "ssl": smtp_ssl,
        }

        # Send email using the emails library's built-in send method
        response = message.send(to=recipient_email, smtp=smtp_options)

        success = response.status_code == 250

        return {
            "response": response,
            "status_code": response.status_code,
            "success": success,
            "smtp_host": smtp_host,
            "html": html,
            "text": message.text,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "email_to": recipient_email,
            "time": datetime.now(timezone.utc),
        }

    @classmethod
    async def asend(
        cls,
        *,
        mjml_template: Optional[Union[str, Path]] = None,
        html_template: Optional[Union[str, Path]] = None,
        html: Optional[str] = None,
        environment: Optional[Dict[str, Any]] = None,
        settings: Optional[EmailSettingABC] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_tls: Optional[bool] = None,
        smtp_ssl: Optional[bool] = None,
        subject: str,
        recipient_email: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachment_path: Optional[Union[str, Path]] = None,
        attachment_paths: Optional[List[Union[str, Path]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if not html:
            html = await cls.use_template(mjml_template, html_template, environment)
        sender_email = settings.sender_email if settings else sender_email
        sender_name = settings.sender_name if settings else sender_name
        smtp_user = settings.smtp_user if settings else smtp_user
        smtp_password = settings.smtp_password if settings else smtp_password
        smtp_host = settings.smtp_host if settings else smtp_host
        smtp_port = settings.smtp_port if settings else smtp_port
        smtp_tls = settings.smtp_tls if settings else smtp_tls
        smtp_ssl = settings.smtp_ssl if settings else smtp_ssl
        if sender_email is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="sender_email is None",
                alert_admin=True,
                missing_params="sender_email",
            )
        if sender_name is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="sender_name is None",
                alert_admin=True,
                missing_params="sender_name",
            )
        if smtp_user is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="smtp_user is None",
                alert_admin=True,
                missing_params="smtp_user",
            )
        if smtp_password is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="smtp_password is None",
                alert_admin=True,
                missing_params="smtp_password",
            )
        if smtp_host is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="smtp_host is None",
                alert_admin=True,
                missing_params="smtp_host",
            )
        if smtp_port is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="smtp_port is None",
                alert_admin=True,
                missing_params="smtp_port",
            )
        if smtp_tls is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="smtp_tls is None",
                alert_admin=True,
                missing_params="smtp_tls",
            )
        if smtp_ssl is None:
            raise keble_exceptions.ServerSideMissingParams(
                admin_note="smtp_ssl is None",
                alert_admin=True,
                missing_params="smtp_ssl",
            )

        return await cls._asend_with_smtp(
            subject=subject,
            recipient_email=recipient_email,
            sender_email=sender_email,
            sender_name=sender_name,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_tls=smtp_tls,
            smtp_ssl=smtp_ssl,
            html=html,
            cc=cc,
            bcc=bcc,
            attachment_path=attachment_path,
            attachment_paths=attachment_paths,
        )
