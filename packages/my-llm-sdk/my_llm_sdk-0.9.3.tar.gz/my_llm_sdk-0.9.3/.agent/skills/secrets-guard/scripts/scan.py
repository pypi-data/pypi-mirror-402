#!/usr/bin/env python3
"""
Secrets detection script for Git staged changes.
Output format: JSON for easy parsing by Claude.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def load_patterns() -> dict:
    """Load patterns from patterns.json."""
    script_dir = Path(__file__).parent.parent
    patterns_file = script_dir / "patterns.json"
    
    if patterns_file.exists():
        with open(patterns_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback to hardcoded patterns if file not found
    return {
        "patterns": {
            "openai_api_key": {"regex": r"sk-[a-zA-Z0-9]{20,}", "severity": "HIGH"},
            "aws_access_key": {"regex": r"AKIA[0-9A-Z]{16}", "severity": "HIGH"},
            "private_key_header": {"regex": r"-----BEGIN.*PRIVATE KEY-----", "severity": "HIGH"},
        },
        "ignore_patterns": {"test_files": [], "placeholder_values": []},
    }


def get_git_diff(staged_only: bool = True) -> tuple[str, list[str]]:
    """Get git diff content and list of changed files."""
    diff_cmd = ["git", "--no-pager", "diff", "--staged"] if staged_only else ["git", "--no-pager", "diff", "HEAD"]
    files_cmd = ["git", "--no-pager", "diff", "--name-only", "--staged"] if staged_only else ["git", "--no-pager", "diff", "--name-only", "HEAD"]
    
    diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
    files_result = subprocess.run(files_cmd, capture_output=True, text=True)
    
    if diff_result.returncode != 0:
        return "", []
    
    files = [f.strip() for f in files_result.stdout.strip().split("\n") if f.strip()]
    return diff_result.stdout, files


def parse_diff_hunks(diff_content: str) -> list[dict]:
    """Parse diff into hunks with file and line information."""
    hunks = []
    current_file = None
    current_line = 0
    
    for line in diff_content.split("\n"):
        # Match file header: +++ b/path/to/file
        if line.startswith("+++ b/"):
            current_file = line[6:]
        # Match hunk header: @@ -old,count +new,count @@
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match:
                current_line = int(match.group(1))
        # Match added lines (potential secrets)
        elif line.startswith("+") and not line.startswith("+++"):
            hunks.append({
                "file": current_file,
                "line": current_line,
                "content": line[1:],  # Remove leading +
            })
            current_line += 1
        elif not line.startswith("-"):
            current_line += 1
    
    return hunks


def is_placeholder(value: str, ignore_placeholders: list[str]) -> bool:
    """Check if a matched value is a placeholder/mock."""
    value_lower = value.lower()
    for placeholder in ignore_placeholders:
        if placeholder.lower() in value_lower:
            return True
    return False


def is_test_file(filepath: str, test_patterns: list[str]) -> bool:
    """Check if a file is a test file."""
    import fnmatch
    for pattern in test_patterns:
        if fnmatch.fnmatch(filepath, pattern):
            return True
    # Also check common test indicators
    return any(indicator in filepath.lower() for indicator in ["test", "spec", "mock", "fixture"])


def scan_content(hunks: list[dict], config: dict) -> list[dict]:
    """Scan diff hunks for secrets."""
    findings = []
    patterns = config.get("patterns", {})
    ignore_config = config.get("ignore_patterns", {})
    placeholder_values = ignore_config.get("placeholder_values", [])
    test_file_patterns = ignore_config.get("test_files", [])
    
    for hunk in hunks:
        content = hunk["content"]
        filepath = hunk["file"] or ""
        
        for pattern_name, pattern_info in patterns.items():
            regex = pattern_info.get("regex", "")
            severity = pattern_info.get("severity", "MEDIUM")
            description = pattern_info.get("description", pattern_name)
            
            for match in re.finditer(regex, content):
                matched_value = match.group(0)
                
                # Calculate confidence based on context
                confidence = severity
                notes = []
                
                # Lower confidence for test files
                if is_test_file(filepath, test_file_patterns):
                    confidence = "LOW"
                    notes.append("Found in test file")
                
                # Lower confidence for placeholders
                if is_placeholder(matched_value, placeholder_values):
                    confidence = "LOW"
                    notes.append("Looks like a placeholder")
                
                # Lower confidence for environment variable references
                if re.search(r"(os\.getenv|os\.environ|process\.env|\$\{?\w+\}?)", content):
                    confidence = "LOW"
                    notes.append("Appears to be env var reference")
                
                findings.append({
                    "pattern": pattern_name,
                    "description": description,
                    "match": matched_value[:20] + "..." if len(matched_value) > 20 else matched_value,
                    "file": filepath,
                    "line": hunk["line"],
                    "confidence": confidence,
                    "context": content[:100] + "..." if len(content) > 100 else content,
                    "notes": notes,
                })
    
    return findings


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan for secrets in git changes")
    parser.add_argument("--staged", action="store_true", default=True, help="Scan staged changes only (default)")
    parser.add_argument("--all", action="store_true", help="Scan all uncommitted changes")
    parser.add_argument("--stdin", action="store_true", help="Read diff from stdin")
    args = parser.parse_args()
    
    config = load_patterns()
    
    if args.stdin:
        diff_content = sys.stdin.read()
        files = []
    else:
        diff_content, files = get_git_diff(staged_only=not args.all)
    
    if not diff_content.strip():
        print(json.dumps({
            "status": "clean",
            "message": "No changes to scan",
            "total_findings": 0,
            "findings": [],
            "exit_code": 0,
        }, indent=2))
        sys.exit(0)
    
    hunks = parse_diff_hunks(diff_content)
    findings = scan_content(hunks, config)
    
    # Separate by confidence
    high_confidence = [f for f in findings if f["confidence"] == "HIGH"]
    medium_confidence = [f for f in findings if f["confidence"] == "MEDIUM"]
    low_confidence = [f for f in findings if f["confidence"] == "LOW"]
    
    result = {
        "status": "findings" if findings else "clean",
        "total_findings": len(findings),
        "high_confidence": len(high_confidence),
        "medium_confidence": len(medium_confidence),
        "low_confidence": len(low_confidence),
        "findings": findings,
        "files_scanned": files,
        "exit_code": 1 if high_confidence else 0,
    }
    
    print(json.dumps(result, indent=2))
    sys.exit(1 if high_confidence else 0)


if __name__ == "__main__":
    main()
