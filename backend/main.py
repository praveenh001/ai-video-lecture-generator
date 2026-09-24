import os
import uuid
import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

from backend.models import (
    TopicAnalysisRequest, TopicAnalysisResponse,
    GenerateLectureRequest, RegenerateSceneRequest,
    Lecture, Scene, VisualSpec, LearningMaterials
)
from backend.services.ai_engine import EducationalAIEngine
from backend.services.tts_engine import TTSService, generate_webvtt
from backend.services.visual_engine import VisualEngine
from backend.services.storage_service import StorageService

app = FastAPI(
    title="AI-Powered Educational Video Lecture Generator",
    description="Transforms any educational topic into an instructional, animated video lecture with AI narration, synchronized visuals, and study materials.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
ai_engine = EducationalAIEngine()
tts_service = TTSService("backend/media/audio")
visual_engine = VisualEngine("backend/media")
storage_service = StorageService("data/lectures.json")

# Ensure required media directories exist
os.makedirs("backend/media/audio", exist_ok=True)
os.makedirs("backend/media/videos", exist_ok=True)
os.makedirs("backend/media/thumbnails", exist_ok=True)
os.makedirs("backend/media/subtitles", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Mount static and media directories
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
app.mount("/media", StaticFiles(directory="backend/media"), name="media")

# Jinja2 template loader
templates = Environment(loader=FileSystemLoader("backend/templates"))

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    template = templates.get_template("index.html")
    return template.render()

@app.get("/api/voices")
async def get_voices():
    return tts_service.list_voices()

@app.post("/api/analyze-topic", response_model=TopicAnalysisResponse)
async def analyze_topic(req: TopicAnalysisRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    return ai_engine.analyze_topic(req.topic, api_key=req.api_key)

@app.post("/api/generate-lecture")
async def generate_lecture(req: GenerateLectureRequest, background_tasks: BackgroundTasks):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    lecture_id = str(uuid.uuid4())[:8]
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Step 1: Pedagogical Plan & Visual Specs
    lecture_plan = ai_engine.plan_and_generate_lecture(
        topic=topic,
        knowledge_level=req.knowledge_level,
        purpose=req.purpose,
        preferred_language=req.preferred_language,
        teaching_style=req.teaching_style,
        lecture_duration=req.lecture_duration,
        voice_name=req.voice_name,
        api_key=req.api_key
    )

    scenes_raw = lecture_plan.get("scenes", [])
    scenes_processed: List[Dict[str, Any]] = []
    total_duration = 0.0

    # Step 2: Synthesize Neural Voiceover & Compute Timestamps for each scene
    for idx, sc in enumerate(scenes_raw):
        sc_id = f"lec_{lecture_id}_s{idx}"
        narration = sc.get("narration_text", "")
        
        audio_url, duration, subtitles = await tts_service.synthesize_scene_audio(
            scene_id=sc_id,
            text=narration,
            voice=req.voice_name
        )

        sc_copy = dict(sc)
        sc_copy["scene_id"] = sc_id
        sc_copy["index"] = idx
        sc_copy["audio_url"] = audio_url
        sc_copy["actual_duration"] = duration
        sc_copy["subtitles"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in subtitles]
        scenes_processed.append(sc_copy)
        total_duration += duration

    # Step 3: Generate WebVTT subtitle file
    vtt_content = generate_webvtt(scenes_processed)
    vtt_filename = f"lec_{lecture_id}.vtt"
    vtt_path = os.path.join("backend/media/subtitles", vtt_filename)
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)
    vtt_url = f"/media/subtitles/{vtt_filename}"

    # Step 4: Assemble complete lecture object
    full_lecture = {
        "id": lecture_id,
        "topic": topic,
        "title": lecture_plan.get("title", f"{topic} Video Lecture"),
        "domain": lecture_plan.get("domain", "general"),
        "subdomain": lecture_plan.get("subdomain", "Educational Concepts"),
        "knowledge_level": req.knowledge_level,
        "teaching_style": req.teaching_style,
        "duration_target": req.lecture_duration,
        "voice_name": req.voice_name,
        "created_at": created_at,
        "total_duration": round(total_duration, 2),
        "scenes": scenes_processed,
        "video_url": None, # Can be rendered on demand or in background
        "subtitles_vtt_url": vtt_url,
        "materials": lecture_plan.get("materials", {})
    }

    # Step 5: Save lecture to local storage
    storage_service.save_lecture(full_lecture)

    # Optionally kick off server video render in background
    def background_render():
        try:
            vid_url = visual_engine.render_full_lecture_video(full_lecture)
            full_lecture["video_url"] = vid_url
            storage_service.save_lecture(full_lecture)
        except Exception as e:
            print(f"Background video rendering notice: {e}")

    background_tasks.add_task(background_render)

    return full_lecture

@app.get("/api/lectures")
async def list_lectures():
    return storage_service.list_lectures()

@app.get("/api/lectures/{lecture_id}")
async def get_lecture(lecture_id: str):
    lec = storage_service.get_lecture(lecture_id)
    if not lec:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return lec

@app.post("/api/lectures/{lecture_id}/render-video")
async def render_lecture_video(lecture_id: str):
    lec = storage_service.get_lecture(lecture_id)
    if not lec:
        raise HTTPException(status_code=404, detail="Lecture not found")
    try:
        vid_url = visual_engine.render_full_lecture_video(lec)
        lec["video_url"] = vid_url
        storage_service.save_lecture(lec)
        return {"status": "success", "video_url": vid_url}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to render video: {str(ex)}")

@app.post("/api/lectures/{lecture_id}/scenes/{scene_idx}/regenerate")
async def regenerate_scene(lecture_id: str, scene_idx: int, req: RegenerateSceneRequest):
    lec = storage_service.get_lecture(lecture_id)
    if not lec:
        raise HTTPException(status_code=404, detail="Lecture not found")
    scenes = lec.get("scenes", [])
    if not (0 <= scene_idx < len(scenes)):
        raise HTTPException(status_code=400, detail="Invalid scene index")

    target_scene = dict(scenes[scene_idx])

    # Update text or chapter title if provided
    if req.narration_text:
        target_scene["narration_text"] = req.narration_text
    if req.chapter_title:
        target_scene["chapter_title"] = req.chapter_title
    if req.visual_type:
        target_scene["visual_spec"]["visual_type"] = req.visual_type
    if req.visual_parameters:
        target_scene["visual_spec"]["parameters"].update(req.visual_parameters)

    # Re-synthesize audio
    voice = req.voice_name or lec.get("voice_name", "en-US-ChristopherNeural")
    audio_url, duration, subtitles = await tts_service.synthesize_scene_audio(
        scene_id=target_scene["scene_id"],
        text=target_scene["narration_text"],
        voice=voice
    )
    target_scene["audio_url"] = audio_url
    target_scene["actual_duration"] = duration
    target_scene["subtitles"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in subtitles]

    updated_lec = storage_service.update_scene(lecture_id, scene_idx, target_scene)

    # Regenerate VTT
    if updated_lec:
        vtt_content = generate_webvtt(updated_lec.get("scenes", []))
        vtt_filename = f"lec_{lecture_id}.vtt"
        vtt_path = os.path.join("backend/media/subtitles", vtt_filename)
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)

    return updated_lec

@app.get("/api/lectures/{lecture_id}/export-notes")
async def export_notes(lecture_id: str):
    lec = storage_service.get_lecture(lecture_id)
    if not lec:
        raise HTTPException(status_code=404, detail="Lecture not found")
    materials = lec.get("materials", {})
    notes_md = materials.get("notes_markdown", f"# {lec.get('title')}\n\n{materials.get('summary', '')}")
    return JSONResponse(content={"markdown": notes_md, "filename": f"{lec.get('topic')}_lecture_notes.md"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
