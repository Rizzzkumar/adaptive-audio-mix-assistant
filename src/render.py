# src/render.py

import os
from pydub import AudioSegment
from mix_engine import combine_and_normalize, duck_music_during_dialogue

def apply_auto_mix(dialogue_clips, music_clips, sfx_clips, settings, outdir, scene_mode, preview=False, ducking_enabled=True):
    os.makedirs(outdir, exist_ok=True)

    print(f"🎬 Scene Mode: {scene_mode}")
    
    # Step 1: Build stems
    dialogue_mix = combine_and_normalize(dialogue_clips, "dialogue", pan_value=0.0)
    music_mix = combine_and_normalize(music_clips, "music", pan_value=-0.3)
    sfx_mix = combine_and_normalize(sfx_clips, "sfx", pan_value=0.2, eq=True, reverb_enabled=settings["reverb"])

    # Step 2: Pad all to match length
    max_len = max(len(dialogue_mix), len(music_mix), len(sfx_mix))
    pad = lambda s: s + AudioSegment.silent(duration=max_len - len(s)) if len(s) < max_len else s

    dialogue_mix = pad(dialogue_mix).fade_in(settings["fade_duration"]).fade_out(settings["fade_duration"]) + settings["gain"]["dialogue"]
    music_mix = pad(music_mix).fade_in(settings["fade_duration"]).fade_out(settings["fade_duration"]) + settings["gain"]["music"]
    sfx_mix = pad(sfx_mix).fade_in(settings["fade_duration"]).fade_out(settings["fade_duration"]) + settings["gain"]["sfx"]

    # Step 3: Ducking if enabled
    if ducking_enabled:
        music_mix = duck_music_during_dialogue(music_mix, dialogue_mix, reduction_db=6)

    # Step 4: Export stems (skip in preview)
    if not preview:
        dialogue_mix.export(os.path.join(outdir, "dialogue_mix.wav"), format="wav")
        music_mix.export(os.path.join(outdir, "music_mix.wav"), format="wav")
        sfx_mix.export(os.path.join(outdir, "sfx_mix.wav"), format="wav")

    # Step 5: Final mix
    intro_pad = settings["music_intro"]
    outro_pad = settings["music_outro"]
    content_mix = music_mix.overlay(dialogue_mix).overlay(sfx_mix)
    full_len = len(content_mix) + intro_pad + outro_pad

    final_mix = AudioSegment.silent(duration=full_len)
    final_mix = final_mix.overlay(music_mix[:intro_pad].fade_in(intro_pad), position=0)
    final_mix = final_mix.overlay(content_mix, position=intro_pad)
    final_mix = final_mix.overlay(music_mix[-outro_pad:].fade_out(outro_pad), position=full_len - outro_pad)

    if preview:
        print("👀 Preview mode: skipping export.")
        return

    final_path = os.path.join(outdir, "auto_mix.wav")
    final_mix.export(final_path, format="wav")
    print(f"✅ Final mix exported: {final_path}")
