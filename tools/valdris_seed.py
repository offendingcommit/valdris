"""Freeze and check a Valdris source manifest. This tool never writes to Palace.

The checked-in manifest contains note metadata only. Reviewed claims and approvals
belong in an operator-controlled copy outside this public repository.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


DESTINATION = {"realm": "valdris_realm", "palace": "valdris_palace_v1", "wing": "wing_valdris"}
STATUSES = {"held", "canon-public", "canon-gm", "proposal", "observation"}
AUDIENCES = {"player", "gm", "undetermined"}
OPERATIONS = {"drawer"}
ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class ValidationError(ValueError):
    pass


def _git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise ValidationError(f"Git source unavailable: {' '.join(args)}") from exc


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_notes(repo: Path, commit: str) -> dict[str, dict[str, str]]:
    notes = {}
    for record in _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit).split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8")
        if not path.endswith(".md"):
            continue
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValidationError(f"Unsupported Markdown source entry: {path}")
        notes[path] = {"blob": blob, "sha256": _sha256(_git(repo, "cat-file", "blob", blob))}
    return notes


def _audience(path: str) -> str:
    # Candidate classification only. Every note stays held until an operator
    # reviews each claim and the audience of that claim.
    if path.startswith("DM Resources/") or path.startswith("Adventures/"):
        return "gm"
    if path == "Welcome.md" or path.startswith("Player Resources/"):
        return "player"
    return "undetermined"


def build_manifest(repo: Path, revision: str, vault: Path) -> dict:
    commit = _git(repo, "rev-parse", f"{revision}^{{commit}}").decode().strip()
    tree = _git(repo, "rev-parse", f"{commit}^{{tree}}").decode().strip()
    source = _source_notes(repo, commit)
    notes = []
    for path, identity in sorted(source.items()):
        vault_file = vault / path
        if vault_file.is_symlink():
            raise ValidationError(f"Vault note is a symlink: {path}")
        vault_digest = _sha256(vault_file.read_bytes()) if vault_file.is_file() else None
        notes.append({
            "path": path,
            "blob": identity["blob"],
            "sha256": identity["sha256"],
            "vault_sha256": vault_digest,
            "vault_match": vault_digest == identity["sha256"],
            "audience": _audience(path),
            "review_status": "held",
        })
    vault_only = {p.relative_to(vault).as_posix() for p in vault.rglob("*.md") if p.is_file()} - set(source)
    return {
        "schema": "valdris-curated-seed/v1",
        "source": {"repository": "offendingcommit/valdris", "commit": commit, "tree": tree},
        "destination": DESTINATION.copy(),
        "vault_only_markdown_count": len(vault_only),
        "notes": notes,
        "items": [],
    }


def _require_fields(value: dict, fields: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValidationError(f"{label} fields must be exactly {sorted(fields)}")


def validate_manifest(manifest: dict, repo: Path, vault: Path) -> dict[str, int]:
    _require_fields(manifest, {"schema", "source", "destination", "vault_only_markdown_count", "notes", "items"}, "manifest")
    if manifest["schema"] != "valdris-curated-seed/v1" or manifest["destination"] != DESTINATION:
        raise ValidationError("Unknown schema or wrong Valdris destination")
    _require_fields(manifest["source"], {"repository", "commit", "tree"}, "source")
    source = manifest["source"]
    if source["repository"] != "offendingcommit/valdris" or not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
        raise ValidationError("Invalid source repository or commit")
    pinned_tree = _git(repo, "rev-parse", f"{source['commit']}^{{tree}}").decode().strip()
    if pinned_tree != source["tree"]:
        raise ValidationError("Pinned source tree differs from manifest")
    pinned_notes = _source_notes(repo, source["commit"])
    if not isinstance(manifest["notes"], list) or not isinstance(manifest["items"], list):
        raise ValidationError("Notes and items must be lists")
    note_by_path = {}
    for note in manifest["notes"]:
        _require_fields(note, {"path", "blob", "sha256", "vault_sha256", "vault_match", "audience", "review_status"}, "note")
        path = note["path"]
        if path in note_by_path or path not in pinned_notes:
            raise ValidationError(f"Duplicate or unknown source note: {path}")
        note_by_path[path] = note
        if {"blob": note["blob"], "sha256": note["sha256"]} != pinned_notes[path]:
            raise ValidationError(f"Pinned note digest or blob changed: {path}")
        if note["audience"] != _audience(path) or note["review_status"] != "held":
            raise ValidationError(f"Invalid held audience classification: {path}")
        vault_file = vault / path
        if vault_file.is_symlink():
            raise ValidationError(f"Vault note is a symlink: {path}")
        current_vault_sha = _sha256(vault_file.read_bytes()) if vault_file.is_file() else None
        if current_vault_sha != note["vault_sha256"] or (current_vault_sha == note["sha256"]) != note["vault_match"]:
            raise ValidationError(f"Changed vault snapshot for source note: {path}")
    if set(note_by_path) != set(pinned_notes):
        raise ValidationError("Source note inventory is incomplete")
    vault_only = {p.relative_to(vault).as_posix() for p in vault.rglob("*.md") if p.is_file()} - set(pinned_notes)
    if manifest["vault_only_markdown_count"] != len(vault_only):
        raise ValidationError("Changed vault-only Markdown inventory")
    ids = set()
    native_ids = set()
    for item in manifest["items"]:
        _require_fields(item, {"id", "source_path", "source_revision", "source_sha256", "source_excerpt", "claim", "audience", "status", "operation", "native_identity", "approval"}, "item")
        item_id = item["id"]
        if not isinstance(item_id, str) or not ID_PATTERN.fullmatch(item_id) or item_id in ids:
            raise ValidationError(f"Invalid or duplicate item ID: {item_id}")
        ids.add(item_id)
        path = item["source_path"]
        if path not in note_by_path or item["source_revision"] != source["commit"] or item["source_sha256"] != note_by_path[path]["sha256"]:
            raise ValidationError(f"Missing or mismatched source provenance for item: {item_id}")
        if item["status"] not in STATUSES:
            raise ValidationError(f"Unknown item status: {item_id}")
        if item["audience"] not in AUDIENCES or item["operation"] not in OPERATIONS:
            raise ValidationError(f"Invalid audience or operation: {item_id}")
        excerpt = item["source_excerpt"]
        if not isinstance(excerpt, str) or not excerpt.strip() or excerpt not in _git(repo, "cat-file", "blob", note_by_path[path]["blob"]).decode("utf-8"):
            raise ValidationError(f"Source excerpt is not present in pinned note: {item_id}")
        if not isinstance(item["claim"], str) or not item["claim"].strip():
            raise ValidationError(f"Empty claim: {item_id}")
        approval = item["approval"]
        if item["status"] == "held":
            if approval is not None or item["native_identity"] is not None:
                raise ValidationError(f"Held item has admission fields: {item_id}")
            continue
        _require_fields(approval, {"decision", "reviewer", "reviewed_at"}, "approval")
        if approval["decision"] != "approved" or not isinstance(approval["reviewer"], str) or not approval["reviewer"].strip():
            raise ValidationError(f"Missing approved reviewer: {item_id}")
        if not isinstance(approval["reviewed_at"], str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", approval["reviewed_at"]):
            raise ValidationError(f"Invalid approval time: {item_id}")
        expected_native = f"valdris-seed-{item_id}"
        if item["native_identity"] != expected_native or expected_native in native_ids:
            raise ValidationError(f"Invalid or duplicate native identity: {item_id}")
        native_ids.add(expected_native)
        if not note_by_path[path]["vault_match"]:
            raise ValidationError(f"Approved item has vault divergence: {item_id}")
        if item["audience"] == "undetermined":
            raise ValidationError(f"Unreviewed audience: {item_id}")
        if note_by_path[path]["audience"] == "gm" and item["audience"] != "gm":
            raise ValidationError(f"GM source cannot enter player audience: {item_id}")
        if (item["status"] == "canon-public" and item["audience"] != "player") or (item["status"] == "canon-gm" and item["audience"] != "gm"):
            raise ValidationError(f"Canon status conflicts with audience: {item_id}")
    return {
        "source_notes": len(pinned_notes),
        "vault_matched": sum(note["vault_match"] for note in manifest["notes"]),
        "held_notes": len(manifest["notes"]),
        "approved_items": sum(item["status"] != "held" for item in manifest["items"]),
        "held_items": sum(item["status"] == "held" for item in manifest["items"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["freeze", "validate", "preview"])
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--revision", default="HEAD", help="Git commit to pin when freezing")
    args = parser.parse_args()
    try:
        if args.command == "freeze":
            manifest = build_manifest(args.repo, args.revision, args.vault)
            if args.manifest.exists():
                raise ValidationError("Refusing to overwrite an existing review manifest")
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        else:
            manifest = json.loads(args.manifest.read_text())
        summary = validate_manifest(manifest, args.repo, args.vault)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"seed manifest blocked: {exc}\n")
    print(json.dumps(summary, sort_keys=True))
    if args.command == "preview":
        print("no-write preview only; approval metadata requires independent operator review")


if __name__ == "__main__":
    main()
