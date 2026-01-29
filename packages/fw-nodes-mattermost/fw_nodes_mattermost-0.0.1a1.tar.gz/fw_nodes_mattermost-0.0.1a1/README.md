# Flowire Mattermost Nodes

Mattermost integration nodes for Flowire workflow automation. This package provides nodes for receiving and sending messages with Mattermost.

## Installation

```bash
uv add fw-nodes-mattermost
```

Then add the package to your Flowire settings:

```python
# settings.py
installed_node_packages = ["fw-nodes-core", "fw-nodes-mattermost"]
```

## Included Nodes

### Triggers

| Node | Description |
|------|-------------|
| `Mattermost Outgoing Webhook` | Receive messages from Mattermost channels via outgoing webhooks |
| `Mattermost Slash Command` | Receive slash command invocations from Mattermost |

### Messaging

| Node | Description |
|------|-------------|
| `Mattermost Post Message` | Post a message to a Mattermost channel |

## Usage Examples

### Outgoing Webhook

Receive channel messages when a trigger word is used:

```python
# Node configuration:
{
    "validate_token": true,
    "token": "{{project.mattermost-webhook-token}}"
}

# Outputs:
# - text: The message content
# - user_name: Who posted the message
# - channel_name: Where it was posted
# - trigger_word: The word that triggered the webhook
```

### Slash Command

Receive slash command invocations (e.g., `/mycommand args`):

```python
# Node configuration:
{
    "validate_token": true,
    "token": "{{project.mattermost-slash-token}}"
}

# Outputs:
# - command: The slash command (e.g., "/weather")
# - text: Arguments after the command
# - user_name: Who invoked the command
# - response_url: URL for delayed responses
```

### Post Message

Send messages to Mattermost channels:

```python
# Node configuration:
{
    "credential_id": "your-mattermost-credential",
    "channel_id": "{{slash-command.channel_id}}",
    "message": "Hello from Flowire! Processing your request...",
    "root_id": "{{slash-command.post_id}}"  # Optional: reply in thread
}
```

## Mattermost Setup

### Outgoing Webhook

1. Go to **Integrations > Outgoing Webhooks** in Mattermost
2. Click **Add Outgoing Webhook**
3. Set the callback URL to your Flowire webhook endpoint
4. Configure trigger words or channels
5. Copy the token and store it as a project variable

### Slash Command

1. Go to **Integrations > Slash Commands** in Mattermost
2. Click **Add Slash Command**
3. Set the request URL to your Flowire webhook endpoint
4. Configure the command (e.g., `/mycommand`)
5. Copy the token and store it as a project variable

### Credentials for Post Message

1. In Mattermost, go to **Account Settings > Security > Personal Access Tokens**
2. Generate a new token with appropriate permissions
3. In Flowire, create a Mattermost credential with:
   - **Server URL**: Your Mattermost server (e.g., `https://mattermost.example.com`)
   - **Access Token**: The personal access token

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run linter
ruff check .

# Auto-fix lint issues
ruff check . --fix

# Format code
ruff format .

# Run tests
pytest
```

## Project Structure

```
fw-nodes-mattermost/
├── fw_nodes_mattermost/
│   ├── __init__.py
│   └── nodes/
│       ├── __init__.py
│       ├── outgoing_webhook.py
│       ├── slash_command.py
│       └── post_message.py
├── tests/
├── pyproject.toml
└── README.md
```

## License

This project is licensed under the [MIT License](LICENSE).
