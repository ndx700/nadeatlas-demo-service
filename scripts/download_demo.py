#!/usr/bin/env python3
"""Browser-only HLTV downloader. Linux: xvfb-run -a python3 scripts/download_demo.py URL [output.rar].
Exit: 0 saved RAR, 1 other error, 2 block page, 3 challenge, 4 missing object.
No CAPTCHA solving or alternate HTTP download client is used.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


def classify(text, status=None):
    text = text.lower()
    if "you have been blocked" in text or "sorry, you have been blocked" in text:
        return 2
    if "just a moment" in text or "verify you are human" in text or "checking your browser" in text:
        return 3
    if status in (404, 410) or "object not found" in text or "nosuchkey" in text:
        return 4
    return 1


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url")
    p.add_argument("output", nargs="?", default="demo.rar")
    p.add_argument("--diag-dir", default="diagnostics")
    p.add_argument("--timeout", type=float, default=300, help="Download-event wait in seconds")
    p.add_argument("--transfer-timeout", type=float, default=1800)
    p.add_argument("--session-wait", type=float, default=10)
    return p


async def snapshot(page, folder, name):
    title, body, url = "", "", ""
    if page is not None:
        url = page.url
        try:
            title = await page.title()
            body = await page.locator("body").inner_text(timeout=3000)
        except Exception:
            pass
        try:
            await page.screenshot(path=str(folder / (name + ".png")), timeout=10000)
        except Exception:
            pass
    (folder / (name + ".txt")).write_text(f"title: {title}\nurl: {url}\n---\n{body[:500]}\n", encoding="utf-8")
    return title + "\n" + body


def validate(path):
    with path.open("rb") as f:
        sig = f.read(8)
    if not (sig.startswith(b"Rar!\x1a\x07\x00") or sig == b"Rar!\x1a\x07\x01\x00"):
        raise ValueError(f"Not a RAR archive: {sig!r}")
    if path.stat().st_size < 20:
        raise ValueError("Truncated RAR header")
    with path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    return {"size_bytes": path.stat().st_size, "sha256": digest, "validation": "RAR signature only; run 7z t for archive integrity"}


async def run(args):
    folder = Path(args.diag_dir)
    folder.mkdir(parents=True, exist_ok=True)
    result = {"exit_code": 1, "url": args.url, "phase": "startup"}
    page = browser = tmp = None
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            try:
                browser = await pw.chromium.launch(headless=False)
                ctx = await browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 800})
                page = await ctx.new_page()
                result["phase"] = "session"
                print("[1/2] Browser session on hltv.org", flush=True)
                try:
                    await page.goto("https://www.hltv.org/", wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(args.session_wait * 1000)
                except Exception as exc:
                    result["session_error"] = str(exc)
                await snapshot(page, folder, "session")
                # A main-site challenge does not establish whether a direct CDN URL works.
                result["phase"] = "download_event"
                result["document_responses"] = []
                def response_seen(response):
                    if response.request.is_navigation_request() and response.frame == page.main_frame:
                        result["document_responses"].append({"url": response.url, "status": response.status})
                page.on("response", response_seen)
                print("[2/2] Navigate to demo in Chromium", flush=True)
                try:
                    async with page.expect_download(timeout=args.timeout * 1000) as event:
                        try:
                            await page.goto(args.url, wait_until="domcontentloaded", timeout=min(60000, args.timeout * 1000))
                        except Exception as exc:
                            # Download navigation may abort; keep the evidence for other errors.
                            result["navigation_error"] = str(exc)
                    download = await event.value
                except Exception as exc:
                    result["error"] = str(exc)
                    text = await snapshot(page, folder, "screenshot")
                    responses = result["document_responses"]
                    result["exit_code"] = classify(text, responses[-1]["status"] if responses else None)
                    return result
                result["phase"] = "transfer"
                out = Path(args.output)
                out.parent.mkdir(parents=True, exist_ok=True)
                if out.exists():
                    raise FileExistsError(f"Refusing to replace existing file: {out}")
                fd, tmp_name = tempfile.mkstemp(prefix=out.name + ".", suffix=".part", dir=out.parent)
                os.close(fd)
                tmp = Path(tmp_name)
                try:
                    await asyncio.wait_for(download.save_as(str(tmp)), timeout=args.transfer_timeout)
                except asyncio.TimeoutError:
                    await download.cancel()
                    raise TimeoutError("Download transfer exceeded --transfer-timeout")
                failure = await download.failure()
                if failure:
                    raise RuntimeError(failure)
                result.update(validate(tmp))
                # Publish only a validated completed file, without clobbering existing data.
                os.link(tmp, out)
                tmp.unlink()
                result.update(exit_code=0, phase="saved", output=str(out), download_url=download.url)
                return result
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
                await snapshot(page, folder, "screenshot")
            finally:
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        pass
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if tmp and tmp.exists():
            tmp.unlink()
        (folder / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


if __name__ == "__main__":
    p = parser()
    args = p.parse_args()
    parsed = urlsplit(args.url)
    if parsed.scheme != "https" or parsed.hostname not in {"www.hltv.org", "hltv.org", "r2-demos.hltv.org"}:
        p.error("Use an HTTPS HLTV download endpoint or r2-demos URL")
    if min(args.timeout, args.transfer_timeout) <= 0 or args.session_wait < 0:
        p.error("Timeouts must be positive; session wait must be nonnegative")
    raise SystemExit(asyncio.run(run(args))["exit_code"])
