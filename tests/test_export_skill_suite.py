import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.export_skill_suite import export_suite


# 支持环境变量覆盖测试根目录
_ROOT_ENV = os.environ.get("DASHENG_ROOT")
if _ROOT_ENV:
    ROOT = Path(_ROOT_ENV)
else:
    # 使用脚本所在目录作为默认值
    ROOT = Path(__file__).parent.parent.resolve()


class ExportSkillSuiteTests(unittest.TestCase):
    def test_export_bundle_contains_formal_runtime_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp_test") as tmpdir:
            export_root = Path(tmpdir) / "bundle"
            export_suite(export_root)

            self.assertTrue((export_root / "skills" / "dasheng-media-sop" / "SKILL.md").exists())
            self.assertTrue((export_root / "skills" / "dasheng-stage-publish" / "SKILL.md").exists())
            self.assertTrue((export_root / "scripts" / "run_mainline_stage.py").exists())
            self.assertTrue((export_root / "tests" / "test_mainline_hardening.py").exists())
            self.assertTrue((export_root / "README.md").exists())
            self.assertTrue((export_root / "ENV_TEMPLATE.env").exists())
            self.assertTrue((export_root / "install_to_openclaw.sh").exists())
            self.assertTrue((export_root / "docs" / "STAGE_INTERFACES.md").exists())

    def test_export_bundle_filters_cache_and_backup_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp_test") as tmpdir:
            export_root = Path(tmpdir) / "bundle"
            export_suite(export_root)

            self.assertFalse(any(export_root.rglob("__pycache__")))
            self.assertFalse(any(export_root.rglob("*.pyc")))
            self.assertFalse(any(".backup." in path.name for path in export_root.rglob("*")))
            self.assertFalse(any(path.name == ".git" for path in export_root.rglob(".git")))

    def test_export_manifest_records_legacy_redirects_and_installation(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp_test") as tmpdir:
            export_root = Path(tmpdir) / "bundle"
            export_suite(export_root)

            manifest = json.loads((export_root / "EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertIn("dasheng-media-sop", manifest["formal_skills"])
            self.assertIn("dasheng-daily-draft", manifest["legacy_redirect_skills"])
            self.assertEqual(manifest["installation"]["openclaw"]["script"], "install_to_openclaw.sh")
            self.assertIn("scripts", manifest["bundled_directories"])


if __name__ == "__main__":
    unittest.main()
