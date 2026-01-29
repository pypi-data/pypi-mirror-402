import tempfile
import unittest
from pathlib import Path

from voidchat.context_tree import (
    create_node,
    load_tree,
    new_tree,
    render_ls,
    resolve_ref,
    save_tree,
    set_status,
)


class TestContextTree(unittest.TestCase):
    def test_new_tree_has_root(self) -> None:
        tree = new_tree(root_title="ws")
        self.assertIn("root", tree.nodes)
        self.assertEqual(tree.nodes["root"].alias, "#0")
        self.assertEqual(tree.nodes["root"].type, "root")

    def test_create_plan_and_task_alias_stable(self) -> None:
        tree = new_tree(root_title="ws")
        plan = create_node(tree, node_type="plan", title="P1", parent_id="root")
        task = create_node(tree, node_type="task", title="T1", parent_id=plan.id)
        self.assertEqual(plan.alias, "#1")
        self.assertEqual(task.alias, "#2")

        set_status(tree, task.id, "closed")
        set_status(tree, task.id, "open")
        # alias must not change
        self.assertEqual(tree.nodes[task.id].alias, "#2")

    def test_resolve_ref(self) -> None:
        tree = new_tree(root_title="ws")
        plan = create_node(tree, node_type="plan", title="P1", parent_id="root")
        self.assertEqual(resolve_ref(tree, plan.id), plan.id)
        self.assertEqual(resolve_ref(tree, plan.alias), plan.id)
        self.assertEqual(resolve_ref(tree, "1"), plan.id)

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "context-tree.json"
            tree = new_tree(root_title="ws")
            plan = create_node(tree, node_type="plan", title="P1", parent_id="root")
            _ = create_node(tree, node_type="task", title="T1", parent_id=plan.id)
            save_tree(path, tree)

            loaded = load_tree(path, root_title="ws")
            self.assertIn(plan.id, loaded.nodes)
            self.assertEqual(loaded.nodes[plan.id].alias, plan.alias)

    def test_render_ls(self) -> None:
        tree = new_tree(root_title="ws")
        plan = create_node(tree, node_type="plan", title="P1", parent_id="root")
        _ = create_node(tree, node_type="task", title="T1", parent_id=plan.id)
        text = render_ls(tree)
        self.assertIn("open nodes:", text)
        self.assertIn("#1 [plan] P1", text)
        self.assertIn("#2 [task] T1", text)


if __name__ == "__main__":
    unittest.main()

