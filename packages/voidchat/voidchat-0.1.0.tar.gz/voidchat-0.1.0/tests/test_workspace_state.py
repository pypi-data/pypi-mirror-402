import tempfile
import unittest
from pathlib import Path

from voidchat.workspace_state import (
    RunState,
    effective_workspace_label,
    load_run_state,
    render_where,
    resolve_workspace_path,
    save_run_state,
    workspace_paths,
)


class TestWorkspaceState(unittest.TestCase):
    def test_resolve_workspace_path_defaults_to_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            self.assertEqual(resolve_workspace_path(workspace=None, cwd=cwd), cwd.resolve())
            self.assertEqual(resolve_workspace_path(workspace="", cwd=cwd), cwd.resolve())

    def test_resolve_workspace_path_relative(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            target = resolve_workspace_path(workspace="subdir", cwd=cwd)
            self.assertEqual(target, (cwd / "subdir").resolve())

    def test_run_state_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            paths = workspace_paths(ws)
            state = RunState(
                workspace_label="demo",
                active_node_id="node-123",
                active_node_alias="#3",
                pending_gate=True,
                next_action="enter_task:#3",
                last_checkpoint="checkpoint",
            )
            save_run_state(paths.run_path, state)

            loaded = load_run_state(paths.run_path)
            self.assertEqual(loaded.schema_version, 1)
            self.assertEqual(loaded.workspace_label, "demo")
            self.assertEqual(loaded.active_node_id, "node-123")
            self.assertEqual(loaded.active_node_alias, "#3")
            self.assertTrue(loaded.pending_gate)
            self.assertEqual(loaded.next_action, "enter_task:#3")
            self.assertEqual(loaded.last_checkpoint, "checkpoint")

    def test_effective_workspace_label_fallbacks_to_basename(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            self.assertEqual(effective_workspace_label(workspace=ws, state=RunState()), ws.resolve().name)
            self.assertEqual(effective_workspace_label(workspace=ws, state=RunState(workspace_label="x")), "x")

    def test_render_where_contains_key_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            paths = workspace_paths(ws)
            text = render_where(
                workspace=ws,
                state=RunState(workspace_label="demo"),
                run_path=paths.run_path,
                allow_write=False,
                allow_scripts=True,
                allow_shell=False,
            )
            self.assertIn("workspace:", text)
            self.assertIn("workspace_label: demo", text)
            self.assertIn("run_state:", text)
            self.assertIn("pending_gate:", text)
            self.assertIn("permissions:", text)


if __name__ == "__main__":
    unittest.main()

