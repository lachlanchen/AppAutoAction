import io
import json
from pathlib import Path
import tempfile
from contextlib import redirect_stdout
import unittest

from agenticapp.cli import main
from agenticapp.scene_spec import built_in_scene_template, create_render_plan, load_scene_spec


ROOT = Path(__file__).resolve().parents[1]


class SceneSpecTests(unittest.TestCase):
    def test_builtin_experiment_template_is_valid(self):
        template = built_in_scene_template("experiment-setup")

        self.assertEqual(template["slug"], "paper-experiment-setup")
        self.assertGreater(len(template["elements"]), 5)

    def test_example_scene_plan(self):
        spec_path = ROOT / "examples" / "paper-optics-setup.scene.json"
        spec = load_scene_spec(spec_path)
        plan = create_render_plan(spec_path, ROOT / "output" / "test-scenes")

        self.assertEqual(spec["title"], "Paper-ready optical experiment setup")
        self.assertEqual(plan.slug, "paper-optics-setup")
        self.assertEqual(plan.png_path.name, "paper-optics-setup.png")

    def test_scene_template_command_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scene.json"
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = main(["scene-template", "experiment-setup", "--output", str(output)])

            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("scene.json", stdout.getvalue())
        self.assertEqual(data["slug"], "paper-experiment-setup")

    def test_render_scene_dry_run(self):
        spec_path = ROOT / "examples" / "paper-optics-setup.scene.json"
        stdout = io.StringIO()
        output_dir = ROOT / "output" / "test-scenes"

        with redirect_stdout(stdout):
            code = main(["render-scene", str(spec_path), "--output-dir", str(output_dir), "--dry-run"])

        result = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["plan"]["png"], str((output_dir / "paper-optics-setup.png").resolve()))


if __name__ == "__main__":
    unittest.main()
