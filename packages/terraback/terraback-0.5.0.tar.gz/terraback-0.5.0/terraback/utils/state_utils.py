from __future__ import annotations

import json
from pathlib import Path
from typing import List


def merge_states(main_state_path: Path, workspace_dirs: List[Path]) -> None:
    """Merge Terraform state files from workspaces into ``main_state_path``.

    The function reads ``terraform.tfstate`` from each workspace directory. If a
    state file exists under ``terraform.tfstate.d/<workspace>/terraform.tfstate``
    it is preferred. All resources from these states are appended to the main
    state which is then written back to ``main_state_path``.
    """
    if main_state_path.exists():
        try:
            main_state = json.loads(main_state_path.read_text())
        except Exception:
            main_state = {"version": 4, "resources": []}
    else:
        main_state = {"version": 4, "resources": []}

    for ws_dir in workspace_dirs:
        ws_state = ws_dir / "terraform.tfstate"
        alt_state = ws_dir / "terraform.tfstate.d" / ws_dir.name / "terraform.tfstate"
        if alt_state.exists():
            ws_state = alt_state
        if ws_state.exists():
            try:
                state = json.loads(ws_state.read_text())
            except Exception:
                state = {}
            main_state.setdefault("resources", [])
            main_state["resources"].extend(state.get("resources", []))

    main_state_path.write_text(json.dumps(main_state))
