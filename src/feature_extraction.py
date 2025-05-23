import os
from pydub import AudioSegment
import librosa
import numpy as np
import csv

DATA_DIR = "data"

def extract_basic_features(audio_path):
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000
    rms = audio.rms
    sample_rate = audio.frame_rate
    return duration_sec, rms, sample_rate

def extract_advanced_features(audio_path):
    y, sr = librosa.load(audio_path, sr=None)  # load audio with original sampling rate

    # Spectral centroid (brightness)
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_centroid_mean = np.mean(spectral_centroids)

    # Zero crossing rate (noisiness)
    zcr = librosa.feature.zero_crossing_rate(y)
    zcr_mean = np.mean(zcr)

    # Tempo (beats per minute)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.squeeze(tempo)) 

    return spectral_centroid_mean, zcr_mean, tempo

def save_features_to_csv(features_list, filename="audio_features.csv"):
    keys = features_list[0].keys()
    with open(filename, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(features_list)

def load_features(csv_path):
    features = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # Convert numeric values
                row["rms"] = float(row["rms"])
                row["zero_crossing_rate"] = float(row["zero_crossing_rate"])
                row["tempo_bpm"] = float(row["tempo_bpm"])
                row["spectral_centroid"] = float(row["spectral_centroid"])
                row["duration_sec"] = float(row["duration_sec"])
                row["sample_rate"] = int(row["sample_rate"])

                # Load the actual audio segment
                audio_path = os.path.join(DATA_DIR, row["filename"])
                row["segment"] = AudioSegment.from_file(audio_path)

                features.append(row)
            except Exception as e:
                print(f"⚠️ Skipping {row['filename']}: {e}")
    return features


def main():
    files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".wav")]
    all_features = []

    for f in files:
        path = os.path.join(DATA_DIR, f)
        duration, rms, sample_rate = extract_basic_features(path)
        spectral_centroid, zcr, tempo = extract_advanced_features(path)

        features = {
            "filename": f,
            "duration_sec": float(duration),
            "rms": float(rms),
            "sample_rate": int(sample_rate),
            "spectral_centroid": float(spectral_centroid),
            "zero_crossing_rate": float(zcr),
            "tempo_bpm": float(tempo)
        }
        all_features.append(features)

    save_features_to_csv(all_features)
    print(f"Saved features for {len(all_features)} files to audio_features.csv")

if __name__ == "__main__":
    main()
