# -*- coding: utf-8 -*-
"""Deploy UE4SS into Wuchang: Fallen Feathers so DumpUSMAP() can generate a .usmap.

NOT executed automatically. Nothing is written to the game folder unless --apply:
  python deploy_ue4ss_wuchang.py            # dry run (default)
  python deploy_ue4ss_wuchang.py --apply    # deploy
  python deploy_ue4ss_wuchang.py --undo     # restore game folder, keep generated usmap

Official basis (UE4SS docs, all verified 2026-11-10):
  * Installation guide: root directory = working directory = game executable directory
    for the basic/developer install; extract the zDEV zip content straight into
    <Game>/Binaries/Win64/. (A `ue4ss/` subfolder is only one of the supported
    override layouts, and is NOT what the official zip uses.)
  * Dumpers doc: ".usmap Dumper ... keybind ... by default Ctrl + Numpad 6",
    also available in GUI Console > Dumpers tab as "Generate .usmap".
  * Lua API doc: DumpUSMAP() generates Mappings.usmap; default includes
    Blueprint-generated types.
  * Changelog v3.0.1 issue #1: "If you have the GUI console enabled and visible,
    and on launch the window is blank/white, go into UE4SS-settings.ini and set
    GraphicsAPI = dx11." Issue #2: bUseUObjectArrayCache=false only for startup crashes.
  * GUI Dumpers tab requires GuiConsoleEnabled=1 and GuiConsoleVisible=1, but the
    Ctrl+Numpad 6 hotkey comes from the Keybinds Lua mod and does NOT need the GUI.

  >>> MEASURED 2026-11-10 22:19 (first real launch) <<<
  This game's OpenGL GUI window renders as a blank white rectangle and blocks the
  view; UE4SS itself is 100% healthy (UE4SS.log: Event loop start, all Lua mods
  incl. Keybinds started, zero errors / zero missing AOB). Per the user's call
  ("just turn it off"), the default deploy now DISABLES the GUI console
  (GuiConsoleEnabled=0 / GuiConsoleVisible=0) and dumps via Ctrl + Numpad 6.
  GraphicsAPI stays at the official opengl default because no GUI is drawn.
  Use --gui only if the GUI Dumpers tab is actually wanted; it then applies the
  official dx11 fix as well.

Engine version evidence: the game's own executable contains the build path
  D:\\WorkDir\\Shipping_UE5.1.1A\\Engine\\...  -> UE 5.1.1 -> override 5 / 1.

The two xinput1_3.dll files in the game are genuine Microsoft DirectX binaries
(verified via file version info), NOT the obsolete UE4SS 2.5.2 proxy. Keep them.
"""
import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

TOOLS = Path(r"E:/steam/steamapps/common/PBZ/workbuddy/tools")
WC = Path(r"E:/steam/steamapps/common/Wuchang Fallen Feathers/Project_Plague/Binaries/Win64")
PBZ_UE4SS = Path(r"E:/steam/steamapps/common/PBZ/platform/steam/ue4ss")
PBZ_PROXY = Path(r"E:/steam/steamapps/common/PBZ/platform/steam/dwmapi.dll")
ZDEV = TOOLS / "third_party/UE4SS/extracted"
MANIFEST = TOOLS / "ue4ss_wuchang_deploy.json"
USMAP_OUT = Path(r"E:/steam/steamapps/common/PBZ/workbuddy/github_wip/usmap")

# Top-level entries of the official zDEV zip that constitute a working install.
# UE4SS.pdb (72 MB), README.md, Changelog.md, API.txt are intentionally omitted.
FLAT_ITEMS = [
    "dwmapi.dll",
    "UE4SS.dll",
    "UE4SS-settings.ini",
    "Mods",
    "UE4SS_Signatures",
    "MapGenBP",
    "MemberVarLayoutTemplates",
    "VTableLayoutTemplates",
    "CustomGameConfigs",
]

