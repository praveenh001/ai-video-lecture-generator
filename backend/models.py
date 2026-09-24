from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class ClarificationOption(BaseModel):
    id: str
    label: str
    description: Optional[str] = None

class ClarificationQuestion(BaseModel):
    id: str
    question: str
    options: List[ClarificationOption]
    default_value: str

class TopicAnalysisRequest(BaseModel):
    topic: str
    knowledge_level: Optional[str] = "Intermediate"
    purpose: Optional[str] = "Deep Understanding"
    preferred_language: Optional[str] = "English"
    teaching_style: Optional[str] = "Animated Visual First"
    lecture_duration: Optional[str] = "Standard (4-5 mins)"
    voice_name: Optional[str] = "en-US-ChristopherNeural"
    api_key: Optional[str] = None

class TopicAnalysisResponse(BaseModel):
    topic: str
    domain: str  # history, economics_business, psychology_philosophy, health_biology, arts_literature, science_nature, computer_science, mathematics, general
    subdomain: str
    overview: str
    clarification_needed: bool
    recommended_level: str
    recommended_style: str
    clarification_questions: List[ClarificationQuestion]

class VisualSpec(BaseModel):
    visual_type: str  # timeline_journey, cycle_loop, hierarchy_pyramid, spectrum_meter, narrative_arc, cause_and_effect, cross_section_sim, algorithm_animator, code_visualizer, math_graph, process_simulation, concept_metaphor, comparison_matrix, diagram_board
    title: str
    subtitle: Optional[str] = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    keyframe_steps: List[Dict[str, Any]] = Field(default_factory=list)

class SubtitleItem(BaseModel):
    start: float
    end: float
    text: str

class Scene(BaseModel):
    scene_id: str
    index: int
    chapter_title: str
    pedagogical_phase: str  # hook, foundation, visual_demonstration, edge_cases, summary
    narration_text: str
    visual_spec: VisualSpec
    estimated_duration: float = 20.0
    actual_duration: Optional[float] = None
    audio_url: Optional[str] = None
    subtitles: List[SubtitleItem] = Field(default_factory=list)

class KeyConcept(BaseModel):
    concept: str
    definition: str
    importance: str

class FormulaOrCodeItem(BaseModel):
    title: str
    type: str  # code, formula, rule
    content: str
    explanation: str

class PracticeQuestion(BaseModel):
    question: str
    hint: str
    solution: str

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_index: int
    explanation: str

class Flashcard(BaseModel):
    id: int
    front: str
    back: str
    category: str

class LearningMaterials(BaseModel):
    notes_markdown: str
    summary: str
    key_concepts: List[KeyConcept]
    formulas_or_code: List[FormulaOrCodeItem]
    practice_questions: List[PracticeQuestion]
    quiz: List[QuizQuestion]
    flashcards: List[Flashcard]

class Lecture(BaseModel):
    id: str
    topic: str
    title: str
    domain: str
    subdomain: str
    knowledge_level: str
    teaching_style: str
    duration_target: str
    voice_name: str
    created_at: str
    total_duration: float = 0.0
    scenes: List[Scene] = Field(default_factory=list)
    video_url: Optional[str] = None
    subtitles_vtt_url: Optional[str] = None
    materials: Optional[LearningMaterials] = None

class GenerateLectureRequest(BaseModel):
    topic: str
    knowledge_level: str = "Intermediate"
    purpose: str = "Deep Understanding"
    preferred_language: str = "English"
    teaching_style: str = "Animated Visual First"
    lecture_duration: str = "Standard (4-5 mins)"
    voice_name: str = "en-US-ChristopherNeural"
    include_background_music: bool = True
    music_mood: str = "lofi_study"
    api_key: Optional[str] = None
    llm_provider: Optional[str] = "auto"  # auto, gemini, builtin

class RegenerateSceneRequest(BaseModel):
    scene_index: int
    narration_text: Optional[str] = None
    chapter_title: Optional[str] = None
    visual_type: Optional[str] = None
    visual_parameters: Optional[Dict[str, Any]] = None
    voice_name: Optional[str] = None
    api_key: Optional[str] = None
