---
name: notion
description: (Notion MCP - Skill) Notion workspace management. Search, create, update, move, duplicate pages and databases. Manage comments, query data sources, and access user/team info. MUST USE for any Notion-related operations.
mcp:
  notion:
    command: npx
    args: ["-y", "mcp-remote", "https://mcp.notion.com/mcp"]
---

# Notion MCP Skill

Notion workspace integration via official Notion MCP server. Provides full CRUD access to pages, databases, comments, and workspace metadata.

---

## Skill Scope & Boundaries

### This Skill PROVIDES
- Workspace-wide search (including connected tools: Slack, Google Drive, Jira)
- Page CRUD: create, read (fetch), update, move, duplicate
- Database management: create databases, update data sources, query views
- Comments: create and retrieve page/block-level comments
- Workspace metadata: users, teams, bot info

### This Skill does NOT HANDLE
- File uploads or media management
- Notion API token management (handled by MCP auth flow)
- Workflow automation or triggers

---

## Trigger Conditions

**MUST load this Skill when:**

- User mentions Notion pages, databases, or workspace
- Requests to search, create, update, or organize Notion content
- Querying meeting notes, project docs, task databases
- Managing comments or discussions on Notion pages

---

## Rate Limits

| Scope | Limit |
|-------|-------|
| General (all tools) | 180 requests/min |
| Search (notion-search) | 30 requests/min |

Avoid excessive parallel searches. Sequential searches typically stay under limits.

---

## Available Tools

Call via `skill_mcp(mcp_name="notion", tool_name="...", arguments={...})`

### 1. notion-search - Workspace Search

Search across Notion workspace and connected tools (Slack, Google Drive, Jira).

> Requires Notion AI for connected tool search. Without AI plan, search is limited to Notion workspace only.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search query text |

**Example prompts:**
- "Search for documents mentioning 'budget approval process'"
- "Find all project pages that mention 'ready for dev'"

### 2. notion-fetch - Fetch Page Content

Retrieves content from a Notion page or database by URL.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | Full Notion page or database URL |

**Example:**
```python
skill_mcp(
  mcp_name="notion",
  tool_name="notion-fetch",
  arguments={"url": "https://notion.so/page-url"}
)
```

### 3. notion-create-pages - Create Pages

