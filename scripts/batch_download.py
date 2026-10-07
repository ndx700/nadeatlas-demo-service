#!/usr/bin/env python3
"""HLTV batch downloader: headed Chromium navigation, verified files, resumable journal.

Only completed archives resume. Partial transfers restart; HTTP Range is not used.
A confirmed security challenge or block stops the batch without automatic retries.
"""
import argparse
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urljoin, urlsplit


class SiteBlocked(RuntimeError):
    pass


class ArchiveInvalid(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def match_url(value):
    u = urlsplit(value)
    if (u.scheme != 'https' or u.hostname != 'www.hltv.org' or u.port
            or u.username or u.password or u.query or u.fragment
            or not re.fullmatch(r'/matches/\d+/[a-zA-Z0-9-]+', u.path)):
        raise ValueError('Expected an HTTPS www.hltv.org/matches/ID/slug path URL')
    return 'https://www.hltv.org' + u.path


def plan_index(data):
    """Accept the handover teams[].matches mapping; deduplicate by numeric match ID."""
    plan, memberships = {}, 0
    for team in data.get('teams', []):
        slug = team['slug']
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
            raise ValueError('Unsafe team slug')
        matches = team['matches']
        if not isinstance(matches, dict):
            raise ValueError('teams[].matches must be a URL-to-label mapping')
        for value in matches:
            url = match_url(value)
            match_id = re.search(r'/matches/(\d+)/', url).group(1)
            memberships += 1
            row = plan.setdefault(match_id, {'match_id': match_id, 'url': url, 'teams': []})
            if slug not in row['teams']:
                row['teams'].append(slug)
    rows = list(plan.values())
    return rows, {'unique_matches': len(rows), 'team_memberships': memberships,
                  'shared_memberships': memberships - len(rows),
                  'declared_total': data.get('total'), 'range': data.get('range')}


def load_manifest(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or any(not isinstance(v, dict) for v in data.values()):
        raise ValueError('Manifest must map keys to record objects; refusing to overwrite it')
    return data


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def output_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / '.batch.lock'
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise RuntimeError('Output is locked. Check its running process before removing .batch.lock')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def get_unrar(value):
    tool = shutil.which(value)
    if not tool:
        raise RuntimeError('Official unrar is required; set --unrar or UNRAR. Validation cannot be skipped')
    proc = subprocess.run([tool], capture_output=True, text=True, timeout=15)
    if 'UNRAR' not in (proc.stdout + proc.stderr).upper():
        raise RuntimeError('The configured program does not identify itself as UNRAR')
    return tool


def verify_archive(path, unrar, expected=None):
    with path.open('rb') as f:
        magic = f.read(8)
    if not (magic.startswith(b'Rar!\x1a\x07\x00') or magic == b'Rar!\x1a\x07\x01\x00'):
        raise ArchiveInvalid('Not a RAR archive')
    if path.stat().st_size < 20:
        raise ArchiveInvalid('Truncated archive')
    digest = sha256(path)
    if expected and digest != expected:
        raise ArchiveInvalid('SHA-256 does not match the saved journal')
    check = subprocess.run([unrar, 't', '-idq', '-p-', str(path)],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=1800)
    if check.returncode != 0:
        raise ArchiveInvalid('unrar integrity test failed: ' + check.stdout[-1200:])
    return {'sha256': digest, 'size': path.stat().st_size, 'validation': 'unrar-test'}


def safe_local_path(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Journal path escapes output directory')
    return path


def resumed_file(root, record, unrar):
    if record.get('status') != 'ok' or not record.get('sha256'):
        return None
    value = record.get('path') or record.get('file') or record.get('output')
    if not isinstance(value, str):
        return None
    try:
        path = safe_local_path(root, value)
        verify_archive(path, unrar, record['sha256'])
        return path
    except (OSError, ValueError, ArchiveInvalid, subprocess.SubprocessError):
        return None


def team_files(root, source, teams, digest):
    files = {}
    for team in teams:
        target = root / team / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if sha256(target) != digest:
                raise ArchiveInvalid('Existing team file conflicts with verified source: ' + str(target))
        else:
            try:
                os.link(source, target)
            except OSError:
                # Android shared storage may not support hard links.
                fd, name = tempfile.mkstemp(dir=target.parent, suffix='.part')
                os.close(fd)
                tmp = Path(name)
                try:
                    shutil.copyfile(source, tmp)
                    if sha256(tmp) != digest:
                        raise ArchiveInvalid('Copied archive hash mismatch')
                    if target.exists():
                        raise FileExistsError(target)
                    os.rename(tmp, target)
                finally:
                    tmp.unlink(missing_ok=True)
        files[team] = str(target.relative_to(root))
    return files


def page_blocked(title, body):
    text = (title + '\n' + body).lower()
    return any(x in text for x in ('just a moment', 'verify you are human',
        'checking your browser', 'you have been blocked', 'security verification',
        '正在进行安全验证', '验证您不是自动程序', '请稍候', 'access denied'))


async def check_page(page):
    title = await page.title()
    body = await page.locator('body').inner_text(timeout=5000)
    if page_blocked(title, body):
        raise SiteBlocked('Site security verification or access block; batch stopped')


async def download_one(page, row, root, unrar, args):
    response = await page.goto(row['url'], wait_until='domcontentloaded', timeout=45000)
    await check_page(page)
    if response and response.status >= 400:
        raise RuntimeError('Match page HTTP ' + str(response.status))
    # Map boxes contain played maps. Veto prose is deliberately not searched.
    maps = [x.strip() for x in await page.locator('.mapname').all_text_contents()]
    if not maps:
        raise RuntimeError('No played-map boxes; page must not be classified as no-demo')
    if 'dust2' not in {m.lower() for m in maps}:
        return {'status': 'not-dust2', 'maps': maps}
    button = page.locator('[data-demo-link]')
    href = await button.first.get_attribute('data-demo-link') if await button.count() else None
    if not href:
        anchor = page.locator('a[href*="/download/demo/"]')
        href = await anchor.first.get_attribute('href') if await anchor.count() else None
    if not href:
        return {'status': 'no-demo', 'maps': maps}
    endpoint = urljoin('https://www.hltv.org/', href)
    parsed = urlsplit(endpoint)
    if parsed.scheme != 'https' or parsed.hostname != 'www.hltv.org' or not re.fullmatch(r'/download/demo/\d+', parsed.path):
        raise RuntimeError('Unexpected demo endpoint')
    download_task = asyncio.create_task(page.wait_for_event('download', timeout=args.download_timeout * 1000))
    try:
        try:
            await page.goto(endpoint, wait_until='domcontentloaded', timeout=30000)
        except Exception as exc:
            if 'ERR_ABORTED' not in str(exc):
                raise
        if not download_task.done():
            # Navigation to an HTML challenge is not a download.
            await check_page(page)
        download = await download_task
    finally:
        if not download_task.done():
            download_task.cancel()
        await asyncio.gather(download_task, return_exceptions=True)
    archives = root / 'archives'
    archives.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=archives, suffix='.part')
    os.close(fd)
    part = Path(name)
    try:
        try:
            await asyncio.wait_for(download.save_as(str(part)), args.transfer_timeout)
        except asyncio.TimeoutError:
            await download.cancel()
            raise TimeoutError('Download transfer timed out')
        if await download.failure():
            raise RuntimeError('Browser reported a failed transfer')
        info = await asyncio.to_thread(verify_archive, part, unrar)
        target = archives / (row['match_id'] + '-' + info['sha256'][:12] + '.rar')
        if target.exists():
            await asyncio.to_thread(verify_archive, target, unrar, info['sha256'])
        else:
            os.rename(part, target)
        info.update(status='ok', path=str(target.relative_to(root)), maps=maps,
                    demo_endpoint=endpoint, download_url=download.url)
        info['team_files'] = await asyncio.to_thread(team_files, root, target, row['teams'], info['sha256'])
        return info
    finally:
        part.unlink(missing_ok=True)


async def execute(rows, root, manifest, unrar, args):
    journal = root / 'manifest.json'
    pending = []
    for row in rows:
        record = manifest.get(row['url'], {})
        source = await asyncio.to_thread(resumed_file, root, record, unrar)
        if not source:
            pending.append(row)
            continue
        record['team_files'] = await asyncio.to_thread(team_files, root, source, row['teams'], record['sha256'])
        record['teams'] = row['teams']
        write_json(journal, manifest)
        print('RESUMED ' + row['url'], flush=True)
    # Fully completed work does not need a browser or another HLTV request.
    if not pending:
        return 0
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        options = {'headless': False}
        if args.chromium:
            options['executable_path'] = args.chromium
        browser = await pw.chromium.launch(**options)
        try:
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            await page.goto('https://www.hltv.org/', wait_until='domcontentloaded', timeout=45000)
            await check_page(page)
            downloaded = 0
            for row in pending:
                key = row['url']
                record = manifest.get(key, {})
                if args.limit is not None and downloaded >= args.limit:
                    break
                if downloaded:
                    await asyncio.sleep(args.delay)
                downloaded += 1
                manifest[key] = {**record, **row, 'status': 'in-progress', 'updated_at': now()}
                write_json(journal, manifest)
                try:
                    result = await download_one(page, row, root, unrar, args)
                except SiteBlocked as exc:
                    result = {'status': 'blocked-or-timeout', 'error': str(exc)}
                    manifest[key].update(result, updated_at=now())
                    write_json(journal, manifest)
                    print('STOP ' + str(exc), flush=True)
                    return 3
                except ArchiveInvalid as exc:
                    result = {'status': 'corrupt', 'error': str(exc)}
                except Exception as exc:
                    # A challenge detected after a timeout also stops the entire batch.
                    try:
                        await check_page(page)
                    except SiteBlocked as blocked:
                        manifest[key].update(status='blocked-or-timeout', error=str(blocked), updated_at=now())
                        write_json(journal, manifest)
                        return 3
                    except Exception:
                        pass
                    result = {'status': 'error', 'error': type(exc).__name__ + ': ' + str(exc)}
                manifest[key].update(result, updated_at=now())
                write_json(journal, manifest)
                print(manifest[key]['status'].upper() + ' ' + key, flush=True)
            return 0 if all(manifest.get(r['url'], {}).get('status') == 'ok' for r in rows) else 1
        finally:
            await browser.close()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--limit', type=int, help='Maximum new attempts; resumed files do not count')
    p.add_argument('--delay', type=float, default=20)
    p.add_argument('--unrar', default=os.environ.get('UNRAR', 'unrar'))
    p.add_argument('--chromium', help='Optional existing Chromium executable')
    p.add_argument('--download-timeout', type=float, default=60)
    p.add_argument('--transfer-timeout', type=float, default=1800)
    args = p.parse_args(argv)
    if args.delay < 8 or (args.limit is not None and args.limit < 1) or min(args.download_timeout, args.transfer_timeout) <= 0:
        p.error('Delay must be >=8 seconds, limit >=1, and timeouts positive')
    try:
        rows, stats = plan_index(json.loads(Path(args.index).read_text(encoding='utf-8')))
        print(json.dumps({'plan': stats, 'matches': rows} if args.dry_run else {'plan': stats}, ensure_ascii=False, indent=2), flush=True)
        if args.dry_run:
            return 0
        if not rows:
            raise ValueError('Index is empty')
        root = Path(args.out).resolve()
        unrar = get_unrar(args.unrar)
        with output_lock(root):
            manifest = load_manifest(root / 'manifest.json')
            return asyncio.run(execute(rows, root, manifest, unrar, args))
    except SiteBlocked as exc:
        print('STOP ' + str(exc), flush=True)
        return 3
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
