from __future__ import annotations

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models.functions import TruncDate, ExtractHour
from django.db.models import Count
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os
import httpx
import socket
import io
import threading
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

from .models import DataSource, NotificationChannel, Rule, TriggerLog, AnomalyDetector, AnomalyLog, FieldStats

# Global dict to track running webhook test servers
_webhook_test_servers = {}
from .serializers import (
	DataSourceSerializer,
	NotificationChannelSerializer,
	RuleSerializer,
	TriggerLogSerializer,
	AnomalyDetectorSerializer,
	AnomalyLogSerializer,
	FieldStatsSerializer,
)
from cdc_stream.dispatchers import SlackDispatcher, WebhookDispatcher, SmtpDispatcher


class NotificationChannelViewSet(viewsets.ModelViewSet):
	queryset = NotificationChannel.objects.all().order_by("-id")
	serializer_class = NotificationChannelSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["name", "channel_type"]
	ordering_fields = ["id", "created_at", "name"]

	@action(detail=False, methods=["post"])
	def check_port(self, request):
		"""Check if a port is available on localhost"""
		port = request.data.get("port")
		if not port:
			return Response({"error": "Port is required"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			port = int(port)
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(1)
			result = sock.connect_ex(('localhost', port))
			sock.close()

			if result == 0:
				# Port is in use (connection successful)
				return Response({"available": False, "message": f"Port {port} is already in use"})
			else:
				# Port is available (connection refused)
				return Response({"available": True, "message": f"Port {port} is available"})
		except ValueError:
			return Response({"error": "Invalid port number"}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=["post"])
	def start_test_server(self, request):
		"""Start a temporary webhook test server on specified port"""
		global _webhook_test_servers

		port = request.data.get("port")
		endpoint = request.data.get("endpoint", "/")
		body_template = request.data.get("body_template", "{}")

		if not port:
			return Response({"error": "Port is required"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			port = int(port)
		except ValueError:
			return Response({"error": "Invalid port number"}, status=status.HTTP_400_BAD_REQUEST)

		# Check if already running on this port
		if port in _webhook_test_servers:
			return Response({"error": f"Test server already running on port {port}"}, status=status.HTTP_400_BAD_REQUEST)

		# Check if port is available
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(1)
		result = sock.connect_ex(('localhost', port))
		sock.close()
		if result == 0:
			return Response({"error": f"Port {port} is already in use by another application"}, status=status.HTTP_400_BAD_REQUEST)

		# Create test data for substitution (system variables)
		test_values = {
			"alert_name": "Test Alert",
			"alert_description": "This is a test alert description",
			"triggered_at": timezone.now().isoformat(),
			"table_name": "orders",
			"schema_name": "public",
			"matched_rows_count": "5",
		}

		# Common field test values (for table fields)
		field_test_values = {
			"id": "12345",
			"user_id": "67890",
			"customer_id": "C-001",
			"order_id": "ORD-2025-001",
			"name": "John Doe",
			"email": "john.doe@example.com",
			"phone": "+1-555-0123",
			"amount": "299.99",
			"price": "49.99",
			"total": "599.99",
			"quantity": "3",
			"count": "10",
			"status": "active",
			"type": "standard",
			"category": "electronics",
			"description": "Sample product description",
			"message": "Test message content",
			"created_at": timezone.now().isoformat(),
			"updated_at": timezone.now().isoformat(),
			"date": timezone.now().strftime("%Y-%m-%d"),
			"time": timezone.now().strftime("%H:%M:%S"),
			"is_active": "true",
			"enabled": "true",
			"verified": "true",
		}

		# Store received requests
		received_requests = []

		# Create handler with closure over body_template and endpoint
		class WebhookTestHandler(BaseHTTPRequestHandler):
			def log_message(self, format, *args):
				pass  # Suppress logging

			def do_POST(self):
				content_length = int(self.headers.get('Content-Length', 0))
				post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'

				try:
					received_json = json.loads(post_data.decode('utf-8'))
				except:
					received_json = {"raw": post_data.decode('utf-8', errors='ignore')}

				# Prepare response body with test values
				response_body = body_template

				# First replace system variables
				for key, value in test_values.items():
					response_body = response_body.replace("{{" + key + "}}", str(value))

				# Then replace known field names with realistic values
				for key, value in field_test_values.items():
					response_body = response_body.replace("{{" + key + "}}", str(value))

				# Replace any remaining {{field}} with a sample value based on field name
				def replace_remaining(match):
					field_name = match.group(1)
					# Try to guess a reasonable value based on field name
					if 'id' in field_name.lower():
						return '"sample-id-001"'
					elif 'date' in field_name.lower() or 'time' in field_name.lower():
						return f'"{timezone.now().isoformat()}"'
					elif 'amount' in field_name.lower() or 'price' in field_name.lower() or 'total' in field_name.lower():
						return '99.99'
					elif 'count' in field_name.lower() or 'num' in field_name.lower() or 'qty' in field_name.lower():
						return '5'
					elif 'is_' in field_name.lower() or 'has_' in field_name.lower():
						return 'true'
					elif 'email' in field_name.lower():
						return '"test@example.com"'
					elif 'name' in field_name.lower():
						return '"Test Name"'
					else:
						return f'"sample_{field_name}"'

				response_body = re.sub(r'\{\{(\w+)\}\}', replace_remaining, response_body)

				# Store the request
				received_requests.append({
					"timestamp": timezone.now().isoformat(),
					"path": self.path,
					"body": received_json
				})

				self.send_response(200)
				self.send_header('Content-Type', 'application/json')
				self.end_headers()

				try:
					# Try to return as valid JSON
					json.loads(response_body)
					self.wfile.write(response_body.encode('utf-8'))
				except:
					# If not valid JSON, wrap in a message
					self.wfile.write(json.dumps({
						"success": True,
						"message": "Webhook received",
						"configured_response": response_body
					}).encode('utf-8'))

			def do_GET(self):
				self.send_response(200)
				self.send_header('Content-Type', 'application/json')
				self.end_headers()
				self.wfile.write(json.dumps({
					"status": "running",
					"port": port,
					"endpoint": endpoint,
					"received_requests": len(received_requests)
				}).encode('utf-8'))

		try:
			server = HTTPServer(('127.0.0.1', port), WebhookTestHandler)
			server.received_requests = received_requests

			# Run server in a thread
			thread = threading.Thread(target=server.serve_forever, daemon=True)
			thread.start()

			# Wait for server to be ready (max 3 seconds)
			import time
			max_attempts = 30
			for attempt in range(max_attempts):
				try:
					test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					test_sock.settimeout(0.5)
					result = test_sock.connect_ex(('127.0.0.1', port))
					test_sock.close()
					if result == 0:
						break
				except:
					pass
				time.sleep(0.1)
			else:
				# Server didn't start properly
				try:
					server.shutdown()
				except:
					pass
				return Response({
					"error": f"Test server failed to start on port {port}"
				}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

			_webhook_test_servers[port] = {
				"server": server,
				"thread": thread,
				"endpoint": endpoint,
				"body_template": body_template,
				"started_at": timezone.now().isoformat(),
				"received_requests": received_requests
			}

			return Response({
				"success": True,
				"message": f"Test server started on http://localhost:{port}{endpoint}",
				"port": port,
				"endpoint": endpoint
			})
		except OSError as e:
			if "already in use" in str(e).lower() or e.errno == 10048:  # Windows error for address in use
				return Response({
					"error": f"Port {port} is already in use by another application"
				}, status=status.HTTP_400_BAD_REQUEST)
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		except Exception as e:
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=["post"])
	def stop_test_server(self, request):
		"""Stop a running webhook test server"""
		global _webhook_test_servers

		port = request.data.get("port")
		if not port:
			return Response({"error": "Port is required"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			port = int(port)
		except ValueError:
			return Response({"error": "Invalid port number"}, status=status.HTTP_400_BAD_REQUEST)

		if port not in _webhook_test_servers:
			return Response({"error": f"No test server running on port {port}"}, status=status.HTTP_404_NOT_FOUND)

		try:
			server_info = _webhook_test_servers[port]
			server_info["server"].shutdown()
			received_count = len(server_info.get("received_requests", []))
			del _webhook_test_servers[port]

			return Response({
				"success": True,
				"message": f"Test server on port {port} stopped",
				"received_requests_count": received_count
			})
		except Exception as e:
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=["get"])
	def test_server_status(self, request):
		"""Get status of running test servers"""
		global _webhook_test_servers

		port = request.query_params.get("port")

		if port:
			try:
				port = int(port)
			except ValueError:
				return Response({"error": "Invalid port number"}, status=status.HTTP_400_BAD_REQUEST)

			if port in _webhook_test_servers:
				info = _webhook_test_servers[port]
				return Response({
					"running": True,
					"port": port,
					"endpoint": info["endpoint"],
					"started_at": info["started_at"],
					"received_requests_count": len(info.get("received_requests", []))
				})
			else:
				return Response({"running": False, "port": port})

		# Return all running servers
		servers = []
		for p, info in _webhook_test_servers.items():
			servers.append({
				"port": p,
				"endpoint": info["endpoint"],
				"started_at": info["started_at"],
				"received_requests_count": len(info.get("received_requests", []))
			})

		return Response({"servers": servers})

	@action(detail=False, methods=["post"])
	def send_test_request(self, request):
		"""Process body template with test values and return the result"""
		global _webhook_test_servers

		port = request.data.get("port")
		body_template = request.data.get("body_template", "{}")

		if not port:
			return Response({"error": "Port is required"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			port = int(port)
		except ValueError:
			return Response({"error": "Invalid port number"}, status=status.HTTP_400_BAD_REQUEST)

		# Check if test server is registered
		if port not in _webhook_test_servers:
			return Response({
				"error": f"No test server running on port {port}. Start the test server first."
			}, status=status.HTTP_400_BAD_REQUEST)

		# Get body template from stored server info or use provided one
		server_info = _webhook_test_servers[port]
		template = body_template if body_template != "{}" else server_info.get("body_template", "{}")

		# Create test data for substitution (system variables)
		test_values = {
			"alert_name": "Test Alert",
			"alert_description": "This is a test alert description",
			"triggered_at": timezone.now().isoformat(),
			"table_name": "orders",
			"schema_name": "public",
			"matched_rows_count": "5",
		}

		# Common field test values (for table fields)
		field_test_values = {
			"id": "12345",
			"user_id": "67890",
			"customer_id": "C-001",
			"order_id": "ORD-2025-001",
			"name": "John Doe",
			"email": "john.doe@example.com",
			"phone": "+1-555-0123",
			"amount": "299.99",
			"price": "49.99",
			"total": "599.99",
			"quantity": "3",
			"count": "10",
			"status": "active",
			"type": "standard",
			"category": "electronics",
			"description": "Sample product description",
			"message": "Test message content",
			"created_at": timezone.now().isoformat(),
			"updated_at": timezone.now().isoformat(),
			"date": timezone.now().strftime("%Y-%m-%d"),
			"time": timezone.now().strftime("%H:%M:%S"),
			"is_active": "true",
			"enabled": "true",
			"verified": "true",
		}

		# Process the template
		response_body = template

		# First replace system variables
		for key, value in test_values.items():
			response_body = response_body.replace("{{" + key + "}}", str(value))

		# Then replace known field names with realistic values
		for key, value in field_test_values.items():
			response_body = response_body.replace("{{" + key + "}}", str(value))

		# Replace any remaining {{field}} with a sample value based on field name
		def replace_remaining(match):
			field_name = match.group(1)
			if 'id' in field_name.lower():
				return '"sample-id-001"'
			elif 'date' in field_name.lower() or 'time' in field_name.lower():
				return f'"{timezone.now().isoformat()}"'
			elif 'amount' in field_name.lower() or 'price' in field_name.lower() or 'total' in field_name.lower():
				return '99.99'
			elif 'count' in field_name.lower() or 'num' in field_name.lower() or 'qty' in field_name.lower():
				return '5'
			elif 'is_' in field_name.lower() or 'has_' in field_name.lower():
				return 'true'
			elif 'email' in field_name.lower():
				return '"test@example.com"'
			elif 'name' in field_name.lower():
				return '"Test Name"'
			else:
				return f'"sample_{field_name}"'

		response_body = re.sub(r'\{\{(\w+)\}\}', replace_remaining, response_body)

		# Try to parse as JSON for nice formatting
		try:
			response_json = json.loads(response_body)
		except:
			response_json = {"raw_response": response_body}

		# Update received requests list (this is shared with the HTTPServer handler)
		if "received_requests" in server_info:
			server_info["received_requests"].append({
				"timestamp": timezone.now().isoformat(),
				"path": server_info.get("endpoint", "/"),
				"body": {"test": True, "source": "send_test_request"},
				"response": response_json
			})

		return Response({
			"success": True,
			"status_code": 200,
			"response": response_json
		})

	@action(detail=False, methods=["post"])
	def preview_template(self, request):
		"""Preview a webhook body template with test values substituted"""
		body_template = request.data.get("body_template", "{}")

		# Create test data for substitution (system variables)
		test_values = {
			"alert_name": "Test Alert",
			"alert_description": "This is a test alert description",
			"triggered_at": timezone.now().isoformat(),
			"table_name": "orders",
			"schema_name": "public",
			"matched_rows_count": "5",
		}

		# Common field test values (for table fields)
		field_test_values = {
			"id": "12345",
			"user_id": "67890",
			"customer_id": "C-001",
			"order_id": "ORD-2025-001",
			"name": "John Doe",
			"email": "john.doe@example.com",
			"phone": "+1-555-0123",
			"amount": "299.99",
			"price": "49.99",
			"total": "599.99",
			"quantity": "3",
			"count": "10",
			"status": "active",
			"type": "standard",
			"category": "electronics",
			"description": "Sample product description",
			"message": "Test message content",
			"created_at": timezone.now().isoformat(),
			"updated_at": timezone.now().isoformat(),
			"date": timezone.now().strftime("%Y-%m-%d"),
			"time": timezone.now().strftime("%H:%M:%S"),
			"is_active": "true",
			"enabled": "true",
			"verified": "true",
		}

		# Process the template
		response_body = body_template

		# First replace system variables
		for key, value in test_values.items():
			response_body = response_body.replace("{{" + key + "}}", str(value))

		# Then replace known field names with realistic values
		for key, value in field_test_values.items():
			response_body = response_body.replace("{{" + key + "}}", str(value))

		# Replace any remaining {{field}} with a sample value based on field name
		def replace_remaining(match):
			field_name = match.group(1)
			if 'id' in field_name.lower():
				return '"sample-id-001"'
			elif 'date' in field_name.lower() or 'time' in field_name.lower():
				return f'"{timezone.now().isoformat()}"'
			elif 'amount' in field_name.lower() or 'price' in field_name.lower() or 'total' in field_name.lower():
				return '99.99'
			elif 'count' in field_name.lower() or 'num' in field_name.lower() or 'qty' in field_name.lower():
				return '5'
			elif 'is_' in field_name.lower() or 'has_' in field_name.lower():
				return 'true'
			elif 'email' in field_name.lower():
				return '"test@example.com"'
			elif 'name' in field_name.lower():
				return '"Test Name"'
			else:
				return f'"sample_{field_name}"'

		response_body = re.sub(r'\{\{(\w+)\}\}', replace_remaining, response_body)

		# Try to parse as JSON for nice formatting
		try:
			response_json = json.loads(response_body)
		except:
			response_json = {"raw_response": response_body}

		return Response({
			"success": True,
			"status_code": 200,
			"response": response_json
		})

	@action(detail=False, methods=["post"])
	def test_email(self, request):
		"""Send a test email via SMTP"""
		smtp_host = request.data.get("smtp_host")
		smtp_port = request.data.get("smtp_port")
		smtp_username = request.data.get("smtp_username")
		smtp_password = request.data.get("smtp_password")
		from_email = request.data.get("from_email")
		to_emails = request.data.get("to_emails")
		use_tls = request.data.get("use_tls", True)

		if not all([smtp_host, smtp_port, smtp_username, smtp_password, from_email, to_emails]):
			return Response({"success": False, "error": "All SMTP fields are required"}, status=status.HTTP_400_BAD_REQUEST)

		import smtplib
		from email.mime.text import MIMEText
		from email.mime.multipart import MIMEMultipart

		# Parse recipients
		recipients = [email.strip() for email in to_emails.split(",") if email.strip()]
		if not recipients:
			return Response({"success": False, "error": "No valid recipient emails"}, status=status.HTTP_400_BAD_REQUEST)

		# Create message
		msg = MIMEMultipart("alternative")
		msg["Subject"] = "🔔 CDCStream Test Alert"
		msg["From"] = from_email
		msg["To"] = ", ".join(recipients)

		# HTML content
		html_content = f"""
		<html>
		<body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
			<div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
				<h1 style="color: #333; margin-bottom: 20px;">🔔 CDCStream Test Alert</h1>
				<div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin-bottom: 20px;">
					<strong style="color: #2e7d32;">Status:</strong> Test Successful ✅
				</div>
				<p style="color: #666;">This is a test email from CDCStream to verify your SMTP configuration is working correctly.</p>
				<hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
				<p style="color: #999; font-size: 12px;">
					<strong>Time:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
					<strong>From:</strong> CDCStream Alert System
				</p>
			</div>
		</body>
		</html>
		"""

		text_content = f"""
CDCStream Test Alert

Status: Test Successful ✅

This is a test email from CDCStream to verify your SMTP configuration is working correctly.

Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
From: CDCStream Alert System
		"""

		msg.attach(MIMEText(text_content, "plain"))
		msg.attach(MIMEText(html_content, "html"))

		try:
			port = int(smtp_port)

			if use_tls:
				server = smtplib.SMTP(smtp_host, port, timeout=15)
				server.starttls()
			else:
				server = smtplib.SMTP(smtp_host, port, timeout=15)

			server.login(smtp_username, smtp_password)
			server.sendmail(from_email, recipients, msg.as_string())
			server.quit()

			return Response({
				"success": True,
				"message": f"Test email sent to {', '.join(recipients)}"
			})
		except smtplib.SMTPAuthenticationError as e:
			return Response({
				"success": False,
				"error": "Authentication failed. Check your username and password. For Gmail, use an App Password."
			})
		except smtplib.SMTPConnectError as e:
			return Response({
				"success": False,
				"error": f"Could not connect to {smtp_host}:{smtp_port}. Check your host and port settings."
			})
		except smtplib.SMTPException as e:
			return Response({
				"success": False,
				"error": f"SMTP error: {str(e)}"
			})
		except Exception as e:
			return Response({
				"success": False,
				"error": str(e)
			})

	@action(detail=False, methods=["post"])
	def test_slack(self, request):
		"""Send a test message to Slack webhook"""
		webhook_url = request.data.get("webhook_url")

		if not webhook_url:
			return Response({"success": False, "error": "Webhook URL is required"}, status=status.HTTP_400_BAD_REQUEST)

		# Slack message format
		slack_message = {
			"text": "🔔 *CDCStream Test Alert*",
			"blocks": [
				{
					"type": "header",
					"text": {
						"type": "plain_text",
						"text": "🔔 CDCStream Test Alert",
						"emoji": True
					}
				},
				{
					"type": "section",
					"fields": [
						{
							"type": "mrkdwn",
							"text": "*Status:*\nTest Successful ✅"
						},
						{
							"type": "mrkdwn",
							"text": f"*Time:*\n{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
						}
					]
				},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": "This is a test message from CDCStream to verify your Slack webhook integration is working correctly."
					}
				},
				{
					"type": "context",
					"elements": [
						{
							"type": "mrkdwn",
							"text": "Sent from *CDCStream Alert System*"
						}
					]
				}
			]
		}

		try:
			response = httpx.post(
				webhook_url,
				json=slack_message,
				headers={"Content-Type": "application/json"},
				timeout=15.0
			)

			if response.status_code == 200:
				return Response({
					"success": True,
					"message": "Test message sent to Slack successfully"
				})
			else:
				return Response({
					"success": False,
					"error": f"Slack returned status {response.status_code}: {response.text}"
				})
		except httpx.ConnectError:
			return Response({
				"success": False,
				"error": "Could not connect to Slack. Check if the webhook URL is correct."
			})
		except httpx.TimeoutException:
			return Response({
				"success": False,
				"error": "Request to Slack timed out."
			})
		except Exception as e:
			return Response({
				"success": False,
				"error": str(e)
			})

	@action(detail=False, methods=["post"], permission_classes=[AllowAny])
	def send_webhook_test(self, request):
		"""Send a test POST request to an external webhook URL"""
		webhook_url = request.data.get("webhook_url")

		if not webhook_url:
			return Response({"success": False, "error": "Webhook URL is required"}, status=status.HTTP_400_BAD_REQUEST)

		# Always use fixed test body - ignore user's body template for testing
		json_body = {
			"test": True,
			"source": "CDCStream Webhook Test",
			"timestamp": timezone.now().isoformat(),
			"message": "This is a test webhook from CDCStream",
			"alert": {
				"name": "Test Alert",
				"description": "Webhook connectivity test"
			},
			"event": {
				"table": "orders",
				"schema": "public",
				"operation": "INSERT"
			},
			"sample_data": {
				"id": 12345,
				"customer_name": "John Doe",
				"amount": 299.99,
				"status": "completed"
			}
		}

		# Send the request to the webhook URL
		try:
			response = httpx.post(
				webhook_url,
				json=json_body,
				headers={"Content-Type": "application/json"},
				timeout=15.0
			)

			try:
				response_json = response.json()
			except:
				response_json = {"raw_response": response.text[:500] if response.text else "Empty response"}

			return Response({
				"success": True,
				"status_code": response.status_code,
				"webhook_url": webhook_url,
				"response": response_json
			})
		except httpx.ConnectError as e:
			return Response({
				"success": False,
				"error": f"Could not connect to {webhook_url}. Check if the URL is correct and the service is running.",
				"webhook_url": webhook_url
			})
		except httpx.TimeoutException:
			return Response({
				"success": False,
				"error": f"Request to {webhook_url} timed out after 15 seconds.",
				"webhook_url": webhook_url
			})
		except Exception as e:
			return Response({
				"success": False,
				"error": str(e),
				"webhook_url": webhook_url
			})

	# NOTE: test_rest_api action removed - use TestRestApiView instead via /api/channels/test_rest_api/

	@action(detail=True, methods=["post"])
	def test(self, request, pk=None):
		channel = self.get_object()
		cfg = channel.config or {}
		result = None

		# Test data for template substitution
		test_event_data = {
			"alert_name": "Test Alert",
			"alert_description": "This is a test alert from CDCStream",
			"triggered_at": timezone.now().isoformat(),
			"table_name": "test_table",
			"schema_name": "test_schema",
			"matched_rows_count": 1,
		}

		if channel.channel_type == "slack":
			result = SlackDispatcher.send(cfg, "CDCStream test message", {"test": True})
		elif channel.channel_type == "webhook":
			# For webhook, first check if port is listening
			webhook_url = cfg.get("webhook_url", "")
			if "localhost" in webhook_url or "127.0.0.1" in webhook_url:
				try:
					# Extract port from URL
					import re
					port_match = re.search(r':(\d+)', webhook_url)
					if port_match:
						port = int(port_match.group(1))
						sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						sock.settimeout(2)
						connection_result = sock.connect_ex(('localhost', port))
						sock.close()
						if connection_result != 0:
							result = {
								"success": False,
								"error": f"Cannot connect to localhost:{port}. Make sure the webhook receiver is running and listening on this port."
							}
							return Response(result)
				except Exception as e:
					pass  # Continue with actual test if port check fails

			result = WebhookDispatcher.send(cfg, {"message": "cdc-stream test", "test": True}, test_event_data)
		elif channel.channel_type in ("smtp", "email"):
			result = SmtpDispatcher.send(cfg, "CDCStream Test", "This is a test email from CDCStream.")
		elif channel.channel_type == "rest_api":
			from cdc_stream.dispatchers import RestApiDispatcher
			result = RestApiDispatcher.send(cfg, {"message": "cdc-stream test", "test": True}, test_event_data)
		else:
			result = {"success": False, "error": f"Unknown channel type {channel.channel_type}"}
		return Response(result)


class DataSourceViewSet(viewsets.ModelViewSet):
	queryset = DataSource.objects.all().order_by("-id")
	serializer_class = DataSourceSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["name", "connector_type", "topic", "status"]
	ordering_fields = ["id", "created_at", "name"]

	def create(self, request, *args, **kwargs):
		"""Create connection after verifying database permissions."""
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		# Check permissions before creating the connection
		config = serializer.validated_data.get('connector_config', {})
		connector_type = serializer.validated_data.get('connector_type', '').lower()

		perm_check = self._check_database_permissions(config, connector_type)

		if not perm_check['success']:
			return Response({
				"error": "Cannot create connection: Insufficient database permissions",
				"permission_error": perm_check['error'],
				"missing_permissions": perm_check.get('missing', []),
				"solution": perm_check.get('solution', 'Check database user permissions.'),
				"can_retry": True
			}, status=status.HTTP_400_BAD_REQUEST)

		# Permissions OK - create the connection
		instance = serializer.save()
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def _check_database_permissions(self, config, connector_type):
		"""Check if database user has required permissions for CDC."""
		result = {'success': True, 'error': None, 'missing': [], 'solution': None}

		host = config.get('host') or config.get('hostname')
		if not host:
			return result  # No config, skip check

		try:
			if connector_type == "postgres":
				import psycopg2
				conn = psycopg2.connect(
					host=host,
					port=config.get('port', 5432),
					user=config.get('user'),
					password=config.get('password'),
					dbname=config.get('database') or config.get('dbname'),
					connect_timeout=5
				)
				cur = conn.cursor()

				# Check CREATE privilege on public schema
				cur.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")
				can_create = cur.fetchone()[0]
				if not can_create:
					result['missing'].append("CREATE ON SCHEMA public")

				# Check USAGE privilege
				cur.execute("SELECT has_schema_privilege(current_user, 'public', 'USAGE')")
				can_usage = cur.fetchone()[0]
				if not can_usage:
					result['missing'].append("USAGE ON SCHEMA public")

				cur.close()
				conn.close()

				if result['missing']:
					result['success'] = False
					result['error'] = f"Missing permissions: {', '.join(result['missing'])}"
					result['solution'] = "Run: GRANT USAGE, CREATE ON SCHEMA public TO your_user;\nGRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;"

			elif connector_type == "sqlserver":
				windows_auth = config.get('windows_auth', False)
				try:
					if windows_auth:
						import pyodbc
						server_str = host
						port = config.get('port', 1433)
						if int(port) != 1433:
							server_str = f"{host},{port}"
						conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_str};DATABASE={config.get('database')};Trusted_Connection=yes"
						conn = pyodbc.connect(conn_str)
					else:
						import pymssql
						conn = pymssql.connect(
							server=host,
							user=config.get('user'),
							password=config.get('password'),
							database=config.get('database')
						)

					cur = conn.cursor()

					# Check CREATE TABLE permission
					cur.execute("SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CREATE TABLE')")
					can_create_table = cur.fetchone()[0]
					if not can_create_table:
						result['missing'].append("CREATE TABLE")

					# Check ALTER permission on dbo schema
					cur.execute("SELECT HAS_PERMS_BY_NAME('dbo', 'SCHEMA', 'ALTER')")
					can_alter = cur.fetchone()[0]
					if not can_alter:
						result['missing'].append("ALTER ON SCHEMA dbo")

					cur.close()
					conn.close()

					if result['missing']:
						result['success'] = False
						result['error'] = f"Missing permissions: {', '.join(result['missing'])}"
						result['solution'] = "Run: GRANT CREATE TABLE TO your_user;\nGRANT ALTER ON SCHEMA::dbo TO your_user;\nGRANT SELECT, INSERT, DELETE ON SCHEMA::dbo TO your_user;"
				except ImportError:
					pass  # Driver not installed

			elif connector_type == "mysql":
				import pymysql
				conn = pymysql.connect(
					host=host,
					port=config.get('port', 3306),
					user=config.get('user'),
					password=config.get('password'),
					database=config.get('database')
				)
				cur = conn.cursor()
				cur.execute("SHOW GRANTS FOR CURRENT_USER")
				grants = cur.fetchall()
				grants_str = str(grants).upper()
				cur.close()
				conn.close()

				has_create = 'CREATE' in grants_str or 'ALL PRIVILEGES' in grants_str
				has_trigger = 'TRIGGER' in grants_str or 'ALL PRIVILEGES' in grants_str
				has_select = 'SELECT' in grants_str or 'ALL PRIVILEGES' in grants_str

				if not has_create:
					result['missing'].append("CREATE")
				if not has_trigger:
					result['missing'].append("TRIGGER")
				if not has_select:
					result['missing'].append("SELECT")

				if result['missing']:
					result['success'] = False
					result['error'] = f"Missing permissions: {', '.join(result['missing'])}"
					result['solution'] = f"Run: GRANT SELECT, INSERT, DELETE, CREATE, TRIGGER ON {config.get('database')}.* TO 'your_user'@'%';\nFLUSH PRIVILEGES;"

		except Exception as e:
			error_str = str(e).lower()
			if any(kw in error_str for kw in ['permission', 'denied', 'privilege', 'access denied', 'login failed']):
				result['success'] = False
				result['error'] = f"Connection/Permission error: {e}"
				result['solution'] = "Check username, password, and database permissions."
			# For connection errors (host unreachable, etc.), let it pass - better error from test_connection

		return result

	@action(detail=True, methods=["post"])
	def register_connector(self, request, pk=None):
		"""
		Kafka Connect üzerinde Debezium connector'ını kaydeder.
		Desteklenen tipler: postgres, mysql, sqlserver, mongodb
		"""
		ds = self.get_object()
		body = request.data or {}
		connector_type = (body.get("connector_type") or ds.connector_type or "").lower()
		if connector_type not in ("postgres", "mysql", "sqlserver", "mongodb"):
			return Response({"detail": "Unsupported connector_type"}, status=status.HTTP_400_BAD_REQUEST)
		connector_name = f"cdc-{ds.name}"

		def post_config(cfg):
			connect_url = settings.KAFKA_CONNECT_URL.rstrip("/") + "/connectors"
			with httpx.Client(timeout=15) as client:
				resp = client.post(connect_url, json=cfg)
				return resp

			# Convert localhost to host.docker.internal for Docker network access
		def get_docker_hostname(hostname):
			hostname = str(hostname).lower()
			if hostname in ("localhost", "127.0.0.1", "::1"):
				return "host.docker.internal"
			return hostname

		if connector_type == "postgres":
			required = ["database_hostname", "database_port", "database_user", "database_password", "database_dbname", "topic_prefix", "schema", "table"]
			missing = [k for k in required if not body.get(k)]
			if missing:
				return Response({"detail": f"Missing fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
			cfg = {
				"name": connector_name,
				"config": {
					"connector.class": "io.debezium.connector.postgresql.PostgresConnector",
					"database.hostname": get_docker_hostname(body["database_hostname"]),
					"database.port": str(body["database_port"]),
					"database.user": str(body["database_user"]),
					"database.password": str(body["database_password"]),
					"database.dbname": str(body["database_dbname"]),
					"slot.name": f"{connector_name}-slot",
					"publication.autocreate.mode": "filtered",
					"plugin.name": "pgoutput",
					"topic.prefix": str(body["topic_prefix"]),
					"tombstones.on.delete": "false",
					"snapshot.mode": "initial",
					"decimal.handling.mode": "string",
					"time.precision.mode": "connect",
					"table.include.list": f'{body["schema"]}.{body["table"]}',
				},
			}
			target_topic = f'{body["topic_prefix"]}.{body["schema"]}.{body["table"]}'
		elif connector_type == "mysql":
			required = ["database_hostname", "database_port", "database_user", "database_password", "database", "topic_prefix", "table"]
			missing = [k for k in required if not body.get(k)]
			if missing:
				return Response({"detail": f"Missing fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
			cfg = {
				"name": connector_name,
				"config": {
					"connector.class": "io.debezium.connector.mysql.MySqlConnector",
					"database.hostname": get_docker_hostname(body["database_hostname"]),
					"database.port": str(body["database_port"]),
					"database.user": str(body["database_user"]),
					"database.password": str(body["database_password"]),
					"database.include.list": str(body["database"]),
					"topic.prefix": str(body["topic_prefix"]),
					"snapshot.mode": "initial",
					"table.include.list": f'{body["database"]}.{body["table"]}',
				},
			}
			target_topic = f'{body["topic_prefix"]}.{body["database"]}.{body["table"]}'
		elif connector_type == "sqlserver":
			required = ["database_hostname", "database_port", "database_user", "database_password", "database", "topic_prefix", "schema", "table"]
			missing = [k for k in required if not body.get(k)]
			if missing:
				return Response({"detail": f"Missing fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
			cfg = {
				"name": connector_name,
				"config": {
					"connector.class": "io.debezium.connector.sqlserver.SqlServerConnector",
					"database.hostname": get_docker_hostname(body["database_hostname"]),
					"database.port": str(body["database_port"]),
					"database.user": str(body["database_user"]),
					"database.password": str(body["database_password"]),
					"database.names": str(body["database"]),
					"topic.prefix": str(body["topic_prefix"]),
					"snapshot.mode": "initial",
					"table.include.list": f'{body["database"]}.dbo.{body["table"]}' if not body.get("schema") else f'{body["database"]}.{body["schema"]}.{body["table"]}',
				},
			}
			dbschema = body.get("schema") or "dbo"
			target_topic = f'{body["topic_prefix"]}.{body["database"]}.{dbschema}.{body["table"]}'
		else:  # mongodb
			required = ["connection_string", "topic_prefix", "database", "collection"]
			missing = [k for k in required if not body.get(k)]
			if missing:
				return Response({"detail": f"Missing fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
			cfg = {
				"name": connector_name,
				"config": {
					"connector.class": "io.debezium.connector.mongodb.MongoDbConnector",
					"mongodb.connection.string": str(body["connection_string"]),
					"topic.prefix": str(body["topic_prefix"]),
					"database.include.list": str(body["database"]),
					"collection.include.list": f'{body["database"]}.{body["collection"]}',
					"snapshot.mode": "initial",
				},
			}
			target_topic = f'{body["topic_prefix"]}.{body["database"]}.{body["collection"]}'

		try:
			resp = post_config(cfg)
			if resp.status_code not in (200, 201, 409):
				return Response({"detail": "Connector creation failed", "status": resp.status_code, "body": resp.text}, status=resp.status_code)
		except Exception as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

		ds.topic = target_topic
		ds.status = "registered"
		ds.connector_type = connector_type
		ds.connector_config = body
		ds.save(update_fields=["topic", "status", "connector_type", "connector_config", "updated_at"])
		return Response({"ok": True, "topic": ds.topic, "connector": connector_name, "type": connector_type})
		connect_url = settings.KAFKA_CONNECT_URL.rstrip("/") + "/connectors"
		try:
			with httpx.Client(timeout=10) as client:
				resp = client.post(connect_url, json=config)
				if resp.status_code not in (200, 201, 409):  # 409 = already exists
					return Response({"detail": "Connector creation failed", "status": resp.status_code, "body": resp.text}, status=resp.status_code)
		except Exception as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
		# Update datasource topic and status
		ds.topic = f'{body["topic_prefix"]}.{body["schema"]}.{body["table"]}'
		ds.status = "registered"
		ds.connector_type = "postgres"
		ds.connector_config = {k: body[k] for k in required if k in body}
		ds.save(update_fields=["topic", "status", "connector_type", "connector_config", "updated_at"])
		return Response({"ok": True, "topic": ds.topic, "connector": connector_name})

	@action(detail=False, methods=["post"])
	def test_connection(self, request):
		body = request.data or {}
		host = body.get("host")
		try:
			port = int(body.get("port") or 0)
		except Exception:
			port = 0
		connector_type = (body.get("connector_type") or "").lower()
		reachable = False
		db_ok = False
		error_msg = None
		ssh_tunnel = None
		target_host = host
		target_port = port
		# Optional SSH tunnel
		ssh = body.get("ssh") or {}
		if ssh.get("enabled"):
			try:
				from sshtunnel import SSHTunnelForwarder  # type: ignore
				import paramiko  # type: ignore
				ssh_host = ssh.get("host")
				ssh_port = int(ssh.get("port") or 22)
				ssh_user = ssh.get("user")
				ssh_password = ssh.get("password")
				ssh_key = ssh.get("private_key")
				ssh_passphrase = ssh.get("passphrase")
				pkey = None
				if ssh_key:
					try:
						pkey = paramiko.RSAKey.from_private_key(io.StringIO(ssh_key), password=ssh_passphrase)  # type: ignore[arg-type]
					except Exception:
						try:
							pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(ssh_key), password=ssh_passphrase)  # type: ignore[arg-type]
						except Exception:
							pkey = None
				ssh_tunnel = SSHTunnelForwarder(
					(ssh_host, ssh_port),
					ssh_username=ssh_user,
					ssh_password=ssh_password if not pkey else None,
					ssh_pkey=pkey,
					remote_bind_address=(host, port),
					local_bind_address=("127.0.0.1", 0),
				)
				ssh_tunnel.start()
				target_host = "127.0.0.1"
				target_port = ssh_tunnel.local_bind_port
			except Exception as exc:
				error_msg = f"SSH tunnel error: {exc}"
		# TCP probe
		if target_host and target_port:
			try:
				with socket.create_connection((str(target_host), int(target_port)), timeout=3):
					reachable = True
			except Exception as exc:
				error_msg = str(exc)
		# Optional driver-level
		try:
			if connector_type == "postgres":
				try:
					import psycopg2  # type: ignore
					conn = psycopg2.connect(
						host=target_host,
						port=int(target_port),
						user=body.get("user"),
						password=body.get("password"),
						dbname=body.get("database"),
						connect_timeout=3,
					)
					conn.close()
					db_ok = True
				except Exception as e:
					db_ok = False
					err_str = str(e).lower()
					if 'authentication failed' in err_str or 'password' in err_str:
						error_msg = f"PostgreSQL: Authentication failed. Check username and password."
					elif 'does not exist' in err_str:
						error_msg = f"PostgreSQL: Database does not exist. Check database name."
					elif 'permission denied' in err_str:
						error_msg = f"PostgreSQL: Permission denied. User needs CONNECT privilege on the database."
					else:
						error_msg = f"PostgreSQL: {e}"
			elif connector_type == "mysql":
				try:
					import pymysql  # type: ignore
					conn = pymysql.connect(
						host=target_host,
						port=int(target_port),
						user=body.get("user"),
						password=body.get("password"),
						database=body.get("database"),
						connect_timeout=3,
					)
					conn.close()
					db_ok = True
				except Exception as e:
					db_ok = False
					err_str = str(e).lower()
					if 'access denied' in err_str or '1045' in str(e):
						error_msg = f"MySQL: Access denied. Check username and password."
					elif 'unknown database' in err_str or '1049' in str(e):
						error_msg = f"MySQL: Database does not exist. Check database name."
					else:
						error_msg = f"MySQL: {e}"
			elif connector_type == "mongodb":
				try:
					from pymongo import MongoClient  # type: ignore
					from pymongo.errors import PyMongoError
					if body.get("connection_string"):
						client = MongoClient(body.get("connection_string"), serverSelectionTimeoutMS=5000)
					else:
						client = MongoClient(host=target_host, port=int(target_port), username=body.get("user"), password=body.get("password"), serverSelectionTimeoutMS=5000)
					client.admin.command("ping")
					reachable = True  # MongoDB ping succeeded

					# Check if MongoDB is running as Replica Set (required for Change Streams)
					is_replica_set = False
					rs_error = None
					try:
						rs_status = client.admin.command("replSetGetStatus")
						is_replica_set = True
						rs_name = rs_status.get("set", "")
						rs_members = len(rs_status.get("members", []))
					except PyMongoError as rs_e:
						rs_error_str = str(rs_e).lower()
						if "not running with --replset" in rs_error_str or "no replset config" in rs_error_str:
							is_replica_set = False
							rs_error = "MongoDB is running in STANDALONE mode. Change Streams require Replica Set."
						else:
							# Some other error, might still be okay
							is_replica_set = False
							rs_error = str(rs_e)

					if not is_replica_set:
						db_ok = False
						error_msg = (
							"MongoDB: Replica Set required!\n\n"
							"CDCStream uses Change Streams which only work with Replica Set or Sharded Cluster.\n\n"
							"🔧 Solutions:\n"
							"1. Convert to single-node Replica Set:\n"
							"   - Add 'replSetName: rs0' to mongod.cfg\n"
							"   - Restart MongoDB\n"
							"   - Run: rs.initiate()\n\n"
							"2. Use MongoDB Atlas (free tier supports Change Streams)\n\n"
							"3. Use Docker: mongod --replSet rs0\n\n"
							f"Technical: {rs_error or 'Not a replica set'}"
						)
					else:
						db_ok = True

					client.close()
				except Exception as e:
					db_ok = False
					err_str = str(e).lower()
					if "authentication" in err_str or "auth failed" in err_str:
						error_msg = f"MongoDB: Authentication failed. Check username and password."
					elif "connection refused" in err_str or "server selection" in err_str:
						error_msg = f"MongoDB: Connection refused. Check if MongoDB is running and host/port are correct."
					else:
						error_msg = f"MongoDB: {e}"
			elif connector_type == "sqlserver":
				try:
					windows_auth = body.get("windows_auth", False)
					if windows_auth:
						# Use pyodbc for Windows Authentication
						import pyodbc  # type: ignore
						# Build server string with instance name support
						server_str = target_host
						if int(target_port) != 1433:
							server_str = f"{target_host},{target_port}"
						conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_str};DATABASE={body.get('database')};Trusted_Connection=yes;Connection Timeout=3"
						conn = pyodbc.connect(conn_str)
						conn.close()
						db_ok = True
					else:
						# Use pymssql for SQL Server Authentication
						import pymssql  # type: ignore
						# Build connection args
						conn_args = {
							"server": target_host,
							"user": body.get("user"),
							"password": body.get("password"),
							"database": body.get("database"),
							"login_timeout": 3,
						}
						# Only add port if not default
						if int(target_port) != 1433:
							conn_args["port"] = str(target_port)
						conn = pymssql.connect(**conn_args)
						conn.close()
						db_ok = True
				except Exception as e:
					db_ok = False
					err_str = str(e).lower()
					if 'login failed' in err_str or '18456' in str(e):
						error_msg = f"MSSQL: Login failed. Check username and password. For SQL Server Authentication, enable 'SQL Server and Windows Authentication mode' in SQL Server."
					elif 'cannot open database' in err_str:
						error_msg = f"MSSQL: Cannot open database. Check database name or user permissions."
					elif 'adaptive server connection failed' in err_str:
						error_msg = f"MSSQL: Connection failed. Check if SQL Server is running and accepting connections. Try Windows Authentication if available."
					else:
						error_msg = f"MSSQL: {e}"
		except Exception as exc:
			error_msg = str(exc)

		# Check permissions if connection succeeded
		permissions_ok = False
		missing_permissions = []

		if db_ok and not error_msg:
			try:
				if connector_type == "postgres":
					import psycopg2  # type: ignore
					conn = psycopg2.connect(
						host=target_host,
						port=int(target_port),
						user=body.get("user"),
						password=body.get("password"),
						dbname=body.get("database"),
						connect_timeout=3,
					)
					cur = conn.cursor()
					# Check CREATE privilege on schema
					cur.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")
					can_create = cur.fetchone()[0]
					if not can_create:
						missing_permissions.append("CREATE ON SCHEMA public")
					# Check if user can create functions
					cur.execute("SELECT has_schema_privilege(current_user, 'public', 'USAGE')")
					can_usage = cur.fetchone()[0]
					if not can_usage:
						missing_permissions.append("USAGE ON SCHEMA public")
					cur.close()
					conn.close()
					permissions_ok = len(missing_permissions) == 0

				elif connector_type == "mysql":
					import pymysql  # type: ignore
					conn = pymysql.connect(
						host=target_host,
						port=int(target_port),
						user=body.get("user"),
						password=body.get("password"),
						database=body.get("database"),
						connect_timeout=3,
					)
					cur = conn.cursor()
					cur.execute("SHOW GRANTS FOR CURRENT_USER")
					grants = cur.fetchall()
					grants_str = str(grants).upper()
					# Check for required permissions
					has_create = 'CREATE' in grants_str or 'ALL PRIVILEGES' in grants_str
					has_trigger = 'TRIGGER' in grants_str or 'ALL PRIVILEGES' in grants_str
					has_select = 'SELECT' in grants_str or 'ALL PRIVILEGES' in grants_str
					if not has_create:
						missing_permissions.append("CREATE")
					if not has_trigger:
						missing_permissions.append("TRIGGER")
					if not has_select:
						missing_permissions.append("SELECT")
					cur.close()
					conn.close()
					permissions_ok = len(missing_permissions) == 0

				elif connector_type == "sqlserver":
					windows_auth = body.get("windows_auth", False)
					if windows_auth:
						import pyodbc  # type: ignore
						server_str = target_host
						if int(target_port) != 1433:
							server_str = f"{target_host},{target_port}"
						conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_str};DATABASE={body.get('database')};Trusted_Connection=yes;Connection Timeout=3"
						conn = pyodbc.connect(conn_str)
					else:
						import pymssql  # type: ignore
						conn_args = {
							"server": target_host,
							"user": body.get("user"),
							"password": body.get("password"),
							"database": body.get("database"),
							"login_timeout": 3,
						}
						if int(target_port) != 1433:
							conn_args["port"] = str(target_port)
						conn = pymssql.connect(**conn_args)
					cur = conn.cursor()
					# Check CREATE TABLE permission
					cur.execute("SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CREATE TABLE')")
					can_create_table = cur.fetchone()[0]
					if not can_create_table:
						missing_permissions.append("CREATE TABLE")
					# Check ALTER permission on dbo schema
					cur.execute("SELECT HAS_PERMS_BY_NAME('dbo', 'SCHEMA', 'ALTER')")
					can_alter = cur.fetchone()[0]
					if not can_alter:
						missing_permissions.append("ALTER ON SCHEMA dbo (for triggers)")
					cur.close()
					conn.close()
					permissions_ok = len(missing_permissions) == 0
				else:
					# For other types, assume permissions are OK
					permissions_ok = True

			except Exception as perm_err:
				# If permission check fails, still allow connection but warn
				permissions_ok = True  # Don't block, just warn
				print(f"⚠️ Permission check failed: {perm_err}")

		# Build permission error message
		permission_error = None
		if db_ok and not permissions_ok and missing_permissions:
			permission_error = f"Missing permissions: {', '.join(missing_permissions)}. CDC Stream needs these to create triggers and track changes."

		# Close SSH tunnel if exists
		if ssh_tunnel:
			try:
				ssh_tunnel.stop()
			except Exception:
				pass

		return Response({
			"reachable": reachable,
			"db_ok": db_ok,
			"permissions_ok": permissions_ok,
			"missing_permissions": missing_permissions,
			"permission_error": permission_error,
			"error": error_msg
		})

	@action(detail=True, methods=["post"])
	def configure_replication(self, request, pk=None):
		"""
		PostgreSQL'de CDC için gerekli replication ayarlarını yapar ve restart eder.
		- wal_level = logical
		- max_replication_slots = 4
		- max_wal_senders = 4
		"""
		ds = self.get_object()
		cfg = ds.connector_config or {}
		connector_type = ds.connector_type or ""

		if connector_type != "postgres":
			return Response({"error": "This feature is only available for PostgreSQL"}, status=status.HTTP_400_BAD_REQUEST)

		result = {
			"success": False,
			"current_settings": {},
			"applied_settings": {},
			"restart_required": False,
			"restart_attempted": False,
			"restart_success": False,
			"message": "",
			"errors": []
		}

		try:
			import psycopg2

			# Connect to PostgreSQL
			conn = psycopg2.connect(
				host=cfg.get("host") or cfg.get("database_hostname") or "localhost",
				port=int(cfg.get("port") or cfg.get("database_port") or 5432),
				user=cfg.get("user") or cfg.get("database_user") or "postgres",
				password=cfg.get("password") or cfg.get("database_password") or "",
				dbname=cfg.get("database") or cfg.get("database_dbname") or "postgres",
				connect_timeout=10,
			)
			conn.autocommit = True
			cur = conn.cursor()

			# 1. Check current settings
			cur.execute("""
				SELECT name, setting, pending_restart
				FROM pg_settings
				WHERE name IN ('wal_level', 'max_replication_slots', 'max_wal_senders')
			""")
			for row in cur.fetchall():
				result["current_settings"][row[0]] = {
					"value": row[1],
					"pending_restart": row[2]
				}

			# Check if already configured
			current_wal = result["current_settings"].get("wal_level", {}).get("value", "")
			current_slots = result["current_settings"].get("max_replication_slots", {}).get("value", "0")
			current_senders = result["current_settings"].get("max_wal_senders", {}).get("value", "0")

			needs_wal_change = current_wal != "logical"
			needs_slots_change = int(current_slots) < 4
			needs_senders_change = int(current_senders) < 4

			if not needs_wal_change and not needs_slots_change and not needs_senders_change:
				result["success"] = True
				result["message"] = "PostgreSQL is already configured for CDC! No changes needed."
				cur.close()
				conn.close()
				return Response(result)

			# 2. Apply settings using ALTER SYSTEM
			applied = []

			if needs_wal_change:
				try:
					cur.execute("ALTER SYSTEM SET wal_level = 'logical'")
					applied.append("wal_level = logical")
					result["applied_settings"]["wal_level"] = "logical"
					result["restart_required"] = True
				except Exception as e:
					result["errors"].append(f"Failed to set wal_level: {str(e)}")

			if needs_slots_change:
				try:
					cur.execute("ALTER SYSTEM SET max_replication_slots = 4")
					applied.append("max_replication_slots = 4")
					result["applied_settings"]["max_replication_slots"] = "4"
					result["restart_required"] = True
				except Exception as e:
					result["errors"].append(f"Failed to set max_replication_slots: {str(e)}")

			if needs_senders_change:
				try:
					cur.execute("ALTER SYSTEM SET max_wal_senders = 4")
					applied.append("max_wal_senders = 4")
					result["applied_settings"]["max_wal_senders"] = "4"
					result["restart_required"] = True
				except Exception as e:
					result["errors"].append(f"Failed to set max_wal_senders: {str(e)}")

			cur.close()
			conn.close()

			# 3. Attempt restart if requested
			attempt_restart = request.data.get("restart", True)

			if result["restart_required"] and attempt_restart:
				result["restart_attempted"] = True

				# Try to restart PostgreSQL using pg_ctl or service commands
				import subprocess
				import platform

				restart_commands = []

				if platform.system() == "Windows":
					# Windows: Try net stop/start or pg_ctl
					restart_commands = [
						["net", "stop", "postgresql-x64-15"],
						["net", "stop", "postgresql-x64-16"],
						["net", "stop", "postgresql"],
						["pg_ctl", "restart", "-D", r"C:\Program Files\PostgreSQL\15\data"],
						["pg_ctl", "restart", "-D", r"C:\Program Files\PostgreSQL\16\data"],
					]
				else:
					# Linux/macOS
					restart_commands = [
						["sudo", "systemctl", "restart", "postgresql"],
						["sudo", "service", "postgresql", "restart"],
						["brew", "services", "restart", "postgresql"],
						["pg_ctl", "restart"],
					]

				restart_success = False
				restart_error = None

				for cmd in restart_commands:
					try:
						proc = subprocess.run(cmd, capture_output=True, timeout=30)
						if proc.returncode == 0:
							restart_success = True
							break
					except FileNotFoundError:
						continue
					except subprocess.TimeoutExpired:
						restart_error = "Restart command timed out"
						continue
					except Exception as e:
						restart_error = str(e)
						continue

				result["restart_success"] = restart_success

				if restart_success:
					result["success"] = True
					result["message"] = f"Settings applied and PostgreSQL restarted successfully! Applied: {', '.join(applied)}"
				else:
					result["success"] = True  # Settings were applied, just restart failed
					result["message"] = f"Settings applied successfully ({', '.join(applied)}), but automatic restart failed. Please restart PostgreSQL manually."
					if restart_error:
						result["errors"].append(f"Restart error: {restart_error}")
			else:
				result["success"] = True
				result["message"] = f"Settings applied: {', '.join(applied)}. PostgreSQL restart is required for changes to take effect."

		except ImportError:
			result["errors"].append("psycopg2 module not installed")
		except Exception as e:
			result["errors"].append(str(e))

		return Response(result)

	@action(detail=True, methods=["get"])
	def check_replication_status(self, request, pk=None):
		"""
		PostgreSQL'in CDC için hazır olup olmadığını kontrol eder.
		"""
		ds = self.get_object()
		cfg = ds.connector_config or {}
		connector_type = ds.connector_type or ""

		if connector_type != "postgres":
			return Response({"error": "This feature is only available for PostgreSQL"}, status=status.HTTP_400_BAD_REQUEST)

		result = {
			"ready": False,
			"settings": {},
			"issues": [],
			"user_has_replication": False
		}

		try:
			import psycopg2

			conn = psycopg2.connect(
				host=cfg.get("host") or cfg.get("database_hostname") or "localhost",
				port=int(cfg.get("port") or cfg.get("database_port") or 5432),
				user=cfg.get("user") or cfg.get("database_user") or "postgres",
				password=cfg.get("password") or cfg.get("database_password") or "",
				dbname=cfg.get("database") or cfg.get("database_dbname") or "postgres",
				connect_timeout=10,
			)
			cur = conn.cursor()

			# Check settings
			cur.execute("""
				SELECT name, setting, pending_restart
				FROM pg_settings
				WHERE name IN ('wal_level', 'max_replication_slots', 'max_wal_senders')
			""")
			for row in cur.fetchall():
				result["settings"][row[0]] = {
					"value": row[1],
					"pending_restart": row[2]
				}

				# Check each setting
				if row[0] == "wal_level" and row[1] != "logical":
					result["issues"].append(f"wal_level is '{row[1]}', should be 'logical'")
				elif row[0] == "max_replication_slots" and int(row[1]) < 1:
					result["issues"].append(f"max_replication_slots is {row[1]}, should be at least 4")
				elif row[0] == "max_wal_senders" and int(row[1]) < 1:
					result["issues"].append(f"max_wal_senders is {row[1]}, should be at least 4")

			# Check user replication privilege
			cur.execute("""
				SELECT rolreplication FROM pg_roles WHERE rolname = current_user
			""")
			row = cur.fetchone()
			if row:
				result["user_has_replication"] = row[0]
				if not row[0]:
					result["issues"].append("Current user does not have REPLICATION privilege")

			cur.close()
			conn.close()

			result["ready"] = len(result["issues"]) == 0

		except Exception as e:
			result["issues"].append(str(e))

		return Response(result)

	@action(detail=True, methods=["get"])
	def fetch_columns(self, request, pk=None):
		"""
		Belirtilen tablo için kolon bilgilerini ve önizleme verilerini getirir.
		Query params: schema, table
		"""
		ds = self.get_object()
		cfg = ds.connector_config or {}
		connector_type = ds.connector_type or ""
		schema_name = request.query_params.get("schema", "")
		table_name = request.query_params.get("table", "")

		if not schema_name or not table_name:
			return Response({"error": "schema and table parameters are required"}, status=status.HTTP_400_BAD_REQUEST)

		result = {"columns": [], "preview": [], "error": None}

		try:
			if connector_type == "postgres":
				import psycopg2
				conn = psycopg2.connect(
					host=cfg.get("host") or cfg.get("database_hostname"),
					port=int(cfg.get("port") or cfg.get("database_port") or 5432),
					user=cfg.get("user") or cfg.get("database_user"),
					password=cfg.get("password") or cfg.get("database_password"),
					dbname=cfg.get("database") or cfg.get("database_dbname"),
					connect_timeout=5,
				)
				cur = conn.cursor()
				# Get columns
				cur.execute("""
					SELECT column_name, data_type
					FROM information_schema.columns
					WHERE table_schema = %s AND table_name = %s
					ORDER BY ordinal_position
				""", (schema_name, table_name))
				result["columns"] = [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
				# Get preview data (first 100 rows)
				cur.execute(f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT 100')
				columns = [desc[0] for desc in cur.description]
				rows = cur.fetchall()
				result["preview"] = [dict(zip(columns, [str(v) if v is not None else None for v in row])) for row in rows]
				cur.close()
				conn.close()

			elif connector_type == "mysql":
				import pymysql
				conn = pymysql.connect(
					host=cfg.get("host") or cfg.get("database_hostname"),
					port=int(cfg.get("port") or cfg.get("database_port") or 3306),
					user=cfg.get("user") or cfg.get("database_user"),
					password=cfg.get("password") or cfg.get("database_password"),
					database=schema_name,  # MySQL'de schema = database
					connect_timeout=5,
				)
				cur = conn.cursor()
				# Get columns
				cur.execute("""
					SELECT COLUMN_NAME, DATA_TYPE
					FROM INFORMATION_SCHEMA.COLUMNS
					WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
					ORDER BY ORDINAL_POSITION
				""", (schema_name, table_name))
				result["columns"] = [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
				# Get preview data
				cur.execute(f"SELECT * FROM `{table_name}` LIMIT 100")
				columns = [desc[0] for desc in cur.description]
				rows = cur.fetchall()
				result["preview"] = [dict(zip(columns, [str(v) if v is not None else None for v in row])) for row in rows]
				cur.close()
				conn.close()

			elif connector_type == "sqlserver":
				import pymssql
				conn_args = {
					"server": cfg.get("host") or cfg.get("database_hostname"),
					"user": cfg.get("user") or cfg.get("database_user"),
					"password": cfg.get("password") or cfg.get("database_password"),
					"database": cfg.get("database"),
					"login_timeout": 5,
				}
				port = int(cfg.get("port") or cfg.get("database_port") or 1433)
				if port != 1433:
					conn_args["port"] = str(port)
				conn = pymssql.connect(**conn_args)
				cur = conn.cursor()
				# Get columns
				cur.execute("""
					SELECT COLUMN_NAME, DATA_TYPE
					FROM INFORMATION_SCHEMA.COLUMNS
					WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
					ORDER BY ORDINAL_POSITION
				""", (schema_name, table_name))
				result["columns"] = [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
				# Get preview data
				cur.execute(f"SELECT TOP 100 * FROM [{schema_name}].[{table_name}]")
				columns = [desc[0] for desc in cur.description]
				rows = cur.fetchall()
				result["preview"] = [dict(zip(columns, [str(v) if v is not None else None for v in row])) for row in rows]
				cur.close()
				conn.close()

			elif connector_type == "mongodb":
				from pymongo import MongoClient
				from bson import ObjectId
				from datetime import datetime as dt
				if cfg.get("connection_string"):
					client = MongoClient(cfg.get("connection_string"), serverSelectionTimeoutMS=5000)
				else:
					client = MongoClient(
						host=cfg.get("host") or cfg.get("database_hostname"),
						port=int(cfg.get("port") or cfg.get("database_port") or 27017),
						username=cfg.get("user") or cfg.get("database_user"),
						password=cfg.get("password") or cfg.get("database_password"),
						serverSelectionTimeoutMS=5000
					)
				db = client[schema_name]
				collection = db[table_name]
				# Get last 5 documents to infer schema (sorted by _id descending)
				sample_docs = list(collection.find().sort("_id", -1).limit(5))

				# Infer field types from sample documents
				field_types = {}  # field_name -> set of types
				for doc in sample_docs:
					for key, val in doc.items():
						if key not in field_types:
							field_types[key] = set()
						# Determine BSON/Python type
						if val is None:
							field_types[key].add("null")
						elif isinstance(val, ObjectId):
							field_types[key].add("objectId")
						elif isinstance(val, bool):  # Must be before int check
							field_types[key].add("boolean")
						elif isinstance(val, int):
							field_types[key].add("int")
						elif isinstance(val, float):
							field_types[key].add("double")
						elif isinstance(val, str):
							field_types[key].add("string")
						elif isinstance(val, list):
							field_types[key].add("array")
						elif isinstance(val, dict):
							field_types[key].add("object")
						elif isinstance(val, dt):
							field_types[key].add("date")
						else:
							field_types[key].add(type(val).__name__)

				# Build columns with inferred types
				columns = []
				for key in sorted(field_types.keys()):
					types = field_types[key]
					# Remove null from type list for display
					display_types = types - {"null"}
					if len(display_types) == 0:
						inferred_type = "null"
					elif len(display_types) == 1:
						inferred_type = list(display_types)[0]
					else:
						inferred_type = "mixed"  # Multiple types found
					columns.append({"name": key, "type": inferred_type})
				result["columns"] = columns

				# Preview data (last 5 records)
				result["preview"] = []
				all_keys = set(field_types.keys())
				for doc in sample_docs:
					row = {}
					for key in all_keys:
						val = doc.get(key)
						row[key] = str(val) if val is not None else None
					result["preview"].append(row)
				client.close()
			else:
				result["error"] = f"Unsupported connector type: {connector_type}"

		except Exception as e:
			result["error"] = str(e)

		return Response(result)

	@action(detail=True, methods=["get"])
	def fetch_schema(self, request, pk=None):
		"""
		Veritabanından şema ve tablo bilgilerini getirir.
		PostgreSQL/SQLServer: schemas ve tables
		MySQL: databases ve tables
		MongoDB: databases ve collections
		"""
		ds = self.get_object()
		cfg = ds.connector_config or {}
		connector_type = ds.connector_type or ""
		result = {"connector_type": connector_type, "schemas": [], "tables": [], "error": None}

		try:
			if connector_type == "postgres":
				import psycopg2
				conn = psycopg2.connect(
					host=cfg.get("host") or cfg.get("database_hostname"),
					port=int(cfg.get("port") or cfg.get("database_port") or 5432),
					user=cfg.get("user") or cfg.get("database_user"),
					password=cfg.get("password") or cfg.get("database_password"),
					dbname=cfg.get("database") or cfg.get("database_dbname"),
					connect_timeout=5,
				)
				cur = conn.cursor()
				# Get schemas
				cur.execute("""
					SELECT schema_name FROM information_schema.schemata
					WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
					ORDER BY schema_name
				""")
				result["schemas"] = [row[0] for row in cur.fetchall()]

				# Get view dependencies first (to filter multi-table views)
				cur.execute("""
					SELECT
						view_schema,
						view_name,
						COUNT(DISTINCT table_name) as base_table_count,
						MIN(table_schema) as base_schema,
						MIN(table_name) as base_table
					FROM information_schema.view_column_usage
					WHERE view_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
					GROUP BY view_schema, view_name
				""")
				view_info = {}
				for row in cur.fetchall():
					view_key = f"{row[0]}.{row[1]}"
					view_info[view_key] = {
						"base_table_count": row[2],
						"base_schema": row[3],
						"base_table": row[4]
					}

				# Get tables using pg_catalog (more reliable for permissions)
				cur.execute("""
					SELECT schemaname, tablename, 'BASE TABLE' as table_type
					FROM pg_catalog.pg_tables
					WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
					UNION ALL
					SELECT schemaname, viewname, 'VIEW' as table_type
					FROM pg_catalog.pg_views
					WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
					ORDER BY 1, 2
				""")
				raw_tables = cur.fetchall()

				tables_and_views = []
				for row in raw_tables:
					schema_name = row[0]
					table_name = row[1]
					table_type = row[2]

					if table_type == 'BASE TABLE':
						# Regular table - always include
						tables_and_views.append({
							"schema": schema_name,
							"table": table_name,
							"type": "table"
						})
					else:
						# View - only include if it has exactly 1 base table
						view_key = f"{schema_name}.{table_name}"
						info = view_info.get(view_key, {})
						base_count = info.get("base_table_count", 0)

						if base_count == 1:
							# Single base table view - include it
							tables_and_views.append({
								"schema": schema_name,
								"table": table_name,
								"type": "view",
								"base_table": {
									"schema": info.get("base_schema", schema_name),
									"table": info.get("base_table", "")
								}
							})
						# Views with 0 or 2+ base tables are excluded

				result["tables"] = tables_and_views

				cur.close()
				conn.close()

			elif connector_type == "mysql":
				import pymysql
				conn = pymysql.connect(
					host=cfg.get("host") or cfg.get("database_hostname"),
					port=int(cfg.get("port") or cfg.get("database_port") or 3306),
					user=cfg.get("user") or cfg.get("database_user"),
					password=cfg.get("password") or cfg.get("database_password"),
					database=cfg.get("database"),
					connect_timeout=5,
				)
				cur = conn.cursor()
				db_name = cfg.get("database")

				# MySQL uses databases instead of schemas
				cur.execute("SHOW DATABASES")
				all_dbs = [row[0] for row in cur.fetchall()]
				result["schemas"] = [db for db in all_dbs if db not in ('information_schema', 'mysql', 'performance_schema', 'sys')]

				# Get views and try to extract base table from VIEW_DEFINITION
				# MySQL doesn't have VIEW_TABLE_USAGE, so we parse the definition
				cur.execute("""
					SELECT TABLE_NAME, VIEW_DEFINITION
					FROM information_schema.VIEWS
					WHERE TABLE_SCHEMA = %s
				""", (db_name,))
				view_info = {}
				for row in cur.fetchall():
					view_name = row[0]
					view_def = row[1] or ""
					# Try to extract base table from simple "SELECT ... FROM table_name" views
					base_table = None
					base_table_count = 0
					# Regex to find FROM clause tables
					# Handle: FROM table, FROM `table`, FROM db.table, FROM `db`.`table`
					import re
					# First try: FROM `db`.`table` or FROM db.table
					from_match = re.search(r'\bFROM\s+`?(\w+)`?\.`?(\w+)`?', view_def, re.IGNORECASE)
					if from_match:
						# Got db.table format - use the table part (group 2)
						base_table = from_match.group(2)
					else:
						# Try: FROM `table` or FROM table
						from_match = re.search(r'\bFROM\s+`?(\w+)`?', view_def, re.IGNORECASE)
						if from_match:
							base_table = from_match.group(1)

					if base_table:
						# Check if there are JOINs (multiple tables)
						if re.search(r'\bJOIN\b', view_def, re.IGNORECASE):
							base_table_count = 2  # Multiple tables
						else:
							base_table_count = 1

					view_info[view_name] = {
						"base_table_count": base_table_count,
						"base_table": base_table
					}

				# Get tables and views from current database
				cur.execute("""
					SELECT TABLE_NAME, TABLE_TYPE
					FROM information_schema.TABLES
					WHERE TABLE_SCHEMA = %s
					ORDER BY TABLE_NAME
				""", (db_name,))

				tables_and_views = []
				for row in cur.fetchall():
					table_name = row[0]
					table_type = row[1]

					if table_type == 'BASE TABLE':
						tables_and_views.append({
							"schema": db_name,
							"table": table_name,
							"type": "table"
						})
					elif table_type == 'VIEW':
						# View - only include if it has exactly 1 base table
						info = view_info.get(table_name, {})
						base_count = info.get("base_table_count", 0)

						if base_count == 1:
							tables_and_views.append({
								"schema": db_name,
								"table": table_name,
								"type": "view",
								"base_table": {
									"schema": db_name,
									"table": info.get("base_table", "")
								}
							})
						elif base_count == 0:
							# MySQL VIEW_TABLE_USAGE might be empty, try to include anyway
							# These views might work if they're simple single-table views
							tables_and_views.append({
								"schema": db_name,
								"table": table_name,
								"type": "view",
								"base_table": None  # Unknown, will be detected at alert creation
							})

				result["tables"] = tables_and_views
				cur.close()
				conn.close()

			elif connector_type == "sqlserver":
				import pymssql
				conn_args = {
					"server": cfg.get("host") or cfg.get("database_hostname"),
					"user": cfg.get("user") or cfg.get("database_user"),
					"password": cfg.get("password") or cfg.get("database_password"),
					"database": cfg.get("database"),
					"login_timeout": 5,
				}
				port = int(cfg.get("port") or cfg.get("database_port") or 1433)
				if port != 1433:
					conn_args["port"] = str(port)
				conn = pymssql.connect(**conn_args)
				cur = conn.cursor()

				# Get schemas (from both tables and views)
				cur.execute("""
					SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES
					UNION
					SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.VIEWS
					ORDER BY 1
				""")
				result["schemas"] = [row[0] for row in cur.fetchall()]

				# Get view dependencies (to find single-table views)
				# Use sys.sql_expression_dependencies with correct column names
				cur.execute("""
					SELECT
						OBJECT_SCHEMA_NAME(v.object_id) as view_schema,
						v.name as view_name,
						COUNT(DISTINCT d.referenced_entity_name) as base_table_count,
						MIN(COALESCE(d.referenced_schema_name, 'dbo')) as base_schema,
						MIN(d.referenced_entity_name) as base_table
					FROM sys.views v
					LEFT JOIN sys.sql_expression_dependencies d
						ON v.object_id = d.referencing_id
						AND d.referenced_class_desc = 'OBJECT_OR_COLUMN'
					GROUP BY v.object_id, v.name
				""")
				view_info = {}
				for row in cur.fetchall():
					view_key = f"{row[0]}.{row[1]}"
					view_info[view_key] = {
						"base_table_count": row[2] or 0,
						"base_schema": row[3] or "dbo",
						"base_table": row[4]
					}

				# Get tables
				cur.execute("""
					SELECT TABLE_SCHEMA, TABLE_NAME, 'table' as obj_type
					FROM INFORMATION_SCHEMA.TABLES
					WHERE TABLE_TYPE = 'BASE TABLE'
					UNION ALL
					SELECT TABLE_SCHEMA, TABLE_NAME, 'view' as obj_type
					FROM INFORMATION_SCHEMA.VIEWS
					ORDER BY 1, 2
				""")

				tables_and_views = []
				for row in cur.fetchall():
					schema_name = row[0]
					table_name = row[1]
					obj_type = row[2]

					if obj_type == 'table':
						tables_and_views.append({
							"schema": schema_name,
							"table": table_name,
							"type": "table"
						})
					else:
						# View - only include if it has exactly 1 base table
						view_key = f"{schema_name}.{table_name}"
						info = view_info.get(view_key, {})
						base_count = info.get("base_table_count", 0)

						if base_count == 1:
							tables_and_views.append({
								"schema": schema_name,
								"table": table_name,
								"type": "view",
								"base_table": {
									"schema": info.get("base_schema", schema_name),
									"table": info.get("base_table", "")
								}
							})

				result["tables"] = tables_and_views
				cur.close()
				conn.close()

			elif connector_type == "mongodb":
				from pymongo import MongoClient
				if cfg.get("connection_string"):
					client = MongoClient(cfg.get("connection_string"), serverSelectionTimeoutMS=5000)
				else:
					client = MongoClient(
						host=cfg.get("host") or cfg.get("database_hostname"),
						port=int(cfg.get("port") or cfg.get("database_port") or 27017),
						username=cfg.get("user") or cfg.get("database_user"),
						password=cfg.get("password") or cfg.get("database_password"),
						serverSelectionTimeoutMS=5000
					)
				# Get databases
				db_names = [db for db in client.list_database_names() if db not in ('admin', 'config', 'local')]
				result["schemas"] = db_names  # MongoDB'de database'ler schema gibi
				# Get collections from all databases
				collections = []
				for db_name in db_names:
					db = client[db_name]
					for coll_name in db.list_collection_names():
						collections.append({"schema": db_name, "table": coll_name})
				result["tables"] = collections
				client.close()
			else:
				result["error"] = f"Unsupported connector type: {connector_type}"

		except Exception as e:
			result["error"] = str(e)

		return Response(result)


class RuleViewSet(viewsets.ModelViewSet):
	queryset = Rule.objects.all().order_by("-id")
	serializer_class = RuleSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["name", "description"]
	ordering_fields = ["id", "created_at", "name"]

	def create(self, request, *args, **kwargs):
		"""Create alert after verifying trigger can be created."""
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		# FIRST: Check if we can create the trigger BEFORE saving the alert
		# This prevents data loss if trigger creation fails
		trigger_check = self._check_trigger_permissions(serializer.validated_data)

		if not trigger_check['success']:
			# DON'T create the alert - return error so user can fix permissions
			return Response({
				"error": "Cannot create alert: Trigger installation will fail",
				"trigger_error": trigger_check['error'],
				"solution": trigger_check.get('solution', 'Check database user permissions.'),
				"can_retry": True  # User can fix permissions and retry
			}, status=status.HTTP_400_BAD_REQUEST)

		# Permissions OK - now save the alert
		instance = serializer.save()

		# Install the trigger (should succeed since we checked permissions)
		trigger_result = self._install_trigger_with_result(instance)

		if not trigger_result['success']:
			# Unexpected failure - but don't delete the alert, just warn
			return Response({
				**serializer.data,
				"warning": "Alert created but trigger installation failed unexpectedly",
				"trigger_error": trigger_result['error'],
				"solution": trigger_result.get('solution', 'Check database user permissions.')
			}, status=status.HTTP_201_CREATED)

		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def _check_trigger_permissions(self, validated_data):
		"""Check if user has permissions to create trigger WITHOUT actually creating anything."""
		result = {'success': True, 'error': None, 'solution': None}

		datasource = validated_data.get('datasource')
		table_name = validated_data.get('table_name')
		schema_name = validated_data.get('schema_name', 'public')

		if not datasource or not table_name:
			# No datasource/table, skip check
			return result

		config = datasource.connector_config or {}
		connector_type = (datasource.connector_type or "").lower()

		if not config.get('host'):
			return result

		try:
			if connector_type == "postgres":
				import psycopg2
				conn = psycopg2.connect(
					host=config.get('host'),
					port=config.get('port', 5432),
					user=config.get('user'),
					password=config.get('password'),
					dbname=config.get('database'),
					connect_timeout=5
				)
				cur = conn.cursor()
				# Check CREATE privilege on schema
				cur.execute(f"SELECT has_schema_privilege(current_user, '{schema_name}', 'CREATE')")
				can_create = cur.fetchone()[0]
				cur.close()
				conn.close()

				if not can_create:
					result['success'] = False
					result['error'] = f"User does not have CREATE privilege on schema '{schema_name}'"
					result['solution'] = f"Run: GRANT CREATE ON SCHEMA {schema_name} TO your_user;"

			elif connector_type == "sqlserver":
				# Check MSSQL permissions
				try:
					windows_auth = config.get('windows_auth', False)
					if windows_auth:
						import pyodbc
						server_str = config.get('host')
						port = config.get('port', 1433)
						if int(port) != 1433:
							server_str = f"{server_str},{port}"
						conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_str};DATABASE={config.get('database')};Trusted_Connection=yes"
						conn = pyodbc.connect(conn_str)
					else:
						import pymssql
						conn = pymssql.connect(
							server=config.get('host'),
							user=config.get('user'),
							password=config.get('password'),
							database=config.get('database')
						)
					cur = conn.cursor()
					cur.execute("SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CREATE TABLE')")
					can_create_table = cur.fetchone()[0]
					cur.execute("SELECT HAS_PERMS_BY_NAME('dbo', 'SCHEMA', 'ALTER')")
					can_alter = cur.fetchone()[0]
					cur.close()
					conn.close()

					if not can_create_table or not can_alter:
						result['success'] = False
						missing = []
						if not can_create_table:
							missing.append("CREATE TABLE")
						if not can_alter:
							missing.append("ALTER ON SCHEMA")
						result['error'] = f"Missing permissions: {', '.join(missing)}"
						result['solution'] = "Run: GRANT CREATE TABLE, ALTER ON SCHEMA::dbo TO your_user;"
				except ImportError:
					pass  # Driver not installed, skip check

			elif connector_type == "mysql":
				import pymysql
				conn = pymysql.connect(
					host=config.get('host'),
					port=config.get('port', 3306),
					user=config.get('user'),
					password=config.get('password'),
					database=config.get('database')
				)
				cur = conn.cursor()
				cur.execute("SHOW GRANTS FOR CURRENT_USER")
				grants = cur.fetchall()
				grants_str = str(grants).upper()
				cur.close()
				conn.close()

				has_create = 'CREATE' in grants_str or 'ALL PRIVILEGES' in grants_str
				has_trigger = 'TRIGGER' in grants_str or 'ALL PRIVILEGES' in grants_str

				if not has_create or not has_trigger:
					result['success'] = False
					missing = []
					if not has_create:
						missing.append("CREATE")
					if not has_trigger:
						missing.append("TRIGGER")
					result['error'] = f"Missing permissions: {', '.join(missing)}"
					result['solution'] = f"Run: GRANT CREATE, TRIGGER ON {config.get('database')}.* TO 'your_user'@'%';"

		except Exception as e:
			error_str = str(e).lower()
			if any(kw in error_str for kw in ['permission', 'denied', 'privilege', 'access denied']):
				result['success'] = False
				result['error'] = f"Permission denied: {e}"
				result['solution'] = "Check database user permissions and try again."
			# For other errors (connection issues, etc.), let it pass - will fail later with better error

		return result

	def update(self, request, *args, **kwargs):
		"""Update alert after verifying trigger can be created."""
		partial = kwargs.pop('partial', False)
		instance = self.get_object()
		serializer = self.get_serializer(instance, data=request.data, partial=partial)
		serializer.is_valid(raise_exception=True)

		# Check permissions before updating if alert is active
		is_active = serializer.validated_data.get('is_active', instance.is_active)
		if is_active:
			trigger_check = self._check_trigger_permissions(serializer.validated_data)
			if not trigger_check['success']:
				return Response({
					"error": "Cannot update alert: Trigger installation will fail",
					"trigger_error": trigger_check['error'],
					"solution": trigger_check.get('solution', 'Check database user permissions.'),
					"can_retry": True
				}, status=status.HTTP_400_BAD_REQUEST)

		# Permissions OK - save the alert
		instance = serializer.save()

		if instance.is_active:
			trigger_result = self._install_trigger_with_result(instance)
			if not trigger_result['success']:
				return Response({
					**serializer.data,
					"warning": "Alert updated but trigger installation failed unexpectedly",
					"trigger_error": trigger_result['error'],
					"solution": trigger_result.get('solution', 'Check database user permissions.')
				}, status=status.HTTP_200_OK)

		return Response(serializer.data)

	def _install_trigger_with_result(self, rule):
		"""Install CDC trigger for a rule. Returns dict with success status and error details."""
		result = {'success': True, 'error': None, 'solution': None}

		if not rule.datasource or not rule.table_name:
			# No datasource/table, skip trigger installation (not an error)
			return result

		ds = rule.datasource
		config = ds.connector_config or {}
		connector_type = (ds.connector_type or "").lower()

		if not config.get('host'):
			return result

		try:
			schema = rule.schema_name or 'public'

			# For views, install trigger on base tables instead
			if rule.object_type == 'view' and rule.base_tables:
				# base_tables can be [{schema, table}, ...] or ["table_name", ...]
				tables_to_trigger = []
				for bt in rule.base_tables:
					if isinstance(bt, dict):
						tables_to_trigger.append(bt.get('table', bt.get('name', '')))
					else:
						tables_to_trigger.append(str(bt))
				tables_to_trigger = [t for t in tables_to_trigger if t]  # Filter empty
				print(f"View detected: {rule.table_name}, installing triggers on base tables: {tables_to_trigger}")
			else:
				tables_to_trigger = [rule.table_name]

			if not tables_to_trigger:
				result['success'] = False
				result['error'] = f"No base table found for view {rule.table_name}"
				result['solution'] = "View must have a single base table to enable CDC triggers."
				return result

			if connector_type == "postgres":
				from cdc_stream.trigger_manager import TriggerManager, get_connection
				conn = get_connection(config)
				manager = TriggerManager(conn)
				all_success = True
				for table in tables_to_trigger:
					success = manager.create_trigger(schema, table)
					if not success:
						all_success = False
				conn.close()

				if not all_success:
					result['success'] = False
					result['error'] = f"Failed to create trigger on {schema}.{', '.join(tables_to_trigger)}"
					result['solution'] = "Run: GRANT CREATE ON SCHEMA public TO your_user; Or use admin/superuser."

			elif connector_type == "sqlserver":
				from cdc_stream.mssql_support import MSSQLTriggerManager, get_mssql_connection
				conn = get_mssql_connection(config)
				manager = MSSQLTriggerManager(conn)
				all_success = True
				for table in tables_to_trigger:
					success = manager.create_trigger(schema, table)
					if not success:
						all_success = False
				conn.close()

				if not all_success:
					result['success'] = False
					result['error'] = f"Failed to create trigger on {schema}.{', '.join(tables_to_trigger)}"
					result['solution'] = "Run: GRANT CREATE TABLE, ALTER ON SCHEMA::dbo TO your_user; Or use admin/sysadmin."

			elif connector_type == "mysql":
				from cdc_stream.mysql_support import MySQLTriggerManager, get_mysql_connection
				conn = get_mysql_connection(config)
				manager = MySQLTriggerManager(conn)
				all_success = True
				for table in tables_to_trigger:
					success = manager.create_triggers(schema, table)
					if not success:
						all_success = False
				conn.close()

				if not all_success:
					result['success'] = False
					result['error'] = f"Failed to create triggers on {schema}.{', '.join(tables_to_trigger)}"
					result['solution'] = "Run: GRANT CREATE, TRIGGER ON database.* TO 'user'@'%'; Or use admin/root."

		except Exception as e:
			result['success'] = False
			error_str = str(e).lower()

			if any(kw in error_str for kw in ['permission', 'denied', 'privilege', 'access denied']):
				result['error'] = f"Permission denied: {e}"
				if connector_type == "postgres":
					result['solution'] = "Run: GRANT USAGE, CREATE ON SCHEMA public TO your_user;"
				elif connector_type == "sqlserver":
					result['solution'] = "Run: GRANT CREATE TABLE, ALTER ON SCHEMA::dbo TO your_user;"
				elif connector_type == "mysql":
					result['solution'] = "Run: GRANT CREATE, TRIGGER ON database.* TO 'user'@'%';"
				else:
					result['solution'] = "Check database user permissions."
			else:
				result['error'] = str(e)
				result['solution'] = "Check database connection and user permissions."

			print(f"Failed to install trigger for {rule.name}: {e}")

		return result

	def _install_trigger(self, rule):
		"""Legacy method - calls new method."""
		return self._install_trigger_with_result(rule)['success']

	@action(detail=True, methods=["post"])
	def install_trigger(self, request, pk=None):
		"""Manually install CDC trigger for this alert."""
		rule = self.get_object()

		if not rule.datasource:
			return Response({"error": "Alert has no datasource"}, status=status.HTTP_400_BAD_REQUEST)
		if not rule.table_name:
			return Response({"error": "Alert has no table configured"}, status=status.HTTP_400_BAD_REQUEST)

		ds = rule.datasource
		config = ds.connector_config or {}
		if not config.get('host'):
			return Response({"error": "Datasource has no connection config"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			from cdc_stream.trigger_manager import TriggerManager, get_connection
			conn = get_connection(config)
			manager = TriggerManager(conn)
			schema = rule.schema_name or 'public'
			success = manager.create_trigger(schema, rule.table_name)
			conn.close()

			if success:
				return Response({"success": True, "message": f"Trigger installed on {schema}.{rule.table_name}"})
			else:
				return Response({"success": False, "message": "Failed to install trigger"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		except Exception as e:
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=["post"])
	def remove_trigger(self, request, pk=None):
		"""Remove CDC trigger for this alert."""
		rule = self.get_object()

		if not rule.datasource or not rule.table_name:
			return Response({"error": "Alert has no datasource/table"}, status=status.HTTP_400_BAD_REQUEST)

		ds = rule.datasource
		config = ds.connector_config or {}
		if not config.get('host'):
			return Response({"error": "Datasource has no connection config"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			from cdc_stream.trigger_manager import TriggerManager, get_connection
			conn = get_connection(config)
			manager = TriggerManager(conn)
			schema = rule.schema_name or 'public'
			success = manager.drop_trigger(schema, rule.table_name)
			conn.close()

			if success:
				return Response({"success": True, "message": f"Trigger removed from {schema}.{rule.table_name}"})
			else:
				return Response({"success": False, "message": "Failed to remove trigger"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		except Exception as e:
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=["get"])
	def trigger_status(self, request, pk=None):
		"""Check if CDC trigger is installed for this alert."""
		rule = self.get_object()

		if not rule.datasource or not rule.table_name:
			return Response({"installed": False, "reason": "No datasource/table configured"})

		ds = rule.datasource
		config = ds.connector_config or {}
		if not config.get('host'):
			return Response({"installed": False, "reason": "No connection config"})

		try:
			from cdc_stream.trigger_manager import TriggerManager, get_connection
			conn = get_connection(config)
			manager = TriggerManager(conn)
			schema = rule.schema_name or 'public'
			exists = manager.trigger_exists(schema, rule.table_name)
			conn.close()

			return Response({
				"installed": exists,
				"schema": schema,
				"table": rule.table_name,
				"trigger_name": f"cdc_stream_{schema}_{rule.table_name}"
			})
		except Exception as e:
			return Response({"installed": False, "error": str(e)})

	@action(detail=True, methods=["post"])
	def toggle_active(self, request, pk=None):
		"""Toggle the is_active status of an alert/worker."""
		rule = self.get_object()

		# Toggle the status
		new_status = not rule.is_active
		rule.is_active = new_status
		rule.save(update_fields=['is_active'])

		# Notify worker about the change
		try:
			from cdc_stream.worker import on_rule_updated
			on_rule_updated(rule)
		except ImportError:
			pass

		return Response({
			"success": True,
			"id": rule.id,
			"name": rule.name,
			"is_active": rule.is_active,
			"message": f"Worker {'started' if new_status else 'stopped'}"
		})


class TriggerLogViewSet(viewsets.ModelViewSet):
	queryset = TriggerLog.objects.all().order_by("-id")
	serializer_class = TriggerLogSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["rule__name", "status"]
	ordering_fields = ["id", "created_at"]

	def get_queryset(self):
		"""Override to support filtering by rule."""
		queryset = TriggerLog.objects.all().order_by("-id")
		rule_id = self.request.query_params.get("rule")
		if rule_id:
			queryset = queryset.filter(rule_id=rule_id)
		return queryset

	@action(detail=False, methods=["get"])
	def recent(self, request):
		"""Get the 5 most recent trigger logs."""
		limit = int(request.query_params.get("limit", 5))
		rule_id = request.query_params.get("rule")
		logs = TriggerLog.objects.select_related("rule").order_by("-created_at")
		if rule_id:
			logs = logs.filter(rule_id=rule_id)
		logs = logs[:limit]
		data = []
		for log in logs:
			data.append({
				"id": log.id,
				"rule_name": log.rule.name if log.rule else "Unknown",
				"rule_id": log.rule_id,
				"status": log.status,
				"event": log.event,
				"error_message": log.error_message,
				"created_at": log.created_at.isoformat(),
			})
		return Response(data)

	@action(detail=False, methods=["get"])
	def recent_by_rule(self, request):
		"""Get last 5 logs for each rule - for alert list page status circles."""
		from django.db.models import Window, F
		from django.db.models.functions import RowNumber

		# Get all rules
		rules = Rule.objects.all()
		result = {}

		for rule in rules:
			logs = TriggerLog.objects.filter(rule=rule).order_by("-created_at")[:5]
			result[rule.id] = [
				{
					"id": log.id,
					"status": log.status,
					"error_message": log.error_message,
					"created_at": log.created_at.isoformat(),
				}
				for log in logs
			]

		return Response(result)

	@action(detail=False, methods=["get"])
	def stats(self, request):
		"""Get statistics for pie charts and reports."""
		days = int(request.query_params.get("days", 30))
		rule_id = request.query_params.get("rule")
		now = timezone.now()
		start = now - timezone.timedelta(days=days)

		# Total counts by status
		qs = TriggerLog.objects.filter(created_at__gte=start)
		if rule_id:
			qs = qs.filter(rule_id=rule_id)

		status_counts = qs.values("status").annotate(count=Count("id"))

		# Counts by rule
		rule_counts = (
			qs.values("rule__name", "rule_id")
			.annotate(count=Count("id"))
			.order_by("-count")[:10]
		)

		# Counts by day
		daily_counts = (
			qs.annotate(day=TruncDate("created_at"))
			.values("day")
			.annotate(count=Count("id"))
			.order_by("day")
		)

		# Hourly distribution
		hourly_counts = (
			qs.annotate(hour=ExtractHour("created_at"))
			.values("hour")
			.annotate(count=Count("id"))
			.order_by("hour")
		)

		return Response({
			"period": {"from": start.isoformat(), "to": now.isoformat(), "days": days},
			"total": qs.count(),
			"by_status": {item["status"]: item["count"] for item in status_counts},
			"by_rule": [
				{"rule_name": item["rule__name"], "rule_id": item["rule_id"], "count": item["count"]}
				for item in rule_counts
			],
			"by_day": [
				{"day": item["day"].isoformat(), "count": item["count"]}
				for item in daily_counts
			],
			"by_hour": [
				{"hour": item["hour"], "count": item["count"]}
				for item in hourly_counts
			],
		})

class WorkerHealthView(APIView):
	"""
	Get worker health status - shows if CDC workers are running.
	"""
	def get(self, request):
		from .models import Rule, TriggerLog, DataSource

		# Count active alerts (alerts with is_active=True)
		all_rules = Rule.objects.all()
		active_rules = all_rules.filter(is_active=True)
		active_alerts = active_rules.count()
		total_alerts = all_rules.count()

		# Check recent activity - if there's been a trigger log in the last 5 minutes
		# or if there are active alerts, worker is likely running
		recent_time = timezone.now() - timezone.timedelta(minutes=5)
		recent_logs = TriggerLog.objects.filter(created_at__gte=recent_time).exists()

		# Get last trigger log time
		last_log = TriggerLog.objects.order_by('-created_at').first()
		last_activity = last_log.created_at.isoformat() if last_log else None

		# Worker is considered "healthy" if there are any alerts (active or not)
		# The actual worker process status would need IPC or a separate health check endpoint
		has_workers = total_alerts > 0

		# Get worker list with details (ALL alerts, not just active)
		workers = []
		for rule in all_rules:
			# Get datasource info
			datasource = DataSource.objects.filter(id=rule.datasource_id).first()
			ds_name = datasource.name if datasource else "Unknown"

			# Get last trigger for this rule
			last_trigger = TriggerLog.objects.filter(rule_id=rule.id).order_by('-created_at').first()
			last_trigger_time = last_trigger.created_at.isoformat() if last_trigger else None
			last_trigger_status = last_trigger.status if last_trigger else None

			workers.append({
				"id": rule.id,
				"name": rule.name,
				"datasource": ds_name,
				"table": f"{rule.schema_name}.{rule.table_name}" if rule.schema_name else rule.table_name,
				"is_active": rule.is_active,
				"last_trigger_time": last_trigger_time,
				"last_trigger_status": last_trigger_status,
			})

		# Get daily cleanup worker status
		daily_cleanup_worker = None
		try:
			from cdc_stream.daily_cleanup import get_daily_cleanup_stats
			daily_cleanup_worker = get_daily_cleanup_stats()
		except ImportError:
			pass

		return Response({
			"has_workers": has_workers,
			"active_alerts": active_alerts,
			"total_alerts": total_alerts,
			"recent_activity": recent_logs,
			"last_activity": last_activity,
			"workers": workers,
			"daily_cleanup_worker": daily_cleanup_worker,
		})


class MetricsSummaryView(APIView):
	def get(self, request):
		now = timezone.now()
		start = now - timezone.timedelta(days=30)
		qs = TriggerLog.objects.filter(created_at__gte=start)
		by_day = (
			qs.annotate(day=TruncDate("created_at"))
			.values("day", "status")
			.annotate(count=Count("id"))
			.order_by("day", "status")
		)
		series = {}
		for row in by_day:
			day = row["day"].isoformat()
			series.setdefault(day, {"success": 0, "failed": 0})
			series[day][row["status"]] = row["count"]
		total_success = qs.filter(status="success").count()
		total_failed = qs.filter(status="failed").count()
		return Response(
			{
				"range": {"from": start.isoformat(), "to": now.isoformat()},
				"totals": {"success": total_success, "failed": total_failed},
				"daily": series,
			}
		)

class ConfigView(APIView):
	def get(self, request):
		from .models import DataSource  # local import to avoid circulars at import time
		db_engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
		has_datasources = DataSource.objects.exists()
		return Response(
			{
				"CDC_STREAM_KAFKA_BOOTSTRAP": os.getenv("CDC_STREAM_KAFKA_BOOTSTRAP", "localhost:29092"),
				"CDC_STREAM_KAFKA_GROUP_ID": os.getenv("CDC_STREAM_KAFKA_GROUP_ID", "cdc-stream"),
				"KAFKA_CONNECT_URL": settings.KAFKA_CONNECT_URL,
				"DB_ENGINE": db_engine,
				"HAS_DATASOURCES": has_datasources,
			}
		)


class WebhookTestReceiverView(APIView):
	"""
	A test endpoint that receives webhook POST requests.
	Useful for testing webhook configurations without an external receiver.
	"""
	def post(self, request):
		# Log the received webhook data
		import logging
		logger = logging.getLogger(__name__)
		logger.info(f"Webhook test received: {request.data}")

		return Response({
			"success": True,
			"message": "Webhook received successfully",
			"received_data": request.data,
			"timestamp": timezone.now().isoformat(),
		})


# ============================================================================
# CDC Live Stream - Database-backed Event Storage
# ============================================================================
import time

MAX_EVENTS_PER_RULE = 100


def add_cdc_event(rule_id: int, event: dict):
	"""Add a CDC event to the database for a specific rule"""
	from .models import CDCEvent
	try:
		CDCEvent.objects.create(
			rule_id=rule_id,
			stage=event.get('stage', 'unknown'),
			event_data=event
		)
		# Cleanup old events (keep last MAX_EVENTS_PER_RULE)
		event_count = CDCEvent.objects.filter(rule_id=rule_id).count()
		if event_count > MAX_EVENTS_PER_RULE:
			# Delete oldest events
			oldest_ids = CDCEvent.objects.filter(rule_id=rule_id).order_by('created_at').values_list('id', flat=True)[:event_count - MAX_EVENTS_PER_RULE]
			CDCEvent.objects.filter(id__in=list(oldest_ids)).delete()
	except Exception as e:
		print(f"Error saving CDC event: {e}")


def get_cdc_events(rule_id: int, since_id: str = None) -> list:
	"""Get CDC events for a rule from TriggerLog"""
	from .models import TriggerLog
	try:
		queryset = TriggerLog.objects.filter(rule_id=rule_id).order_by('-created_at')

		if since_id:
			# Parse the since_id to get the event id
			try:
				event_pk = int(since_id)
				queryset = queryset.filter(id__gt=event_pk)
			except (ValueError, TypeError):
				pass

		events = []
		for log in queryset[:20]:
			event_data = log.event or {}
			event_data['id'] = str(log.id)
			event_data['timestamp'] = log.created_at.isoformat()
			event_data['status'] = log.status
			event_data['matched'] = log.status in ['success', 'partial']
			event_data['dispatch_results'] = log.dispatch_results
			events.append(event_data)
		return events
	except Exception as e:
		print(f"Error getting CDC events: {e}")
		return []


def clear_cdc_events(rule_id: int):
	"""Clear CDC events for a specific rule"""
	from .models import CDCEvent
	try:
		CDCEvent.objects.filter(rule_id=rule_id).delete()
	except Exception as e:
		print(f"Error clearing CDC events: {e}")


class CDCLiveStreamView(APIView):
	"""
	SSE endpoint for streaming CDC events in real-time.
	GET /api/cdc-stream/{rule_id}/
	"""
	def get(self, request, rule_id):
		from django.http import StreamingHttpResponse

		# Check if rule exists
		try:
			rule = Rule.objects.get(id=rule_id)
		except Rule.DoesNotExist:
			return Response({"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND)

		def event_stream():
			last_event_id = None
			heartbeat_count = 0

			while True:
				# Get new events
				events = get_cdc_events(rule_id, last_event_id)

				if events:
					last_event_id = events[0].get("id")
					for event in reversed(events):  # Send oldest first
						yield f"data: {json.dumps(event)}\n\n"
				else:
					# Send heartbeat every 3 seconds
					heartbeat_count += 1
					if heartbeat_count >= 3:
						yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': timezone.now().isoformat()})}\n\n"
						heartbeat_count = 0

				time.sleep(1)

		response = StreamingHttpResponse(
			event_stream(),
			content_type='text/event-stream'
		)
		response['Cache-Control'] = 'no-cache'
		response['X-Accel-Buffering'] = 'no'
		return response


class CDCEventsView(APIView):
	"""
	Polling endpoint for getting recent CDC events.
	GET /api/cdc-events/{rule_id}/
	"""
	def get(self, request, rule_id):
		# Check if rule exists
		try:
			rule = Rule.objects.get(id=rule_id)
		except Rule.DoesNotExist:
			return Response({"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND)

		since_id = request.query_params.get("since_id")
		events = get_cdc_events(rule_id, since_id)

		return Response({
			"rule_id": rule_id,
			"rule_name": rule.name,
			"events": events,
			"count": len(events),
		})


class RestApiEchoView(APIView):
	"""
	Mock REST API endpoint for testing - echoes back request details.
	Supports all HTTP methods: GET, POST, PUT, PATCH, DELETE.

	Query params:
	- status_code: Return specific status code (default: 200)
	- delay: Add delay in seconds (max 10)
	- error: If "true", return error response
	"""
	# Disable authentication and permission for this test endpoint
	authentication_classes = []
	permission_classes = []

	def _save_log(self, request, method, response_status):
		"""Save the request to RestApiTestLog for viewing in UI"""
		from .models import RestApiTestLog
		try:
			# Parse body
			body_str = ""
			body_json = None
			if request.data:
				if isinstance(request.data, dict):
					body_json = request.data
					body_str = json.dumps(request.data, ensure_ascii=False)
				else:
					body_str = str(request.data)

			# Get headers (filter sensitive)
			headers = {}
			for key, value in request.headers.items():
				if key.lower() not in ['cookie']:
					if key.lower() == 'authorization':
						headers[key] = '***masked***'
					else:
						headers[key] = value

			# Get client IP
			x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
			if x_forwarded:
				source_ip = x_forwarded.split(',')[0].strip()
			else:
				source_ip = request.META.get('REMOTE_ADDR', '')

			RestApiTestLog.objects.create(
				method=method,
				path=request.path,
				query_params=dict(request.query_params),
				headers=headers,
				body=body_str,
				body_json=body_json,
				source_ip=source_ip,
				response_status=response_status
			)

			# Cleanup old logs (keep last 100)
			log_count = RestApiTestLog.objects.count()
			if log_count > 100:
				oldest_ids = RestApiTestLog.objects.order_by('created_at').values_list('id', flat=True)[:log_count - 100]
				RestApiTestLog.objects.filter(id__in=list(oldest_ids)).delete()

		except Exception as e:
			print(f"Error saving REST API test log: {e}")

	def _build_response(self, request, method):
		import time
		import base64

		# Get query params
		status_code = int(request.query_params.get("status_code", 200))
		delay = min(float(request.query_params.get("delay", 0)), 10)  # Max 10 sec
		simulate_error = request.query_params.get("error", "").lower() == "true"

		# Authentication validation params
		require_auth = request.query_params.get("require_auth", "").lower()  # bearer, basic, api_key
		expected_token = request.query_params.get("expected_token", "")
		expected_api_key = request.query_params.get("expected_api_key", "")
		api_key_header = request.query_params.get("api_key_header", "X-API-Key")

		# Validate authentication if required
		auth_header = request.headers.get("Authorization", "")
		auth_result = {"required": require_auth or "none", "provided": "none", "valid": True}

		if require_auth == "bearer":
			if not auth_header.startswith("Bearer "):
				self._save_log(request, method, 401)
				return Response({
					"success": False,
					"error": "Bearer token required",
					"auth": {"required": "bearer", "provided": "none", "valid": False}
				}, status=401)
			token = auth_header[7:]  # Remove "Bearer "
			auth_result["provided"] = "bearer"
			if expected_token and token != expected_token:
				self._save_log(request, method, 401)
				return Response({
					"success": False,
					"error": "Invalid bearer token",
					"auth": {"required": "bearer", "provided": "bearer", "valid": False}
				}, status=401)

		elif require_auth == "basic":
			if not auth_header.startswith("Basic "):
				self._save_log(request, method, 401)
				return Response({
					"success": False,
					"error": "Basic authentication required",
					"auth": {"required": "basic", "provided": "none", "valid": False}
				}, status=401)
			auth_result["provided"] = "basic"
			# Decode and validate (expected_token format: "username:password")
			try:
				credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
				if expected_token and credentials != expected_token:
					self._save_log(request, method, 401)
					return Response({
						"success": False,
						"error": "Invalid credentials",
						"auth": {"required": "basic", "provided": "basic", "valid": False}
					}, status=401)
			except Exception:
				self._save_log(request, method, 401)
				return Response({
					"success": False,
					"error": "Invalid Basic auth format",
					"auth": {"required": "basic", "provided": "invalid", "valid": False}
				}, status=401)

		elif require_auth == "api_key":
			api_key = request.headers.get(api_key_header, "") or request.query_params.get(api_key_header, "")
			if not api_key:
				self._save_log(request, method, 401)
				return Response({
					"success": False,
					"error": f"API Key required in header '{api_key_header}'",
					"auth": {"required": "api_key", "provided": "none", "valid": False}
				}, status=401)
			auth_result["provided"] = "api_key"
			if expected_api_key and api_key != expected_api_key:
				self._save_log(request, method, 401)
				return Response({
					"success": False,
					"error": "Invalid API key",
					"auth": {"required": "api_key", "provided": "api_key", "valid": False}
				}, status=401)

		# Detect provided auth type for echo
		if auth_header.startswith("Bearer "):
			auth_result["provided"] = "bearer"
		elif auth_header.startswith("Basic "):
			auth_result["provided"] = "basic"
		elif request.headers.get(api_key_header):
			auth_result["provided"] = "api_key"

		# Add delay if requested
		if delay > 0:
			time.sleep(delay)

		# Save to log
		final_status = 500 if simulate_error else status_code
		self._save_log(request, method, final_status)

		# Simulate error
		if simulate_error:
			return Response({
				"success": False,
				"error": "Simulated error for testing",
				"auth": auth_result,
				"echo": self._get_echo_data(request, method)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		# Build echo response
		echo_data = self._get_echo_data(request, method)

		return Response({
			"success": True,
			"message": f"Echo response for {method} request",
			"auth": auth_result,
			"echo": echo_data
		}, status=status_code)

	def _get_echo_data(self, request, method):
		"""Extract request details for echo response"""
		# Get headers (filter out sensitive ones)
		headers = {}
		for key, value in request.headers.items():
			if key.lower() not in ['cookie', 'authorization']:
				headers[key] = value
			elif key.lower() == 'authorization':
				# Show auth type but mask the value
				if value.startswith('Bearer '):
					headers[key] = 'Bearer ***masked***'
				elif value.startswith('Basic '):
					headers[key] = 'Basic ***masked***'
				else:
					headers[key] = '***masked***'

		return {
			"method": method,
			"path": request.path,
			"query_params": dict(request.query_params),
			"headers": headers,
			"body": request.data if request.data else None,
			"content_type": request.content_type,
			"timestamp": timezone.now().isoformat(),
		}

	def get(self, request):
		return self._build_response(request, "GET")

	def post(self, request):
		return self._build_response(request, "POST")

	def put(self, request):
		return self._build_response(request, "PUT")

	def patch(self, request):
		return self._build_response(request, "PATCH")

	def delete(self, request):
		return self._build_response(request, "DELETE")


class RestApiTestLogsView(APIView):
	"""
	Get recent REST API test logs for viewing in UI.
	GET /api/rest-api-logs/
	"""
	# Disable authentication for test logs
	authentication_classes = []
	permission_classes = []

	def get(self, request):
		from .models import RestApiTestLog
		logs = RestApiTestLog.objects.order_by('-created_at')[:50]

		data = []
		for log in logs:
			data.append({
				"id": log.id,
				"method": log.method,
				"path": log.path,
				"query_params": log.query_params,
				"headers": log.headers,
				"body": log.body,
				"body_json": log.body_json,
				"source_ip": log.source_ip,
				"response_status": log.response_status,
				"created_at": log.created_at.isoformat(),
			})

		return Response({
			"logs": data,
			"count": len(data)
		})

	def delete(self, request):
		"""Clear all test logs"""
		from .models import RestApiTestLog
		RestApiTestLog.objects.all().delete()
		return Response({"success": True, "message": "All logs cleared"})


class TestRestApiView(APIView):
	"""
	Test a REST API configuration without saving.
	POST /api/channels/test_rest_api/
	"""
	# Disable authentication for test endpoint
	authentication_classes = []
	permission_classes = []

	def post(self, request):
		import sys
		config = request.data

		# Debug: Log incoming request
		print(f"[TestRestApiView] Received config: {config}", flush=True)
		sys.stdout.flush()

		# Required fields
		api_url = config.get("api_url")
		http_method = config.get("http_method", "POST").upper()

		if not api_url:
			return Response({"success": False, "error": "API URL is required"}, status=400)

		# Handle authentication
		auth_type = config.get("auth_type", "none")

		# If using mock endpoint (/api/rest-echo/), auto-add require_auth parameter
		if "/api/rest-echo" in api_url and auth_type != "none":
			separator = "&" if "?" in api_url else "?"
			if auth_type == "bearer":
				api_url = f"{api_url}{separator}require_auth=bearer"
			elif auth_type == "basic":
				api_url = f"{api_url}{separator}require_auth=basic"
			elif auth_type == "api_key":
				api_key_name = config.get("api_key_name") or "X-API-Key"
				api_url = f"{api_url}{separator}require_auth=api_key&api_key_header={api_key_name}"

		# Helper function to safely convert to string
		def safe_str(val, default=""):
			if val is None:
				return default
			if isinstance(val, bytes):
				try:
					return val.decode('utf-8')
				except:
					return default
			return str(val)

		# Build headers
		headers = {"Content-Type": "application/json"}

		# Add custom headers (ensure string keys/values)
		custom_headers = config.get("headers") or []
		for h in custom_headers:
			if not isinstance(h, dict):
				continue
			key = safe_str(h.get("key"), "")
			value = safe_str(h.get("value"), "")
			# Only add if both key and value are non-empty strings
			if key and value and key.strip() and value.strip():
				headers[key.strip()] = value.strip()

		# Add auth headers
		if auth_type == "basic":
			username = safe_str(config.get("auth_username"), "")
			password = safe_str(config.get("auth_password"), "")
			if username:
				import base64
				credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
				headers["Authorization"] = f"Basic {credentials}"

		elif auth_type == "bearer":
			token = safe_str(config.get("auth_token"), "")
			if token:
				headers["Authorization"] = f"Bearer {token}"

		elif auth_type == "api_key":
			api_key_name = safe_str(config.get("api_key_name"), "X-API-Key") or "X-API-Key"
			api_key_value = safe_str(config.get("api_key_value"), "")
			api_key_location = safe_str(config.get("api_key_location"), "header") or "header"

			# Ensure api_key_name is valid
			api_key_name = api_key_name.strip() if api_key_name else "X-API-Key"
			if not api_key_name:
				api_key_name = "X-API-Key"

			if api_key_value and api_key_value.strip():
				if api_key_location == "header":
					headers[api_key_name] = api_key_value.strip()
				elif api_key_location == "query":
					separator = "&" if "?" in api_url else "?"
					api_url = f"{api_url}{separator}{api_key_name}={api_key_value.strip()}"

		# Build body - For TEST, always use sample body (ignore user template)
		body = None
		if http_method in ["POST", "PUT", "PATCH"]:
			# Always send a valid test body - don't rely on user's template
			body = {
				"test": True,
				"source": "CDCStream REST API Test",
				"timestamp": timezone.now().isoformat(),
				"alert_name": "Test Alert",
				"alert_description": "This is a test request from CDCStream",
				"table_name": "test_table",
				"schema_name": "public",
				"operation": "INSERT",
				"sample_data": {
					"id": 12345,
					"department_id": 123,
					"name": "Test Record"
				}
			}

		# Final sanitization - ensure all headers are valid non-empty strings
		clean_headers = {}
		for k, v in headers.items():
			# Skip if key or value is None/empty/not string
			if not k or not v:
				continue
			# Convert to string if needed
			key_str = safe_str(k, "")
			val_str = safe_str(v, "")
			# Only add if both are non-empty after stripping
			if key_str.strip() and val_str.strip():
				clean_headers[key_str.strip()] = val_str.strip()

		headers = clean_headers

		# Debug log
		print(f"[TestRestApiView] Sending request to {api_url}")
		print(f"[TestRestApiView] Headers: {list(headers.keys())}")

		# Make the request
		try:
			with httpx.Client(timeout=30) as client:
				if http_method == "GET":
					resp = client.get(api_url, headers=headers)
				elif http_method == "POST":
					resp = client.post(api_url, json=body, headers=headers)
				elif http_method == "PUT":
					resp = client.put(api_url, json=body, headers=headers)
				elif http_method == "PATCH":
					resp = client.patch(api_url, json=body, headers=headers)
				elif http_method == "DELETE":
					resp = client.delete(api_url, headers=headers)
				else:
					return Response({"success": False, "error": f"Unsupported method: {http_method}"}, status=400)

				# Parse response
				try:
					response_body = resp.json()
				except:
					response_body = resp.text[:2000] if len(resp.text) > 2000 else resp.text

				return Response({
					"success": resp.is_success,
					"status_code": resp.status_code,
					"response_time_ms": int(resp.elapsed.total_seconds() * 1000),
					"response_headers": dict(resp.headers),
					"response_body": response_body,
					"request": {
						"method": http_method,
						"url": api_url,
						"headers": {k: v if k.lower() != "authorization" else "***" for k, v in headers.items()},
						"body": body
					}
				})

		except httpx.ConnectError as e:
			return Response({
				"success": False,
				"error": f"Connection failed: Could not connect to {api_url}",
				"details": str(e)
			}, status=200)

		except httpx.TimeoutException:
			return Response({
				"success": False,
				"error": f"Request timed out after 30 seconds"
			}, status=200)

		except Exception as e:
			return Response({
				"success": False,
				"error": str(e)
			}, status=200)


class AnomalyDetectorViewSet(viewsets.ModelViewSet):
	"""CRUD operations for anomaly detectors."""
	queryset = AnomalyDetector.objects.all().order_by("-id")
	serializer_class = AnomalyDetectorSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["name", "description", "algorithm"]
	ordering_fields = ["id", "created_at", "name", "algorithm"]

	@action(detail=True, methods=["get"])
	def stats(self, request, pk=None):
		"""Get detailed statistics for this detector."""
		detector = self.get_object()
		stats = FieldStats.objects.filter(detector=detector)
		serializer = FieldStatsSerializer(stats, many=True)
		return Response({
			"detector_id": detector.id,
			"detector_name": detector.name,
			"algorithm": detector.algorithm,
			"training_sample_count": detector.training_sample_count,
			"last_trained_at": detector.last_trained_at,
			"field_stats": serializer.data,
		})

	@action(detail=True, methods=["post"])
	def reset_stats(self, request, pk=None):
		"""Reset all statistics for this detector."""
		detector = self.get_object()
		detector.field_stats.all().delete()
		detector.model_state = {}
		detector.training_sample_count = 0
		detector.last_trained_at = None
		detector.save()
		return Response({"success": True, "message": "Statistics reset successfully"})

	@action(detail=True, methods=["post"])
	def test(self, request, pk=None):
		"""Test detector with sample data."""
		from cdc_stream.anomaly import anomaly_engine

		detector = self.get_object()
		sample_data = request.data.get("sample_data", {})

		if not sample_data:
			return Response(
				{"error": "sample_data is required"},
				status=status.HTTP_400_BAD_REQUEST
			)

		# Build detector config
		detector_config = {
			"id": detector.id,
			"algorithm": detector.algorithm,
			"parameters": detector.parameters,
			"target_columns": detector.target_columns,
		}

		# Process the sample
		result, _ = anomaly_engine.process_event(
			detector_config,
			{"data": sample_data},
			detector.model_state,
		)

		return Response({
			"is_anomaly": result.is_anomaly,
			"score": result.score,
			"threshold": result.threshold,
			"anomaly_fields": result.anomaly_fields,
			"details": result.details,
		})

	@action(detail=False, methods=["get"])
	def algorithms(self, request):
		"""Get list of available algorithms with their descriptions."""
		algorithms = [
			{
				"id": "zscore",
				"name": "Z-Score (Standart Sapma)",
				"description": "Verinin ortalamadan ne kadar saptığını ölçer. En hızlı ve en yaygın kullanılan yöntem.",
				"parameters": [
					{"name": "threshold", "type": "float", "default": 3.0, "description": "Z-Score eşiği (genelde 2-3)"},
					{"name": "min_samples", "type": "int", "default": 30, "description": "Min öğrenme örneği"},
				],
				"speed": "⚡ Çok Hızlı",
				"use_case": "Tek değişkenli anomaliler (maaş, fiyat, tutar)",
			},
			{
				"id": "hbos",
				"name": "HBOS (Histogram Tabanlı)",
				"description": "Histogram kullanarak yoğunluk bazlı anomali tespiti. Log tabloları için ideal.",
				"parameters": [
					{"name": "n_bins", "type": "int", "default": 10, "description": "Histogram kutu sayısı"},
					{"name": "alpha", "type": "float", "default": 0.1, "description": "Anomali oranı"},
					{"name": "min_samples", "type": "int", "default": 100, "description": "Min öğrenme örneği"},
				],
				"speed": "⚡ Çok Hızlı",
				"use_case": "Yüksek hacimli log verileri",
			},
			{
				"id": "ecod",
				"name": "ECOD (Parametresiz)",
				"description": "Kümülatif dağılım tabanlı. Kullanıcıdan parametre istemez, otomatik öğrenir.",
				"parameters": [
					{"name": "contamination", "type": "float", "default": 0.1, "description": "Beklenen anomali oranı"},
					{"name": "max_samples", "type": "int", "default": 1000, "description": "Hafızada tutulacak örnek"},
				],
				"speed": "🚀 Hızlı",
				"use_case": "Auto-Pilot mod: 'Bu tabloyu izle' senaryosu",
			},
			{
				"id": "isolation_forest",
				"name": "Isolation Forest (Çok Boyutlu)",
				"description": "Ağaç tabanlı izolasyon. Birden fazla sütun kombinasyonlarını yakalar.",
				"parameters": [
					{"name": "contamination", "type": "float", "default": 0.1, "description": "Beklenen anomali oranı"},
					{"name": "n_estimators", "type": "int", "default": 50, "description": "Ağaç sayısı"},
					{"name": "min_samples", "type": "int", "default": 100, "description": "Min öğrenme örneği"},
				],
				"speed": "🔄 Orta",
				"use_case": "Çok boyutlu anomaliler (örn: düşük adet + yüksek fiyat)",
			},
			{
				"id": "mahalanobis",
				"name": "Mahalanobis Distance (Korelasyon)",
				"description": "Değişkenler arası korelasyonu hesaba katar. Bot aktivitesi tespiti için ideal.",
				"parameters": [
					{"name": "threshold", "type": "float", "default": 3.0, "description": "Mesafe eşiği"},
					{"name": "min_samples", "type": "int", "default": 50, "description": "Min öğrenme örneği"},
				],
				"speed": "🐢 Yavaş (boyuta bağlı)",
				"use_case": "Korele değişkenler (giriş sayısı vs işlem sayısı)",
			},
		]
		return Response(algorithms)


class AnomalyLogViewSet(viewsets.ReadOnlyModelViewSet):
	"""Read-only access to anomaly logs."""
	queryset = AnomalyLog.objects.all().order_by("-id")
	serializer_class = AnomalyLogSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["detector__name"]
	ordering_fields = ["id", "created_at", "anomaly_score"]

	def get_queryset(self):
		queryset = super().get_queryset()
		detector_id = self.request.query_params.get("detector_id")
		if detector_id:
			queryset = queryset.filter(detector_id=detector_id)
		return queryset