Creates one or more Notion pages with properties and content. Creates private page if no parent specified.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pages` | array | Array of page objects with properties and content |

**⚠️ CRITICAL: Page Object Format**

Each page object in the `pages` array uses a **flat key-value structure** for properties, NOT the nested Notion API property format.

```json
{
  "parent": {"data_source_id": "your-database-data-source-id"},
  "properties": {
    "Name": "Page Title Here",
    "Status": "Active",
    "Priority": 5,
    "Amount": 123.45,
    "Category": "Finance",
    "date:Due Date:start": "2026-01-15T10:30:00",
    "date:Due Date:is_datetime": 1
  },
  "content": "## Page Body\n\nMarkdown content goes here.\n\n- Bullet point 1\n- Bullet point 2"
}
```

**Property Value Types (flat format, NOT nested Notion API format):**

| Property Type | Value Format | Example |
|---------------|-------------|---------|
| `title` | string | `"Name": "My Page"` |
| `rich_text` | string | `"Notes": "Some text"` |
| `number` | number | `"Price": 99.99` |
| `select` | string (option name) | `"Status": "Active"` |
| `checkbox` | boolean | `"Done": true` |
| `url` | string | `"Link": "https://..."` |
| `date` | **special key format** | See below |

**⚠️ Date Properties — Special Key Syntax:**

Date fields use a special key naming convention (NOT the standard Notion API format):

```json
{
  "date:Field Name:start": "2026-01-15T10:30:00",
  "date:Field Name:is_datetime": 1
}
```

- `date:{PropertyName}:start` — ISO 8601 date string (e.g., `"2026-01-15"` or `"2026-01-15T10:30:00"`)
- `date:{PropertyName}:is_datetime` — Set to `1` to include time, omit or `0` for date-only

**⚠️ Parent — Using `data_source_id`:**

When inserting pages into a database, use `data_source_id` (returned from `notion-create-database`), NOT `database_id`:

```json
{"parent": {"data_source_id": "845722ac-f631-4b61-a202-452e916518cd"}}
```

**Full Example — Batch Insert:**
```python
skill_mcp(
  mcp_name="notion",
  tool_name="notion-create-pages",
  arguments={
    "pages": [
      {
        "parent": {"data_source_id": "your-data-source-id"},
        "properties": {
          "Name": "ETH-USDT-SWAP 空 10x",
          "交易对": "ETH-USDT-SWAP",
          "方向": "空",
          "杠杆": 10,
          "开仓价": 2198.51,
          "平仓价": 2199.74,
          "已实现收益(U)": -1.23,
          "收益率": -0.0126,
          "保证金(U)": 97.83,
          "保证金模式": "全仓",
          "费用(U)": -0.69,
          "结果": "亏损",
          "date:开仓时间:start": "2026-02-04T22:00:30",
          "date:开仓时间:is_datetime": 1,
          "date:平仓时间:start": "2026-02-04T22:04:13",
          "date:平仓时间:is_datetime": 1
        },
        "content": "### 经验分析\n\n持仓仅3分钟，方向判断错误..."
      },
      {
        "parent": {"data_source_id": "your-data-source-id"},
        "properties": {
          "Name": "BTC-USDT-SWAP 多 5x",
          "交易对": "BTC-USDT-SWAP",
          "方向": "多",
          "杠杆": 5,
          "开仓价": 95174.0,
          "平仓价": 95422.2,
          "已实现收益(U)": 1.74,
          "收益率": 0.0095,
          "保证金(U)": 182.73,
          "保证金模式": "全仓",
          "费用(U)": -0.64,
          "结果": "盈利",
          "date:开仓时间:start": "2026-01-14T09:43:42",
          "date:开仓时间:is_datetime": 1,
          "date:平仓时间:start": "2026-01-14T10:18:26",
          "date:平仓时间:is_datetime": 1
        },
        "content": "### 经验分析\n\n5x杠杆方向正确，低风险操作..."
      }
    ]
  }
)
```

**Batch Size**: Recommended 10-20 pages per call for reliability. Max supported is 100.

**Example prompts:**
- "Create a project kickoff page under our Projects folder"
- "Add a new feature request to our feature database"

### 4. notion-update-page - Update Page

Update a page's properties or content.

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_id` | string | ID of the page to update |
| `properties` | object | Properties to update |
| `content` | string | New content to add or replace |

**Example prompts:**
- "Change the status of this task from 'In Progress' to 'Complete'"
- "Add a new section about risks to the project plan"

### 5. notion-move-pages - Move Pages

Move one or more pages or databases to a new parent.

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_ids` | array | IDs of pages to move |
| `parent_id` | string | Target parent page/database ID |

**Example prompts:**
- "Move my weekly meeting notes to the 'Team Meetings' page"
- "Reorganize all project documents under 'Active Projects'"

### 6. notion-duplicate-page - Duplicate Page

Duplicate a page within the workspace. Completes asynchronously.

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_id` | string | ID of the page to duplicate |

**Example prompts:**
- "Duplicate my project template for the new Q3 initiative"

### 7. notion-create-database - Create Database

Creates a new database with specified properties, data source, and initial view.

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Database title |
| `properties` | object | Column definitions (see format below) |
| `parent_id` | string | Parent page ID (optional) |

**⚠️ CRITICAL: Property Definition Format**

Properties MUST use Notion API format: `{property_name: {property_type: {config}}}`, NOT `{"type": "property_type"}`.

```json
// ✅ CORRECT
{
  "Name": {"title": {}},
  "Status": {"select": {"options": [{"name": "Active"}, {"name": "Done"}]}},
  "Priority": {"number": {"format": "number"}},
  "Due Date": {"date": {}},
  "Notes": {"rich_text": {}}
}

// ❌ WRONG — will fail
{
  "Notes": {"type": "rich_text"},
  "Priority": {"type": "number"}
}
```

