import re
import sys
import time
import zipfile
import pathlib
import xml.etree.ElementTree as ET

import requests

# --- konfiguracja 
BUCKET = "https://s3.amazonaws.com/tripdata"
YEARS = {"2021", "2022", "2023", "2024", "2025"}

ROOT = pathlib.Path(__file__).resolve().parents[1]
ZIP_DIR = ROOT / "data" / "zips"
RAW_DIR = ROOT / "data" / "raw"
DONE_FILE = ROOT / "data" / "done.txt"

ZIP_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


# --- listing bucketu S3 -----------------------------------------------------
def list_keys():
    """Zwraca listę (nazwa_pliku, rozmiar) z całego bucketu (XML z paginacją)."""
    keys, token = [], None
    while True:
        params = {"list-type": "2"}
        if token:
            params["continuation-token"] = token
        r = requests.get(BUCKET, params=params, timeout=60)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {"s": root.tag.split("}")[0].strip("{")}
        for c in root.findall("s:Contents", ns):
            keys.append((c.find("s:Key", ns).text, int(c.find("s:Size", ns).text)))
        if root.find("s:IsTruncated", ns).text == "true":
            token = root.find("s:NextContinuationToken", ns).text
        else:
            return keys


def wanted(key):
    """Tylko Nowy Jork (bez JC- = Jersey City), tylko ZIP, tylko wybrane lata."""
    m = re.match(r"(\d{4})", key)
    return (
        key.endswith(".zip")
        and not key.startswith("JC-")
        and "citibike-tripdata" in key
        and m is not None
        and m.group(1) in YEARS
    )


# --- ukończone pliki
def load_done():
    if DONE_FILE.exists():
        return set(DONE_FILE.read_text(encoding="utf-8").split())
    return set()


def mark_done(key):
    with open(DONE_FILE, "a", encoding="utf-8") as f:
        f.write(key + "\n")


# --- pobieranie
def download(key, size):
    dest = ZIP_DIR / key.replace("/", "_")
    part = dest.with_suffix(".part")

    if dest.exists() and dest.stat().st_size == size:
        print(f"[zip już jest] {key}")
        return dest

    for attempt in range(1, 4):
        try:
            with requests.get(f"{BUCKET}/{key}", stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(part, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if part.stat().st_size == size:
                part.replace(dest)
                print(f"[pobrano] {key}")
                return dest
            print(f"[zły rozmiar, próba {attempt}] {key}")
        except requests.RequestException as e:
            print(f"[błąd, próba {attempt}] {key}: {e}")
        time.sleep(5 * attempt)

    raise RuntimeError(f"Nie udało się pobrać {key}")


# --- rozpakowywanie
def extract(zip_path, out_dir):
    """Rozpakowuje ZIP. Zagnieżdżone ZIP-y rozpakowuje rekurencyjnie.
    Pomija śmieci z macOS (__MACOSX, ._pliki)."""
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.startswith("__MACOSX") or name.endswith("/") or "/._" in name:
                continue

            base = pathlib.Path(name).name
            if base.startswith("._"):
                continue

            if name.lower().endswith(".zip"):
                tmp_dir = out_dir / "_tmp"
                tmp_dir.mkdir(parents=True, exist_ok=True)
                inner = tmp_dir / base
                inner.write_bytes(z.read(name))
                extract(inner, out_dir)
                inner.unlink()

            elif name.lower().endswith(".csv"):
                target = out_dir / base
                if target.exists():
                    continue
                tmp_target = target.with_suffix(".csv.part")
                with z.open(name) as src, open(tmp_target, "wb") as dst:
                    while chunk := src.read(1 << 20):
                        dst.write(chunk)
                tmp_target.replace(target)   # plik pojawia się dopiero gdy jest kompletny

    tmp_dir = out_dir / "_tmp"
    if tmp_dir.exists() and not any(tmp_dir.iterdir()):
        tmp_dir.rmdir()


# --- main
if __name__ == "__main__":
    items = [(k, s) for k, s in list_keys() if wanted(k)]
    done = load_done()
    todo = [(k, s) for k, s in items if k not in done]

    total_all = sum(s for _, s in items) / 1e9
    total_todo = sum(s for _, s in todo) / 1e9
    print(f"Plików łącznie: {len(items)} (~{total_all:.1f} GB w ZIP)")
    print(f"Do pobrania:    {len(todo)} (~{total_todo:.1f} GB w ZIP)")
    for k, s in todo:
        print(f"   {k}  ({s / 1e6:.0f} MB)")

    if not todo:
        print("Wszystko już pobrane.")
        sys.exit()

    if input("Pobierać? [t/N] ").strip().lower() != "t":
        sys.exit()

    for k, s in todo:
        zip_path = download(k, s)
        extract(zip_path, RAW_DIR)
        zip_path.unlink()
        mark_done(k)
        print(f"[gotowe] {k}")

    print("Koniec. CSV-ki są w:", RAW_DIR)