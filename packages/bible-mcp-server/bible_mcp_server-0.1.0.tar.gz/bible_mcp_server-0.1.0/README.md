# Bible MCP Server

A comprehensive Bible server providing verse lookup, search, study tools, and devotional content using Bible APIs

## Installation

```bash
uvx bible-mcp-server
```

## Tools

- `get_verse`: Get a specific Bible verse or passage
- `search_verses`: Search for Bible verses containing specific words or phrases
- `get_random_verse`: Get a random Bible verse for inspiration or daily reading
- `get_chapter_info`: Get information about a Bible book or chapter, including verse count and summary
- `compare_translations`: Compare a Bible verse across different translations

## Resources

- `bible://books/{testament}`: List of all Bible books with basic information
- `bible://popular/{category}`: Collection of popular and frequently referenced Bible verses

## Prompts

- `bible_study_guide`: Generate a Bible study guide for a specific passage or topic
- `sermon_outline`: Create a sermon outline based on a Bible passage
- `devotional_reflection`: Generate a personal devotional reflection on a Bible verse or passage

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "bible-mcp-server": {
      "command": "uvx",
      "args": ["bible-mcp-server"]
    }
  }
}
```

---

Generated with MCP Builder
