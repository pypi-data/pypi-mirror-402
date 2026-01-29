from __future__ import annotations

import json
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Mapping

import httpx


def _success(result: Dict[str, Any]) -> Dict[str, Any]:
	return {"success": True, **result}


def _failure(error: str, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
	payload = {"success": False, "error": error}
	if extra:
		payload.update(extra)
	return payload


def _render_template(template: str, context: Mapping[str, Any]) -> str:
	"""
	Render a template with {{variable}} placeholders.

	Supports:
	- {{alert_name}} or {{rule_name}} - alert/rule name
	- {{table}} - table name
	- {{schema}} - schema name
	- {{operation}} - INSERT/UPDATE/DELETE
	- {{timestamp}} - event timestamp
	- {{field_name}} - direct access to any data field (e.g., {{location_id}})
	- {{data}} - full data as JSON
	- {{data.field_name}} - specific field from data
	- {{old_data.field_name}} - specific field from old data (for UPDATE/DELETE)
	"""
	result = template

	# First, handle nested data access like {{data.field_name}}
	def replace_nested(match):
		path = match.group(1)
		parts = path.split('.')
		value = context
		try:
			for part in parts:
				if isinstance(value, dict):
					value = value.get(part, '')
				else:
					return ''
			if isinstance(value, (dict, list)):
				return json.dumps(value, ensure_ascii=False)
			return str(value) if value is not None else ''
		except:
			return ''

	result = re.sub(r'\{\{([^}]+)\}\}', replace_nested, result)
	return result


def _build_default_slack_message(context: Mapping[str, Any]) -> str:
	"""Build default Slack message in Markdown format."""
	operation = context.get('operation', 'UNKNOWN')
	table = context.get('table', 'unknown')
	schema = context.get('schema', 'public')
	data = context.get('data', {})

	emoji = {'INSERT': '🟢', 'UPDATE': '🟡', 'DELETE': '🔴'}.get(operation, '⚪')

	message = f"{emoji} *{operation}* on `{schema}.{table}`\n\n"
	message += "```\n"
	message += json.dumps(data, indent=2, ensure_ascii=False)
	message += "\n```"

	return message


def _build_default_html_email(context: Mapping[str, Any]) -> tuple[str, str]:
	"""Build default HTML email body. Returns (html, plain_text)."""
	operation = context.get('operation', 'UNKNOWN')
	table = context.get('table', 'unknown')
	schema = context.get('schema', 'public')
	data = context.get('data', {})
	timestamp = context.get('timestamp', '')

	color = {'INSERT': '#28a745', 'UPDATE': '#ffc107', 'DELETE': '#dc3545'}.get(operation, '#6c757d')
	emoji = {'INSERT': '🟢', 'UPDATE': '🟡', 'DELETE': '🔴'}.get(operation, '⚪')

	html = f"""
<!DOCTYPE html>
<html>
<head>
	<style>
		body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
		.container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
		.header {{ background: {color}; color: white; padding: 20px; text-align: center; }}
		.header h1 {{ margin: 0; font-size: 24px; }}
		.content {{ padding: 20px; }}
		.meta {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
		.meta-item {{ margin: 5px 0; }}
		.meta-label {{ font-weight: bold; color: #495057; }}
		.data-section {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 6px; overflow-x: auto; }}
		.data-section pre {{ margin: 0; font-family: 'Consolas', 'Monaco', monospace; font-size: 13px; white-space: pre-wrap; }}
		.footer {{ background: #f8f9fa; padding: 15px; text-align: center; color: #6c757d; font-size: 12px; }}
	</style>
</head>
<body>
	<div class="container">
		<div class="header">
			<h1>{emoji} {operation}</h1>
		</div>
		<div class="content">
			<div class="meta">
				<div class="meta-item"><span class="meta-label">Table:</span> {schema}.{table}</div>
				<div class="meta-item"><span class="meta-label">Operation:</span> {operation}</div>
				<div class="meta-item"><span class="meta-label">Timestamp:</span> {timestamp}</div>
			</div>
			<h3>Data</h3>
			<div class="data-section">
				<pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
			</div>
		</div>
		<div class="footer">
			Sent by CDC Stream
		</div>
	</div>
</body>
</html>
"""

	plain = f"""
{emoji} {operation} on {schema}.{table}

Timestamp: {timestamp}

Data:
{json.dumps(data, indent=2, ensure_ascii=False)}

--
Sent by CDC Stream
"""

	return html, plain


class SlackDispatcher:
	@staticmethod
	def send(config: Mapping[str, Any], message: str, extra: Mapping[str, Any] | None = None) -> Dict[str, Any]:
		webhook_url = config.get("webhook_url")
		if not webhook_url:
			return _failure("Missing webhook_url")

		# Check for custom template
		template = config.get("message_template")
		if template and extra:
			# Use extra directly as context - it already has alert_name, data fields, etc.
			rendered_message = _render_template(template, extra)
		elif extra:
			# Use default formatted message
			rendered_message = _build_default_slack_message(extra)
		else:
			rendered_message = message

		payload = {
			"blocks": [
				{
					"type": "section",
					"text": {"type": "mrkdwn", "text": rendered_message}
				}
			],
			"text": message  # Fallback for notifications
		}

		try:
			with httpx.Client(timeout=10) as client:
				resp = client.post(str(webhook_url), json=payload)
				return _success({"status_code": resp.status_code, "body": resp.text})
		except Exception as exc:
			return _failure(str(exc))


class WebhookDispatcher:
	@staticmethod
	def send(config: Mapping[str, Any], payload: Mapping[str, Any], event_data: Mapping[str, Any] | None = None) -> Dict[str, Any]:
		# Support multiple URL field names from frontend
		url = config.get("url") or config.get("webhook_url")
		if not url:
			port = config.get("webhook_port")
			endpoint = config.get("webhook_endpoint", "/")
			if port:
				url = f"http://localhost:{port}{endpoint}"

		if not url:
			return _failure("Missing webhook url or port/endpoint")

		# Get body template and replace placeholders
		body_template = config.get("body")
		if body_template and event_data:
			body_str = body_template
			for key, value in event_data.items():
				placeholder = "{{" + str(key) + "}}"
				quoted_placeholder = '"' + placeholder + '"'

				# Check if placeholder is already quoted in template
				if quoted_placeholder in body_str:
					# User wrote "{{field}}" - replace with proper JSON value
					# json.dumps handles escaping and adds quotes for strings
					replacement = json.dumps(value, ensure_ascii=False, default=str)
					body_str = body_str.replace(quoted_placeholder, replacement)
				elif placeholder in body_str:
					# User wrote {{field}} without quotes (for values)
					# Preserve type: number stays number, string gets quoted
					if isinstance(value, (int, float)) and not isinstance(value, bool):
						# Number - no quotes
						replacement = str(value)
					elif isinstance(value, bool):
						# Boolean - lowercase
						replacement = "true" if value else "false"
					elif value is None:
						replacement = "null"
					else:
						# String or other - add quotes
						replacement = json.dumps(str(value), ensure_ascii=False)
					body_str = body_str.replace(placeholder, replacement)

			try:
				payload = json.loads(body_str)
			except json.JSONDecodeError as e:
				# Show first 300 chars of the problematic JSON for debugging
				preview = body_str[:300] + "..." if len(body_str) > 300 else body_str
				return _failure(f"Invalid JSON: {e}. Result: {preview}")

		headers = {"Content-Type": "application/json"}
		try:
			with httpx.Client(timeout=10) as client:
				resp = client.post(str(url), json=payload, headers=headers)
				return _success({"status_code": resp.status_code, "body": resp.text})
		except httpx.ConnectError:
			# Connection refused - no server listening on that port
			return _failure(f"Connection refused. No server is listening at {url}. Make sure your webhook receiver is running.")
		except httpx.TimeoutException:
			return _failure(f"Connection timed out while trying to reach {url}")
		except Exception as exc:
			error_msg = str(exc)
			# Make Windows error messages more user-friendly
			if "10061" in error_msg or "Connection refused" in error_msg.lower():
				return _failure(f"Connection refused. No server is listening at {url}. Make sure your webhook receiver is running.")
			return _failure(error_msg)


class RestApiDispatcher:
	@staticmethod
	def send(config: Mapping[str, Any], payload: Mapping[str, Any], event_data: Mapping[str, Any] | None = None) -> Dict[str, Any]:
		url = config.get("api_url")
		if not url:
			return _failure("Missing api_url")

		method = config.get("http_method", "POST").upper()
		auth_type = config.get("auth_type", "none")

		# If using mock endpoint (/api/rest-echo/), auto-add require_auth parameter for testing
		if "/api/rest-echo" in str(url) and auth_type and auth_type != "none":
			separator = "&" if "?" in url else "?"
			if auth_type == "bearer":
				url = f"{url}{separator}require_auth=bearer"
			elif auth_type == "basic":
				url = f"{url}{separator}require_auth=basic"
			elif auth_type == "api_key":
				api_key_name = config.get("api_key_name") or "X-API-Key"
				url = f"{url}{separator}require_auth=api_key&api_key_header={api_key_name}"

		# Build headers
		headers = {"Content-Type": "application/json"}

		# Parse custom headers (supports both array of {key, value} and dict)
		custom_headers = config.get("headers") or config.get("custom_headers")
		if custom_headers:
			try:
				if isinstance(custom_headers, str):
					custom_headers = json.loads(custom_headers)

				if isinstance(custom_headers, list):
					# Array format: [{"key": "X-Header", "value": "val"}, ...]
					for h in custom_headers:
						key = str(h.get("key") or "").strip()
						value = str(h.get("value") or "").strip()
						if key and value:
							headers[key] = value
				elif isinstance(custom_headers, dict):
					# Dict format: {"X-Header": "val", ...}
					for k, v in custom_headers.items():
						key = str(k or "").strip()
						value = str(v or "").strip()
						if key and value:
							headers[key] = value
			except json.JSONDecodeError:
				pass  # Ignore invalid JSON

		# Authentication
		auth = None
		if auth_type == "bearer":
			token = config.get("auth_token")
			if token:
				headers["Authorization"] = f"Bearer {token}"
		elif auth_type == "basic":
			username = config.get("auth_username")
			password = config.get("auth_password")
			if username and password:
				auth = (username, password)
		elif auth_type == "api_key":
			key_name = config.get("api_key_name") or "X-API-Key"
			key_value = config.get("api_key_value")
			key_location = config.get("api_key_location") or "header"
			if key_value:
				if key_location == "query":
					# Add to URL as query parameter
					separator = "&" if "?" in url else "?"
					url = f"{url}{separator}{key_name}={key_value}"
				else:
					# Default: add to header
					headers[key_name] = key_value

		# Process body template (same logic as WebhookDispatcher)
		body_template = config.get("body")
		request_payload = payload
		if body_template and event_data:
			body_str = body_template
			for key, value in event_data.items():
				placeholder = "{{" + str(key) + "}}"
				quoted_placeholder = '"' + placeholder + '"'

				if quoted_placeholder in body_str:
					# Key or quoted value: json.dumps preserves type
					replacement = json.dumps(value, ensure_ascii=False, default=str)
					body_str = body_str.replace(quoted_placeholder, replacement)
				elif placeholder in body_str:
					# Unquoted value: preserve type (number stays number)
					if isinstance(value, (int, float)) and not isinstance(value, bool):
						replacement = str(value)
					elif isinstance(value, bool):
						replacement = "true" if value else "false"
					elif value is None:
						replacement = "null"
					else:
						replacement = json.dumps(str(value), ensure_ascii=False)
					body_str = body_str.replace(placeholder, replacement)

			try:
				request_payload = json.loads(body_str)
			except json.JSONDecodeError as e:
				preview = body_str[:300] + "..." if len(body_str) > 300 else body_str
				return _failure(f"Invalid JSON: {e}. Result: {preview}")

		try:
			with httpx.Client(timeout=30) as client:
				if method == "GET":
					resp = client.get(str(url), headers=headers, auth=auth)
				elif method == "POST":
					resp = client.post(str(url), json=request_payload, headers=headers, auth=auth)
				elif method == "PUT":
					resp = client.put(str(url), json=request_payload, headers=headers, auth=auth)
				elif method == "PATCH":
					resp = client.patch(str(url), json=request_payload, headers=headers, auth=auth)
				elif method == "DELETE":
					resp = client.delete(str(url), headers=headers, auth=auth)
				else:
					return _failure(f"Unsupported HTTP method: {method}")

				return _success({"status_code": resp.status_code, "body": resp.text})
		except httpx.ConnectError:
			return _failure(f"Connection refused. Cannot reach {url}. Make sure the API endpoint is accessible.")
		except httpx.TimeoutException:
			return _failure(f"Connection timed out while trying to reach {url}")
		except Exception as exc:
			error_msg = str(exc)
			if "10061" in error_msg or "Connection refused" in error_msg.lower():
				return _failure(f"Connection refused. Cannot reach {url}. Make sure the API endpoint is accessible.")
			return _failure(error_msg)


class SmtpDispatcher:
	@staticmethod
	def send(config: Mapping[str, Any], subject: str, body: str, event_data: Mapping[str, Any] | None = None) -> Dict[str, Any]:
		# Support both naming conventions (UI: smtp_host vs standard: host)
		host = config.get("host") or config.get("smtp_host")
		port = int(config.get("port") or config.get("smtp_port") or 587)
		username = config.get("username") or config.get("smtp_username")
		password = config.get("password") or config.get("smtp_password")
		use_tls = bool(config.get("use_tls", True))
		mail_from = config.get("from") or config.get("from_email")
		mail_to = config.get("to") or config.get("to_emails")

		if not all([host, mail_from, mail_to]):
			return _failure("Missing SMTP config fields (host, from, to)")

		# Use event_data directly as context - it already has alert_name, data fields, etc.
		context = event_data or {}

		# Check for custom body template
		body_template = config.get("body_template")
		use_html = config.get("use_html", True)

		if body_template and context:
			# User provided custom template
			rendered_body = _render_template(body_template, context)
			if use_html:
				html_body = rendered_body
				plain_body = re.sub('<[^<]+?>', '', rendered_body)  # Strip HTML tags for plain text
			else:
				html_body = None
				plain_body = rendered_body
		elif context:
			# Use default beautiful HTML template
			html_body, plain_body = _build_default_html_email(context)
		else:
			# Fallback to simple body
			html_body = None
			plain_body = body

		# Render subject template if provided
		subject_template = config.get("subject_template")
		if subject_template and context:
			subject = _render_template(subject_template, context)
		elif context and not subject:
			operation = context.get('operation', 'Event')
			table = context.get('table', 'table')
			subject = f"[CDC] {operation} on {table}"

		try:
			if html_body:
				# Send multipart email (HTML + plain text fallback)
				msg = MIMEMultipart('alternative')
				msg["Subject"] = subject
				msg["From"] = mail_from
				msg["To"] = mail_to if isinstance(mail_to, str) else ", ".join(mail_to)

				part1 = MIMEText(plain_body, 'plain', 'utf-8')
				part2 = MIMEText(html_body, 'html', 'utf-8')
				msg.attach(part1)
				msg.attach(part2)
			else:
				msg = EmailMessage()
				msg["Subject"] = subject
				msg["From"] = mail_from
				msg["To"] = mail_to if isinstance(mail_to, str) else ", ".join(mail_to)
				msg.set_content(plain_body)

			if use_tls:
				context_ssl = ssl.create_default_context()
				with smtplib.SMTP(host, port, timeout=10) as server:
					server.starttls(context=context_ssl)
					if username and password:
						server.login(username, password)
					server.send_message(msg)
			else:
				with smtplib.SMTP(host, port, timeout=10) as server:
					if username and password:
						server.login(username, password)
					server.send_message(msg)
			return _success({})
		except Exception as exc:
			return _failure(str(exc))
