#!/usr/bin/env python3
"""Build a question-led editorial investigation storyboard from article HTML."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from video_explainer_storyboard import HtmlArticle, clean_text, section_summaries, short_script, template_match


VOX_STATE_MACHINE = [
    "cold_open",
    "central_question",
    "evidence_map",
    "historical_context",
    "mechanism_explainer",
    "field_or_human_evidence",
    "counterargument",
    "data_resolution",
    "qualified_conclusion",
]

VOX_SHOT_BLUEPRINTS: dict[str, list[tuple[str, str, str]]] = {
    "cold_open": [
        ("evidence_first", "topic_specific_real_footage", "fast_push_in"),
        ("contradiction", "torn_headline_and_marker_circle", "lateral_track"),
        ("question_reveal", "paper_question_strip", "settle_closeup"),
    ],
    "central_question": [
        ("reduce", "single_question_on_evidence_desk", "overhead_drop"),
        ("connect", "red_thread_to_candidate_causes", "slow_orbit"),
        ("lock", "question_stamp", "micro_push_in"),
    ],
    "evidence_map": [
        ("map_open", "shared_paper_world", "pull_back"),
        ("pillar_build", "evidence_objects_stagger", "tabletop_track"),
        ("relationship", "red_thread_and_arrows", "overhead_hold"),
    ],
    "historical_context": [
        ("archive_enter", "dated_documents_and_newsprint", "document_dolly"),
        ("timeline_move", "paper_timeline_or_physicalized_chart", "left_to_right_track"),
        ("source_hold", "source_label_and_exact_value", "reading_hold"),
    ],
    "mechanism_explainer": [
        ("parts", "mechanism_objects_separate", "wide_establish"),
        ("process", "objects_transform_and_pass_value", "follow_the_action"),
        ("result", "causal_path_locks", "result_closeup"),
    ],
    "field_or_human_evidence": [
        ("human_source", "interview_or_news_as_taped_screen", "source_push_in"),
        ("claim_bind", "quote_to_data_or_document", "match_move"),
        ("proof_hold", "readable_source_state", "reading_hold"),
    ],
    "counterargument": [
        ("claim", "first_explanation_board", "left_hold"),
        ("tear", "paper_rip_or_crosscut", "snap_reframe"),
        ("boundary", "counterevidence_board", "right_hold"),
    ],
    "data_resolution": [
        ("full_read", "complete_data_source", "overhead_hold"),
        ("physicalize", "bars_routes_or_regions_in_paper_world", "depth_track"),
        ("resolve", "one_annotated_data_conclusion", "endpoint_push_in"),
    ],
    "qualified_conclusion": [
        ("return", "all_evidence_objects_return", "slow_pull_back"),
        ("separate", "known_inferred_unknown_layers", "layer_separation"),
        ("final_line", "qualified_conclusion_strip", "clean_lock"),
    ],
}

VOX_SHOT_FRAMING: dict[str, list[tuple[str, float]]] = {
    "cold_open": [("EST_WIDE", 1.0), ("MEDIUM", 0.82), ("CLOSE", 0.66)],
    "central_question": [("MEDIUM", 0.82), ("CLOSE", 0.66), ("DETAIL", 0.50)],
    "evidence_map": [("EST_WIDE", 1.0), ("MEDIUM", 0.82), ("CLOSE", 0.66)],
    "historical_context": [("WIDE", 0.92), ("MEDIUM", 0.82), ("CLOSE", 0.66)],
    "mechanism_explainer": [("WIDE", 0.92), ("MEDIUM", 0.82), ("CLOSE", 0.66)],
    "field_or_human_evidence": [("MEDIUM", 0.82), ("CLOSE", 0.66), ("DETAIL", 0.50)],
    "counterargument": [("WIDE", 0.92), ("MEDIUM", 0.82), ("CLOSE", 0.66)],
    "data_resolution": [("EST_WIDE", 1.0), ("MEDIUM", 0.82), ("DETAIL", 0.50)],
    "qualified_conclusion": [("WIDE", 0.92), ("MEDIUM", 0.82), ("CLOSE", 0.66)],
}


def vox_micro_shots(scene_id: str, narrative_function: str) -> list[dict[str, Any]]:
    blueprints = VOX_SHOT_BLUEPRINTS[narrative_function]
    framings = VOX_SHOT_FRAMING[narrative_function]
    count = len(blueprints)
    return [
        {
            "id": f"{scene_id}_{index + 1:02d}",
            "phase": phase,
            "visual_mechanism": visual_mechanism,
            "camera_move": camera_move,
            "shot_size": framings[index][0],
            "focus": {"x": 0.5, "y": 0.5},
            "crop_scale": framings[index][1],
            "sound_cue": "paper slide, marker stroke or restrained mechanical click",
            "start_ratio": round(index / count, 3),
            "end_ratio": round((index + 1) / count, 3),
            "continuity_anchor": "shared_paper_evidence_world",
        }
        for index, (phase, visual_mechanism, camera_move) in enumerate(blueprints)
    ]


def central_question_for(title: str) -> str:
    title = clean_text(title).rstrip("。！？?!")
    if re.search(r"为什么|为何|如何|怎么|究竟|吗$", title):
        return f"{title}？"
    return f"{title}，真正决定结果的变量是什么？"


def section_text(section: dict[str, Any]) -> str:
    return clean_text("。".join(section.get("paragraphs") or []) or str(section.get("heading") or ""))


def find_section(sections: list[dict[str, Any]], pattern: str) -> dict[str, Any] | None:
    regex = re.compile(pattern, re.I)
    return next(
        (
            section
            for section in sections
            if regex.search(f"{section.get('heading', '')} {section_text(section)}")
        ),
        None,
    )


def build_vox_storyboard(
    article: HtmlArticle,
    *,
    source_html: str | None = None,
    duration_target_sec: int = 300,
    router: dict[str, Any] | None = None,
    aspect: str = "16:9",
    central_question: str | None = None,
) -> dict[str, Any]:
    router = router or {"part_router": {}}
    sections = section_summaries(article)
    question = clean_text(central_question or central_question_for(article.title))
    pillars = [
        {
            "id": f"pillar_{index:02d}",
            "title": str(section.get("heading") or f"证据 {index}"),
            "summary": short_script(section_text(section), 100),
            "source_locator": f"article_section:{section.get('heading')}",
        }
        for index, section in enumerate(sections[:6], 1)
    ]
    if not pillars:
        pillars = [{"id": "pillar_01", "title": "待核验事实", "summary": article.title, "source_locator": "article_title"}]

    history = find_section(sections, r"历史|过去|此前|周期|起点|背景") or sections[0]
    counter = find_section(sections, r"风险|反例|但是|不过|边界|争议|质疑|限制")
    mechanism_sections = [section for section in sections if section is not history and section is not counter][:3]
    if not mechanism_sections:
        mechanism_sections = sections[:2]
    field_section = find_section(sections, r"访谈|现场|公司|人物|产业|工厂|发布会|机构") or sections[min(1, len(sections) - 1)]
    final_section = sections[-1]

    scenes: list[dict[str, Any]] = []
    cursor = 0.0

    def add_scene(
        narrative_function: str,
        title: str,
        narration: str,
        duration: float,
        *,
        beat_class: str,
        content_part: str,
        fallback_template: str,
        visual_grammar: str,
        epistemic_status: str,
        evidence_refs: list[str] | None = None,
        variables: dict[str, Any] | None = None,
        evidence_gap: str = "",
    ) -> None:
        nonlocal cursor
        speech_sec = max(4.0, len(clean_text(narration)) / 5.0)
        scene_duration = max(duration, speech_sec)
        match = template_match(router, content_part, fallback_template)
        scene_id = f"scene_{len(scenes) + 1:03d}"
        scenes.append(
            {
                "id": scene_id,
                "type": narrative_function,
                "narrative_function": narrative_function,
                "title": title,
                "narration": narration,
                "start_sec": round(cursor, 3),
                "end_sec": round(cursor + scene_duration, 3),
                "duration_sec": round(scene_duration, 3),
                "beat_class": beat_class,
                "content_part": content_part,
                "template_id": match["template_id"],
                "template_match": match,
                "visual_grammar": visual_grammar,
                "visual_system": "vox_editorial_paper_collage",
                "world_id": "shared_paper_evidence_world",
                "epistemic_status": epistemic_status,
                "evidence_required": narrative_function not in {"central_question", "evidence_map"},
                "evidence_refs": evidence_refs or [],
                "evidence_gap": evidence_gap,
                "variables": variables or {},
                "asset_strategy": {
                    "priority": [
                        "direct_news_interview_or_archival_footage",
                        "source_document_or_verified_data",
                        "topic_specific_contextual_footage",
                        "generated_explanatory_visual",
                    ],
                    "generic_background_is_last_resort": True,
                    "human_anchor_policy": "pip_or_split_unless_the_original_statement_is_direct_evidence",
                },
                "motion": {
                    "entrance": "shared_element_or_clean_cut",
                    "focus_change": visual_grammar,
                    "exit": "overlap_protected_cut",
                },
                "micro_shots": vox_micro_shots(scene_id, narrative_function),
                "image2_scene_policy": {
                    "mode": "one_complete_scene_still_per_micro_shot",
                    "master_reference": "first_approved_scene_or_external_reference",
                    "crop_review_required": True,
                    "must_preserve_shared_world": True,
                },
                "image2_shot_packet": {
                    "mode": "image2_scene_to_video",
                    "style_reference_required": True,
                    "image_prompt_required": True,
                    "scene_still_required": True,
                    "crop_outputs_required": ["16:9", "1:1", "9:16"],
                    "motion_prompt_required": True,
                    "duration_sec": round(scene_duration / max(3, len(VOX_SHOT_BLUEPRINTS[narrative_function])), 3),
                    "sound_cue_required": True,
                    "exact_text_overlay": "remotion_only",
                    "evidence_role": "illustrative",
                },
                "html_animation_behavior": f"live_{visual_grammar}_with_source_annotations",
                "transition_to_next": "semantic_match_cut_without_blank_frame",
                "risk_notes": [
                    "Keep source labels, dates, axes, legends, faces, and original lower thirds readable.",
                    "Do not present contextual footage as direct proof.",
                ],
            }
        )
        cursor += scene_duration

    first_summary = short_script(section_text(sections[0]), 120)
    add_scene(
        "cold_open",
        article.title,
        first_summary,
        12.0,
        beat_class="hook",
        content_part="opening_hook",
        fallback_template="frame-light-leak-cinema",
        visual_grammar="real_video_title_question_data_composite",
        epistemic_status="context",
        evidence_refs=[pillars[0]["source_locator"]],
        variables={"question": question, "opening_layers": ["real_video", "title", "question_map", "data", "captions"]},
    )
    add_scene(
        "central_question",
        "真正的问题",
        question,
        8.0,
        beat_class="claim",
        content_part="logic_chain",
        fallback_template="frame-decision-tree",
        visual_grammar="central_question_map",
        epistemic_status="question",
        variables={"central_question": question},
    )
    add_scene(
        "evidence_map",
        "先看哪几组证据",
        "要回答这个问题，需要把这些证据放到同一张地图上。",
        10.0,
        beat_class="chapter",
        content_part="logic_chain",
        fallback_template="deck-blueprint",
        visual_grammar="evidence_pillar_board",
        epistemic_status="question",
        variables={"pillars": pillars},
    )
    add_scene(
        "historical_context",
        str(history.get("heading") or "历史背景"),
        short_script(section_text(history), 150),
        16.0,
        beat_class="evidence_document",
        content_part="news_or_document",
        fallback_template="article-magazine",
        visual_grammar="archive_timeline_with_document_collage",
        epistemic_status="fact",
        evidence_refs=[f"article_section:{history.get('heading')}"] ,
        variables={"timeline_required": True, "archive_footage_required": True},
    )
    mechanism_text = "。".join(section_text(section) for section in mechanism_sections)
    add_scene(
        "mechanism_explainer",
        "机制如何运转",
        short_script(mechanism_text, 180),
        22.0,
        beat_class="logic_chain",
        content_part="logic_chain",
        fallback_template="frame-decision-tree",
        visual_grammar="mechanism_nodes_paths_and_causal_labels",
        epistemic_status="inference",
        evidence_refs=[f"article_section:{section.get('heading')}" for section in mechanism_sections],
        variables={"mechanism_steps": [pillar["title"] for pillar in pillars[:4]]},
    )
    add_scene(
        "field_or_human_evidence",
        str(field_section.get("heading") or "现场证据"),
        short_script(section_text(field_section), 150),
        16.0,
        beat_class="evidence_document",
        content_part="news_or_document",
        fallback_template="deck-guizang-editorial",
        visual_grammar="direct_footage_pip_split_and_source_lower_third",
        epistemic_status="fact",
        evidence_refs=[f"article_section:{field_section.get('heading')}"] ,
        variables={"search_exact_entities_first": True, "preferred_assets": ["news", "interview", "speech", "on_site", "archival"]},
        evidence_gap="downloaded direct footage with provenance is required before render",
    )
    counter_text = short_script(section_text(counter), 150) if counter else "这个解释并非无条件成立，还要验证反例、时间边界和适用范围。"
    add_scene(
        "counterargument",
        str(counter.get("heading") if counter else "反证与边界"),
        counter_text,
        16.0,
        beat_class="objection",
        content_part="warning_or_risk",
        fallback_template="deck-safety-alert",
        visual_grammar="claim_vs_counterevidence_split",
        epistemic_status="counterargument",
        evidence_refs=[f"article_section:{counter.get('heading')}"] if counter else [],
        variables={"counterargument_required": True, "boundary_conditions_required": True},
        evidence_gap="counterevidence_or_boundary_source_required" if counter is None else "",
    )
    table = article.tables[0][:8] if article.tables else []
    add_scene(
        "data_resolution",
        "数据把答案推到哪里",
        "把口径、时间和数据放在一起，才能判断哪种解释更接近事实。",
        18.0,
        beat_class="evidence_data",
        content_part="financial_chart" if table else "data_table",
        fallback_template="frame-data-chart-nyt",
        visual_grammar="data_native_chart_then_full_reading_hold",
        epistemic_status="fact" if table else "unresolved",
        evidence_refs=["article_table:1"] if table else [],
        variables={"table": table, "chart_policy": "verified_data_only", "full_contain_before_detail": True},
        evidence_gap="verified dataset or source table required" if not table else "",
    )
    add_scene(
        "qualified_conclusion",
        "有限结论",
        f"更稳妥的结论是：{short_script(section_text(final_section), 150)}",
        14.0,
        beat_class="recap",
        content_part="closing_outro",
        fallback_template="frame-logo-outro",
        visual_grammar="evidence_map_resolve_with_known_unknown_labels",
        epistemic_status="qualified_conclusion",
        evidence_refs=[f"article_section:{final_section.get('heading')}"] ,
        variables={"separate": ["known", "inference", "unknown"], "avoid_absolute_claim": True},
    )

    if cursor > duration_target_sec:
        scale = duration_target_sec / cursor
        cursor = 0.0
        for scene in scenes:
            duration = max(5.0, float(scene["duration_sec"]) * scale)
            scene["start_sec"] = round(cursor, 3)
            scene["duration_sec"] = round(duration, 3)
            scene["end_sec"] = round(cursor + duration, 3)
            cursor += duration

    return {
        "schema_version": "dasheng.vox_storyboard.v1",
        "lane": "vox_explainer_video",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_html": source_html,
        "title": article.title,
        "aspect": aspect,
        "renderer": "html-video+remotion",
        "narrative_mode": "question_led_investigation",
        "central_question": question,
        "evidence_map": pillars,
        "director_state_machine": VOX_STATE_MACHINE,
        "research_contract": {
            "evidence_pillars_target": [3, 6],
            "counterargument_required": True,
            "separate_fact_opinion_inference_unknown": True,
            "direct_audiovisual_evidence_priority": True,
        },
        "visual_bible": {
            "schema_version": "dasheng.video.vox_visual_bible.v1",
            "system": "vox_editorial_paper_collage",
            "world": "one_continuous_tabletop_evidence_world",
            "materials": ["torn_newsprint", "cardboard_depth", "paper_cutouts", "ink_stamp", "red_thread", "masking_tape"],
            "palette": {
                "ink": "#181410",
                "paper": "#e7d8b8",
                "paper_light": "#f4ead4",
                "signal_red": "#cf3f32",
                "evidence_teal": "#1f756d",
                "gold": "#bd8c34",
            },
            "type_system": "condensed_sans_labels_plus_serif_editorial_headlines",
            "continuity_rules": [
                "Reuse the same paper world, palette, hero objects and red-thread logic across scenes.",
                "Move the camera through evidence instead of replacing the full canvas with isolated cards.",
                "Every 12-20 seconds introduce a new spatial mechanism, not merely a new background.",
                "Real evidence appears as taped screens, source documents or full-frame inserts inside the same world.",
            ],
            "generation_route": {
                "style_board_first": True,
                "style_reference_frame": "one_master_reference_per_visual_world",
                "prompt_packet": ["image_prompt", "motion_prompt", "duration_sec", "sound_cue"],
                "scene_keyframes": "start_and_end_pair",
                "motion_prompt": "camera_action_object_action_sound_cue",
                "generated_shots": "selective_hero_and_transition_only",
                "exact_text_overlay": "remotion_only",
                "default_compositor": "remotion",
            },
        },
        "duration_estimate_sec": round(max((scene["end_sec"] for scene in scenes), default=0.0), 3),
        "style": {
            "direction": "continuous_editorial_paper_world_horizontal",
            "use": ["paper_diorama", "physicalized_data", "archival_collage", "maps", "timelines", "documents", "interviews", "source_annotations", "camera_choreography"],
            "avoid": ["article_chapter_recitation", "generic_broll_as_proof", "static_screenshot_slideshow", "isolated_white_chart_cards", "absolute_conclusion", "effect_overuse"],
        },
        "scenes": scenes,
    }
