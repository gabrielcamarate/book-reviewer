import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from revisor.provider import InvalidModelResponse, codex_runner


class ProviderTest(unittest.TestCase):
    def test_invalid_json_is_a_rejected_response_and_exit_failure_is_not(self):
        def invalid_json(command, **kwargs):
            output = Path(command[command.index('--output-last-message') + 1])
            output.write_text('{invalid fixture')
            return subprocess.CompletedProcess(command, 0)
        with patch('revisor.provider.subprocess.run', side_effect=invalid_json):
            with self.assertRaisesRegex(InvalidModelResponse, 'JSON inválido'):
                codex_runner(prompt='Texto sintético.', schema={}, model='codex-default')
        with patch('revisor.provider.subprocess.run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(RuntimeError) as failure:
                codex_runner(prompt='Texto sintético.', schema={}, model='codex-default')
            self.assertNotIsInstance(failure.exception, InvalidModelResponse)

    def test_codex_uses_isolated_read_only_directory_and_configured_model(self):
        calls = []
        def run(command, **kwargs):
            calls.append((command, kwargs))
            output = Path(command[command.index('--output-last-message') + 1])
            output.write_text(json.dumps({'result': 'ok'}))
            self.assertEqual(Path(kwargs['cwd']), output.parent)
            self.assertEqual(command[command.index('--sandbox') + 1], 'read-only')
            self.assertIn('--skip-git-repo-check', command)
            return subprocess.CompletedProcess(command, 0)
        with patch('revisor.provider.subprocess.run', side_effect=run):
            self.assertEqual(codex_runner(prompt='Texto sintético.', schema={}, model='codex-default'), {'result': 'ok'})
            self.assertEqual(calls[-1][0][calls[-1][0].index('-m')+1], 'gpt-6.1-sol')
            self.assertIn('model_reasoning_effort="low"', calls[-1][0])
            codex_runner(prompt='Texto sintético.', schema={}, model='chosen-model')
            self.assertEqual(calls[-1][0][calls[-1][0].index('-m') + 1], 'chosen-model')
