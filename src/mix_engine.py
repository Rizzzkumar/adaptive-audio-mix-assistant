# src/mix_engine.py

from pydub import AudioSegment, effects
from pydub.silence import detect_nonsilent

def trim_silence_tail(segment, silence_thresh=-40.0, chunk_size=100, min_tail_ms=1500):
    reversed_seg = segment.reverse()
    silent_ms = 0
    for i in range(0, len(reversed_seg), chunk_size):
        chunk = reversed_seg[i:i+chunk_size]
        if chunk.dBFS < silence_thresh:
            silent_ms += chunk_size
        else:
            break
    if silent_ms >= min_tail_ms:
        trim_point = len(segment) - silent_ms
        trimmed = segment[:trim_point].fade_out(500)
        print(f"✂️ Trimmed {silent_ms}ms of silence from tail.")
        return trimmed
    else:
        return segment

def apply_reverb(audio, intensity="medium"):
    delay_ms = {"small": 60, "medium": 150, "large": 300}.get(intensity, 150)
    base = audio - 8
    combined = audio
    for i in range(1, 4):
        echo = base - (i * 2)
        combined = combined.overlay(echo, position=i * delay_ms)
    return combined

def combine_and_normalize(clips, label, pan_value=0.0, eq=False, reverb_enabled=True):
    segments = []
    for clip in clips:
        seg = clip.get("segment")
        if not seg or len(seg) < 100:
            print(f"⚠️ Skipping: {clip['filename']}")
            continue
        seg = trim_silence_tail(seg)
        seg = effects.normalize(seg).pan(pan_value)
        if eq:
            seg = seg.low_pass_filter(8000).high_pass_filter(300)
        if reverb_enabled and label == "sfx":
            fname = clip["filename"].lower()
            if "cave" in fname:
                seg = apply_reverb(seg, "large")
            elif "room" in fname:
                seg = apply_reverb(seg, "small")
            elif "outdoor" in fname or "open" in fname:
                seg = apply_reverb(seg, "medium")
        segments.append(seg)
    if not segments:
        return AudioSegment.silent(duration=1)
    elif len(segments) == 1:
        return segments[0]
    else:
        combined = segments[0]
        for seg in segments[1:]:
            combined = combined.overlay(seg)
        return combined

def duck_music_during_dialogue(music, dialogue, reduction_db=6, silence_thresh=-40, min_silence_len=300):
    print("🎚️ Applying music ducking during dialogue...")
    ducked = music[:]
    ranges = detect_nonsilent(dialogue, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    for start, end in ranges:
        before = ducked[:start]
        to_duck = ducked[start:end] - reduction_db
        after = ducked[end:]
        ducked = before + to_duck + after

    print(f"📉 Ducking applied to {len(ranges)} dialogue regions.")
    return ducked