**Supported property types:**
- `title`: `{"title": {}}` — Every database must have exactly one title property
- `rich_text`: `{"rich_text": {}}` — Plain text field
- `number`: `{"number": {"format": "number"}}` — Numeric value. Format options: `"number"`, `"percent"`, `"dollar"`, `"yuan"`, etc.
- `select`: `{"select": {"options": [{"name": "Option1"}, {"name": "Option2"}]}}` — Single select
- `multi_select`: `{"multi_select": {"options": [{"name": "Tag1"}, {"name": "Tag2"}]}}` — Multi select
- `date`: `{"date": {}}` — Date/datetime field
- `checkbox`: `{"checkbox": {}}` — Boolean field
- `url`: `{"url": {}}` — URL field
- `email`: `{"email": {}}` — Email field

**Example:**
```python
skill_mcp(
  mcp_name="notion",
  tool_name="notion-create-database",
  arguments={
    "title": "Task Tracker",
    "parent_id": "parent-page-id-here",
    "properties": {
      "Name": {"title": {}},
      "Status": {"select": {"options": [{"name": "Todo"}, {"name": "In Progress"}, {"name": "Done"}]}},
      "Priority": {"number": {"format": "number"}},
      "Due Date": {"date": {}},
      "Notes": {"rich_text": {}}
    }
  }
)
```

**Returns**: Created database object containing `data_source_id` (needed for inserting pages into this database).

### 8. notion-update-data-source - Update Data Source

Update a data source's properties, name, description, or attributes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data_source_id` | string | ID of the data source |
| `properties` | object | Properties to update |

**Example prompts:**
- "Add a status field to track project completion"
- "Update the task database to include priority levels"

### 9. notion-query-data-sources - Query Data Sources

Query across multiple data sources with structured summaries, grouping, and filters.

> Requires Enterprise plan with Notion AI.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Natural language query |

**Example prompts:**
- "What's due for me this week across all tasks? Group by priority."
- "Show all risks from Engineering and Product databases this month"

### 10. notion-query-database-view - Query Database View

Query data from a database using a pre-defined view's filters and sorts.

> Requires Business plan or higher with Notion AI. Only available when notion-query-data-sources is not available.

| Parameter | Type | Description |
|-----------|------|-------------|
| `database_id` | string | Database ID |
| `view_id` | string | View ID to use |

**Example prompts:**
- "Query my 'In Progress' tasks view"
- "Get all items from the 'High Priority' view"

### 11. notion-create-comment - Create Comment

Add a comment to a page or specific content block.

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_id` | string | Page ID to comment on |
| `content` | string | Comment text |
| `block_id` | string | Specific block to comment on (optional) |
| `discussion_id` | string | Reply to existing discussion (optional) |

**Example prompts:**
- "Add a feedback comment to this design proposal"
- "Reply to the discussion about deadline concerns"

### 12. notion-get-comments - Get Comments

Lists all comments and discussions on a page.

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_id` | string | Page ID to get comments from |
| `include_resolved` | boolean | Include resolved threads (optional) |

**Example prompts:**
- "Get all discussions on this page, including resolved ones"
- "Show me the comments on the Requirements section"

### 13. notion-get-teams - Get Teams

Retrieves list of teams (teamspaces) in the workspace.

**Example prompts:**
- "Search for teams by name and membership status"
- "Get a team's ID for search filtering"

### 14. notion-get-users - Get Users

Lists all users in the workspace with details.

**Example prompts:**
- "Get contact details for the page creator"
- "Look up the person assigned to this task"

### 15. notion-get-user - Get User by ID

Retrieve user information by ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | User ID to look up |

### 16. notion-get-self - Get Bot Info

Retrieves information about the bot user and connected workspace.

**Example prompts:**
- "Which Notion workspace am I connected to?"
- "What's my file size upload limit?"

---

## Usage Examples

```python
# Search workspace
skill_mcp(
  mcp_name="notion",
  tool_name="notion-search",
  arguments={"query": "project roadmap Q3"}
)

# Fetch a page by URL
skill_mcp(
  mcp_name="notion",
  tool_name="notion-fetch",
  arguments={"url": "https://www.notion.so/your-page-url"}
)

# Get bot/workspace info
skill_mcp(
  mcp_name="notion",
  tool_name="notion-get-self",
  arguments={}
)

# Get all users
skill_mcp(
  mcp_name="notion",
  tool_name="notion-get-users",
  arguments={}
)

# Get comments on a page
skill_mcp(
  mcp_name="notion",
  tool_name="notion-get-comments",
  arguments={"page_id": "page-id-here"}
)
```

