---
description: Critical execution rules for maintaining environment consistency and valid paths.
---
# Rule 00: Project Runtime Environment & Infrastructure

This rule is the **FOUNDATION** of this project. You must strictly adhere to these execution patterns to ensure stability across Windows and macOS/Linux.

## 1. Source of Truth: `.context/project_env.yaml`
Before running any command, you MUST check `.context/project_env.yaml` for:
- `conda_env`: The name of the Conda environment to use.
- `sdk_path_env_var`: The environment variable name for the SDK path (e.g., `MY_LLM_SDK_PATH`).

## 2. Mandatory Execution Pattern: `conda run`
**NEVER** assume an environment is active. **ALWAYS** explicitly bind the command to the environment.

- **❌ Forbidden:**
  ```bash
  python vibe.py              # Do NOT do this
  pip install -r requirements.txt # Do NOT do this
  pytest                      # Do NOT do this
  ```

- **✅ Required:**
  ```bash
  # Powershell/Bash compatible
  conda run -n <ENV_NAME> python vibe.py
  conda run -n <ENV_NAME> pip install -r requirements.txt
  conda run -n <ENV_NAME> pytest
  ```

> **Windows Powershell Tip**: If `conda run` causes quoting issues with complex arguments, use `conda run -n <ENV_NAME> --no-capture-output python script.py`.

## 3. Preflight Checks (Before Execution)
Before executing a new sequence of commands, verify your context:

1.  **Environment Check**:
    ```bash
    conda run -n <ENV_NAME> python -c "import sys; print(sys.executable)"
    ```
    *Ensure the output path contains the environment name.*

2.  **SDK Availability**:
    Verify that the environment variable specified in `sdk_path_env_var` (e.g., `MY_LLM_SDK_PATH`) is set in your current shell/system.
    *   If not set: You cannot run the code. Ask the user to set it.
    *   If set: Ensure it points to a valid directory.

## 4. Environment Management
- If the environment does not exist, ask the user for permission to create it using `environment.yml` or `requirements.txt`.
- Do not install packages into `base` or the system Python.

---
**Enforcement**: If you cannot verify strict environment isolation, **STOP** and ask the user for help.
