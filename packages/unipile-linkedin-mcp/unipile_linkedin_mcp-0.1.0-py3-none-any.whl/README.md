# Unipile LinkedIn MCP Server

A fully-featured [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for the [Unipile](https://unipile.com/) LinkedIn API. Enables AI assistants to interact with LinkedIn for search, messaging, connections, and Sales Navigator features.

## Features

- **LinkedIn Search** - People, companies, and posts search with Classic and Sales Navigator filters
- **Profile Management** - View profiles, company pages, and your own profile
- **Connections** - Send/accept/decline invitations, list connections
- **Messaging** - List chats, send messages, start conversations
- **InMail** - Send InMail to non-connections (Premium/Sales Navigator)
- **Sales Navigator** - Advanced filters like tenure, seniority, company headcount

## Installation

### Using uvx (recommended)

```bash
uvx unipile-linkedin-mcp
```

### Using pip

```bash
pip install unipile-linkedin-mcp
```

## Configuration

### Environment Variables

Set these environment variables before running:

```bash
export UNIPILE_API_KEY="your-api-key"
export UNIPILE_BASE_URL="https://api13.unipile.com:14376/api/v1"
export UNIPILE_ACCOUNT_ID="your-account-id"
```

Or create a `.env` file in your working directory.

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "unipile-linkedin": {
      "command": "uvx",
      "args": ["unipile-linkedin-mcp"],
      "env": {
        "UNIPILE_API_KEY": "your-api-key",
        "UNIPILE_BASE_URL": "https://api13.unipile.com:14376/api/v1",
        "UNIPILE_ACCOUNT_ID": "your-account-id"
      }
    }
  }
}
```

## Available Tools (22 total)

### Search
| Tool | Description |
|------|-------------|
| `search_people` | Search people with Classic LinkedIn filters |
| `search_people_sales_nav` | Search with Sales Navigator advanced filters |
| `search_companies` | Search for companies |
| `search_posts` | Search LinkedIn posts/content |
| `get_search_params` | Get valid filter IDs (locations, industries, etc.) |

### Profiles
| Tool | Description |
|------|-------------|
| `list_accounts` | List all connected LinkedIn accounts |
| `get_my_profile` | Get authenticated user's profile |
| `get_profile` | Get any user's full profile |
| `get_company_profile` | Get company page details |

### Connections
| Tool | Description |
|------|-------------|
| `send_invitation` | Send connection request (max 300 char message) |
| `list_invitations_sent` | View pending outbound invites |
| `list_invitations_received` | View inbound connection requests |
| `accept_invitation` | Accept a connection request |
| `decline_invitation` | Decline a connection request |
| `cancel_invitation` | Withdraw a sent invitation |
| `list_relations` | List 1st degree connections |

### Messaging
| Tool | Description |
|------|-------------|
| `list_chats` | List message conversations |
| `get_chat_messages` | Get messages from a chat |
| `send_message` | Send message in existing chat |
| `start_chat` | Start new conversation with connections |

### InMail (Premium)
| Tool | Description |
|------|-------------|
| `send_inmail` | Send InMail to non-connections |
| `get_inmail_credits` | Check remaining InMail credits |

## Usage Examples

### Search for People

```python
# Classic LinkedIn search
search_people(keywords="software engineer", location=["103644278"], limit=10)

# Sales Navigator search with advanced filters
search_people_sales_nav(
    keywords="CTO",
    company_headcount=[{"min": 51, "max": 200}],
    changed_jobs=True,
    seniority_level=["Director", "VP"]
)
```

### Get Search Parameter IDs

```python
# Find location IDs
get_search_params(param_type="LOCATION", query="San Francisco")

# Find industry IDs
get_search_params(param_type="INDUSTRY", query="Software")
```

### Send a Connection Request

```python
send_invitation(
    provider_id="ACoAAB...",
    message="Hi! I'd love to connect."
)
```

### Start a Conversation

```python
# With 1st degree connection
start_chat(
    attendees_ids=["ACoAAB..."],
    text="Hello! Great connecting with you."
)

# InMail to non-connection (requires credits)
send_inmail(
    attendees_ids=["ACoAAB..."],
    subject="Quick question",
    text="Hi, I noticed your work at..."
)
```

## Getting Unipile Credentials

1. Sign up at [Unipile](https://unipile.com/)
2. Connect your LinkedIn account
3. Get your API key and account ID from the dashboard
4. Note your base URL (varies by region)

## Rate Limits

Unipile recommends these daily limits:
- Profile views: 80-100/day (Classic), 150/day (Sales Nav)
- Invitations: 80-100/day (paid), 15/week (free)
- Messages: 100-150/day

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.
