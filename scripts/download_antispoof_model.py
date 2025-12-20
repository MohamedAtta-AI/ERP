"""
Download Minivision Silent-Face-Anti-Spoofing deployment models (Caffe).

Why Caffe here?
- OpenCV DNN loads Caffe models directly
- no PyTorch runtime needed
- matches how the upstream repo runs inference

Downloads into:
  <repo-root>/models/
    - 2.7_80x80_MiniFASNetV2.prototxt
    - 2.7_80x80_MiniFASNetV2.caffemodel
    - 4_0_0_80x80_MiniFASNetV1SE.prototxt
    - 4_0_0_80x80_MiniFASNetV1SE.caffemodel

Upstream repo:
  https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/tree/master
"""

from pathlib import Path
from urllib.request import urlopen, Request


BASE = (
    "https://raw.githubusercontent.com/"
    "minivision-ai/Silent-Face-Anti-Spoofing/master/resources/anti_spoof_models/"
)

FILES = [
    "2.7_80x80_MiniFASNetV2.prototxt",
    "2.7_80x80_MiniFASNetV2.caffemodel",
    "4_0_0_80x80_MiniFASNetV1SE.prototxt",
    "4_0_0_80x80_MiniFASNetV1SE.caffemodel",
]


def _download(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "ERP-Downloader/1.0"})
    with urlopen(req) as r:
        return r.read()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    models_dir = repo_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    for name in FILES:
        url = BASE + name
        out_path = models_dir / name
        print(f"Downloading: {url}")
        data = _download(url)
        if len(data) < 1024:
            raise RuntimeError(f"Downloaded file looks too small ({len(data)} bytes): {name}")
        out_path.write_bytes(data)
        print(f"Saved: {out_path} ({out_path.stat().st_size} bytes)")

    print("Done.")


if __name__ == "__main__":
    main()


