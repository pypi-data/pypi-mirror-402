# ToothFairyAI CLI

**Command-line interface for interacting with ToothFairyAI agents.**

**Quick access**: Use either `tf` or `toothfairy` commands!

## 📦 Installation

```bash
pip install toothfairy-cli
```

## 🌍 Multi-Region Support

ToothFairyAI operates in multiple regions. Configure your CLI to connect to the appropriate region:

| Region | AI URL | API URL |
|--------|--------|---------|
| **Australia** (default) | https://ai.toothfairyai.com | https://api.toothfairyai.com |
| **United States** | https://ai.us.toothfairyai.com | https://api.us.toothfairyai.com |
| **Europe** | https://ai.eu.toothfairyai.com | https://api.eu.toothfairyai.com |

### Configure for your region:
```bash
# Australia (default - no URLs needed)
tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE

# United States
tf configure \
  --api-key YOUR_KEY \
  --workspace-id YOUR_WORKSPACE \
  --ai-url https://ai.us.toothfairyai.com \
  --base-url https://api.us.toothfairyai.com

# Europe
tf configure \
  --api-key YOUR_KEY \
  --workspace-id YOUR_WORKSPACE \
  --ai-url https://ai.eu.toothfairyai.com \
  --base-url https://api.eu.toothfairyai.com
```

## 🚀 Getting Started

### 1. Configure your credentials and region
```bash
tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE
```

### 2. Send a message to an agent
```bash
tf send "Hello, I need help" --agent-id YOUR_AGENT_ID
```

### 3. Search the knowledge hub
```bash
tf search "AI configuration help"
```

### 4. Explore your workspace
```bash
tf chats                    # List all conversations
tf config-show              # View current settings
```

## ✨ Features

- **💬 Agent Communication**: Send messages to ToothFairyAI agents
- **🔍 Knowledge Hub Search**: Search documents with advanced filtering
- **📋 Chat Management**: List and view chat conversations
- **⚙️ Configuration**: Flexible credential and settings management
- **🎨 Rich Output**: Beautiful terminal interface with colors and tables
- **📊 Multiple Formats**: JSON and text output for both interactive and scripted use
- **🔐 Secure**: Safe credential storage and validation
- **📱 Cross-Platform**: Works on Windows, macOS, and Linux
- **🌍 Multi-Region**: Support for Australia, US, and EU regions

## 💬 Agent Communication Examples

| Use Case | Command |
|----------|---------|
| Simple message | `tf send "What are your hours?" --agent-id "info-agent"` |
| With customer info | `tf send "Schedule appointment" --agent-id "scheduler" --customer-info '{"name": "John"}'` |
| Verbose output | `tf send "Hello" --agent-id "agent-123" --verbose` |
| JSON for scripting | `tf send "Help" --agent-id "agent-123" --output json` |

### Advanced Agent Communication
```bash
# Send message with detailed customer information
tf send "Check my insurance coverage" \
  --agent-id "insurance-agent" \
  --customer-info '{
    "name": "Sarah Johnson",
    "dateOfBirth": "1985-03-15",
    "insurance": {
      "provider": "BlueCross BlueShield",
      "policyNumber": "BC123456789"
    }
  }'
```

## 🔍 Knowledge Hub Search Examples

| Use Case | Command |
|----------|---------|
| Basic search | `tf search "AI agent configuration"` |
| Filter by status | `tf search "machine learning" --status published` |
| Limit results | `tf search "troubleshooting" --top-k 3` |
| Topic filtering | `tf search "automation" --topics "topic_123,topic_456"` |
| Specific document | `tf search "settings" --document-id "doc_550..."` |
| Verbose details | `tf search "deployment" --verbose` |
| JSON output | `tf search "API docs" --output json` |

### Search Filtering Guide

Knowledge Hub search supports powerful filtering options:

- **`--status`**: Filter documents by 'published' or 'suspended' status
- **`--topics`**: Use topic IDs from ToothFairyAI (comma-separated)
- **`--document-id`**: Search within a specific document
- **`--top-k`**: Control number of results (1-50)
- **`--verbose`**: Show relevance scores and metadata

