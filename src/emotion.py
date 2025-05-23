# src/emotion.py

def detect_emotion_from_filenames(clips):
    """
    Detects the dominant emotion by checking for keywords in filenames.

    Parameters:
        clips (list of dict): List of feature dictionaries (from CSV), each containing 'filename'.

    Returns:
        str: Detected emotion (or 'neutral' if unknown).
    """
    keywords = {"sad": "sad", "happy": "happy", "tense": "tense", "calm": "calm", "angry": "angry"}
    counts = {e: 0 for e in keywords.values()}

    for clip in clips:
        name = clip["filename"].lower()
        for k, label in keywords.items():
            if k in name:
                counts[label] += 1

    top = max(counts, key=counts.get)
    return top if counts[top] > 0 else "neutral"

