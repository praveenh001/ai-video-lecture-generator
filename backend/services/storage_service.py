import os
import json
from typing import Dict, Any, List, Optional
from backend.models import Lecture

DATA_DIR = "data"
LECTURES_FILE = os.path.join(DATA_DIR, "lectures.json")

class StorageService:
    def __init__(self, data_file: str = LECTURES_FILE):
        self.data_file = data_file
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _read_all(self) -> Dict[str, Any]:
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_all(self, data: Dict[str, Any]):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_lecture(self, lecture_dict: Dict[str, Any]):
        all_lectures = self._read_all()
        lecture_id = lecture_dict.get("id")
        if lecture_id:
            all_lectures[lecture_id] = lecture_dict
            self._write_all(all_lectures)

    def get_lecture(self, lecture_id: str) -> Optional[Dict[str, Any]]:
        all_lectures = self._read_all()
        return all_lectures.get(lecture_id)

    def list_lectures(self) -> List[Dict[str, Any]]:
        all_lectures = self._read_all()
        # Return summary list sorted by creation time descending
        summaries = []
        for lid, lec in all_lectures.items():
            summaries.append({
                "id": lid,
                "title": lec.get("title", "Lecture"),
                "topic": lec.get("topic", ""),
                "domain": lec.get("domain", "general"),
                "created_at": lec.get("created_at", ""),
                "total_duration": lec.get("total_duration", 0),
                "num_scenes": len(lec.get("scenes", [])),
                "has_video": bool(lec.get("video_url"))
            })
        summaries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return summaries

    def update_scene(self, lecture_id: str, scene_index: int, updated_scene: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        all_lectures = self._read_all()
        lec = all_lectures.get(lecture_id)
        if not lec:
            return None
        scenes = lec.get("scenes", [])
        if 0 <= scene_index < len(scenes):
            scenes[scene_index] = updated_scene
            # Recalculate total duration
            total_dur = sum(s.get("actual_duration") or s.get("estimated_duration", 15.0) for s in scenes)
            lec["total_duration"] = round(total_dur, 2)
            all_lectures[lecture_id] = lec
            self._write_all(all_lectures)
            return lec
        return None
