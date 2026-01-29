# v0.4.1 Release Notes

## Overview

This release addresses two high-impact user requests: kanban column filtering and selective tool loading to reduce context window usage.

---

## New Features

### Column Filtering for `list_tasks`

**Problem:** AI assistants couldn't list tasks within a specific kanban column, making kanban workflows cumbersome.

**Solution:** Added `column_id` filter to `ticktick_list_tasks`.

**Usage:**
```json
{
  "project_id": "abc123",
  "column_id": "def456"
}
```

**Workflow enabled:**
1. `ticktick_list_columns` → Get column IDs for a project
2. `ticktick_list_tasks` with `column_id` → See tasks in "To Do", "In Progress", etc.
3. `ticktick_update_tasks` with `column_id` → Move tasks between columns

---

### Tool Filtering CLI Flags

**Problem:** The MCP server loads all 43 tools at startup, consuming ~30-40% of available context window before any messages are sent.

**Solution:** Added `--enabledTools` and `--enabledModules` CLI flags to selectively enable tools.

#### `--enabledModules` - Category-based filtering

Enable entire categories of tools:

```bash
# Enable only task and project tools (16 tools instead of 43)
ticktick-sdk server --enabledModules tasks,projects

# Minimal setup for basic task management
ticktick-sdk server --enabledModules tasks
```

**Available modules:**

| Module | Description | Tool Count |
|--------|-------------|------------|
| `tasks` | Task CRUD, completion, movement, subtasks, pinning, search | 11 |
| `projects` | Project CRUD and listing | 5 |
| `folders` | Folder CRUD | 4 |
| `columns` | Kanban column CRUD | 4 |
| `tags` | Tag CRUD and merging | 5 |
| `habits` | Habit CRUD, check-ins, sections | 8 |
| `user` | Profile, status, statistics, preferences | 4 |
| `focus` | Focus/pomodoro heatmap and distribution | 2 |

#### `--enabledTools` - Individual tool selection

Enable specific tools by name:

```bash
# Enable only specific tools
ticktick-sdk server --enabledTools ticktick_create_tasks,ticktick_list_tasks,ticktick_complete_tasks
```

#### Combined usage

Both flags can be used together - tools are merged:

```bash
# Enable user module + focus heatmap tool (5 tools total)
ticktick-sdk server --enabledModules user --enabledTools ticktick_focus_heatmap
```

#### Context savings

| Configuration | Tools Loaded | Approximate Context Usage |
|---------------|--------------|---------------------------|
| Default (no flags) | 43 | ~30-40% |
| `--enabledModules tasks,projects` | 16 | ~12-15% |
| `--enabledModules tasks` | 11 | ~8-10% |
| `--enabledTools` (3 tools) | 3 | ~3-5% |

---

## Tool Reference

### Tasks Module (11 tools)
- `ticktick_create_tasks`
- `ticktick_get_task`
- `ticktick_list_tasks`
- `ticktick_update_tasks`
- `ticktick_complete_tasks`
- `ticktick_delete_tasks`
- `ticktick_move_tasks`
- `ticktick_set_task_parents`
- `ticktick_unparent_tasks`
- `ticktick_search_tasks`
- `ticktick_pin_tasks`

### Projects Module (5 tools)
- `ticktick_list_projects`
- `ticktick_get_project`
- `ticktick_create_project`
- `ticktick_update_project`
- `ticktick_delete_project`

### Folders Module (4 tools)
- `ticktick_list_folders`
- `ticktick_create_folder`
- `ticktick_rename_folder`
- `ticktick_delete_folder`

### Columns Module (4 tools)
- `ticktick_list_columns`
- `ticktick_create_column`
- `ticktick_update_column`
- `ticktick_delete_column`

### Tags Module (5 tools)
- `ticktick_list_tags`
- `ticktick_create_tag`
- `ticktick_update_tag`
- `ticktick_delete_tag`
- `ticktick_merge_tags`

### Habits Module (8 tools)
- `ticktick_habits`
- `ticktick_habit`
- `ticktick_habit_sections`
- `ticktick_create_habit`
- `ticktick_update_habit`
- `ticktick_delete_habit`
- `ticktick_checkin_habits`
- `ticktick_habit_checkins`

### User Module (4 tools)
- `ticktick_get_profile`
- `ticktick_get_status`
- `ticktick_get_statistics`
- `ticktick_get_preferences`

### Focus Module (2 tools)
- `ticktick_focus_heatmap`
- `ticktick_focus_by_tag`

---

## Error Handling

Invalid module or tool names produce warnings but don't fail:

```
$ ticktick-sdk server --enabledModules tasks,invalid
Warning: Unknown module 'invalid'. Available: tasks, projects, folders, columns, tags, habits, user, focus
Tool filtering enabled: 11 of 43 tools
```

```
$ ticktick-sdk server --enabledTools ticktick_create_tasks,invalid_tool
Warning: Unknown tool 'invalid_tool', skipping
Tool filtering enabled: 1 of 43 tools
```

---

## Upgrade Notes

1. Update your package: `pip install --upgrade ticktick-sdk`
2. Optionally add `--enabledModules` or `--enabledTools` to your MCP configuration to reduce context usage
3. Use `column_id` filter in `list_tasks` for kanban workflows

---

## Files Changed

- `src/ticktick_sdk/tools/inputs.py` - Added `column_id` field to `TaskListInput`
- `src/ticktick_sdk/server.py` - Added column filtering logic and `_apply_tool_filtering()`
- `src/ticktick_sdk/cli.py` - Added `TOOL_MODULES`, `--enabledTools`, `--enabledModules` flags

---

**Full Changelog**: v0.4.0...v0.4.1
