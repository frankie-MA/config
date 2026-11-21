"""Offline tests: config preservation, backups, conflicts and explicit migration."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.local/bin/setup-ai-env'
loader = importlib.machinery.SourceFileLoader('ai_setup', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


class SetupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')

    def tearDown(self):
        self.temp.cleanup()

    def write(self, rel, text):
        path = self.home / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_setup(self, *args):
        return subprocess.run(['python3', str(SCRIPT), *args], env=self.env, capture_output=True, text=True)

    def test_apply_preserves_secrets_models_and_unknown_servers(self):
        secret = 'test-local-auth-value'
        self.write('.claude.json', json.dumps({'oauth': secret, 'mcpServers': {'custom': {'command': 'keep-me'}}}))
        self.write('.codex/config.toml', 'model = "keep-model"\n[mcp_servers.custom]\ncommand = "keep-me"\n')
        self.write('.config/opencode/opencode.json', json.dumps({'model': 'keep-model', 'mcp': {'custom': {'type': 'remote', 'url': 'https://example.invalid', 'headers': {'Authorization': secret}}}}))
        result = self.run_setup('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(secret, result.stdout + result.stderr)
        claude = json.loads((self.home / '.claude.json').read_text())
        self.assertEqual(claude['oauth'], secret)
        self.assertEqual(claude['mcpServers']['custom']['command'], 'keep-me')
        codex = tomllib.loads((self.home / '.codex/config.toml').read_text())
        self.assertEqual(codex['model'], 'keep-model')
        opencode = json.loads((self.home / '.config/opencode/opencode.json').read_text())
        self.assertEqual(opencode['model'], 'keep-model')
        self.assertEqual(opencode['mcp']['servers']['custom']['headers']['Authorization'], secret)
        backups = list((self.home / '.config-backup/ai').rglob('.claude.json'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(backups[0].read_text())['oauth'], secret)
        before = {p: p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        result = self.run_setup('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in self.home.rglob('*') if p.is_file()})

    def test_plan_does_not_write(self):
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_jsonc_stops_before_other_clients_are_changed(self):
        self.write('.config/opencode/opencode.jsonc', '{}')
        self.assertNotEqual(self.run_setup('--apply').returncode, 0)
        self.assertFalse((self.home / '.claude.json').exists())

    def test_known_legacy_github_requires_explicit_migration(self):
        legacy = {'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-github'], 'env': {'GITHUB_TOKEN': 'test-value'}}
        self.write('.claude.json', json.dumps({'mcpServers': {'github': legacy}}))
        self.write('.codex/config.toml', '[mcp_servers.github]\ncommand = "npx"\nargs = ["-y", "@modelcontextprotocol/server-github"]\n[mcp_servers.github.env]\nGITHUB_TOKEN = "test-value"\n[mcp_servers.custom]\ncommand = "keep-me"\n')
        self.assertEqual(self.run_setup('--apply').returncode, 0)
        self.assertEqual(json.loads((self.home / '.claude.json').read_text())['mcpServers']['github'], legacy)
        result = self.run_setup('--apply', '--replace-legacy-github')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads((self.home / '.claude.json').read_text())['mcpServers']['github']['command'].endswith('github-mcp-gh'))
        codex = tomllib.loads((self.home / '.codex/config.toml').read_text())
        self.assertNotIn('env', codex['mcp_servers']['github'])
        self.assertEqual(codex['mcp_servers']['custom']['command'], 'keep-me')

    def test_template_conflict_preserves_existing_file(self):
        file = self.write('.config/opencode/agents/review.md', 'local customized review')
        result = self.run_setup('--apply', '--client', 'opencode')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(file.read_text(), 'local customized review')
        self.assertIn('conflict', result.stdout)

    def test_config_symlink_is_rejected(self):
        target = self.write('private.json', '{}')
        (self.home / '.claude.json').symlink_to(target)
        self.assertNotEqual(self.run_setup('--apply').returncode, 0)
        self.assertEqual(target.read_text(), '{}')

    def test_check_has_no_network_or_changes(self):
        manifest = json.loads((ROOT / '.config/dotfiles-ai/environment.json').read_text())
        with patch.object(Path, 'home', return_value=self.home), patch.object(module, 'fetch', side_effect=AssertionError('network')):
            self.assertEqual(module.check(['claude'], manifest), 1)
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
