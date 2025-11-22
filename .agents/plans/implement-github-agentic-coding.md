# Module 8: GitHub Agentic Coding Implementation Plan

## Overview

Enable AI coding agents to be triggered directly from GitHub Issues and Pull Requests, allowing for remote, asynchronous code development using the PIV (Plan-Implement-Verify) loop.

## Implementation Status: Complete

### Files Created

```
.github/
├── workflows/
│   ├── issue-agent.yml      # Issue comment agent commands
│   ├── pr-review.yml        # Automated PR review
│   └── piv-loop.yml         # Full PIV cycle orchestration
└── ISSUE_TEMPLATE/
    └── agent-task.md        # Template for agent tasks
```

## Workflow Reference

### Issue Agent (`issue-agent.yml`)

**Trigger:** Issue comments containing `/agent`

**Commands:**
- `/agent plan` - Create implementation plan for issue
- `/agent implement` - Implement changes described in issue
- `/agent review` - Review related codebase
- `/agent help` - Show available commands

**Use Case:** Quick tasks, questions, or partial automation.

### PR Review (`pr-review.yml`)

**Trigger:**
- `pull_request` opened/synchronized - Auto-review
- PR comments with `/agent` - Respond to feedback

**Features:**
- Automatic code review on PR creation
- Responds to review comments with `/agent`
- Posts review as PR comment

**Review Criteria:**
1. Code correctness
2. Type safety (MyPy/Pyright compliance)
3. Performance implications
4. Security considerations
5. Test coverage

### PIV Loop (`piv-loop.yml`)

**Trigger:** Issue comments containing `/piv`

**Phases:**
- `/piv full` - Complete Plan → Implement → Verify cycle (default)
- `/piv plan` - Create implementation plan only
- `/piv implement` - Execute existing plan
- `/piv verify` - Run verification checks

**Process:**
1. Creates feature branch: `agent/issue-{number}`
2. **Plan:** Uses `/core_piv_loop:plan-feature` to create plan
3. **Implement:** Executes plan with `/core_piv_loop:execute`
4. **Verify:** Runs type checking, linting, tests
5. **PR:** Creates pull request linked to issue

## Setup Requirements

### 1. Repository Secrets

Configure in GitHub Settings → Secrets → Actions:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key for agent operations |

Note: `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### 2. Repository Permissions

Ensure Actions has permissions in Settings → Actions → General:

- **Workflow permissions:** Read and write permissions
- **Allow GitHub Actions to create and approve pull requests:** Enabled

### 3. Push to GitHub

```bash
# Initialize remote if needed
git remote add origin https://github.com/YOUR_USERNAME/obsidian-ai-agent.git

# Push workflows
git add .github/
git commit -m "feat: add Module 8 GitHub agentic coding workflows"
git push -u origin master
```

## Usage Examples

### Example 1: Full PIV Loop

1. Create issue using "Agent Task" template
2. Comment: `/piv full`
3. Agent creates plan, implements, verifies, and opens PR

### Example 2: Incremental Development

1. Create issue with feature description
2. Comment: `/piv plan` (review the plan)
3. Comment: `/piv implement` (after plan approval)
4. Comment: `/piv verify` (check implementation)

### Example 3: Quick Agent Help

On any issue:
```
/agent review - analyze this component
```

### Example 4: PR Feedback

On PR review comment:
```
/agent explain this logic
```

## Integration with Existing Commands

The workflows leverage your existing slash commands:

| Workflow Phase | Slash Command Used |
|----------------|-------------------|
| Plan | `/core_piv_loop:plan-feature` |
| Implement | `/core_piv_loop:execute` |
| Verify | `/validation:code-review` |

## Monitoring & Troubleshooting

### View Workflow Runs

GitHub → Actions tab → Select workflow

### Common Issues

**1. Workflow not triggering**
- Check issue comment contains exact command (`/piv`, `/agent`)
- Verify workflow file syntax (YAML validation)

**2. Permission denied**
- Enable "Read and write permissions" in repository settings
- Check `ANTHROPIC_API_KEY` secret is set

**3. Claude Code failures**
- Check Anthropic API key validity
- Review workflow logs for error details

**4. PR creation fails**
- Ensure branch doesn't already have PR
- Check `GITHUB_TOKEN` permissions

## Security Considerations

1. **API Keys:** Stored as encrypted secrets, never in code
2. **Permissions:** Scoped to minimum required
3. **Branch Protection:** Consider requiring reviews for `agent/*` branches
4. **Rate Limits:** Monitor GitHub Actions minutes and API usage

## Future Enhancements

- [ ] Slack/Discord notifications for workflow status
- [ ] Custom agent personas for different task types
- [ ] Parallel agent execution for large tasks
- [ ] Integration with Module 9 Remote Agentic Coding System
