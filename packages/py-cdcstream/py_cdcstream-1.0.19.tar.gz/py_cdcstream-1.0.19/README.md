# 🔄 CDC Stream

**Real-time database change notifications - No Docker, No Kafka, Just Python!**

CDC Stream captures database changes (INSERT, UPDATE, DELETE) and sends notifications to Slack, Email, Webhooks, or REST APIs.

## ✨ Features

- 🚀 **Simple Setup**: Just `pip install` and `start`
- 🐘 **PostgreSQL Support**: Native trigger-based CDC
- 📡 **Multiple Notification Channels**: Slack, Email, Webhook, REST API
- 🎯 **Flexible Rules**: Filter and route events based on conditions
- 🌐 **Web UI**: Beautiful dashboard for configuration
- 🐍 **Pure Python**: No Docker, Kafka, or external dependencies required

## 🚀 Quick Start

```bash
# Install
pip install cdc-stream

# Start (that's it!)
python -m cdc_stream start

# Open http://localhost:5858 in your browser
```

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install cdc-stream
```

### From Source

```bash
git clone https://github.com/yourusername/cdc-stream.git
cd cdc-stream
pip install -e .
```

## 🎯 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Database                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  INSERT/UPDATE/DELETE on your tables                │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │ TRIGGER (auto-installed)         │
│                         ▼                                   │
│              pg_notify('cdc_stream_events')                │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    CDC Stream Worker                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LISTEN → Filter → Rule Check → Send Notification   │   │
│  └─────────────────────────────────────────────────────┘   │
│         │              │              │              │      │
│         ▼              ▼              ▼              ▼      │
│     📧 Email      💬 Slack      🔗 Webhook     🌐 REST     │
└─────────────────────────────────────────────────────────────┘
```

## 🖥️ Web UI

Open `http://localhost:5858` after starting CDC Stream:

1. **Add Connection**: Configure your PostgreSQL database
2. **Create Alert**: Select table, define filters, choose notification channel
3. **Watch Live**: Real-time event stream visualization

## 📋 CLI Commands

```bash
# Start everything (web UI + worker)
python -m cdc_stream start

# Start with custom port
python -m cdc_stream start --port 8080

# Start only web server
python -m cdc_stream webserver

# Start only worker
python -m cdc_stream worker

# Check status
python -m cdc_stream status

# Show version
python -m cdc_stream version

# Manage triggers
python -m cdc_stream triggers <datasource_id> list
python -m cdc_stream triggers <datasource_id> sync
python -m cdc_stream triggers <datasource_id> remove

# Test listener
python -m cdc_stream test-listener <datasource_id>
```

## 🔔 Notification Channels

### Slack
```json
{
  "webhook_url": "https://hooks.slack.com/services/..."
}
```

### Email (SMTP)
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your@email.com",
  "smtp_password": "app-password",
  "from_email": "alerts@yourcompany.com",
  "to_emails": ["team@yourcompany.com"]
}
```

### Webhook
```json
{
  "url": "https://your-api.com/webhook",
  "method": "POST",
  "headers": {"Authorization": "Bearer token"}
}
```

### REST API
```json
{
  "method": "POST",
  "url": "https://api.example.com/events",
  "auth_type": "bearer",
  "auth_token": "your-token",
  "headers": {},
  "body": "{\"event\": \"{{data}}\"}"
}
```

## 🎯 Filter & Rule Examples

### Filters (Pre-condition)
Only process events matching these conditions:

```json
[
  {"field": "status", "operator": "==", "value": "active"},
  {"field": "amount", "operator": ">", "value": 1000}
]
```

### Rules (Alert condition)
Send notification when these conditions are met:

```json
[
  {"field": "priority", "operator": "==", "value": "critical"}
]
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Change default ports
CDC_STREAM_PORT=5858
CDC_STREAM_DB_PATH=./cdc_stream.db
```

### Database Requirements

CDC Stream requires PostgreSQL 10+ with these settings (usually default):

```sql
-- Check your settings
SHOW wal_level;  -- Should work with any value
```

**Note**: Unlike traditional CDC tools, CDC Stream uses trigger-based capture which works without changing `wal_level`.

## 📊 System Requirements

- **Python**: 3.9+
- **Database**: PostgreSQL 10+
- **RAM**: ~50MB
- **Disk**: ~10MB

## 🔒 Security

- Credentials stored locally in SQLite
- No external services required
- All communication stays within your infrastructure

## 🐛 Troubleshooting

### Worker not receiving events

1. Check if triggers are installed:
```bash
python -m cdc_stream triggers <datasource_id> list
```

2. Sync triggers with alerts:
```bash
python -m cdc_stream triggers <datasource_id> sync
```

### Connection issues

1. Verify database is accessible
2. Check firewall settings
3. Ensure user has CREATE TRIGGER permission

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

---

Made with ❤️ for the developer community