# Only documented, necessary ini changes. Everything else keeps official defaults.
# Default: GUI console OFF (measured blank/white OpenGL window on this game).
BASE_INI_CHANGES = {
    "[EngineVersionOverride]": {"MajorVersion": "5", "MinorVersion": "1"},
    "[Debug]": {"GuiConsoleEnabled": "0", "GuiConsoleVisible": "0"},
}
# --gui: official Changelog issue #1 workaround applied together with the GUI.
GUI_INI_CHANGES = {
    "[EngineVersionOverride]": {"MajorVersion": "5", "MinorVersion": "1"},
    "[Debug]": {"GuiConsoleEnabled": "1", "GuiConsoleVisible": "1",
                "GraphicsAPI": "dx11"},
}

def collect(source: str):
    """Return (list of (relative_path, absolute_source_file), label)."""
    if source == "official":
        if not (ZDEV / "UE4SS.dll").exists():
            raise SystemExit("official zDEV release not extracted: " + str(ZDEV))
    elif source == "pbz":
        # Contingency if the official 3.0.1 DLL cannot hook this game: use the
        # newer PBZ-proven binaries ONLY, and keep the clean official Lua/Mods
        # environment. PBZ's own Mods/ and UE4SS_Signatures/*.lua are PBZ-specific
        # and must never be copied into another game.
        if not (PBZ_UE4SS / "UE4SS.dll").exists() or not PBZ_PROXY.exists():
            raise SystemExit("PBZ UE4SS not found: " + str(PBZ_UE4SS))
        official, _ = collect("official")
        skip = {"UE4SS.dll", "dwmapi.dll"}
        out = [(r, s) for r, s in official if r.parts[0] not in skip]
        out.append((Path("UE4SS.dll"), PBZ_UE4SS / "UE4SS.dll"))
        out.append((Path("dwmapi.dll"), PBZ_PROXY))
        return out, "PBZ UE4SS.dll/proxy + official zDEV clean Mods & config"
    else:
        raise SystemExit("unknown source: " + source)

    src, label = ZDEV, "official zDEV-UE4SS_v3.0.1 (2024-02-14)"
    out = []
    for name in FLAT_ITEMS:
        p = src / name
        if not p.exists():
            continue
        if p.is_file():
            out.append((Path(name), p))
        else:
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    out.append((Path(name) / f.relative_to(p), f))
    return out, label