## 📋 Workspace Management Examples

| Use Case | Command |
|----------|---------|
| List all chats | `tf chats` |
| View chat details | `tf chat CHAT_ID` |
| Show config | `tf config-show` |
| Detailed help | `tf help-guide` |

## ⚙️ Configuration

The CLI supports multiple configuration methods (in order of priority):

### Configuration Methods

| Method | Description | Example |
|--------|-------------|---------|
| Environment | Set environment variables | `export TF_API_KEY=your_key` |
| Config file | Use ~/.toothfairy/config.yml | `api_key: your_key`<br/>`workspace_id: your_workspace` |
| CLI arguments | Pass config file path | `tf --config /path/to/config.yml send ...` |

### Setting up configuration

#### Interactive Configuration
```bash
# Australia (default)
tf configure \
  --api-key "your-api-key" \
  --workspace-id "your-workspace-id"

# United States
tf configure \
  --api-key "your-api-key" \
  --workspace-id "your-workspace-id" \
  --base-url "https://api.us.toothfairyai.com" \
  --ai-url "https://ai.us.toothfairyai.com"

# Europe
tf configure \
  --api-key "your-api-key" \
  --workspace-id "your-workspace-id" \
  --base-url "https://api.eu.toothfairyai.com" \
  --ai-url "https://ai.eu.toothfairyai.com"

# View current configuration
tf config-show
```

#### Environment Variables
```bash
# Required
export TF_API_KEY="your-api-key"
export TF_WORKSPACE_ID="your-workspace-id"

# Optional - Region endpoints (defaults to Australia)
# For US:
export TF_BASE_URL="https://api.us.toothfairyai.com"
export TF_AI_URL="https://ai.us.toothfairyai.com"

# For EU:
export TF_BASE_URL="https://api.eu.toothfairyai.com"
export TF_AI_URL="https://ai.eu.toothfairyai.com"
```

#### Config File Format
Create `~/.toothfairy/config.yml`:
```yaml
# Required
api_key: "your-api-key"
workspace_id: "your-workspace-id"

# Optional - Region endpoints (defaults to Australia)
# For US:
base_url: "https://api.us.toothfairyai.com"
ai_url: "https://ai.us.toothfairyai.com"

# For EU:
# base_url: "https://api.eu.toothfairyai.com"
# ai_url: "https://ai.eu.toothfairyai.com"
```

## 📊 Output Formats

The CLI supports `--output` or `-o` flag:

- **`text`** (default): Pretty formatted tables and panels
- **`json`**: Raw JSON output for scripting

```bash
# Get JSON output for scripting
tf send "Hello" --agent-id "agent-123" --output json | jq '.agentResponse.contents.content'

# Search with JSON output
tf search "documentation" --output json | jq '.[].title'
```

## 🔧 Command Reference

### Global Options
- `--config`, `-c`: Path to configuration file
- `--verbose`, `-v`: Enable verbose logging and API debugging

### Commands

#### `configure`
Set up CLI credentials and configuration.

**Options:**
- `--api-key`: API key (required)
- `--workspace-id`: Workspace ID (required)
- `--base-url`: ToothFairy API base URL (optional)
- `--ai-url`: ToothFairyAI URL (optional)
- `--config-path`: Custom path to save config file

#### `send <message>`
Send a message to a ToothFairyAI agent.

**Arguments:**
- `message`: The message text to send

**Options:**
- `--agent-id`: Agent ID to send message to (required)
- `--phone-number`: Phone number for SMS channel (optional)
- `--customer-id`: Customer ID (optional)
- `--provider-id`: SMS provider ID (optional)
- `--customer-info`: Customer info as JSON string (optional)
- `--output`, `-o`: Output format (json|text)
- `--verbose`, `-v`: Show detailed response information

#### `search <query>`
Search for documents in the knowledge hub.

**Arguments:**
- `query`: The search query text

