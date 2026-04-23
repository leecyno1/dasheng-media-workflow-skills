import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


# 支持环境变量覆盖测试根目录
_ROOT_ENV = os.environ.get("DASHENG_ROOT")
if _ROOT_ENV:
    ROOT = Path(_ROOT_ENV)
else:
    # 使用脚本所在目录作为默认值
    ROOT = Path(__file__).parent.parent.resolve()
PYTHON = sys.executable


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class WorkflowDoctorTests(unittest.TestCase):
    def test_doctor_reports_missing_material_manifest_issue(self):
        run_id = "run-doctor-missing-material"
        intake_dir = ROOT / "产物/01_内容采集" / run_id
        brief_dir = ROOT / "产物/02_内容聚合及选题分析" / run_id
        draft_dir = ROOT / "产物/05_初稿生成" / run_id
        cleanup_targets = [intake_dir, brief_dir, draft_dir]
        try:
            write_json(intake_dir / "intake_manifest.json", {"run_id": run_id, "stage": "intake"})
            write_json(brief_dir / "brief_manifest.json", {"run_id": run_id, "stage": "brief"})
            write_json(
                brief_dir / "selected_topics.json",
                {"run_id": run_id, "status": "approved", "selected_topics": [{"topic_id": "t1"}]},
            )
            write_json(draft_dir / "draft_manifest.json", {"run_id": run_id, "stage": "draft"})
            write_json(
                draft_dir / "final_structure_snapshot.json",
                {"run_id": run_id, "status": "approved", "topics": [{"topic_id": "t1"}]},
            )

            proc = subprocess.run(
                [PYTHON, str(ROOT / "scripts/workflow_doctor.py"), "--run-id", run_id],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(any("material" in issue for issue in payload["issues"]))
        finally:
            for target in cleanup_targets:
                if target.exists():
                    shutil.rmtree(target)

    def test_doctor_can_inspect_nonexistent_run(self):
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/workflow_doctor.py"), "--run-id", "non-existent-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["run_id"], "non-existent-run")
        self.assertIn("canonical_contract", payload)


if __name__ == "__main__":
    unittest.main()
