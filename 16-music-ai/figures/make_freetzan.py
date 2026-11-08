"""Precompute clip-level features of FreeTZAN for the genre classification example.

FreeTZAN (https://huggingface.co/datasets/gclef-cmu/freetzan) is 1,200 30-second clips
from the Free Music Archive in 10 genres, with train / valid / test splits of 1000 / 100 /
100 that share no artists. Each clip has its own Creative Commons (or CC0 / PDM) license,
recorded in the dataset's metadata.csv. This file is *not* student-facing.

The audio (about 1 GB) is downloaded to ~/.cache/freetzan. The chapter can't ship the
audio, so this script reduces each clip to three small feature vectors, saved together
in ../assets/freetzan-features.npz (float16):

- `waveform`: one second from the middle of the clip, resampled to 1 kHz (1000 values).
- `spectrum_<n>`: the log-amplitude spectrogram (STFT with frame length n and hop n / 4),
  averaged over time, for n in N_FFTS (n / 2 + 1 values each).
- `mfcc`: 20 MFCCs, averaged over time.

It also saves a few short training clips (licenses allowing derivatives) as previews.

Run with the project virtualenv (needs librosa and requests):
    PYTHONPATH=../../../pyquist python make_freetzan.py
"""

import csv
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import librosa
import numpy as np
import requests

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
CACHE = Path.home() / ".cache" / "freetzan"
BASE = "https://huggingface.co/datasets/gclef-cmu/freetzan/resolve/main/"

SR = 22050
N_FFTS = [256, 512, 1024, 2048]
GENRES = ["ambient", "classical", "electronic", "experimental", "folk", "hiphop", "jazz",
          "pop", "punk", "rock"]
PREVIEW_GENRES = ["classical", "hiphop", "punk"]   # one preview clip each
PREVIEW_SECONDS = 10.0


def download(relative_path: str) -> Path:
    path = CACHE / relative_path
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(BASE + relative_path, timeout=60)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path


def load_metadata() -> list[dict]:
    with open(download("metadata.csv"), newline="") as f:
        return list(csv.DictReader(f))


def features(path: Path) -> dict[str, np.ndarray]:
    y, _ = librosa.load(path, sr=SR, mono=True)
    middle = len(y) // 2
    second = y[middle - SR // 2:middle + SR // 2]
    out = {"waveform": librosa.resample(second, orig_sr=SR, target_sr=1000)[:1000]}
    for n in N_FFTS:
        S = np.abs(librosa.stft(y, n_fft=n, hop_length=n // 4))
        out[f"spectrum_{n}"] = np.log(S + 1e-6).mean(axis=1)
    out["mfcc"] = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=20).mean(axis=1)
    return out


def write_preview(row: dict, name: str) -> None:
    y, _ = librosa.load(download(row["path"]), sr=44100, mono=False)
    y = np.atleast_2d(y).T[: int(PREVIEW_SECONDS * 44100)]
    fade = int(0.5 * 44100)
    y[-fade:] *= np.linspace(1, 0, fade)[:, None]
    y *= 10 ** (-6 / 20) / np.abs(y).max()
    import pyquist as pq
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "x.wav"
        pq.Audio(y, sample_rate=44100).write(str(wav), subtype="PCM_16")
        subprocess.run(["lame", "--quiet", "--cbr", "-b", "128", str(wav),
                        str(ASSETS / name)], check=True)
    print(f"wrote {name}: {row['track_title']} by {row['artist_name']} ({row['license']})")


def main() -> None:
    rows = load_metadata()
    print(f"{len(rows)} clips")
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda row: download(row["path"]), rows))
    with ThreadPoolExecutor(8) as pool:
        feats = list(pool.map(lambda row: features(CACHE / row["path"]), rows))
    arrays = {key: np.stack([f[key] for f in feats]).astype(np.float16) for key in feats[0]}
    arrays["split"] = np.array([row["split"] for row in rows])
    arrays["genre"] = np.array([GENRES.index(row["genre"]) for row in rows])
    arrays["genres"] = np.array(GENRES)
    np.savez_compressed(ASSETS / "freetzan-features.npz", **arrays)
    print("wrote freetzan-features.npz", {k: v.shape for k, v in arrays.items()})
    for genre in PREVIEW_GENRES:
        row = next(r for r in rows if r["split"] == "train" and r["genre"] == genre
                   and r["derivatives_ok"] == "True" and r["commercial_ok"] == "True")
        write_preview(row, f"audio-freetzan-{genre}.mp3")


if __name__ == "__main__":
    main()