**Options:**
- `--top-k`, `-k`: Number of documents to retrieve (1-50, default: 10)
- `--status`: Filter by document status (published|suspended)
- `--document-id`: Search within specific document ID
- `--topics`: Comma-separated topic IDs to filter by
- `--output`, `-o`: Output format (json|text)
- `--verbose`, `-v`: Show detailed search information

#### `chats`
List all chats in the workspace.

**Options:**
- `--output`, `-o`: Output format (json|text)

#### `chat <chat-id>`
Get details of a specific chat.

**Arguments:**
- `chat-id`: The chat ID to retrieve

**Options:**
- `--output`, `-o`: Output format (json|text)

#### `config-show`
Display current configuration (with masked API key).

#### `help-guide`
Show detailed help with examples, common issues, and pro tips.

## 💡 Usage Examples

### Basic Workflow
```bash
# Configure once
tf configure --api-key "tf-key-abc123" --workspace-id "workspace-456"

# Send messages to agents
tf send "I'd like to schedule a session" --agent-id "my-scheduler"

# Search for relevant information
tf search "appointment scheduling help"

# Manage conversations
tf chats
tf chat chat-abc123
```

### Scripting Examples
```bash
#!/bin/bash

# Send message and extract agent response
RESPONSE=$(tf send "What are your hours?" \
  --agent-id "info-agent" \
  --output json)

# Extract the agent's text response
AGENT_TEXT=$(echo "$RESPONSE" | jq -r '.agentResponse.contents.content')
echo "Agent said: $AGENT_TEXT"

# Search documents and extract relevant content
SEARCH_RESULTS=$(tf search "office hours" --output json)
TOP_RESULT=$(echo "$SEARCH_RESULTS" | jq -r '.[0].raw_text')
echo "Found documentation: $TOP_RESULT"

# Get chat ID for follow-up
CHAT_ID=$(echo "$RESPONSE" | jq -r '.chatId')
echo "Chat ID: $CHAT_ID"
```

## ⚠️ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Configuration incomplete | Run: `tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE` |
| No text response found | Use `--verbose` flag to see full response details |
| Agent not responding | Check agent-id is correct and agent is active |
| Network errors | Verify API endpoints are accessible and credentials are valid |

## 🐛 Troubleshooting

### Debug Mode
Use the `--verbose` flag to see detailed API request/response information:

```bash
tf --verbose send "test message" --agent-id "agent-123"
tf search "test" --verbose
```

### Configuration Issues
1. **Check current configuration:**
   ```bash
   tf config-show
   ```

2. **Verify credentials:**
   ```bash
   tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE
   ```

3. **Test connection:**
   ```bash
   tf chats --verbose
   ```

## 📖 More Help

- **Command-specific help**: `tf COMMAND --help`
- **Detailed examples**: `tf help-guide`
- **Verbose debugging**: Use `--verbose` flag
- **JSON output**: Use `--output json` for machine-readable output
- **Configuration priority**: Environment variables → ~/.toothfairy/config.yml → CLI args

## ✨ Pro Tips

💾 **Save time**: Configure once with `tf configure`, then just use `tf send` and `tf search`

🔍 **Debug issues**: Use `--verbose` to see full API responses and troubleshoot

📝 **Scripting**: Use `--output json` and tools like `jq` to parse responses

⚡ **Quick tests**: Only `--agent-id` is required for send, only query for search

🎯 **Better search**: Use `--status`, `--topics`, and `--document-id` for targeted results

🔧 **Multiple environments**: Use different config files with `--config` flag

🌍 **Regional performance**: Choose the region closest to you for best performance

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **Repository**: [ToothFairy CLI on Gitea](https://gitea.toothfairyai.com/ToothFairyAI/tooth-fairy-website/toothfairy-cli)
- **Python Package**: [toothfairy-cli on PyPI](https://pypi.org/project/toothfairy-cli/)
- **Issues**: [Report bugs and feature requests](https://gitea.toothfairyai.com/ToothFairyAI/tooth-fairy-website/toothfairy-cli/issues)
