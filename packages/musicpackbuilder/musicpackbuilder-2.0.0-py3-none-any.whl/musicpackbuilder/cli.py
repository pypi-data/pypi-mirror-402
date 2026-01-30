from pathlib import Path
import shutil
import json
import argparse
import sys
import importlib.resources as res
import os

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import mutagen
from pydub import AudioSegment

print("CLI loaded successfully")

# ----- Configuration -----

if getattr(sys, 'frozen', False):
    os.chdir(Path(sys.executable).parent)

DISCS_LIST = [
    ("blocks", 345), ("precipice", 299), ("ward", 251), ("wait", 237),
    ("relic", 219), ("mall", 197), ("otherside", 195), ("strad", 188),
    ("cat", 185), ("chirp", 185), ("13", 178), ("5", 178),
    ("creator", 176), ("tears", 175), ("far", 174), ("stal", 150),
    ("pigstep", 148), ("lava_chicken", 135), ("mellohi", 96),
    ("creator_music_box", 73), ("11", 71)
]

MAX_DISCS_ALLOWED = 21
LANGUAGES = ["en_au", "en_us"]
DATA_PACKAGE = "musicpackbuilder.data"

def ffmpeg_path():
    base = Path(__file__).parent / "ffmpeg"
    return str(base / "ffmpeg.exe")

def ffprobe_path():
    base = Path(__file__).parent / "ffmpeg"
    return str(base / "ffprobe.exe")

AudioSegment.converter = ffmpeg_path()
AudioSegment.ffprobe = ffprobe_path()


