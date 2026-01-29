# ToothFairyAI CLI (Node.js)

A Node.js command-line interface for interacting with ToothFairyAI agents.

## Installation

### From NPM
```bash
npm install -g @toothfairyai/cli
```

### From Source
```bash
git clone <repository-url>
cd toothfairy-cli-js
npm install
npm link  # Makes 'toothfairy' command available globally
```

## Quick Start

1. **Configure your credentials:**
```bash
toothfairy configure \
  --api-key "your-api-key" \
  --workspace-id "your-workspace-id"
```

2. **Send a message to an agent:**
```bash
toothfairy send "Hello, I need help with my appointment" \
  --agent-id "agent-123"
```

3. **Search the knowledge hub:**
```bash
toothfairy search "appointment scheduling help"
```

4. **List your chats:**
```bash
toothfairy chats
```

## Available Commands

### Global Options
- `-c, --config <path>`: Path to configuration file
- `-v, --verbose`: Enable verbose logging

### Commands

#### `configure`
Configure ToothFairy CLI credentials and settings.

**Options:**
- `--api-key <key>`: API key (required)
- `--workspace-id <id>`: Workspace ID (required)
- `--base-url <url>`: ToothFairy API base URL (optional, defaults to production)
- `--ai-url <url>`: ToothFairyAI URL (optional, defaults to production)
- `--config-path <path>`: Custom path to save config file

**Example:**
```bash
toothfairy configure --api-key "your-key" --workspace-id "your-workspace"
```

#### `send <message>`
Send a message to a ToothFairyAI agent.

**Arguments:**
- `message`: The message text to send

**Options:**
- `--agent-id <id>`: Agent ID to send message to (required)
- `--phone-number <number>`: Phone number for SMS channel (optional)
- `--customer-id <id>`: Customer ID (optional)
- `--provider-id <id>`: SMS provider ID (optional)
- `--customer-info <json>`: Customer info as JSON string (optional)
- `-o, --output <format>`: Output format (json|text, default: text)
- `-v, --verbose`: Show detailed response information

**Examples:**
```bash
# Simple message
toothfairy send "What are your hours?" --agent-id "info-agent"

# With customer information
toothfairy send "Schedule appointment" \
  --agent-id "scheduler" \
  --customer-info '{"name": "John", "phone": "+1234567890"}'

# With verbose output
toothfairy send "Hello" --agent-id "agent-123" --verbose
```

#### `search <query>`
Search for documents in the knowledge hub.

**Arguments:**
- `query`: The search query text

**Options:**
- `-k, --top-k <number>`: Number of documents to retrieve (1-50, default: 10)
- `--status <status>`: Filter by document status (published|suspended)
- `--document-id <id>`: Search within specific document ID
- `--topics <topics>`: Comma-separated topic IDs to filter by
- `-o, --output <format>`: Output format (json|text, default: text)
- `-v, --verbose`: Show detailed search information

**Examples:**
```bash
# Basic search
toothfairy search "AI agent configuration"

# Filter by status and limit results
toothfairy search "machine learning" --status published --top-k 5

# Search with topic filtering
toothfairy search "automation" --topics "topic_123,topic_456"

# Verbose search with JSON output
toothfairy search "deployment" --verbose --output json
```

#### `chats`
List all chats in the workspace.

**Options:**
- `-o, --output <format>`: Output format (json|text, default: text)

**Example:**
```bash
toothfairy chats
toothfairy chats --output json
```

#### `chat <chat-id>`
Get details of a specific chat.

**Arguments:**
- `chat-id`: The chat ID to retrieve

**Options:**
- `-o, --output <format>`: Output format (json|text, default: text)

**Example:**
```bash
toothfairy chat "chat-abc123"
```

#### `config-show`
Display current configuration (with masked API key).

**Example:**
```bash
toothfairy config-show
```

#### `help-guide`
Show detailed help with examples, common issues, and pro tips.

**Example:**
```bash
toothfairy help-guide
```

## Configuration

The CLI supports multiple configuration methods (in order of priority):

1. **Environment variables:**
```bash
export TF_API_KEY="your-api-key"
export TF_WORKSPACE_ID="your-workspace-id"
export TF_BASE_URL="https://api.toothfairyai.com"  # optional
export TF_AI_URL="https://ai.toothfairyai.com"     # optional
```

2. **Config file at `~/.toothfairy/config.yml`:**
```yaml
api_key: "your-api-key"
workspace_id: "your-workspace-id"
base_url: "https://api.toothfairyai.com"  # optional
ai_url: "https://ai.toothfairyai.com"     # optional
```

3. **CLI arguments:**
```bash
toothfairy --config /path/to/config.yml send "Hello" --agent-id "agent-123"
```

## Output Formats

Both `json` and `text` output formats are supported:

- **`text`** (default): Pretty formatted tables and panels
- **`json`**: Raw JSON output for scripting

```bash
# Get JSON output for scripting
toothfairy send "Hello" --agent-id "agent-123" --output json | jq '.agentResponse.contents.content'

# Search with JSON output
toothfairy search "documentation" --output json | jq '.[].title'
```

## SDK Usage

This package also provides a JavaScript SDK for programmatic access to ToothFairyAI.

### Basic SDK Usage

```javascript
const ToothFairyAPI = require('@toothfairyai/cli/src/api');

const api = new ToothFairyAPI(
  'https://api.toothfairyai.com',    // baseUrl
  'https://ai.toothfairyai.com',     // aiUrl
  'https://stream.toothfairyai.com', // aiStreamUrl
  'your-api-key',                    // apiKey
  'your-workspace-id',               // workspaceId
  false                              // verbose mode
);

// Send a message with streaming response
await api.sendMessageToAgentStream(
  'Hello!',
  'agent-id',
  null, // phoneNumber
  null, // customerId
  null, // providerId
  {},   // customerInfo
  (eventType, data) => {
    console.log(`Event: ${eventType}`, data);
  }
);
```

### New in v1.1.0: Show Progress Flag

The SDK now supports a `showProgress` flag that enables tracking of all events from the SSE endpoint, similar to the CLI's `--show-progress` flag:

```javascript
// Default behavior (standard events only)
await api.sendMessageToAgentStream(
  'Hello!', 
  'agent-id', 
  null, null, null, {}, 
  (eventType, data) => {
    // Receives: 'status', 'progress', 'data', 'complete', 'error', etc.
    console.log(eventType, data);
  }
);

// With showProgress enabled (all SSE events)
await api.sendMessageToAgentStream(
  'Hello!', 
  'agent-id', 
  null, null, null, {}, 
  (eventType, data) => {
    if (eventType === 'sse_event') {
      // Raw SSE event with complete data from streaming endpoint
      console.log('Raw SSE event:', data);
    } else {
      // Standard processed events
      console.log('Standard event:', eventType, data);
    }
  },
  {}, // attachments
  true // showProgress = true
);
```

**Event Types:**
- `'status'`: Connection status ('connected', 'complete')
- `'progress'`: Agent processing status updates
- `'data'`: Streaming response text chunks
- `'complete'`: Final response with metadata
- `'error'`: Error events
- `'sse_event'`: All raw SSE events (when showProgress=true)

For full documentation and cross-platform examples, see the main [README.md](../README.md) in the parent directory.

## Development

```bash
npm install
npm run lint
npm test
```

## License

MIT