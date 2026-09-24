import os
import asyncio
import subprocess
import json
import edge_tts
from typing import List, Tuple, Dict, Any
import imageio_ffmpeg
from backend.models import SubtitleItem

VOICE_CATALOG = [
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher (US Male - Clear & Authoritative Teacher)",
        "gender": "Male",
        "locale": "en-US",
        "style": "Instructional, Authoritative"
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (US Female - Engaging & Clear Professor)",
        "gender": "Female",
        "locale": "en-US",
        "style": "Friendly, Engaging"
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (US Male - Tech Lead & Practical Engineer)",
        "gender": "Male",
        "locale": "en-US",
        "style": "Practical, Modern"
    },
    {
        "id": "en-US-AriaNeural",
        "name": "Aria (US Female - Academic & Expressive)",
        "gender": "Female",
        "locale": "en-US",
        "style": "Expressive, Crisp"
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (British Female - Polished & Sophisticated)",
        "gender": "Female",
        "locale": "en-GB",
        "style": "Articulate, Academic"
    },
    {
        "id": "en-US-EricNeural",
        "name": "Eric (US Male - Warm & Conversational)",
        "gender": "Male",
        "locale": "en-US",
        "style": "Warm, Patient"
    }
]

def get_ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_audio_duration_seconds(audio_file_path: str) -> float:
    """Uses ffmpeg to probe the duration of an audio file in seconds."""
    if not os.path.exists(audio_file_path):
        return 0.0
    exe = get_ffmpeg_path()
    try:
        cmd = [
            exe, "-i", audio_file_path,
            "-f", "null", "-"
        ]
        proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
        # Parse Duration: HH:MM:SS.xx
        for line in proc.stderr.splitlines():
            if "Duration:" in line:
                part = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = part.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception as e:
        print(f"Error probing audio duration: {e}")
    # Fallback estimate based on file size for 48kbps mp3
    try:
        size = os.path.getsize(audio_file_path)
        return max(3.0, size / 6000.0)
    except Exception:
        return 10.0

class TTSService:
    def __init__(self, media_dir: str = "backend/media/audio"):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)

    def list_voices(self) -> List[Dict[str, str]]:
        return VOICE_CATALOG

    async def synthesize_scene_audio(
        self,
        scene_id: str,
        text: str,
        voice: str = "en-US-ChristopherNeural"
    ) -> Tuple[str, float, List[SubtitleItem]]:
        """
        Synthesizes speech for a single scene script.
        Returns: (audio_relative_url, duration_seconds, subtitles_list)
        """
        filename = f"{scene_id}.mp3"
        output_path = os.path.join(self.media_dir, filename)
        subtitles: List[SubtitleItem] = []

        try:
            communicate = edge_tts.Communicate(text, voice)
            audio_bytes = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.extend(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    # offset and duration in 100-nanosecond units
                    start = chunk["offset"] / 10_000_000.0
                    duration = chunk["duration"] / 10_000_000.0
                    end = start + duration
                    sub_text = chunk.get("text", "").strip()
                    if sub_text:
                        subtitles.append(SubtitleItem(
                            start=round(start, 2),
                            end=round(end, 2),
                            text=sub_text
                        ))

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            duration = get_audio_duration_seconds(output_path)

            # If no sentence boundaries were captured, estimate evenly
            if not subtitles and text:
                sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
                if not sentences:
                    sentences = [text]
                step = duration / len(sentences)
                for i, s in enumerate(sentences):
                    subtitles.append(SubtitleItem(
                        start=round(i * step, 2),
                        end=round((i + 1) * step, 2),
                        text=s + "."
                    ))

            # Ensure final subtitle bounds match duration
            if subtitles and duration > 0:
                subtitles[-1].end = max(subtitles[-1].end, round(duration, 2))

            rel_url = f"/media/audio/{filename}"
            return rel_url, round(duration, 2), subtitles

        except Exception as ex:
            print(f"TTS synthesis error for {scene_id}: {ex}. Creating fallback synthesized audio.")
            # Fallback: estimate reading speed (~140 wpm) and generate a silent track
            word_count = len(text.split())
            duration = max(4.0, (word_count / 140.0) * 60.0)
            exe = get_ffmpeg_path()
            try:
                subprocess.run([
                    exe, "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
                    "-t", str(duration), "-q:a", "9", "-acodec", "libmp3lame",
                    output_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except Exception:
                pass

            # Basic sentences
            sentences = [s.strip() for s in text.split(".") if s.strip()]
            step = duration / max(1, len(sentences))
            for i, s in enumerate(sentences):
                subtitles.append(SubtitleItem(
                    start=round(i * step, 2),
                    end=round((i + 1) * step, 2),
                    text=s + "."
                ))

            return f"/media/audio/{filename}", round(duration, 2), subtitles

def generate_webvtt(scenes: List[Any]) -> str:
    """Generates a complete WebVTT file with chapter cues and time-synced subtitles."""
    lines = ["WEBVTT", ""]
    current_time_offset = 0.0

    def fmt_vtt(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    for scene in scenes:
        scene_dur = (scene.get("actual_duration") if isinstance(scene, dict) else getattr(scene, "actual_duration", None)) or \
                    (scene.get("estimated_duration") if isinstance(scene, dict) else getattr(scene, "estimated_duration", None)) or 15.0
        
        chap_title = scene.get("chapter_title") if isinstance(scene, dict) else getattr(scene, "chapter_title", "")
        if chap_title:
            lines.append(f"NOTE Chapter: {chap_title}")
            lines.append("")

        subs = scene.get("subtitles") if isinstance(scene, dict) else getattr(scene, "subtitles", [])
        if subs:
            for sub in subs:
                s_start = sub["start"] if isinstance(sub, dict) else getattr(sub, "start", 0.0)
                s_end = sub["end"] if isinstance(sub, dict) else getattr(sub, "end", s_start + 2.0)
                s_text = sub["text"] if isinstance(sub, dict) else getattr(sub, "text", "")
                abs_start = current_time_offset + s_start
                abs_end = current_time_offset + s_end
                lines.append(f"{fmt_vtt(abs_start)} --> {fmt_vtt(abs_end)}")
                lines.append(s_text)
                lines.append("")
        else:
            narr_text = scene.get("narration_text") if isinstance(scene, dict) else getattr(scene, "narration_text", "")
            lines.append(f"{fmt_vtt(current_time_offset)} --> {fmt_vtt(current_time_offset + scene_dur)}")
            lines.append(narr_text[:120] + "...")
            lines.append("")

        current_time_offset += scene_dur

    return "\n".join(lines)
