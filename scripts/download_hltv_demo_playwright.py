#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BLOCK_TEXTS = (
    "you have been blocked",
    "sorry, you have been blocked",
)
CHALLENGE_TEXTS = (
    "just a moment",
    "verify you are human",
    "performing security verification",
)
NOT_FOUND_TEXTS = (
    "object not found",
    "404 not found",
    "no such key",
)


def page_text(page) -> str:
    try:
        title = page.title()
    except Exception:
        title = ""
    try:
        body = page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:
        body = ""
    return (title + "\n" + body).lower()


def dump_diagnostics(page, diag_dir: str) -> str:
    path = Path(diag_dir)
    path.mkdir(parents=True, exist_ok=True)

    try:
        title = page.title()
    except Exception as exc:
        title = f"<title unavailable: {exc}>"
    try:
        url = page.url
    except Exception:
        url = ""
    try:
        body = page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception as exc:
        body = f"<body unavailable: {exc}>"

    try:
        page.screenshot(path=str(path / "screenshot.png"), full_page=True)
    except Exception as exc:
        print(f"      (screenshot failed: {exc})")

    (path / "page.txt").write_text(
        f"title: {title}\nurl: {url}\n---\n{body[:2000]}\n",
        encoding="utf-8",
    )

    print(f"      diagnostics: {path}/")
    print(f"      title: {title}")
    print(f"      url: {url}")
    print(f"      body: {body[:160]!r}")
    return (title + "\n" + body).lower()


def classify(text: str) -> int:
    if any(x in text for x in BLOCK_TEXTS):
        print("RESULT=IP_BLOCKED")
        print("Cloudflare/IP block page detected. Retrying on the same runner IP is unlikely to help.")
        return 2
    if any(x in text for x in NOT_FOUND_TEXTS) or "\n404" in text:
        print("RESULT=LINK_INVALID")
        print("The demo endpoint/object appears to be missing or expired.")
        return 4
    if any(x in text for x in CHALLENGE_TEXTS):
        print("RESULT=CF_CHALLENGE")
        print("Cloudflare challenge was not cleared automatically.")
        return 3
    print("RESULT=UNKNOWN_FAILURE")
    return 1


def download_demo(url: str, out_path: str, diag_dir: str, wait_ms: int) -> int:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            accept_downloads=True,
            locale="en-US",
        )
        page = ctx.new_page()

        print("[1/2] Open HLTV main site and establish browser session...")
        try:
            response = page.goto(
                "https://www.hltv.org/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            if response is not None:
                print(f"      main status: {response.status}")
        except Exception as exc:
            print(f"      main navigation exception: {type(exc).__name__}: {exc}")

        page.wait_for_timeout(wait_ms)
        print(f"      main title: {page.title()!r}")
        initial_text = page_text(page)
        if any(x in initial_text for x in BLOCK_TEXTS):
            text = dump_diagnostics(page, diag_dir)
            browser.close()
            return classify(text)

        print("[2/2] Navigate to demo endpoint/direct URL and wait for browser download...")
        print(f"      target: {url}")
        try:
            with page.expect_download(timeout=60000) as dl_info:
                try:
                    page.goto(url, wait_until="commit", timeout=60000)
                except Exception as exc:
                    # Download navigations commonly abort the document navigation.
                    print(f"      navigation ended with: {type(exc).__name__}: {exc}")
            download = dl_info.value
        except PlaywrightTimeoutError:
            print("      no download event before timeout")
            text = dump_diagnostics(page, diag_dir)
            browser.close()
            return classify(text)
        except Exception as exc:
            print(f"      download wait failed: {type(exc).__name__}: {exc}")
            text = dump_diagnostics(page, diag_dir)
            browser.close()
            return classify(text)

        print(f"      suggested filename: {download.suggested_filename}")
        failure = download.failure()
        if failure:
            print(f"      browser reported download failure: {failure}")
            text = dump_diagnostics(page, diag_dir)
            browser.close()
            return classify(text)

        download.save_as(out_path)
        browser.close()

    size = os.path.getsize(out_path)
    with open(out_path, "rb") as f:
        sig = f.read(8)

    print(f"      saved: {out_path}")
    print(f"      size: {size / 1024 / 1024:.2f} MiB")
    print(f"      first bytes: {sig!r}")

    if not sig.startswith(b"Rar!"):
        print("RESULT=BAD_FILE")
        print("Downloaded content does not have a RAR signature.")
        return 1

    print("RESULT=SUCCESS")
    print("RAR signature valid.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("out", nargs="?", default="demo.rar")
    parser.add_argument("--diag-dir", default="diagnostics")
    parser.add_argument("--wait-ms", type=int, default=8000)
    args = parser.parse_args()
    return download_demo(args.url, args.out, args.diag_dir, args.wait_ms)


if __name__ == "__main__":
    sys.exit(main())