# ----- Resource helpers -----
def load_default_lang_json(lang: str) -> dict:
    """Load a bundled default language JSON from package data."""
    try:
        with res.files(DATA_PACKAGE).joinpath(f"{lang}.json").open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def copy_default_pack_assets(target_dir: Path):
    """Copy bundled default pack.mcmeta and pack.png into target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for fname in ("pack.mcmeta", "pack.png"):
        try:
            src = res.files(DATA_PACKAGE).joinpath(fname)
            if src.is_file():
                shutil.copy(src, target_dir / fname)
        except FileNotFoundError:
            continue


# ----- Utility functions -----
def load_lang_jsons_with_fallback(languages, base_dir: Path) -> dict:
    """Load local JSONs if present, otherwise use bundled defaults."""
    data = {}
    for lang in languages:
        file = base_dir / f"{lang}.json"
        if file.exists():
            with file.open("r", encoding="utf-8") as fh:
                data[lang] = json.load(fh)
            print(f"✓ Loaded local {file.name}")
        else:
            data[lang] = load_default_lang_json(lang)
            print(f"⚠ {file.name} not found. Using bundled default.")
    return data


def get_song_metadata(audio_path: Path) -> str:
    """Read metadata or fall back to filename."""
    try:
        mp = MP3(str(audio_path), ID3=EasyID3)
        artist = mp.get("artist", [None])[0]
        title = mp.get("title", [None])[0]
        if artist and title:
            return f"{title} - {artist}"
        if title:
            return title
    except Exception:
        pass
    return audio_path.stem


def get_audio_duration_seconds(audio_path: Path) -> float:
    """Get duration using mutagen or fallback to pydub."""
    try:
        audio = mutagen.File(str(audio_path))
        if audio and getattr(audio, "info", None):
            return float(audio.info.length)
    except Exception:
        pass

    seg = AudioSegment.from_file(str(audio_path))
    return seg.duration_seconds


def process_audio_file(input_path: Path, output_path: Path, max_duration: int | None = None):
    """Convert to mono, optionally truncate, export as .ogg."""
    song = AudioSegment.from_file(str(input_path))
    song = song.set_channels(1)
    if max_duration and len(song) > max_duration * 1000:
        song = song[: max_duration * 1000]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    song.export(str(output_path), format="ogg")


def create_resource_pack_structure(base_name: str = "Custom Music") -> Path:
    """Create resource pack folder structure and copy bundled assets."""
    base = Path(base_name)
    (base / "assets" / "minecraft" / "sounds" / "records").mkdir(parents=True, exist_ok=True)
    (base / "assets" / "minecraft" / "lang").mkdir(parents=True, exist_ok=True)
    copy_default_pack_assets(base)
    return base


def save_json_to_resource_pack(json_data: dict, resource_pack_path: Path):
    """Write language JSONs into the resource pack."""
    for lang, data in json_data.items():
        lang_file = resource_pack_path / "assets" / "minecraft" / "lang" / f"{lang}.json"
        with lang_file.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        print(f"✓ Created {lang}.json in resource pack")



# ----- Main flow -----
def main(args: argparse.Namespace):
    cwd = Path.cwd()
    audio_dir = cwd / (args.audio_dir or "Audio Files")
    export_dir = cwd / (args.export_dir or "Export Files")
    export_dir.mkdir(parents=True, exist_ok=True)

    json_data = load_lang_jsons_with_fallback(LANGUAGES, cwd)

    if not audio_dir.exists():
        print(f"✗ Audio directory not found: {audio_dir}")
        sys.exit(1)

    audio_files = [p for p in sorted(audio_dir.iterdir()) if p.is_file()]
    if len(audio_files) > MAX_DISCS_ALLOWED:
        print(f"✗ Too many files! Max is {MAX_DISCS_ALLOWED}, found {len(audio_files)}")
        sys.exit(1)

    print(f"✓ Found {len(audio_files)} audio files")

    songs = []
    for p in audio_files:
        try:
            dur = round(get_audio_duration_seconds(p))
            songs.append((p, int(dur)))
        except Exception as e:
            print(f"⚠ Could not read duration for {p.name}: {e}")

    songs.sort(key=lambda item: item[1], reverse=True)
    pairs = list(zip(songs, DISCS_LIST[: len(songs)]))

    print("\n" + "=" * 50)
    print("Processing songs...")
    print("=" * 50)

    for (audio_path, duration), (disc_name, max_duration) in pairs:
        output_path = export_dir / f"{disc_name}.ogg"
        title = get_song_metadata(audio_path)

        print(f"\n Processing: {audio_path.name}")
        print(f"  Title: {title}")
        print(f"  Duration: {duration}s / Max: {max_duration}s")

        if duration > max_duration:
            print(f"  ⚠ Song is too long by {duration - max_duration} seconds")

            if args.auto_truncate:
                resp = "y"
                print(f"  Auto-truncating to {max_duration}s")
            elif args.skip_long_songs:
                resp = "n"
                print(f"  Auto-skipping long song")
            else:
                resp = input(f"  Cut to {max_duration}s? (y/n): ").strip().lower()

            if resp == "y":
                process_audio_file(audio_path, output_path, max_duration)
                print(f"  ✓ Truncated and exported as {disc_name}.ogg")
            else:
                print(f"  ✗ Skipping {audio_path.name}")
                continue
        else:
            process_audio_file(audio_path, output_path)
            print(f"  ✓ Exported as {disc_name}.ogg")

        for lang in LANGUAGES:
            json_data[lang][f"item.minecraft.music_disc_{disc_name}"] = title
            json_data[lang][f"item.minecraft.music_disc_{disc_name}.desc"] = title
            json_data[lang][f"jukebox_song.minecraft.{disc_name}"] = title

    print("\n" + "=" * 50)
    print("Building resource pack...")
    print("=" * 50)

    resource_pack_path = create_resource_pack_structure()

    for f in export_dir.iterdir():
        if f.is_file():
            dest = resource_pack_path / "assets" / "minecraft" / "sounds" / "records" / f.name
            shutil.copy(f, dest)

    save_json_to_resource_pack(json_data, resource_pack_path)

    zip_name = f"{resource_pack_path.name}.zip"
    if Path(zip_name).exists():
        Path(zip_name).unlink()

    shutil.make_archive(resource_pack_path.name, "zip", resource_pack_path)
    shutil.rmtree(resource_pack_path)

    print(f"\n Your resource pack is ready: {zip_name}")
    print("Place it in your Minecraft resource packs folder!")


# ----- CLI entry point -----
def run():
    parser = argparse.ArgumentParser(description="Create Minecraft music disc resource packs from audio files.")
    parser.add_argument("--audio-dir", help="Directory containing source audio files (default: 'Audio Files').")
    parser.add_argument("--export-dir", help="Directory to export processed .ogg files (default: 'Export Files').")
    parser.add_argument("--auto-truncate", action="store_true", help="Automatically truncate songs that are too long.")
    parser.add_argument("--skip-long-songs", action="store_true", help="Automatically skip songs that are too long.")
    args = parser.parse_args()
    main(args)

if __name__ == "__main__":
    run()
