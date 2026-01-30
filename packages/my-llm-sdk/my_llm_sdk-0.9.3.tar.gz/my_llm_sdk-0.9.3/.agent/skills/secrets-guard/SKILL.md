---
name: secrets-guard
description: Scan staged Git changes for potential secrets (API keys, tokens, private keys) before commit. Use automatically before any git commit operation or when user asks to check for exposed credentials.
---

# Secrets Guard Skill

This skill helps prevent accidental commits of sensitive information by scanning staged Git changes for common secret patterns.

## When to Use This Skill

- User says "commit" or "git commit"
- User asks to "check for secrets" or "scan for API keys"
- User mentions "pre-commit hook" or "security check"
- Before any Git commit operation

## How It Works

### Step 1: Run the Scan Script

Execute the bundled `scan.py` script:

```bash
python .agent/skills/secrets-guard/scripts/scan.py
```

Options:
- `--staged` (default): Scan staged changes only
- `--all`: Scan all uncommitted changes
- `--stdin`: Read diff from stdin

### Step 2: Analyze JSON Results

The script outputs structured JSON:

```json
{
  "status": "findings",
  "total_findings": 2,
  "high_confidence": 1,
  "medium_confidence": 1,
  "low_confidence": 0,
  "findings": [
    {
      "pattern": "openai_api_key",
      "description": "OpenAI API key",
      "match": "sk-proj-abc123...",
      "file": "config.py",
      "line": 42,
      "confidence": "HIGH",
      "context": "API_KEY = \"sk-proj-...\"",
      "notes": []
    }
  ],
  "exit_code": 1
}
```

### Step 3: Apply Contextual Judgment

**CRITICAL**: Don't just report all findings. Analyze each one:

#### Safe Patterns (typically false positives)
- Test files (`test_*.py`, `*_test.go`, `tests/`)
- Obvious placeholders (`your-api-key-here`, `xxx...`, `example`)
- Environment variable references (`os.getenv("API_KEY")`)
- Documentation examples in comments

#### Risky Patterns (likely real secrets)
- High-entropy strings in production code
- Real-looking API key formats in config files
- Private keys in non-test files
- Credentials in `.env` files being committed

### Step 4: Report to User

Present findings grouped by confidence level:

**HIGH CONFIDENCE (block commit):**
```
⛔ [config.py:42] Found OpenAI API key: `sk-proj-...`
   Action: Move to environment variable or .env (gitignored)
```

**MEDIUM CONFIDENCE (warn):**
```
⚠️ [utils.py:15] High-entropy string - might be a secret
   Action: Verify if this is sensitive data
```

**LOW CONFIDENCE (informational):**
```
ℹ️ [tests/test_api.py:8] Found key-like pattern in test file
   Note: Likely a mock credential, safe to commit
```

## Decision Flow

```
if high_confidence > 0:
    BLOCK commit
    Suggest: Move secrets to env vars, use .env.example
elif medium_confidence > 0:
    WARN user
    Ask: "These look suspicious. Proceed anyway?"
else:
    ALLOW commit
    Note: "No secrets detected. Safe to commit."
```

## Error Handling

- If `git diff --staged` is empty: Inform user nothing is staged
- If script fails: Fall back to manual pattern check
- Always allow user to override with explicit confirmation ("commit anyway")

## Examples

### Example 1: Clean Commit
User: "Commit these changes"
```
Claude: [Runs scan.py, finds nothing]
"✅ No secrets detected in staged changes. Proceeding with commit..."
```

### Example 2: Detected Secret
User: "git commit -m 'Add API integration'"
```
Claude: [Runs scan.py, finds sk-proj-...]
"⛔ STOP: Found potential OpenAI API key in `config.py` line 42.

This looks like a real secret. Options:
1. Remove the file from staging: `git reset HEAD config.py`
2. Move the key to environment variable (I can help)
3. Proceed anyway (not recommended)

What would you like to do?"
```

### Example 3: False Positive in Test
User: "Commit my test changes"
```
Claude: [Runs scan.py, finds sk-test-... in tests/]
"ℹ️ Found key-like pattern in `tests/api_test.py` but it's:
   - In a test file
   - Contains 'test' in the value

This is likely a mock credential. Proceeding with commit..."
```

## Extending Patterns

Edit `patterns.json` to add new detection rules:

```json
{
  "patterns": {
    "my_custom_key": {
      "regex": "myapp_[a-z0-9]{32}",
      "severity": "HIGH",
      "description": "My App API key"
    }
  }
}
```
