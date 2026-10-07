import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import release_version as mod  # noqa: E402

PYPROJECT = '[project]\nname = "fixture"\nversion = "{v}"\n'


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        (self.root / 'frontend').mkdir()
        self.write_version('0.2.0')
        (self.root / 'CHANGELOG.md').write_text('# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - 2026-10-07\n\n### Adicionado\n\n- Baseline.\n')
        self.commit()
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True, stderr=subprocess.DEVNULL)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def write_version(self, version, package=None, pyproject=None):
        (self.root / 'VERSION').write_text(version + '\n')
        (self.root / 'frontend/package.json').write_text(json.dumps({'name': 'f', 'version': package or version}) + '\n')
        (self.root / 'pyproject.toml').write_text(PYPROJECT.format(v=pyproject or version))

    def add_note(self):
        p = self.root / 'CHANGELOG.md'
        p.write_text(p.read_text().replace('## [Unreleased]\n', '## [Unreleased]\n\n### Corrigido\n\n- Corrige comportamento.\n', 1))

    def test_cut_updates_every_source_and_validates(self):
        self.add_note()
        (self.root / 'backend.py').write_text('x = 1\n')
        self.assertEqual(mod.cut(self.root, 'patch'), '0.2.1')
        self.commit()
        self.assertEqual(mod.check(self.root, self.base, 'HEAD'), '0.2.1')
        self.assertEqual(json.loads((self.root / 'frontend/package.json').read_text())['version'], '0.2.1')
        self.assertIn('version = "0.2.1"', (self.root / 'pyproject.toml').read_text())

    def test_cut_is_allowed_on_main(self):
        self.git('branch', '-M', 'main')
        self.add_note()
        self.assertEqual(mod.cut(self.root, 'minor'), '0.3.0')

    def test_code_without_version_is_rejected(self):
        (self.root / 'backend.py').write_text('x = 1\n')
        self.commit()
        with self.assertRaises(ValueError):
            mod.check(self.root, self.base, 'HEAD')

    def test_readme_only_needs_no_release(self):
        (self.root / 'README.md').write_text('clarification')
        self.commit()
        self.assertEqual(mod.check(self.root, self.base, 'HEAD'), '0.2.0')

    def test_contracts_and_design_require_bump(self):
        for name in ['AGENTS.md', 'RUNBOOK.md', 'design/tokens.json']:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('changed contract')
            self.commit()
            with self.subTest(name=name), self.assertRaises(ValueError):
                mod.check(self.root, self.base, 'HEAD')

    def test_empty_cut_does_not_modify_metadata(self):
        with self.assertRaises(ValueError):
            mod.cut(self.root, 'patch')
        self.assertEqual((self.root / 'VERSION').read_text(), '0.2.0\n')

    def test_historical_notes_are_immutable(self):
        self.add_note()
        mod.cut(self.root, 'minor')
        p = self.root / 'CHANGELOG.md'
        p.write_text(p.read_text().replace('Baseline.', 'Rewritten.'))
        self.commit()
        with self.assertRaises(ValueError):
            mod.check(self.root, self.base, 'HEAD')

    def test_mirror_mismatch_fails(self):
        for package, pyproject in [('9.0.0', None), (None, '9.0.0')]:
            self.write_version('0.2.0', package, pyproject)
            self.commit()
            with self.subTest(package=package, pyproject=pyproject), self.assertRaises(ValueError):
                mod.check(self.root, None, 'HEAD')

    def test_downgrade_or_skipped_increment_is_rejected(self):
        self.add_note()
        mod.cut(self.root, 'minor')
        for version in ['0.1.9', '0.9.0']:
            self.write_version(version)
            p = self.root / 'CHANGELOG.md'
            p.write_text(re.sub(r'## \[0\.[0-9]+\.[0-9]+\] -', '## [' + version + '] -', p.read_text(), count=1))
            self.commit()
            with self.subTest(version=version), self.assertRaises(ValueError):
                mod.check(self.root, self.base, 'HEAD')

    def test_invalid_and_duplicate_versions_rejected(self):
        for version in ['01.0.0', '1.0', 'v1.0.0', '1.0.0;bad']:
            with self.assertRaises(ValueError):
                mod.parse_version(version)
        p = self.root / 'CHANGELOG.md'
        p.write_text(p.read_text() + '\n## [0.2.0] - 2026-10-07\n\n- Duplicate.\n')
        self.commit()
        with self.assertRaises(ValueError):
            mod.check(self.root, None, 'HEAD')

    def test_first_versioned_commit_must_be_initial_baseline(self):
        repo = Path(self.tmp.name) / 'fresh'
        repo.mkdir()
        run = lambda *a: subprocess.check_output(['git', *a], cwd=repo, text=True, stderr=subprocess.DEVNULL)
        run('init', '-q')
        run('config', 'user.email', 'fixture@example.invalid')
        run('config', 'user.name', 'Fixture')
        (repo / 'README.md').write_text('before versioning')
        run('add', '.')
        run('commit', '-qm', 'old')
        old = run('rev-parse', 'HEAD').strip()
        (repo / 'frontend').mkdir()
        for version, ok in [('0.2.0', True), ('0.3.0', False)]:
            (repo / 'VERSION').write_text(version + '\n')
            (repo / 'frontend/package.json').write_text(json.dumps({'version': version}))
            (repo / 'pyproject.toml').write_text(PYPROJECT.format(v=version))
            (repo / 'CHANGELOG.md').write_text(f'# Changelog\n\n## [Unreleased]\n\n## [{version}] - 2026-10-07\n\n- Baseline.\n')
            run('add', '.')
            run('commit', '-qm', 'versioned')
            with self.subTest(version=version):
                if ok:
                    self.assertEqual(mod.check(repo, old, 'HEAD'), version)
                else:
                    with self.assertRaises(ValueError):
                        mod.check(repo, old, 'HEAD')


if __name__ == '__main__':
    unittest.main()
