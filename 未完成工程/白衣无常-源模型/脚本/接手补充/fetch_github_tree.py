# -*- coding: utf-8 -*-
"""Download a subtree from StarryNightSquad/Phantom-Blade-Zero into a local dir.

Usage:
  python fetch_github_tree.py <repo_subpath> <output_dir> [ref]

Uses the GitHub contents API for listing and raw.githubusercontent.com for files.
The raw URL is percent-encoded because repository paths contain Chinese chars.
Re-runs are safe: files whose size already matches are skipped.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OWNER = "StarryNightSquad"
REPO = "Phantom-Blade-Zero"
HEADERS = {
    "User-Agent": "WorkBuddy-tree-fetch",
    "Accept": "application/vnd.github+json",
}
WORKERS = 6


def api_list(subpath, ref):
    url = "https://api.github.com/repos/{}/{}/contents/{}?ref={}".format(
        OWNER, REPO, urllib.parse.quote(subpath, safe="/"), ref
    )
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def raw_url(repo_path, ref):
    return "https://raw.githubusercontent.com/{}/{}/{}/{}".format(
        OWNER, REPO, ref, urllib.parse.quote(repo_path, safe="/")
    )


def download(url, dest, expected_size):
    if dest.exists() and expected_size and dest.stat().st_size == expected_size:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # ASCII-safe URL (quote keeps already-encoded %XX sequences intact)
    safe_url = urllib.parse.quote(url, safe=":/%?=&#+,;@!$*()-_~.")
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(safe_url, headers={"User-Agent": "WorkBuddy-tree-fetch"})
            with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            actual = dest.stat().st_size
            if expected_size and actual != expected_size:
                raise IOError("size mismatch: got {} expected {}".format(actual, expected_size))
            return "ok"
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if dest.exists():
                dest.unlink()
            time.sleep(1 + attempt)
    raise RuntimeError("failed {} : {}".format(dest, last_err))


def walk(subpath, root, outroot, ref, files):
    entries = api_list(subpath, ref)
    if isinstance(entries, dict):
        entries = [entries]
    for ent in sorted(entries, key=lambda e: e["name"]):
        rel = Path(ent["path"]).relative_to(root)
        dest = outroot / rel
        if ent["type"] == "dir":
            walk(ent["path"], root, outroot, ref, files)
        else:
            files.append(
                {
                    "path": str(rel).replace("\\", "/"),
                    "repo_path": ent["path"],
                    "size": ent.get("size", 0),
                    "dest": dest,
                }
            )


def main():
    subpath = sys.argv[1].strip("/")
    outroot = Path(sys.argv[2])
    ref = sys.argv[3] if len(sys.argv) > 3 else "main"
    outroot.mkdir(parents=True, exist_ok=True)

    files = []
    walk(subpath, subpath, outroot, ref, files)
    total = sum(f["size"] for f in files)
    print("LIST {} files, {:.2f} MiB".format(len(files), total / 1048576), flush=True)

    ok = skipped = failed = 0
    errors = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(download, raw_url(f["repo_path"], ref), f["dest"], f["size"]): f
            for f in files
        }
        for fut in as_completed(futures):
            f = futures[fut]
            done += 1
            try:
                state = fut.result()
                if state == "skip":
                    skipped += 1
                else:
                    ok += 1
                print(
                    "[{:3d}/{:3d}] {:4s} {:>10} B  {}".format(
                        done, len(files), state.upper(), f["size"], f["path"]
                    ),
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                errors.append("{} : {}".format(f["path"], exc))
                print("[FAIL] {} : {}".format(f["path"], exc), flush=True)

    manifest = {
        "repo": "{}/{}".format(OWNER, REPO),
        "ref": ref,
        "subpath": subpath,
        "output_dir": str(outroot),
        "files": len(files),
        "bytes": total,
        "downloaded": ok,
        "skipped": skipped,
        "failed": failed,
        "errors": errors,
    }
    (outroot / "_download_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY " + json.dumps(manifest, ensure_ascii=False), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
