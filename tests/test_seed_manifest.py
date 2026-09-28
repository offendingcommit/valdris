import copy
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.valdris_seed import ValidationError, build_manifest, validate_manifest


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args]).decode().strip()


class SeedManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.vault = Path(self.tmp.name) / "vault"
        self.repo.mkdir()
        self.vault.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Test")
        (self.repo / "Welcome.md").write_text("The Great Silence marks year zero.\n")
        (self.repo / "DM Resources").mkdir()
        (self.repo / "DM Resources" / "Secret.md").write_text("A hidden door exists.\n")
        (self.vault / "Welcome.md").write_bytes((self.repo / "Welcome.md").read_bytes())
        (self.vault / "DM Resources").mkdir()
        (self.vault / "DM Resources" / "Secret.md").write_bytes(
            (self.repo / "DM Resources" / "Secret.md").read_bytes()
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "source")
        self.manifest = build_manifest(self.repo, "HEAD", self.vault)

    def test_pinned_inventory_is_deterministic_and_held(self):
        self.assertEqual(self.manifest, build_manifest(self.repo, "HEAD", self.vault))
        self.assertEqual(len(self.manifest["notes"]), 2)
        self.assertEqual({n["review_status"] for n in self.manifest["notes"]}, {"held"})
        self.assertEqual({n["audience"] for n in self.manifest["notes"]}, {"player", "gm"})
        self.assertEqual(self.manifest["items"], [])
        validate_manifest(self.manifest, self.repo, self.vault)

    def test_vault_divergence_blocks_an_approved_item(self):
        (self.vault / "Welcome.md").write_text("Different text.\n")
        divergent = build_manifest(self.repo, "HEAD", self.vault)
        self.assertFalse(next(n for n in divergent["notes"] if n["path"] == "Welcome.md")["vault_match"])
        divergent["items"] = [self.approved_item()]
        with self.assertRaisesRegex(ValidationError, "vault divergence"):
            validate_manifest(divergent, self.repo, self.vault)

    def test_approval_needs_provenance_and_exact_source_excerpt(self):
        item = self.approved_item()
        self.manifest["items"] = [item]
        validate_manifest(self.manifest, self.repo, self.vault)
        broken = copy.deepcopy(self.manifest)
        del broken["items"][0]["approval"]["reviewer"]
        with self.assertRaisesRegex(ValidationError, "reviewer"):
            validate_manifest(broken, self.repo, self.vault)
        broken = copy.deepcopy(self.manifest)
        broken["items"][0]["source_excerpt"] = "an invented source line"
        with self.assertRaisesRegex(ValidationError, "excerpt"):
            validate_manifest(broken, self.repo, self.vault)

    def test_duplicate_or_unknown_status_is_rejected(self):
        self.manifest["items"] = [self.approved_item(), self.approved_item()]
        with self.assertRaisesRegex(ValidationError, "duplicate"):
            validate_manifest(self.manifest, self.repo, self.vault)
        self.manifest["items"] = [self.approved_item()]
        self.manifest["items"][0]["status"] = "secret-canon"
        with self.assertRaisesRegex(ValidationError, "status"):
            validate_manifest(self.manifest, self.repo, self.vault)

    def test_changed_pinned_tree_or_vault_blocks_preview(self):
        changed = copy.deepcopy(self.manifest)
        changed["notes"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValidationError, "digest"):
            validate_manifest(changed, self.repo, self.vault)
        (self.vault / "Welcome.md").write_text("Changed after manifest.\n")
        with self.assertRaisesRegex(ValidationError, "vault snapshot"):
            validate_manifest(self.manifest, self.repo, self.vault)

    def test_wrong_destination_and_unsupported_kg_operation_fail_closed(self):
        wrong = copy.deepcopy(self.manifest)
        wrong["destination"]["palace"] = "private_palace_v1"
        with self.assertRaisesRegex(ValidationError, "wrong Valdris destination"):
            validate_manifest(wrong, self.repo, self.vault)
        self.manifest["items"] = [self.approved_item()]
        self.manifest["items"][0]["operation"] = "kg_add"
        with self.assertRaisesRegex(ValidationError, "operation"):
            validate_manifest(self.manifest, self.repo, self.vault)

    def test_manifest_cannot_relabel_a_gm_note_as_player(self):
        gm = next(note for note in self.manifest["notes"] if note["path"] == "DM Resources/Secret.md")
        gm["audience"] = "player"
        with self.assertRaisesRegex(ValidationError, "audience classification"):
            validate_manifest(self.manifest, self.repo, self.vault)

    def test_vault_symlink_is_not_followed(self):
        (self.vault / "Welcome.md").unlink()
        (self.vault / "Welcome.md").symlink_to(self.repo / "Welcome.md")
        with self.assertRaisesRegex(ValidationError, "symlink"):
            build_manifest(self.repo, "HEAD", self.vault)

    def test_review_can_classify_an_undetermined_note_but_cannot_publish_gm_source(self):
        (self.repo / "Timeline.md").write_text("The Great Silence marks year zero.\n")
        (self.vault / "Timeline.md").write_bytes((self.repo / "Timeline.md").read_bytes())
        git(self.repo, "add", "Timeline.md")
        git(self.repo, "commit", "-q", "-m", "timeline")
        manifest = build_manifest(self.repo, "HEAD", self.vault)
        timeline = next(note for note in manifest["notes"] if note["path"] == "Timeline.md")
        self.assertEqual(timeline["audience"], "undetermined")
        item = self.approved_item()
        item.update(source_path="Timeline.md", source_revision=manifest["source"]["commit"],
                    source_sha256=timeline["sha256"])
        manifest["items"] = [item]
        validate_manifest(manifest, self.repo, self.vault)

        gm = next(note for note in manifest["notes"] if note["path"] == "DM Resources/Secret.md")
        item.update(source_path=gm["path"], source_sha256=gm["sha256"],
                    source_excerpt="A hidden door exists.", claim="A hidden door exists.")
        with self.assertRaisesRegex(ValidationError, "GM source"):
            validate_manifest(manifest, self.repo, self.vault)

    def approved_item(self):
        note = next(n for n in self.manifest["notes"] if n["path"] == "Welcome.md")
        return {
            "id": "great-silence-year-zero",
            "source_path": note["path"],
            "source_revision": self.manifest["source"]["commit"],
            "source_sha256": note["sha256"],
            "source_excerpt": "The Great Silence marks year zero.",
            "claim": "The Great Silence marks year zero.",
            "audience": "player",
            "status": "canon-public",
            "operation": "drawer",
            "native_identity": "valdris-seed-great-silence-year-zero",
            "approval": {"decision": "approved", "reviewer": "operator", "reviewed_at": "2026-09-28T20:00:00Z"},
        }


if __name__ == "__main__":
    unittest.main()
