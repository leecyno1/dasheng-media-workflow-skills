import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path('/Volumes/PSSD/Projects/公众号文章/scripts')))
ROOT = Path('/Volumes/PSSD/Projects/公众号文章')
TMP_ROOT = ROOT / '.tmp_test'

import phase2_rebuilder as mod


def project_tempdir():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TMP_ROOT)


class Phase2AIBriefTests(unittest.TestCase):
    def setUp(self):
        evidence_pool = [
            {
                "title": "油价上行后，美债和黄金同步波动",
                "url": "https://example.com/a",
                "source_type": "聚合新闻",
                "source_tier": "mainstream_media",
                "note": "市场开始重新交易通胀与利率预期。",
                "entities": ["油价", "美联储", "黄金"],
                "trendradar_signal": True,
                "signal_score": 8.4,
                "logic_chain_id": "oil-fed-chain",
            },
            {
                "title": "美联储官员讲话强调通胀粘性",
                "url": "https://example.com/b",
                "source_type": "聚合新闻",
                "source_tier": "official",
                "note": "政策口径偏谨慎，降息预期反复。",
                "entities": ["美联储", "通胀"],
                "trendradar_signal": False,
                "signal_score": 8.0,
                "logic_chain_id": "oil-fed-chain",
            },
            {
                "title": "特朗普关税表态后，市场再估输入型通胀风险",
                "url": "https://example.com/c",
                "source_type": "微博",
                "source_tier": "platform_hotspot",
                "note": "风险溢价与再通胀叙事重新纠缠。",
                "entities": ["特朗普", "关税", "通胀"],
                "trendradar_signal": True,
                "signal_score": 7.7,
                "logic_chain_id": "oil-fed-chain",
            },
        ]
        self.signal_bundle = {
            "requested_topic_count": 8,
            "manual_topics": [{"title": "再通胀不是事件，而是主线", "must_cover": True}],
            "trusted_evidence_pool": evidence_pool,
            "editorial_priority_pool": evidence_pool,
            "logic_chain_summaries": [
                {
                    "chain_id": "oil-fed-chain",
                    "summary_title": "油价 / 美联储",
                    "dominant_tokens": ["油价", "美联储", "通胀"],
                    "top_entities": ["特朗普"],
                    "top_titles": [item["title"] for item in evidence_pool],
                },
                {
                    "chain_id": "semi-chain",
                    "summary_title": "半导体 / 英伟达",
                    "dominant_tokens": ["半导体", "英伟达"],
                    "top_entities": ["英伟达"],
                    "top_titles": ["英伟达回暖不等于半导体全面复苏"],
                },
            ],
        }

    def sample_ai_cards(self):
        cards = []
        for index in range(8):
            cards.append(
                {
                    "topic_id": f"topic-{index}",
                    "topic_kind": "independent",
                    "title": f"再通胀不是事件，而是主线 {index}",
                    "one_line_judgment": "市场表面在交易事件，真正被重估的是通胀和利率预期。",
                    "core_proposition": f"第 {index} 题围绕再通胀和资产定价链条，证明市场主线并不是表面事件。",
                    "why_now": "油价、利率、黄金和政策口径同时出现再定价信号。",
                    "reader_payoff": "帮助读者识别哪些是情绪，哪些是真正影响股债商品的变量。",
                    "article_use": "判断稿",
                    "distinctiveness_reason": f"第 {index} 题从不同角度切入，但不重复上一题。",
                    "evidence_gap_summary": "还缺高频通胀与政策预期联动数据。",
                    "proof_requirements": ["拆开油价和利率预期", "验证政策口径变化"],
                    "recommended_data_angles": ["油价与通胀预期对照", "美债收益率变化"],
                    "recommended_visual_angles": ["交易屏", "美联储新闻截图"],
                    "priority_people": ["特朗普"],
                    "priority_orgs": ["美联储"],
                    "priority_news_queries": ["oil inflation fed latest news"],
                    "structure_hint": {
                        "opening": "先指出市场把事件当主线的误判。",
                        "part_1": "拆开油价与通胀预期。",
                        "part_2": "拆开政策口径与利率定价。",
                        "part_3": "落到股债商品如何分化。",
                        "ending": "给出下一步该盯的变量。",
                    },
                }
            )
        return {"topic_cards": cards}

    def test_build_brief_signal_bundle_keeps_real_evidence(self):
        records = [
            mod.IntakeRecord(
                title="油价上行后，美债和黄金同步波动",
                summary="市场开始重新交易通胀与利率预期。",
                source="reports",
                source_item_id="1",
                raw_payload={"url": "https://example.com/a"},
                meta={"run_id": "2026-04-05_170457"},
                source_quality_tier="mainstream_media",
                entities={"commodities": ["油价"], "orgs": ["美联储"]},
                noise_tags=[],
                dynamic_cluster_key="oil-fed",
                dynamic_tokens=["油价", "通胀", "利率"],
                editor_labels=["宏观"],
                trendradar_signal=True,
                freshness_score=0.9,
                heat_score=82.0,
                heat_level="A",
                source_freshness_weight=0.9,
                source_timeliness_weight=0.95,
                source_authority_weight=1.1,
            )
        ]
        aux = {
            "brief_input": {"top_entities": {"orgs": [{"name": "美联储", "count": 3}]}},
            "channel_top10": {"reports": [{"title": "油价上行后，美债和黄金同步波动", "url": "https://example.com/a", "heat_level": "A", "heat_score": 82}]},
            "event_clusters": [{"cluster_id": "oil-fed", "cluster_title_candidate": "油价 / 美联储", "cluster_summary": "样本 1 条", "count": 1, "source_mix": {"reports": 1}, "dominant_entities": ["油价", "美联储"], "dominant_actions": ["波动"], "representative_titles": ["油价上行后，美债和黄金同步波动"], "representative_links": ["https://example.com/a"], "authority_score": 1.1, "timeliness_score": 0.95, "trendradar_coverage": 1.0, "avg_heat_score": 82.0, "noise_ratio": 0.0}],
        }
        bundle = mod.build_brief_signal_bundle("2026-04-05_170457", records, aux, ["再通胀不是事件，而是主线"], 8)
        self.assertEqual(bundle["stats"]["trusted_evidence_count"], 1)
        self.assertEqual(bundle["trusted_evidence_pool"][0]["title"], "油价上行后，美债和黄金同步波动")
        self.assertEqual(bundle["manual_topics"][0]["title"], "再通胀不是事件，而是主线")
        self.assertIn("logic_chain_summaries", bundle)

    def test_normalize_ai_brief_cards_outputs_flat_independent_cards(self):
        cards = mod.normalize_ai_brief_cards(self.sample_ai_cards(), self.signal_bundle)
        self.assertEqual(len(cards), 8)
        self.assertEqual(cards[0]["topic_kind"], "independent")
        self.assertEqual(cards[0]["mother_topic_id"], cards[0]["topic_id"])
        self.assertEqual(cards[0]["existing_evidence"][0]["url"], "https://example.com/a")

    def test_normalize_ai_brief_cards_enriches_ai_returned_evidence_with_chain(self):
        ai_result = self.sample_ai_cards()
        ai_result["topic_cards"][0]["existing_evidence"] = [
            {
                "title": "特朗普关税表态后，市场再估输入型通胀风险",
                "url": "https://example.com/c",
            }
        ]
        cards = mod.normalize_ai_brief_cards(ai_result, self.signal_bundle)
        self.assertEqual(cards[0]["existing_evidence"][0]["logic_chain_id"], "oil-fed-chain")

    def test_infer_card_logic_chain_prefers_enriched_evidence_vote(self):
        card = {
            "title": "再通胀不是事件，而是主线",
            "core_proposition": "市场在重新定价通胀和利率预期。",
            "one_line_judgment": "真正被重估的是通胀主线。",
            "priority_people": ["特朗普"],
            "priority_orgs": ["美联储"],
            "existing_evidence": [
                {"title": "美联储官员讲话强调通胀粘性", "logic_chain_id": "oil-fed-chain"},
                {"title": "特朗普关税表态后，市场再估输入型通胀风险", "logic_chain_id": "oil-fed-chain"},
                {"title": "英伟达回暖不等于半导体全面复苏", "logic_chain_id": "semi-chain"},
            ],
        }
        chain_id = mod.infer_card_logic_chain_id(card, self.signal_bundle)
        self.assertEqual(chain_id, "oil-fed-chain")

    def test_build_editorial_priority_pool_filters_weak_lifestyle_items(self):
        records = [
            mod.IntakeRecord(
                title="油价上行后，美债和黄金同步波动",
                summary="市场开始重新交易通胀与利率预期。",
                source="reports",
                source_item_id="1",
                raw_payload={"url": "https://example.com/a"},
                meta={},
                source_quality_tier="mainstream_media",
                entities={"commodities": ["油价"], "orgs": ["美联储"]},
                noise_tags=[],
                dynamic_cluster_key="oil-fed",
                dynamic_tokens=["油价", "通胀", "利率"],
                editor_labels=["宏观"],
                trendradar_signal=True,
                freshness_score=0.9,
                heat_score=82.0,
                heat_level="A",
                source_freshness_weight=0.9,
                source_timeliness_weight=0.95,
                source_authority_weight=1.1,
            ),
            mod.IntakeRecord(
                title="一次成功的饼干🍪！！！",
                summary="今天的烘焙小确幸。",
                source="xhs",
                source_item_id="2",
                raw_payload={"url": "https://example.com/b"},
                meta={},
                source_quality_tier="platform_hotspot",
                entities={},
                noise_tags=[],
                dynamic_cluster_key="cookie",
                dynamic_tokens=["饼干", "烘焙"],
                editor_labels=["其他观察"],
                trendradar_signal=False,
                freshness_score=1.0,
                heat_score=70.0,
                heat_level="A",
                source_freshness_weight=1.0,
                source_timeliness_weight=1.0,
                source_authority_weight=0.95,
            ),
        ]
        logic_chains, logic_chain_map = mod.build_logic_chains(records)
        pool = mod.build_editorial_priority_pool(records, logic_chain_map, limit=10)
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0]["title"], "油价上行后，美债和黄金同步波动")

    def test_validate_logic_chain_balance_rejects_single_chain_majority(self):
        cards = mod.normalize_ai_brief_cards(self.sample_ai_cards(), self.signal_bundle)
        ok, reason = mod.validate_logic_chain_balance(cards, self.signal_bundle)
        self.assertFalse(ok)
        self.assertIn("题目过多", reason)

    def test_normalize_ai_brief_cards_rejects_insufficient_output(self):
        short_result = {"topic_cards": self.sample_ai_cards()["topic_cards"][:3]}
        with self.assertRaises(RuntimeError):
            mod.normalize_ai_brief_cards(short_result, self.signal_bundle)

    def test_write_failure_manifest_marks_ai_only_failed(self):
        with project_tempdir() as tmpdir:
            outdir = Path(tmpdir)
            manifest = mod.write_failure_manifest(outdir, "2026-04-05_170457", Path("/tmp/intake_records.json"), "Pass A 发散生成失败")
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["generation_mode"], "ai_only")
            self.assertEqual(payload["failure_reason"], "Pass A 发散生成失败")

    def test_write_selected_topics_files_keeps_compat_fields(self):
        cards = mod.normalize_ai_brief_cards(self.sample_ai_cards(), self.signal_bundle)
        with project_tempdir() as tmpdir:
            outdir = Path(tmpdir)
            template_file, selected_file = mod.write_selected_topics_files(outdir, "2026-04-05_170457", cards)
            template = json.loads(template_file.read_text(encoding="utf-8"))
            selected = json.loads(selected_file.read_text(encoding="utf-8"))
            self.assertEqual(template["candidate_topics"][0]["topic_kind"], "independent")
            self.assertEqual(template["candidate_topics"][0]["mother_topic_id"], template["candidate_topics"][0]["topic_id"])
            self.assertEqual(selected["status"], "pending_editor_review")


if __name__ == '__main__':
    unittest.main()
