import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock, AsyncMock

spec = importlib.util.spec_from_file_location('batch', Path(__file__).parents[1] / 'scripts/batch_download.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
URL = 'https://www.hltv.org/matches/2398725/spirit-vs-parivision-esl-pro-league-season-24'


class JournalTests(unittest.TestCase):
    def test_deduplicate_numeric_id_even_if_slug_differs(self):
        rows, stats = batch.plan_index({'total': 51, 'teams': [
            {'slug': 'spirit', 'matches': {URL: 'Dust2'}},
            {'slug': 'falcons', 'matches': {URL.replace('spirit-vs', 'falcons-vs'): 'Dust2'}}]})
        self.assertEqual(stats['unique_matches'], 1)
        self.assertEqual(stats['team_memberships'], 2)
        self.assertEqual(rows[0]['teams'], ['spirit', 'falcons'])

    def test_reject_unsafe_urls_and_team_paths(self):
        for url in ['http://www.hltv.org/matches/123/x', URL + '?team=1', URL.replace('www.hltv.org', 'evil.example')]:
            with self.assertRaises(ValueError):
                batch.match_url(url)
        with self.assertRaises(ValueError):
            batch.plan_index({'teams': [{'slug': '../escape', 'matches': {URL: 'Dust2'}}]})

    def test_lock_excludes_second_writer_and_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with batch.output_lock(root):
                with self.assertRaises(RuntimeError):
                    with batch.output_lock(root):
                        pass
            self.assertFalse((root / '.batch.lock').exists())

    def test_atomic_manifest_preserves_existing_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'manifest.json'
            data = {'old': {'status': 'error'}, URL: {'status': 'in-progress'}}
            batch.write_json(path, data)
            self.assertEqual(batch.load_manifest(path), data)
            self.assertEqual(len(list(Path(tmp).glob('*.tmp'))), 0)

    def test_rar_header_alone_never_passes_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'invalid.rar'
            path.write_bytes(b'Rar!\x1a\x07\x01\x00' + b'x' * 50)
            with patch.object(batch.subprocess, 'run', return_value=Mock(returncode=3, stdout='CRC failed')):
                with self.assertRaises(batch.ArchiveInvalid):
                    batch.verify_archive(path, 'unrar')

    def test_hash_mismatch_rejected_before_unrar(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'archive.rar'
            path.write_bytes(b'Rar!\x1a\x07\x01\x00' + b'x' * 50)
            with patch.object(batch.subprocess, 'run') as run:
                with self.assertRaises(batch.ArchiveInvalid):
                    batch.verify_archive(path, 'unrar', '0' * 64)
                run.assert_not_called()

    def test_missing_or_outside_file_not_resumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for value in ('missing.rar', '../outside.rar'):
                self.assertIsNone(batch.resumed_file(root, {'status': 'ok', 'sha256': 'a' * 64, 'path': value}, 'unrar'))

    def test_resume_requires_ok_hash_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / 'archive.rar'
            file.write_bytes(b'hello')
            with patch.object(batch, 'verify_archive', side_effect=batch.ArchiveInvalid('bad')):
                self.assertIsNone(batch.resumed_file(root, {'status': 'ok', 'sha256': 'a' * 64, 'path': file.name}, 'unrar'))
            with patch.object(batch, 'verify_archive', return_value={}):
                self.assertEqual(batch.resumed_file(root, {'status': 'ok', 'sha256': 'a' * 64, 'path': file.name}, 'unrar'), file)
                self.assertIsNone(batch.resumed_file(root, {'status': 'corrupt', 'sha256': 'a' * 64, 'path': file.name}, 'unrar'))

    def test_android_copy_fallback_and_conflict_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.rar'
            source.write_bytes(b'archive')
            digest = batch.sha256(source)
            with patch.object(batch.os, 'link', side_effect=OSError('unsupported')):
                files = batch.team_files(root, source, ['spirit', 'falcons'], digest)
            self.assertEqual(len(files), 2)
            self.assertEqual((root / files['falcons']).read_bytes(), b'archive')
            (root / files['spirit']).write_bytes(b'conflict')
            with self.assertRaises(batch.ArchiveInvalid):
                batch.team_files(root, source, ['spirit'], digest)
            self.assertEqual((root / files['spirit']).read_bytes(), b'conflict')

    def test_dry_run_needs_no_playwright_or_unrar(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed = Path(__file__).parents[1] / 'config/hltv_takeover_seed.json'
            with patch.object(batch, 'get_unrar', side_effect=AssertionError('should not be called')):
                self.assertEqual(batch.main(['--index', str(seed), '--out', tmp, '--dry-run']), 0)


class PageTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmed_block_stops_before_the_next_match(self):
        page = Mock()
        page.goto = AsyncMock()
        page.title = AsyncMock(return_value='HLTV')
        page.locator.return_value.inner_text = AsyncMock(return_value='Normal page')
        context = Mock()
        context.new_page = AsyncMock(return_value=page)
        browser = Mock()
        browser.new_context = AsyncMock(return_value=context)
        browser.close = AsyncMock()
        pw = Mock()
        pw.chromium.launch = AsyncMock(return_value=browser)
        manager = Mock()
        manager.__aenter__ = AsyncMock(return_value=pw)
        manager.__aexit__ = AsyncMock(return_value=False)
        module = SimpleNamespace(async_playwright=lambda: manager)
        rows = [{'url': URL, 'teams': ['spirit'], 'match_id': '2398725'},
                {'url': URL.replace('2398725', '2398726'), 'teams': ['spirit'], 'match_id': '2398726'}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {}
            with patch.dict('sys.modules', {'playwright.async_api': module}), patch.object(batch, 'download_one', new=AsyncMock(side_effect=batch.SiteBlocked('verification'))) as download:
                result = await batch.execute(rows, root, manifest, 'unrar', SimpleNamespace(chromium=None, limit=None, delay=20))
            self.assertEqual(result, 3)
            self.assertEqual(download.await_count, 1)
            self.assertEqual(manifest[URL]['status'], 'blocked-or-timeout')
            self.assertNotIn(rows[1]['url'], manifest)
            self.assertEqual(batch.load_manifest(root / 'manifest.json')[URL]['status'], 'blocked-or-timeout')
            browser.close.assert_awaited_once()

    async def test_completed_batch_resumes_without_network_or_playwright(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'verified.rar'
            source.write_bytes(b'archive')
            digest = batch.sha256(source)
            rows = [{'url': URL, 'teams': ['spirit'], 'match_id': '2398725'}]
            manifest = {URL: {'status': 'ok', 'path': source.name, 'sha256': digest}}
            with patch.object(batch, 'verify_archive', return_value={}), patch.dict('sys.modules', {'playwright.async_api': None}):
                result = await batch.execute(rows, root, manifest, 'unrar', Mock())
            self.assertEqual(result, 0)
            self.assertTrue((root / 'spirit' / source.name).exists())

    async def test_challenge_is_not_no_demo(self):
        page = Mock()
        page.goto = AsyncMock(return_value=Mock(status=200))
        page.title = AsyncMock(return_value='Just a moment...')
        page.locator.return_value.inner_text = AsyncMock(return_value='Verify you are human')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(batch.SiteBlocked):
                await batch.download_one(page, {'url': URL}, Path(tmp), 'unrar', Mock())
        page.locator.assert_called_once_with('body')

    async def test_missing_maps_is_error_instead_of_no_demo(self):
        page = Mock()
        page.goto = AsyncMock(return_value=Mock(status=200))
        page.title = AsyncMock(return_value='Match')
        page.locator.return_value.inner_text = AsyncMock(return_value='Normal page')
        page.locator.return_value.all_text_contents = AsyncMock(return_value=[])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'No played-map'):
                await batch.download_one(page, {'url': URL}, Path(tmp), 'unrar', Mock())

    async def test_veto_dust2_does_not_count_as_played_map(self):
        page = Mock()
        page.goto = AsyncMock(return_value=Mock(status=200))
        page.title = AsyncMock(return_value='Match')
        page.locator.return_value.inner_text = AsyncMock(return_value='Dust2 was removed')
        page.locator.return_value.all_text_contents = AsyncMock(return_value=['Ancient', 'Mirage'])
        with tempfile.TemporaryDirectory() as tmp:
            result = await batch.download_one(page, {'url': URL}, Path(tmp), 'unrar', Mock())
        self.assertEqual(result['status'], 'not-dust2')


if __name__ == '__main__':
    unittest.main()
