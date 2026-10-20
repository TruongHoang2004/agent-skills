"""Behavioral installer and baseline tests; no model calls or remote services."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import aidlc

spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aidlc-tests-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "project with spaces"

    def install(self, *args, ok=True, cwd=None):
        result = subprocess.run(
            [str(ROOT / "install.sh"), "--target", str(self.repo), *args],
            cwd=cwd, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return json.loads(result.stdout if result.returncode == 0 else result.stderr)

    def runtime(self, *args, ok=True, cwd=None):
        result = subprocess.run(
            [sys.executable, str(self.repo / ".aidlc/runtime/aidlc.py"), "--root", str(self.repo), *args],
            cwd=cwd, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return json.loads(result.stdout if result.returncode == 0 else result.stderr)

    def source(self, relative="src/app.py", text="def add(a, b):\n    return a + b\n"):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def baseline(self, publish=True):
        info = self.runtime("baseline-init")
        directory = Path(info["directory"])
        analysis = json.loads((directory / "analysis.json").read_text())
        inventory = json.loads((directory / "snapshot.json").read_text())
        for name in aidlc.DOCUMENTS:
            (directory / name).write_text(
                "# Fixture observations\n\n"
                "Observed fixture contains the paths in snapshot.json. "
                "No runtime topology is inferred by this structural test.\n"
            )
            analysis["documents"][name] = {
                "evidence": list(inventory)[:1],
                "notPresent": "" if inventory else "The captured repository inventory is empty.",
            }
        analysis["complete"] = True
        (directory / "analysis.json").write_text(json.dumps(analysis))
        if publish:
            self.runtime("baseline-publish", "--revision", info["revision"])
        return directory

    def local_tickets(self):
        p = self.repo / ".aidlc/config/tickets.json"
        p.write_text(json.dumps({
            "schemaVersion": 1, "defaultProvider": "local",
            "providers": {"local": {"root": "tickets"}},
            "routing": [{"prefix": "local:", "provider": "local"}], "writeBack": "draft",
        }))

    def test_each_host_installs_its_bundle_in_any_directory(self):
        for host in installer.HOSTS:
            with self.subTest(host=host):
                self.repo = self.base / ("project " + host)
                self.source()
                data = self.install("--agent", host, cwd=self.base)
                self.assertEqual(data["hosts"], [host])
                skills, agents, bridge = installer.LAYOUT[host]
                self.assertEqual(len(list((self.repo / skills).glob("*/SKILL.md"))), 14)
                for skill in (self.repo / skills).glob("*/SKILL.md"):
                    self.assertTrue(skill.is_symlink())
                    self.assertEqual(skill.resolve(), ROOT / "skills" / skill.parent.name / "SKILL.md")
                self.assertEqual(len(list((self.repo / agents).glob("*"))), 8)
                self.assertTrue((self.repo / bridge).exists())
                self.assertTrue((self.repo / ".aidlc/work").is_dir())
                for folder in (".agent", ".agents", ".codex", ".claude"):
                    self.assertFalse((self.repo / folder / ".aidlc").exists())
                self.assertEqual(self.install("--check")["status"], "ok")

    def test_all_hosts_share_skills_and_memory(self):
        self.install("--all")
        self.assertEqual(len(list((self.repo / ".agents/skills").glob("*/SKILL.md"))), 14)
        self.assertEqual(len(list((self.repo / ".claude/skills").glob("*/SKILL.md"))), 14)
        self.assertEqual(
            (self.repo / ".agents/skills/dev/SKILL.md").read_bytes(),
            (self.repo / ".claude/skills/dev/SKILL.md").read_bytes(),
        )

    def test_second_host_preserves_identity_rules_and_baseline(self):
        self.install("--agent", "codex")
        self.source()
        revision = self.baseline().name
        self.local_tickets()
        rules = self.repo / ".aidlc/rules/index.md"
        rules.write_text("# Existing team policy\n")
        project = (self.repo / ".aidlc/project.json").read_bytes()
        self.install("--agent", "claude-code")
        self.install("--agent", "antigravity")
        self.assertEqual((self.repo / ".aidlc/project.json").read_bytes(), project)
        self.assertEqual(rules.read_text(), "# Existing team policy\n")
        self.assertEqual(self.runtime("gate", "--skill", "dev")["baselineRevision"], revision)

    def test_reinstall_is_idempotent(self):
        self.install()
        before = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        data = self.install()
        after = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(data["changes"], [])

    def test_dry_run_creates_nothing(self):
        self.install("--dry-run", "--agent", "codex")
        self.assertFalse(self.repo.exists())

    def test_existing_instructions_and_settings_are_preserved(self):
        self.repo.mkdir()
        original = b"# Team rules\n\nKeep our formatting.\n"
        for name in ("AGENTS.md", "CLAUDE.md"):
            (self.repo / name).write_bytes(original)
        self.source(".claude/settings.json", '{"existing": true}\n')
        self.install()
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.repo / name).read_bytes()
            self.assertTrue(text.startswith(original))
            self.assertEqual(text.count(aidlc.START.encode()), 1)
        self.assertEqual((self.repo / ".claude/settings.json").read_text(), '{"existing": true}\n')
        self.install("--uninstall")
        for name in ("AGENTS.md", "CLAUDE.md"):
            self.assertIn(original, (self.repo / name).read_bytes())

    def test_skill_collision_fails_before_any_other_write(self):
        p = self.source(".agents/skills/dev/SKILL.md", "User-owned skill")
        self.assertEqual(self.install("--agent", "codex", ok=False)["code"], "INSTALL_CONFLICT")
        self.assertEqual(p.read_text(), "User-owned skill")
        self.assertFalse((self.repo / ".aidlc").exists())
        self.assertFalse((self.repo / "AGENTS.md").exists())

    def test_modified_managed_skill_blocks_upgrade_and_uninstall(self):
        self.install("--agent", "codex")
        p = self.repo / ".agents/skills/dev/SKILL.md"
        original = p.read_text()
        p.unlink()
        p.write_text(original + "\nLocal customization\n")
        before = (self.repo / ".aidlc/install.json").read_bytes()
        self.install("--agent", "claude-code", ok=False)
        self.assertFalse((self.repo / ".claude").exists())
        self.install("--uninstall", ok=False)
        self.assertEqual((self.repo / ".aidlc/install.json").read_bytes(), before)
        self.assertIn("Local customization", p.read_text())

    def test_upgrade_previous_copy_to_link_preserves_memory(self):
        self.install("--agent", "codex")
        memory = (self.repo / ".aidlc/project.json").read_bytes()
        name = ".agents/skills/dev/SKILL.md"
        path = self.repo / name
        content = path.read_bytes()
        path.unlink()
        path.write_bytes(content)
        manifest = self.repo / ".aidlc/install.json"
        state = json.loads(manifest.read_text())
        state["files"][name].update(kind="file", sha256=aidlc.digest(content))
        manifest.write_bytes(aidlc.encoded(state))
        self.install("--agent", "codex")
        self.assertTrue(path.is_symlink())
        self.assertEqual((self.repo / ".aidlc/project.json").read_bytes(), memory)

    def test_broken_owned_link_is_reported_and_can_be_uninstalled(self):
        self.install("--agent", "codex")
        name = ".agents/skills/dev/SKILL.md"
        path = self.repo / name
        path.unlink()
        target = str(self.base / "missing-source.md")
        path.symlink_to(target)
        manifest = self.repo / ".aidlc/install.json"
        state = json.loads(manifest.read_text())
        state["files"][name]["sha256"] = installer.fingerprint(installer.Link(target))
        manifest.write_bytes(aidlc.encoded(state))
        result = self.install("--check", ok=False)
        self.assertIn("broken link", result["reason"])
        self.install("--uninstall")
        self.assertFalse(path.is_symlink())
        self.assertTrue((ROOT / "skills/dev/SKILL.md").is_file())

    def test_link_replacement_rolls_back_without_writing_source(self):
        self.repo.mkdir()
        source = self.base / "shared.md"
        source.write_text("Shared content")
        path = self.repo / "skill.md"
        path.symlink_to(source)
        with patch.object(installer, "atomic_write", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                installer.apply(self.repo, {
                    "skill.md": installer.Link(str(self.base / "other.md")),
                    "fail.txt": b"fail",
                })
        self.assertEqual(path.resolve(), source.resolve())
        self.assertEqual(source.read_text(), "Shared content")

    def test_user_edits_outside_managed_bridge_survive(self):
        self.install("--agent", "codex")
        p = self.repo / "AGENTS.md"
        p.write_text("# Added user policy\n\n" + p.read_text())
        self.install("--agent", "antigravity")
        self.assertTrue(p.read_text().startswith("# Added user policy"))
        self.install("--check")

    def test_modified_bridge_blocks_reinstall(self):
        self.install("--agent", "codex")
        p = self.repo / "AGENTS.md"
        p.write_text(p.read_text().replace("Project memory", "Changed memory"))
        self.install(ok=False)

    def test_partial_uninstall_keeps_other_hosts_and_memory(self):
        self.install()
        self.baseline()
        self.source(".aidlc/work/example/progress.md", "Preserve this history.")
        identity = (self.repo / ".aidlc/project.json").read_bytes()
        self.install("--uninstall", "--agent", "codex")
        self.assertTrue((self.repo / ".agents/skills/dev/SKILL.md").exists())
        self.assertFalse((self.repo / ".codex/agents/aidlc-security.toml").exists())
        self.install("--uninstall", "--agent", "antigravity")
        self.assertFalse((self.repo / ".agents/skills/dev/SKILL.md").exists())
        self.assertTrue((self.repo / ".claude/skills/dev/SKILL.md").exists())
        self.install("--uninstall", "--agent", "claude-code")
        self.assertEqual((self.repo / ".aidlc/project.json").read_bytes(), identity)
        self.assertEqual((self.repo / ".aidlc/work/example/progress.md").read_text(), "Preserve this history.")
        self.assertTrue((self.repo / ".aidlc/knowledge/current.json").exists())

    def test_symlink_destination_is_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.repo.mkdir()
        (self.repo / ".agents").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.install("--agent", "codex", ok=False)["code"], "SYMLINK_PATH")
        self.assertEqual(list(outside.iterdir()), [])

    def test_baseline_and_rule_symlink_is_rejected(self):
        self.repo.mkdir()
        outside = self.base / "shared-memory"
        outside.mkdir()
        (self.repo / ".aidlc").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.install(ok=False)["code"], "SYMLINK_PATH")

    def test_writer_lock_blocks_install_and_baseline_mutations(self):
        self.install("--agent", "codex")
        lock = self.repo / ".aidlc/.write-lock"
        lock.write_text('{"pid": 123}')
        self.assertEqual(self.install("--agent", "claude-code", ok=False)["code"], "WORKSPACE_LOCKED")
        self.assertEqual(self.runtime("baseline-init", ok=False)["code"], "WORKSPACE_LOCKED")
        self.assertTrue(lock.exists())

    def test_apply_rolls_back_files_on_write_failure(self):
        self.repo.mkdir()
        self.source("a.txt", "old")
        real = installer.atomic_write

        def fail_second(path, data):
            if path.name == "b.txt":
                raise OSError("simulated disk failure")
            return real(path, data)

        with patch.object(installer, "atomic_write", side_effect=fail_second):
            with self.assertRaises(OSError):
                installer.apply(self.repo, {"a.txt": b"new", "b.txt": b"other"})
        self.assertEqual((self.repo / "a.txt").read_text(), "old")
        self.assertFalse((self.repo / "b.txt").exists())

    def test_missing_baseline_blocks_every_other_skill(self):
        self.install()
        self.assertEqual(self.runtime("gate", "--skill", "reverse-engineer")["status"], "allowed")
        for skill in aidlc.SKILLS:
            if skill != "reverse-engineer":
                self.assertEqual(self.runtime("gate", "--skill", skill, ok=False)["code"], "BASELINE_MISSING")

    def test_empty_non_git_and_unborn_git_baselines(self):
        for git in (False, True):
            with self.subTest(git=git):
                self.repo = self.base / ("empty-" + str(git))
                self.install("--agent", "codex")
                if git:
                    subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
                self.baseline()
                self.assertEqual(self.runtime("gate", "--skill", "inception")["status"], "allowed")

    def test_draft_or_missing_evidence_cannot_publish(self):
        self.install()
        info = self.runtime("baseline-init")
        self.runtime("baseline-publish", "--revision", info["revision"], ok=False)
        directory = self.baseline(publish=False)
        analysis = json.loads((directory / "analysis.json").read_text())
        analysis["documents"][aidlc.DOCUMENTS[0]] = {"evidence": [], "notPresent": ""}
        (directory / "analysis.json").write_text(json.dumps(analysis))
        self.assertEqual(self.runtime("baseline-publish", "--revision", directory.name, ok=False)["code"], "EVIDENCE_MISSING")

    def test_published_documents_are_immutable(self):
        self.install()
        directory = self.baseline()
        self.assertEqual(self.runtime("baseline-publish", "--revision", directory.name, ok=False)["code"], "IMMUTABLE_REVISION")
        (directory / aidlc.DOCUMENTS[0]).write_text("tampered")
        self.assertEqual(self.runtime("gate", "--skill", "rules", ok=False)["code"], "BASELINE_INVALID")

    def test_source_change_during_analysis_prevents_publish(self):
        self.install()
        self.source()
        directory = self.baseline(publish=False)
        self.source(text="changed")
        self.assertEqual(self.runtime("baseline-publish", "--revision", directory.name, ok=False)["code"], "SOURCE_CHANGED")

    def test_dirty_untracked_and_deleted_source_invalidate_baseline(self):
        self.install()
        original = self.source()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "src/app.py"], check=True)
        self.baseline()
        original.write_text("changed but not committed")
        self.assertEqual(self.runtime("gate", "--skill", "inception", ok=False)["code"], "BASELINE_STALE")
        self.baseline()
        self.source("src/new.py", "new untracked")
        self.assertEqual(self.runtime("gate", "--skill", "rules", ok=False)["code"], "BASELINE_STALE")
        self.baseline()
        original.unlink()
        self.assertEqual(self.runtime("gate", "--skill", "rules", ok=False)["code"], "BASELINE_STALE")

    def test_work_delta_allows_only_declared_paths(self):
        self.install()
        self.source()
        self.baseline()
        self.runtime("work-start", "--id", "W1", "--skill", "construction", "--allow", "src")
        self.source(text="intended change")
        self.assertEqual(self.runtime("gate", "--skill", "aidlc-review", "--work", "W1")["status"], "allowed")
        self.source("outside.txt", "unexpected")
        self.assertEqual(self.runtime("gate", "--skill", "aidlc-review", "--work", "W1", ok=False)["code"], "BASELINE_STALE")

    def test_work_cannot_escape_project_or_overwrite_state(self):
        self.install()
        self.baseline()
        self.runtime("work-start", "--id", "../evil", "--skill", "construction", "--allow", "src", ok=False)
        self.runtime("work-start", "--id", "W1", "--skill", "construction", "--allow", "../other", ok=False)
        self.runtime("work-start", "--id", "W1", "--skill", "construction", "--allow", "src")
        self.assertEqual(self.runtime("work-start", "--id", "W1", "--skill", "construction", "--allow", "other", ok=False)["code"], "WORK_EXISTS")

    def test_missing_ticket_provider_blocks_dev_but_rules_can_configure(self):
        self.install()
        self.baseline()
        self.runtime("gate", "--skill", "rules")
        self.assertEqual(self.runtime("gate", "--skill", "dev", ok=False)["code"], "PROVIDER_NOT_CONFIGURED")
        self.local_tickets()
        self.runtime("gate", "--skill", "dev")

    def test_project_identity_rejects_copied_baseline(self):
        self.install()
        self.baseline()
        first = self.repo
        self.repo = self.base / "other"
        self.install()
        shutil.copytree(first / ".aidlc/knowledge", self.repo / ".aidlc/knowledge", dirs_exist_ok=True)
        self.assertEqual(self.runtime("gate", "--skill", "rules", ok=False)["code"], "BASELINE_INVALID")

    def test_configuration_isolated_and_invalid_paths_blocked(self):
        self.install()
        self.local_tickets()
        self.install("--check")
        first = self.repo
        self.repo = self.base / "separate"
        self.install()
        self.assertIsNone(json.loads((self.repo / ".aidlc/config/tickets.json").read_text())["defaultProvider"])
        self.repo = first
        path = self.repo / ".aidlc/config/tickets.json"
        value = json.loads(path.read_text())
        value["providers"]["local"]["root"] = "../escape"
        path.write_text(json.dumps(value))
        self.runtime("config-check", ok=False)

    def test_runtime_finds_root_from_nested_directory(self):
        self.install()
        self.baseline()
        nested = self.repo / "package"
        nested.mkdir()
        result = subprocess.run(
            [sys.executable, str(self.repo / ".aidlc/runtime/aidlc.py"), "status"],
            cwd=nested, capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout)["root"], str(self.repo.resolve()))

    def test_bundle_integrity_and_english_skill_metadata(self):
        for host in installer.HOSTS:
            for path in (ROOT / "skills").glob("*/SKILL.md"):
                text = path.read_text()
                self.assertTrue(text.startswith("---\nname: " + path.parent.name + "\n"))
                self.assertIn("description:", text)
                self.assertTrue(text.isascii())
                for reference in ("protocol.md",):
                    self.assertTrue((path.parent / "references" / reference).is_file())
        try:
            import tomllib
        except ImportError:
            self.skipTest("Native TOML parser requires Python 3.11+; installer supports 3.9+")
        for path, text in installer.outputs().items():
            if path.suffix != ".toml":
                continue
            value = tomllib.loads(text)
            self.assertEqual(value["name"], path.stem)
            self.assertIn("developer_instructions", value)


if __name__ == "__main__":
    unittest.main()
