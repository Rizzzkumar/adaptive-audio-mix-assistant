import csv
import os
import random
import argparse
from pydub import AudioSegment, effects
from mix_engine import (
    trim_silence_tail,
    apply_reverb,
    combine_and_normalize,
    duck_music_during_dialogue
)
from render import apply_auto_mix

def parse_args():
    parser = argparse.ArgumentParser(description="Adaptive Audio Mix Assistant")
    parser.add_argument("--mode", type=str, default="cinematic", help="Scene mode: cinematic, podcast, trailer, interview, custom")
    parser.add_argument("--features", type=str, default="audio_features.csv", help="Path to feature CSV file")
    parser.add_argument("--outdir", type=str, default="outputs", help="Output directory for mix and logs")
    parser.add_argument("--reverb", type=str, choices=["on", "off"], help="Force reverb ON or OFF")
    parser.add_argument("--preview", action="store_true", help="Preview mode: skips exporting files")
    parser.add_argument("--ducking", type=str, choices=["on", "off"], help="Enable or disable speech-aware music ducking")
    return parser.parse_args()

def get_mode_settings(mode):
    default = {
        "gain": {"dialogue": 4, "music": -3, "sfx": -2},
        "fade_duration": 1000,
        "reverb": True,
        "music_intro": 2000,
        "music_outro": 3000
    }

    presets = {
        "cinematic": {
            "gain": {"dialogue": 3, "music": -5, "sfx": -3},
            "fade_duration": 1500,
            "reverb": True,
            "music_intro": 2000,
            "music_outro": 3000
        },
        "trailer": {
            "gain": {"dialogue": 5, "music": 0, "sfx": -1},
            "fade_duration": 1200,
            "reverb": True,
            "music_intro": 1500,
            "music_outro": 2500
        },
        "podcast": {
            "gain": {"dialogue": 6, "music": -6, "sfx": -6},
            "fade_duration": 800,
            "reverb": False,
            "music_intro": 1000,
            "music_outro": 1000
        },
        "interview": {
            "gain": {"dialogue": 5, "music": -10, "sfx": -10},
            "fade_duration": 500,
            "reverb": False,
            "music_intro": 0,
            "music_outro": 0
        },
        "custom": default
    }

    return presets.get(mode.lower(), default)


def load_features(csv_file):
    features = []
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["rms"] = float(row["rms"])
                row["zero_crossing_rate"] = float(row["zero_crossing_rate"])
                row["tempo_bpm"] = float(row["tempo_bpm"])
                row["spectral_centroid"] = float(row["spectral_centroid"])
                row["duration_sec"] = float(row["duration_sec"])
                row["sample_rate"] = int(row["sample_rate"])
                row["filename"] = row["filename"]
                features.append(row)
            except Exception as e:
                print(f"⚠️ Skipping row due to error: {e}")
    return features

def categorize(features):
    dialogue, music, sfx = [], [], []
    for f in features:
        name = f["filename"].lower()
        if "dialogue" in name:
            dialogue.append(f)
        elif "music" in name:
            music.append(f)
        elif "sfx" in name or "fx" in name:
            sfx.append(f)
    return dialogue, music, sfx

def suggest_mixes(dialogue, music, sfx, outdir, preview=False):
    print("\n🎧 Mixing Suggestions:\n")
    suggestions = []

    if not dialogue or not music:
        suggestions.append("⚠️ Need at least one dialogue and one music clip.")
        if not preview:
            save_suggestions_to_file(suggestions, outdir)
        return

    avg_d_rms = sum(d["rms"] for d in dialogue) / len(dialogue)
    avg_m_rms = sum(m["rms"] for m in music) / len(music)
    if avg_d_rms < avg_m_rms - 500:
        suggestions.append("🔉 Dialogue is too quiet vs music.")

    if sfx:
        avg_d_cent = sum(d["spectral_centroid"] for d in dialogue) / len(dialogue)
        avg_s_cent = sum(s["spectral_centroid"] for s in sfx) / len(sfx)
        if abs(avg_s_cent - avg_d_cent) < 800:
            suggestions.append("🎧 SFX may spectrally clash with dialogue.")

    suggestions.append("✅ Mix check complete.")
    for line in suggestions:
        print(line)
    
    if not preview:
        save_suggestions_to_file(suggestions, outdir)

def save_suggestions_to_file(suggestions, outdir):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "suggestions.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("🎧 Adaptive Audio Mix Assistant – Suggestions\n\n")
        for line in suggestions:
            f.write(line + "\n")
    print(f"💾 Suggestions saved to: {path}")


def main():
    args = parse_args()
    ducking_enabled = True  # default

    if args.ducking:
        ducking_enabled = (args.ducking.lower() == "on")
    elif args.mode in ["podcast", "interview"]:
        ducking_enabled = True
    else:
        ducking_enabled = False

    scene_mode = args.mode
    CSV_FILE = args.features
    outdir = args.outdir
    preview = args.preview

    settings = get_mode_settings(scene_mode)
    if args.reverb:
        settings["reverb"] = (args.reverb.lower() == "on")

    features = load_features(CSV_FILE)
    dialogue, music, sfx = categorize(features)

    def attach_segments(clips):
        for c in clips:
            path = os.path.join("data", c["filename"])
            if os.path.exists(path):
                c["segment"] = AudioSegment.from_file(path)
            else:
                print(f"❌ Missing: {c['filename']}")
                c["segment"] = AudioSegment.silent(duration=1000)

    attach_segments(dialogue)
    attach_segments(music)
    attach_segments(sfx)
    
    suggest_mixes(dialogue, music, sfx, outdir, preview)
    apply_auto_mix(dialogue, music, sfx, settings, outdir, scene_mode, preview, ducking_enabled)

if __name__ == "__main__":
    main()

