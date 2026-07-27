from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_square_video_standard_is_canonical_and_referenced() -> None:
    standard = (ROOT / "docs/technical/no-human-square-video-production-standard.md").read_text(encoding="utf-8")
    sop = (ROOT / "skills/dasheng-media-sop/SKILL.md").read_text(encoding="utf-8")
    bridge = (ROOT / "skills/dasheng-html-video-bridge/SKILL.md").read_text(encoding="utf-8")
    explainer = (ROOT / "skills/dasheng-video-explainer-html/SKILL.md").read_text(encoding="utf-8")

    assert "1080x1080" in standard
    assert "live HTML Video" in standard
    assert "Remotion" in standard
    assert "/v1/v1/" in standard
    assert "no-human-square-video-production-standard.md" in sop
    assert "no-human-square-video-production-standard.md" in bridge
    assert "no-human-square-video-production-standard.md" in explainer
