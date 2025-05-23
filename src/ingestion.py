import os
from pydub import AudioSegment

DATA_DIR = "data"
OUTPUT_DIR = "../outputs"

def load_and_process(path):
    audio = AudioSegment.from_file(path)
    audio = audio.set_channels(1).set_frame_rate(44100)
    return audio

def process_files_by_type(file_prefix):
    processed = []
    print("📁 Files in data/:", os.listdir(DATA_DIR))
    for filename in os.listdir(DATA_DIR):
        if filename.startswith(file_prefix) and filename.endswith(".wav"):
            full_path = os.path.join(DATA_DIR, filename)
            print(f"🔄 Processing {filename}...")
            audio = load_and_process(full_path)
            processed.append(audio)
    return processed

def main():
    print("📂 Loading and processing all audio files...")

    dialogue_clips = process_files_by_type("dialogue")
    music_clips = process_files_by_type("music")
    sfx_clips = process_files_by_type("sfx")

    print(f"✅ Loaded {len(dialogue_clips)} dialogue, {len(music_clips)} music, {len(sfx_clips)} sfx clips.")

    # Example: Save first dialogue file for testing output
    if dialogue_clips:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        dialogue_clips[0].export(os.path.join(OUTPUT_DIR, "dialogue_preview.wav"), format="wav")
        print("💾 Saved preview to outputs/dialogue_preview.wav")

if __name__ == "__main__":
    main()
