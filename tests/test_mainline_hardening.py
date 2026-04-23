import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path


# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from path_config import get_project_root

ROOT = get_project_root()
PYTHON = sys.executable
TMP_ROOT = ROOT / ".tmp_test"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_tempdir():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TMP_ROOT)


@contextmanager
def load_script_module(name: str, path: Path):
    scripts_dir = str(path.parent)
    inserted = False
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
        inserted = True
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[name] = module
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(name, None)
        if inserted:
            sys.path.remove(scripts_dir)


class MainlineHardeningTests(unittest.TestCase):
    def test_build_stage3_draft_emits_final_structure_gate(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            selected_topics = tmp / "selected_topics.json"
            topic_cards = tmp / "topic_cards.json"
            out_dir = tmp / "draft_out"
            fake_draft = tmp / "fake_draft.md"

            write_json(
                selected_topics,
                {
                    "run_id": "run-hardening-001",
                    "status": "approved",
                    "selected_topics": [
                        {
                            "topic_id": "topic1",
                            "title": "测试选题",
                            "selection_reason": "用于验证 gate",
                            "editor_note": "",
                        }
                    ],
                },
            )
            write_json(
                topic_cards,
                [
                    {
                        "topic_id": "topic1",
                        "title": "测试选题",
                        "core_thesis": "验证主链硬化是否会生成 final gate。",
                        "counterintuitive_angle": "不是先猜目录，而是先锁 gate。",
                        "audience": "编辑团队",
                        "proof_requirements": ["证明 gate 是否生成", "证明 draft_manifest 正常落盘", "证明下游可读取"],
                        "chart_needs": ["图表A", "图表B", "图表C"],
                        "existing_evidence": [
                            {"title": "证据1", "url": "https://example.com/1", "source_tier": "official"},
                            {"title": "证据2", "url": "https://example.com/2", "source_tier": "official"},
                        ],
                        "missing_evidence": ["需要编辑确认结构"],
                        "structure_hint": {
                            "opening": "解释为什么 gate 比模板更重要",
                            "part_1": "说明 canonical manifest 的意义",
                            "part_2": "说明 gate 的作用",
                            "part_3": "说明下游如何继承",
                            "ending": "回到结构化主链",
                        },
                        "meta": {"id": "topic-card:topic1"},
                    }
                ],
            )
            fake_draft.write_text("# 测试选题\n\n" + ("这是一段用于测试的中文正文。" * 450), encoding="utf-8")
            env = os.environ.copy()
            env["DASHENG_DRAFT_FAKE_RESPONSE_FILE"] = str(fake_draft)

            proc = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/build_stage3_draft.py"),
                    str(selected_topics),
                    str(topic_cards),
                    "--output-dir",
                    str(out_dir),
                ],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            gate_file = out_dir / "final_structure_snapshot.json"
            self.assertTrue(gate_file.exists())
            payload = json.loads(gate_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pending_editor_review")
            self.assertEqual(payload["gate"], "Final Structure Gate")

    def test_material_requires_final_structure_gate(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            draft_manifest = tmp / "draft_manifest.json"
            write_json(
                draft_manifest,
                {
                    "run_id": "run-hardening-002",
                    "stage": "draft",
                    "drafts": [{"topic_id": "topic1"}],
                },
            )
            proc = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/material_execute_pack.py"),
                    "--draft-manifest",
                    str(draft_manifest),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Final Structure Gate", proc.stderr or proc.stdout)

    def test_rewrite_requires_final_structure_gate(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            material_dir = tmp / "material"
            source_root = tmp / "rewrite_source"
            source_root.mkdir(parents=True, exist_ok=True)
            write_json(
                material_dir / "material_manifest.json",
                {
                    "run_id": "run-hardening-003",
                    "stage": "material",
                    "upstream": {},
                    "pack_root": str(tmp / "pack_assets"),
                },
            )
            write_json(
                material_dir / "material_acceptance.json",
                {
                    "run_id": "run-hardening-003",
                    "status": "approved",
                    "topics": [{"topic_id": "topic1"}],
                },
            )
            proc = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/rewrite_rerun_with_final_structure.py"),
                    "--material-manifest",
                    str(material_dir / "material_manifest.json"),
                    "--source-root",
                    str(source_root),
                    "--final-structure",
                    str(tmp / "missing_final_structure.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Final Structure Gate", proc.stderr or proc.stdout)

    def test_publish_requires_publish_decision_gate(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            rewrite_dir = tmp / "rewrite"
            material_dir = tmp / "material"
            rewrite_root = tmp / "rewrite_root"
            pack_root = tmp / "pack_assets"
            rewrite_root.mkdir(parents=True, exist_ok=True)
            pack_root.mkdir(parents=True, exist_ok=True)
            write_json(
                rewrite_dir / "rewrite_manifest.json",
                {
                    "run_id": "run-hardening-004",
                    "stage": "rewrite",
                    "output_root": str(rewrite_root),
                },
            )
            write_json(
                material_dir / "material_manifest.json",
                {
                    "run_id": "run-hardening-004",
                    "stage": "material",
                    "pack_root": str(pack_root),
                },
            )
            proc = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/publish_video_supplement.py"),
                    "--rewrite-manifest",
                    str(rewrite_dir / "rewrite_manifest.json"),
                    "--material-manifest",
                    str(material_dir / "material_manifest.json"),
                    "--publish-decision",
                    str(tmp / "missing_publish_decision.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Channel Gate", proc.stderr or proc.stdout)

    def test_legacy_entrypoints_redirect_to_dasheng_media_sop(self):
        proc = subprocess.run(
            ["node", str(ROOT / "skills/dasheng-daily-draft/index.js")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("dasheng-media-sop", proc.stderr or proc.stdout)

    def test_more_legacy_entrypoints_redirect_to_dasheng_media_sop(self):
        for target in [
            ROOT / "skills/dasheng-daily-clustering/index.js",
            ROOT / "skills/dasheng-daily-outline/index.js",
        ]:
            proc = subprocess.run(
                ["node", str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("dasheng-media-sop", proc.stderr or proc.stdout)

    def test_mainline_brief_requires_explicit_run_id_or_input(self):
        proc = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/run_mainline_stage.py"),
                "brief",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("不再允许猜最新目录", proc.stderr or proc.stdout)

    def test_material_parallel_launcher_material_manifest_is_canonical_entry(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            pack_root = tmp / "pack_assets"
            (pack_root / "topic-1" / "config").mkdir(parents=True, exist_ok=True)
            (pack_root / "topic-1" / "config" / "topic_config.json").write_text("{}", encoding="utf-8")

            draft_manifest = tmp / "draft" / "draft_manifest.json"
            material_manifest = tmp / "material" / "material_manifest.json"
            write_json(draft_manifest, {"run_id": "run-hardening-005", "stage": "draft", "drafts": [{"topic_id": "t1"}]})
            write_json(
                material_manifest,
                {
                    "run_id": "run-hardening-005",
                    "stage": "material",
                    "upstream": {"draft_manifest": str(draft_manifest)},
                    "pack_root": str(pack_root),
                    "runtime_material_manifest": str(tmp / "runtime" / "material_manifest.json"),
                },
            )

            with load_script_module("material_parallel_launcher_test", ROOT / "scripts/material_parallel_launcher.py") as module:
                pack_root_result, draft_manifest_result, metadata = module.resolve_execution_entry(
                    Namespace(
                        draft_manifest=None,
                        material_manifest=str(material_manifest),
                        run_id=None,
                        rebuild_material_plan=False,
                    )
                )

            self.assertEqual(pack_root_result, pack_root.resolve())
            self.assertEqual(draft_manifest_result, draft_manifest.resolve())
            self.assertEqual(metadata["material_manifest"], str(material_manifest.resolve()))
            self.assertEqual(metadata["draft_manifest"], str(draft_manifest.resolve()))

    def test_material_parallel_launcher_no_longer_accepts_pack_root_flag(self):
        proc = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/material_parallel_launcher.py"),
                "--pack-root",
                "/tmp/fake-pack-root",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--pack-root", proc.stderr or proc.stdout)

    def test_publish_supports_flat_rewrite_manifest_topics(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            rewrite_root = tmp / "rewrite_root"
            rewrite_root.mkdir(parents=True, exist_ok=True)
            hot_file = rewrite_root / "06_改写_示例_wechat_hot.md"
            normal_file = rewrite_root / "06_改写_示例_xiaohongshu_normal.md"
            hot_file.write_text("## 标题\n\n这是公众号热烈版。", encoding="utf-8")
            normal_file.write_text("## 标题\n\n这是小红书普通版。", encoding="utf-8")

            rewrite_manifest = {
                "run_id": "run-hardening-006",
                "stage": "rewrite",
                "output_root": str(rewrite_root),
                "topics": [
                    {
                        "topic_id": "topic-flat-1",
                        "title": "扁平改写测试",
                        "variants": [
                            {"variant": "wechat_luxun_hot", "file": str(hot_file)},
                            {"variant": "xhs_video_lemon_normal", "file": str(normal_file)},
                        ],
                    }
                ],
            }

            with load_script_module("publish_video_flat_test", ROOT / "scripts/publish_video_supplement.py") as module:
                topics = module.extract_rewrite_topic_sources(rewrite_manifest, rewrite_root)

            self.assertEqual(len(topics), 1)
            self.assertEqual(topics[0].topic_id, "topic-flat-1")
            self.assertEqual(topics[0].topic_name, "扁平改写测试")
            self.assertEqual(topics[0].rewrite_source.resolve(), normal_file.resolve())

    def test_publish_resolves_material_dir_from_manifest_topics(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            pack_root = tmp / "pack_assets"
            assets_dir = pack_root / "中文素材目录"
            assets_dir.mkdir(parents=True, exist_ok=True)

            material_manifest = {
                "run_id": "run-hardening-007",
                "stage": "material",
                "pack_root": str(pack_root),
                "topics": [
                    {
                        "topic_id": "topic-flat-2",
                        "title": "素材映射测试",
                        "assets_dir": str(assets_dir),
                    }
                ],
            }

            with load_script_module("publish_video_material_test", ROOT / "scripts/publish_video_supplement.py") as module:
                topic = module.RewriteTopicSource(
                    topic_id="topic-flat-2",
                    topic_name="素材映射测试",
                    topic_prefix="topic_flat_2",
                    rewrite_source=tmp / "dummy.md",
                )
                resolved = module.resolve_material_pack_topic_dir(material_manifest, topic, pack_root)

            self.assertEqual(resolved.resolve(), assets_dir.resolve())

    def test_publish_builds_channel_manifests_with_pending_execution_status(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            video_topic_dir = tmp / "video_supplement" / "topic_demo"
            (video_topic_dir / "videos" / "motion_narrative").mkdir(parents=True, exist_ok=True)
            (video_topic_dir / "videos" / "interactive_charts").mkdir(parents=True, exist_ok=True)
            (video_topic_dir / "videos" / "motion_narrative" / "demo.mp4").write_text("video", encoding="utf-8")
            topic_video_manifest = video_topic_dir / "topic_video_manifest.json"
            topic_video_manifest.write_text("{}", encoding="utf-8")

            rewrite_file = tmp / "wechat_hot.md"
            rewrite_file.write_text("## 标题\n\n正文", encoding="utf-8")
            xhs_file = tmp / "xhs_hot.md"
            xhs_file.write_text("## 标题\n\n视频正文", encoding="utf-8")

            rewrite_manifest = {
                "run_id": "run-hardening-008",
                "stage": "rewrite",
                "topics": [
                    {
                        "topic_id": "topic-demo",
                        "title": "发布阶段测试",
                        "variants": [
                            {"variant": "wechat_luxun_hot", "file": str(rewrite_file)},
                            {"variant": "xhs_video_luxun_hot", "file": str(xhs_file)},
                        ],
                    }
                ],
            }
            publish_decision = {
                "run_id": "run-hardening-008",
                "gate": "Channel Gate",
                "status": "ready",
                "topics": [
                    {
                        "topic_id": "topic-demo",
                        "topic_name": "发布阶段测试",
                        "channels": ["wechat_article", "xiaohongshu_video", "bilibili_video"],
                        "title_candidates": ["题目A", "题目B"],
                        "cover_candidates": ["cover-a.png"],
                        "publish_time": "2026-04-13T22:00:00+08:00",
                    }
                ],
            }
            topic_manifests = [
                {
                    "topic_id": "topic-demo",
                    "topic": "发布阶段测试",
                    "topic_prefix": "topic_demo",
                    "topic_video_manifest": str(topic_video_manifest),
                    "exports": {
                        "interactive_charts": {"ok": False},
                        "motion_narrative": {"ok": True},
                    },
                }
            ]

            with load_script_module("publish_stage_outputs_test", ROOT / "scripts/publish_video_supplement.py") as module:
                outputs = module.build_publish_stage_outputs(
                    run_id="run-hardening-008",
                    rewrite_manifest_path=tmp / "rewrite_manifest.json",
                    material_manifest_path=tmp / "material_manifest.json",
                    publish_decision_path=tmp / "publish_decision.json",
                    rewrite_manifest=rewrite_manifest,
                    publish_decision=publish_decision,
                    topic_manifests=topic_manifests,
                    video_supplement_manifest_path=tmp / "publish_video_supplement_manifest.json",
                    video_supplement_report_path=tmp / "publish_video_supplement_report.md",
                )

            adaptation = outputs["adaptation_manifest"]
            execution = outputs["execution_manifest"]
            verification = outputs["verification_report"]
            publish_manifest = outputs["publish_manifest"]

            self.assertEqual(adaptation["status"], "ready_for_execution")
            self.assertEqual(len(adaptation["topics"][0]["channel_packs"]), 3)
            self.assertEqual(execution["status"], "ready_for_channel_execution")
            self.assertEqual(
                [item["status"] for item in execution["executions"]],
                ["pending_user_confirmation", "pending_execution", "manual_only"],
            )
            self.assertEqual(verification["status"], "pending_execution")
            self.assertEqual(publish_manifest["status"], "pending_channel_execution")
            self.assertIsNone(publish_manifest["next_stage"])
            self.assertEqual(publish_manifest["channel_packs"][0]["channels"], ["wechat_article", "xiaohongshu_video", "bilibili_video"])
            self.assertIn("publish_skill_stack", publish_manifest)
            self.assertIn("wechat", publish_manifest["publish_skill_stack"])

    def test_publish_can_load_existing_topic_video_manifests(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            output_root = tmp / "video_supplement"
            topic_dir = output_root / "topic_demo"
            topic_dir.mkdir(parents=True, exist_ok=True)
            write_json(
                topic_dir / "topic_video_manifest.json",
                {
                    "topic_id": "topic-demo",
                    "topic": "测试题",
                    "exports": {},
                },
            )

            with load_script_module("publish_video_reuse_test", ROOT / "scripts/publish_video_supplement.py") as module:
                manifests = module.load_existing_topic_manifests(output_root)

            self.assertEqual(len(manifests), 1)
            self.assertEqual(manifests[0]["topic_id"], "topic-demo")
            self.assertEqual(manifests[0]["topic_video_manifest"], str(topic_dir / "topic_video_manifest.json"))

    def test_build_for_topic_sets_topic_video_manifest_path(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            rewrite_file = tmp / "rewrite.md"
            rewrite_file.write_text("## 一\n\n这是一段测试内容 123%。", encoding="utf-8")
            topic_dir = tmp / "pack"
            (topic_dir / "charts" / "csv").mkdir(parents=True, exist_ok=True)
            output_root = tmp / "out"

            with load_script_module("publish_build_topic_manifest_test", ROOT / "scripts/publish_video_supplement.py") as module:
                prototypes = module.load_prototypes()
                original_run_export = module.run_export
                module.run_export = lambda deck_path, out_dir: {"ok": True, "command": "stub", "stdout": "", "stderr": "", "returncode": 0, "timed_out": False}
                try:
                    result = module.build_for_topic(
                        module.RewriteTopicSource(
                            topic_id="topic-demo",
                            topic_name="测试题",
                            topic_prefix="topic_demo",
                            rewrite_source=rewrite_file,
                        ),
                        topic_dir,
                        topic_dir,
                        output_root,
                        prototypes,
                    )
                finally:
                    module.run_export = original_run_export

            self.assertTrue(result["topic_video_manifest"].endswith("topic_video_manifest.json"))
            self.assertTrue(Path(result["topic_video_manifest"]).exists())

    def test_publish_autofill_default_channel_matrix(self):
        with project_tempdir() as tmpdir:
            tmp = Path(tmpdir)
            assets_dir = tmp / "pack_assets" / "topic_demo"
            assets_dir.mkdir(parents=True, exist_ok=True)
            cover = assets_dir / "01_cover.jpg"
            cover.write_text("fake", encoding="utf-8")

            rewrite_manifest = {
                "run_id": "run-hardening-009",
                "topics": [
                    {
                        "topic_id": "topic-demo",
                        "title": "测试发布默认矩阵",
                        "variants": [
                            {"variant": "wechat_luxun_hot", "file": str(tmp / "wechat.md")},
                            {"variant": "xhs_video_luxun_hot", "file": str(tmp / "xhs.md")},
                        ],
                    }
                ],
            }
            material_manifest = {
                "run_id": "run-hardening-009",
                "topics": [
                    {
                        "topic_id": "topic-demo",
                        "assets_dir": str(assets_dir),
                        "assets": {
                            "images": [{"file": "01_cover.jpg"}],
                        },
                    }
                ],
            }
            publish_decision = {
                "run_id": "run-hardening-009",
                "gate": "Channel Gate",
                "status": "ready",
                "topics": [{"topic_id": "topic-demo"}],
            }

            with load_script_module("publish_autofill_test", ROOT / "scripts/publish_video_supplement.py") as module:
                filled, changed = module.autofill_publish_decision(
                    publish_decision=publish_decision,
                    rewrite_manifest=rewrite_manifest,
                    material_manifest=material_manifest,
                )

            self.assertTrue(changed)
            row = filled["topics"][0]
            self.assertEqual(
                row["channels"],
                ["wechat_article", "weibo_post", "x_post", "xiaohongshu_video", "douyin_video", "bilibili_video"],
            )
            self.assertEqual(row["title_candidates"], ["测试发布默认矩阵"])
            self.assertEqual(row["cover_candidates"], [str(cover)])
            self.assertEqual(row["editor_status"], "auto_filled_publish_defaults")

    def test_publish_autofill_extends_legacy_auto_default_channels(self):
        rewrite_manifest = {
            "run_id": "run-hardening-010",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "title": "测试旧默认路由升级",
                    "variants": [
                        {"variant": "wechat_luxun_hot", "file": "wechat.md"},
                        {"variant": "xhs_video_luxun_hot", "file": "xhs.md"},
                    ],
                }
            ],
        }
        material_manifest = {"run_id": "run-hardening-010", "topics": []}
        publish_decision = {
            "run_id": "run-hardening-010",
            "gate": "Channel Gate",
            "status": "ready",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "topic_name": "测试旧默认路由升级",
                    "channels": ["wechat_article", "weibo_post", "x_post"],
                    "editor_status": "auto_filled_default",
                }
            ],
        }

        with load_script_module("publish_autofill_extend_test", ROOT / "scripts/publish_video_supplement.py") as module:
            filled, changed = module.autofill_publish_decision(
                publish_decision=publish_decision,
                rewrite_manifest=rewrite_manifest,
                material_manifest=material_manifest,
            )

        self.assertTrue(changed)
        self.assertEqual(
            filled["topics"][0]["channels"],
            ["wechat_article", "weibo_post", "x_post", "xiaohongshu_video", "douyin_video", "bilibili_video"],
        )

    def test_publish_supports_optional_zhihu_channel_rule(self):
        with load_script_module("publish_zhihu_rule_test", ROOT / "scripts/publish_video_supplement.py") as module:
            self.assertEqual(module.normalize_channel_name("zhihu"), "zhihu_post")
            self.assertEqual(module.CHANNEL_EXECUTION_RULES["zhihu_post"]["executor_skill"], "zhihu-post")

    def test_publish_execution_manifest_contains_callable_executor_invocations(self):
        with load_script_module("publish_executor_invocation_test", ROOT / "scripts/publish_video_supplement.py") as module:
            execution_manifest = module.build_channel_execution_manifest(
                run_id="run-hardening-executors",
                adaptation_manifest={
                    "topics": [
                        {
                            "topic_id": "topic-demo",
                            "topic_name": "执行器调用测试",
                            "channel_packs": [
                                {
                                    "channel": "wechat_article",
                                    "variant": "wechat_luxun_hot",
                                    "variant_file": "/tmp/demo-wechat.md",
                                    "executor_skill": "baoyu-post-to-wechat",
                                    "automation_level": "semi_automated",
                                    "mode": "draft_or_browser_confirm",
                                    "requires_video": False,
                                    "assets_ready": True,
                                    "helper_skills": ["wechat-public-cli", "publish-guard"],
                                },
                                {
                                    "channel": "xiaohongshu_video",
                                    "variant": "xhs_video_luxun_hot",
                                    "variant_file": "/tmp/demo-xhs.md",
                                    "executor_skill": "xiaohongshu-auto",
                                    "automation_level": "automated",
                                    "mode": "auto_publish",
                                    "requires_video": True,
                                    "assets_ready": True,
                                    "available_videos": ["/tmp/demo.mp4"],
                                    "helper_skills": ["xiaohongshu-ops", "publish-guard"],
                                },
                                {
                                    "channel": "zhihu_post",
                                    "variant": "wechat_luxun_hot",
                                    "variant_file": "/tmp/demo-zhihu.md",
                                    "executor_skill": "zhihu-post",
                                    "automation_level": "semi_automated",
                                    "mode": "browser_confirm",
                                    "requires_video": False,
                                    "assets_ready": True,
                                    "helper_skills": ["publish-guard"],
                                },
                            ],
                        }
                    ]
                },
            )

        executions = {item["channel"]: item for item in execution_manifest["executions"]}
        self.assertEqual(
            executions["wechat_article"]["helper_invocations"][0]["command"],
            ["wechat-public-cli", "wechat:draft", "--file", "/tmp/demo-wechat.md"],
        )
        self.assertEqual(
            executions["xiaohongshu_video"]["executor_invocation"]["command"],
            ["openclaw", "skill", "xiaohongshu-auto", "publish", "--title", "执行器调用测试", "--content-file", "/tmp/demo-xhs.md", "--video", "/tmp/demo.mp4"],
        )
        self.assertEqual(executions["zhihu_post"]["executor_invocation"]["type"], "browser_procedure")

    def test_material_manifest_exposes_material_skill_stack(self):
        with load_script_module("material_skill_stack_test", ROOT / "scripts/material_execute_pack.py") as module:
            stack = module.MATERIAL_SKILL_STACK
        self.assertIn("evidence_search", stack)
        self.assertTrue(any(item["skill"] == "baoyu-image-gen" for item in stack["visual_generation"]))


if __name__ == "__main__":
    unittest.main()