def patch_ini(path: Path, changes: dict):
    """Section-aware patch: only the keys in `changes` are touched."""
    raw = path.read_text(encoding="utf-8-sig", errors="ignore")
    lines = raw.splitlines()
    out, section, seen = [], "", set()
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s
            out.append(line)
            continue
        key = s.split("=", 1)[0].strip() if "=" in s and not s.startswith((";", "#")) else ""
        target = changes.get(section, {})
        if key in target:
            out.append(f"{key} = {target[key]}")
            seen.add((section, key))
        else:
            out.append(line)
    for sec, kv in changes.items():
        missing = [(k, v) for k, v in kv.items() if (sec, k) not in seen]
        if missing:
            out += ["", sec] + [f"{k} = {v}" for k, v in missing]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def relpaths(items):
    return [str(r).replace("\\", "/") for r, _ in items]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually deploy (default: dry run)")
    ap.add_argument("--undo", action="store_true", help="restore game folder from backup")
    ap.add_argument("--source", choices=("official", "pbz"), default="official")
    ap.add_argument("--gui", action="store_true",
                    help="enable the GUI console + apply the official dx11 blank-window fix")
    args = ap.parse_args()

    if args.undo:
        return undo()

    changes = GUI_INI_CHANGES if args.gui else BASE_INI_CHANGES

    if not WC.exists():
        raise SystemExit("target dir missing: " + str(WC))
    if MANIFEST.exists():
        raise SystemExit("already deployed (manifest exists). Run --undo first: " + str(MANIFEST))

    items, label = collect(args.source)
    total = sum(s.stat().st_size for _, s in items)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = WC / ("_ue4ss_backup_" + stamp)
    existing = [r for r, _ in items if (WC / r).exists()]

    print("SOURCE      :", label)
    print("TARGET      :", WC, "(official flat layout: root == working dir)")
    print("FILES       :", len(items), "/", f"{total:,}", "bytes")
    print("WOULD PATCH : UE4SS-settings.ini ->", changes)
    print("GUI CONSOLE :", "ON (+dx11, official Changelog issue #1)" if args.gui
          else "OFF (measured blank/white OpenGL window; dump via Ctrl+Numpad 6)")
    kept = "GraphicsAPI=opengl, ConsoleEnabled=1" if not args.gui else "ConsoleEnabled=1"
    print("OFFICIAL DEFAULTS KEPT:", kept + ", bUseUObjectArrayCache=true, mods.txt as shipped")
    print("EXISTING (will be backed up):", len(existing))
    for r in existing[:12]:
        print("   ", r)
    if len(existing) > 12:
        print("    ...")
    print("BACKUP DIR  :", backup_root)
    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply after user confirmation.")
        return 0

    for r, s in items:
        dst = WC / r
        if dst.exists():
            bak = backup_root / r
            bak.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(bak))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, dst)

    ini = WC / "UE4SS-settings.ini"
    if ini.exists():
        patch_ini(ini, changes)

    MANIFEST.write_text(json.dumps({
        "stamp": stamp,
        "source": args.source,
        "gui": args.gui,
        "ini_changes": changes,
        "label": label,
        "backup_root": str(backup_root),
        "created": relpaths(items),
        "backed_up": [str(r).replace("\\", "/") for r in existing],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nDEPLOYED. Next steps (user must launch the game):")
    print("  1. Start Wuchang: Fallen Feathers via Steam.")
    print("     Verify UE4SS.log appears in", WC, "and contains 'Event loop start'.")
    if args.gui:
        print("  2. GUI Console > Dumpers tab > 'Generate .usmap' (or Ctrl + Numpad 6).")
        print("     GraphicsAPI=dx11 applied per official Changelog issue #1.")
    else:
        print("  2. Press Ctrl + Numpad 6 to dump .usmap. NO GUI window is drawn")
        print("     (this game's OpenGL GUI renders blank/white; the hotkey comes from")
        print("     the Keybinds Lua mod and does not need the GUI).")
        print("     Fallback: type DumpUSMAP() in the UE4SS console window.")
    print("  3. Output Mappings.usmap (or <Game>-<UEver>-<sha>.usmap) lands in", WC)
    print("  4. Run: python deploy_ue4ss_wuchang.py --undo")
    print("     --undo copies any *.usmap / UE4SS.log out to", USMAP_OUT, "before cleanup.")
    print("\nTroubleshooting (official v3.0.1 Changelog, only if symptoms appear):")
    print("  * crash on startup        -> set bUseUObjectArrayCache = false")
    print("  * 'missing AOB' in log    -> see docs.ue4ss.com/dev/guides/fixing-compatibility-problems.html")
    print("  * Keep xinput1_3.dll (genuine Microsoft DirectX, verified).")
    return 0


def undo():
    if not MANIFEST.exists():
        raise SystemExit("no deployment manifest: " + str(MANIFEST))
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stamp = m["stamp"]
    backup_root = Path(m["backup_root"])

    # Preserve dumper output / log before removing anything.
    saved = []
    for p in sorted(WC.rglob("*.usmap")) + sorted(WC.glob("UE4SS.log")):
        if not p.is_file():
            continue
        dst = USMAP_OUT / stamp / p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        saved.append(str(dst))

    for r in m.get("created", []):
        p = WC / r
        if p.is_file():
            p.unlink()
    # remove empty directories created by the flat copy (deepest first)
    for d in sorted({(WC / r).parent for r in m.get("created", [])},
                    key=lambda x: len(x.parts), reverse=True):
        try:
            if d != WC and d.exists() and not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass

    for r in m.get("backed_up", []):
        src, dst = backup_root / r, WC / r
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    if backup_root.exists() and not any(backup_root.rglob("*")):
        backup_root.rmdir()

    MANIFEST.unlink()
    print("UNDONE. Restored", len(m.get("backed_up", [])), "original file(s).")
    print("Preserved dumper output:", saved if saved else "(none found)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
