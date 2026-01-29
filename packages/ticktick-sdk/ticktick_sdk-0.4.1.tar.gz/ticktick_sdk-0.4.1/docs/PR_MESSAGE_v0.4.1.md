# PR Title

```
feat: column filtering and tool filtering CLI flags (v0.4.1)
```

# PR Body

## Summary

- **Add `column_id` filter to `list_tasks`** - AI assistants can now list tasks within a specific kanban column, enabling proper kanban workflows (list columns → find tasks in column → move tasks)
- **Add `--enabledTools` and `--enabledModules` CLI flags** - Users can selectively enable tools to reduce context window usage from ~30-40% to ~5-10%, addressing a major pain point for Claude users

## Test plan

- [ ] Run `pytest tests/ -v` - all 352 tests should pass
- [ ] Test column filtering: `{"project_id": "...", "column_id": "..."}` in `list_tasks`
- [ ] Test `--enabledModules tasks,projects` - should load only 16 tools
- [ ] Test `--enabledTools ticktick_create_tasks,ticktick_list_tasks` - should load only 2 tools
- [ ] Test combined: `--enabledModules user --enabledTools ticktick_focus_heatmap` - should load 5 tools
- [ ] Verify `ticktick-sdk server --help` shows new flags with descriptions
- [ ] Test invalid module name warning: `--enabledModules invalid` should warn and continue
- [ ] Test invalid tool name warning: `--enabledTools invalid_tool` should warn and continue

🤖 Generated with [Claude Code](https://claude.com/claude-code)
