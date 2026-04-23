import unittest
from pathlib import Path


ROOT = Path("/Volumes/PSSD/Projects/公众号文章")


class DocsConsistencyTests(unittest.TestCase):
    def test_stage_interfaces_doc_exists_and_is_referenced(self):
        doc = ROOT / "docs" / "STAGE_INTERFACES.md"
        self.assertTrue(doc.exists())

        for target in [
            ROOT / "README.md",
            ROOT / "docs" / "INSTALLATION.md",
            ROOT / "skills" / "dasheng-media-sop" / "SKILL.md",
        ]:
            content = target.read_text(encoding="utf-8")
            self.assertIn("docs/STAGE_INTERFACES.md", content)

    def test_root_install_files_exist(self):
        for target in [
            ROOT / ".gitignore",
            ROOT / "requirements.txt",
            ROOT / "ENV_TEMPLATE.env",
            ROOT / "install_to_openclaw.sh",
            ROOT / "install_to_hermes.sh",
        ]:
            self.assertTrue(target.exists(), msg=str(target))


if __name__ == "__main__":
    unittest.main()