---

## Parameter Extraction Rules

| User Says | Action |
|-----------|--------|
| "搜索Notion", "在Notion里找" | Use notion-search |
| "打开这个页面", "看看这个链接" + URL | Use notion-fetch with URL |
| "创建页面", "新建文档" | Use notion-create-pages |
| "更新页面", "修改状态" | Use notion-update-page |
| "移动到", "归类到" | Use notion-move-pages |
| "复制页面", "克隆模板" | Use notion-duplicate-page |
| "创建数据库", "新建表格" | Use notion-create-database |
| "查询数据库", "筛选任务" | Use notion-query-database-view |
| "添加评论", "留言" | Use notion-create-comment |
| "查看评论", "看讨论" | Use notion-get-comments |
| "团队列表", "teamspace" | Use notion-get-teams |
| "用户列表", "成员信息" | Use notion-get-users |

---

## Integration Notes

- **Authentication**: Handled automatically by `mcp-remote` via Notion OAuth flow. On first use, a browser window will open for authorization.
- **Page IDs**: Can be extracted from Notion URLs (the 32-char hex string at the end).
- **Connected Tools Search**: Requires Notion AI plan for searching Slack, Google Drive, Jira via notion-search.
- **Enterprise Features**: `notion-query-data-sources` requires Enterprise plan with Notion AI.

---

## Known Pitfalls & Lessons Learned

### Pitfall 1: Database Property Schema Format

**Problem**: `notion-create-database` properties use `{type: {config}}` format, NOT `{"type": "typename"}`.

```json
// ❌ WRONG — causes API error
{"Notes": {"type": "rich_text"}}
{"Amount": {"type": "number"}}

// ✅ CORRECT
{"Notes": {"rich_text": {}}}
{"Amount": {"number": {"format": "number"}}}
```

**Root cause**: Notion API uses property-type-as-key convention. This differs from many other APIs that use `{"type": "..."}` pattern.

### Pitfall 2: Page Properties Use Flat Values (NOT Notion API Nested Format)

**Problem**: When creating pages via `notion-create-pages`, property values are flat (string, number, boolean) — NOT the nested Notion API property value objects.

```json
// ❌ WRONG — Notion API format (too verbose, will fail)
{
  "Status": {"select": {"name": "Active"}},
  "Priority": {"number": 5}
}

// ✅ CORRECT — Flat MCP format
{
  "Status": "Active",
  "Priority": 5
}
```

### Pitfall 3: Date Properties Use Special Key Naming

**Problem**: Date properties in `notion-create-pages` require a unique key syntax:

```json
// ❌ WRONG
{"Due Date": "2026-01-15T10:30:00"}
{"Due Date": {"start": "2026-01-15T10:30:00"}}

// ✅ CORRECT
{
  "date:Due Date:start": "2026-01-15T10:30:00",
  "date:Due Date:is_datetime": 1
}
```

**Key format**: `date:{PropertyName}:start` for value, `date:{PropertyName}:is_datetime` for time inclusion.

### Pitfall 4: Parent Uses `data_source_id`, NOT `database_id`

**Problem**: When adding pages to a database, use the `data_source_id` returned from `notion-create-database`, not a standard `database_id`.

```json
// ❌ WRONG
{"parent": {"database_id": "..."}}

// ✅ CORRECT
{"parent": {"data_source_id": "845722ac-f631-4b61-a202-452e916518cd"}}
```

### Pitfall 5: Percent Values Stored as Decimals

**Problem**: Number properties with `percent` format expect decimal values, not whole numbers.

```json
// ❌ WRONG — will show 422%
{"收益率": 4.22}

// ✅ CORRECT — will show 4.22%
{"收益率": 0.0422}
```

### Pitfall 6: Batch Size for `notion-create-pages`

**Recommendation**: Use 10-20 pages per batch call. While the API supports up to 100, large batches with complex content may time out or silently fail. Split into multiple calls for reliability.
