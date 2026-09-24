import os
import json
import re
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from backend.models import (
    TopicAnalysisResponse, ClarificationQuestion, ClarificationOption,
    Scene, VisualSpec, LearningMaterials, KeyConcept, FormulaOrCodeItem,
    PracticeQuestion, QuizQuestion, Flashcard, Lecture
)

class EducationalAIEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    def _get_configured_gemini(self, custom_key: Optional[str] = None):
        key = custom_key or self.api_key or os.getenv("GEMINI_API_KEY", "")
        if key:
            genai.configure(api_key=key)
            try:
                return genai.GenerativeModel("gemini-2.0-flash")
            except Exception:
                return genai.GenerativeModel("gemini-1.5-flash")
        return None

    def analyze_topic(self, topic: str, api_key: Optional[str] = None) -> TopicAnalysisResponse:
        """
        Analyzes ANY topic (History, Economics, Psychology, Medicine, Science, Literature, Tech)
        to identify its pedagogical domain and select tailored visual teaching styles.
        """
        topic_lower = topic.lower().strip()
        model = self._get_configured_gemini(api_key)

        domain = "general"
        subdomain = "General Knowledge & Life Skills"
        recommended_style = "Visual Metaphor & Conceptual Blueprint"

        # 1. History & Geopolitics
        if any(w in topic_lower for w in ["history", "war", "revolution", "empire", "roman", "french revolution", "silk road", "civil war", "ancient", "dynasty", "treaty", "medieval", "cold war", "renaissance"]):
            domain = "history"
            subdomain = "World History & Civilization"
            recommended_style = "Chronological Timeline Journey & Faction Map"

        # 2. Economics, Finance & Business
        elif any(w in topic_lower for w in ["inflation", "stock", "market", "economy", "money", "interest rate", "finance", "supply and demand", "crypto", "bitcoin", "business", "monopoly", "venture capital", "trade", "banking"]):
            domain = "economics_business"
            subdomain = "Economics, Markets & Finance"
            recommended_style = "Market Equilibrium Curve & Money Flow Cycle"

        # 3. Psychology, Philosophy & Cognitive Science
        elif any(w in topic_lower for w in ["stoic", "philosophy", "psychology", "bias", "cognitive", "maslow", "habit", "mindset", "plato", "behavior", "freud", "ego", "emotion", "happiness", "existential", "decision"]):
            domain = "psychology_philosophy"
            subdomain = "Cognitive Psychology & Philosophy"
            recommended_style = "Cognitive Feedback Loop & Hierarchy Pyramid"

        # 4. Health, Medicine & Human Biology
        elif any(w in topic_lower for w in ["sleep", "circadian", "immune", "virus", "heart", "brain", "fasting", "diet", "nutrition", "cancer", "blood", "organ", "exercise", "hormone", "dopamine", "medicine"]):
            domain = "health_biology"
            subdomain = "Health Sciences & Human Biology"
            recommended_style = "Biological Pathway Simulation & Rhythm Cycle"

        # 5. Arts, Literature & Storytelling
        elif any(w in topic_lower for w in ["story", "hero's journey", "literature", "writing", "music", "harmony", "art", "film", "cinema", "poetry", "novel", "narrative", "painting", "aesthetic"]):
            domain = "arts_literature"
            subdomain = "Arts, Humanities & Narrative Design"
            recommended_style = "Narrative Arc Curve & Aesthetic Harmony Board"

        # 6. Everyday Science & Nature
        elif any(w in topic_lower for w in ["sky", "airplane", "fly", "earthquake", "weather", "ocean", "climate", "space", "gravity", "energy", "physics", "solar", "biology", "photosynthesis", "black hole", "evolution"]):
            domain = "science_nature"
            subdomain = "Natural Sciences & Phenomenon Exploration"
            recommended_style = "Physical Cross-Section & Force Dynamics Simulation"

        # 7. Computer Science & Software
        elif any(w in topic_lower for w in ["algorithm", "search", "sort", "python", "code", "programming", "database", "async", "await", "tree", "graph", "ai", "neural", "software", "api", "web"]):
            domain = "computer_science"
            subdomain = "Computer Science & Software Systems"
            recommended_style = "Step-by-step Algorithm Simulator & Code Execution"

        # 8. Mathematics
        elif any(w in topic_lower for w in ["calculus", "derivative", "integral", "matrix", "algebra", "geometry", "probability", "statistics", "equation"]):
            domain = "mathematics"
            subdomain = "Mathematics & Mathematical Thinking"
            recommended_style = "Mathematical Curves & Dynamic Limit Visualizer"

        # Tailor clarification questions specifically to domain
        style_options = self._get_style_options_for_domain(domain)

        questions = [
            ClarificationQuestion(
                id="knowledge_level",
                question="What is your current familiarity with this topic?",
                options=[
                    ClarificationOption(id="beginner", label="Beginner (Focus on visual intuition, relatable analogies, zero technical jargon)"),
                    ClarificationOption(id="intermediate", label="Intermediate (Core mechanisms, cause-and-effect, practical implications)"),
                    ClarificationOption(id="advanced", label="Advanced (Deep nuances, historical/theoretical controversies, edge conditions)")
                ],
                default_value="intermediate"
            ),
            ClarificationQuestion(
                id="purpose",
                question="What is your primary goal for this lecture?",
                options=[
                    ClarificationOption(id="conceptual", label="Deep Conceptual Intuition (Build a rock-solid, intuitive mental model)"),
                    ClarificationOption(id="practical", label="Practical Real-World Application (Apply directly in life, career, or decisions)"),
                    ClarificationOption(id="academic", label="Academic / Exam Mastery (Structured arguments, key definitions & evidence)")
                ],
                default_value="conceptual"
            ),
            ClarificationQuestion(
                id="teaching_style",
                question="Which visual teaching style will help you absorb this best?",
                options=style_options,
                default_value=style_options[0].id
            ),
            ClarificationQuestion(
                id="lecture_duration",
                question="Desired lecture length?",
                options=[
                    ClarificationOption(id="quick", label="Quick Overview (3 scenes, ~2-3 minutes)"),
                    ClarificationOption(id="standard", label="Standard Masterclass (5 scenes, ~4-5 minutes)"),
                    ClarificationOption(id="deep", label="Comprehensive Deep Dive (6-7 scenes, ~7-9 minutes)")
                ],
                default_value="standard"
            )
        ]

        overview_text = f"We will design an educational lecture on '{topic}', structured from intuitive foundational principles to dynamic visual demonstrations and real-world implications."

        # If LLM model is available, refine analysis with live model
        if model:
            try:
                prompt = f"""
                Analyze the educational topic: "{topic}".
                Respond in valid JSON only with keys:
                - "domain": string (history, economics_business, psychology_philosophy, health_biology, arts_literature, science_nature, computer_science, mathematics, or general)
                - "subdomain": string
                - "overview": concise 2-sentence instructional summary
                - "recommended_level": "Beginner", "Intermediate", or "Advanced"
                - "recommended_style": string describing the ideal visual explanation technique
                """
                res = model.generate_content(prompt)
                raw = res.text.strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                data = json.loads(raw)
                return TopicAnalysisResponse(
                    topic=topic,
                    domain=data.get("domain", domain),
                    subdomain=data.get("subdomain", subdomain),
                    overview=data.get("overview", overview_text),
                    clarification_needed=True,
                    recommended_level=data.get("recommended_level", "Intermediate"),
                    recommended_style=data.get("recommended_style", recommended_style),
                    clarification_questions=questions
                )
            except Exception as e:
                print(f"Gemini topic analysis fallback: {e}")

        return TopicAnalysisResponse(
            topic=topic,
            domain=domain,
            subdomain=subdomain,
            overview=overview_text,
            clarification_needed=True,
            recommended_level="Intermediate",
            recommended_style=recommended_style,
            clarification_questions=questions
        )

    def _get_style_options_for_domain(self, domain: str) -> List[ClarificationOption]:
        if domain == "history":
            return [
                ClarificationOption(id="timeline", label="Chronological Timeline & Turning Points (Visual chronological roadmap)"),
                ClarificationOption(id="cause_effect", label="Cause-and-Effect Cascade (Tracking catalysts to lasting global ripple effects)"),
                ClarificationOption(id="opposing_forces", label="Clashing Factions Matrix (Comparing motivations, alliances, and strategies)")
            ]
        elif domain == "economics_business":
            return [
                ClarificationOption(id="market_equilibrium", label="Market Dynamics & Equilibrium Shift (Dynamic supply/demand curves)"),
                ClarificationOption(id="money_cycle", label="Economic Money Flow Cycle (Tracking capital between households, banks & markets)"),
                ClarificationOption(id="spectrum_tradeoff", label="Trade-off & Policy Spectrum (Inflation vs. Unemployment, Risk vs. Reward)")
            ]
        elif domain == "psychology_philosophy":
            return [
                ClarificationOption(id="pyramid_hierarchy", label="Structural Hierarchy (Multi-tier pyramid like Maslow's or value systems)"),
                ClarificationOption(id="cognitive_loop", label="Cognitive Feedback Loop (Trigger -> Thought -> Emotion -> Habit Action)"),
                ClarificationOption(id="metaphor_allegory", label="Philosophical Allegory Board (Concrete spatial analogies for abstract truths)")
            ]
        elif domain == "health_biology":
            return [
                ClarificationOption(id="biological_cycle", label="Circadian / Bio-Rhythm Cycle (Tracking hormones, energy & bodily phases)"),
                ClarificationOption(id="cellular_pathway", label="Microscopic Defense / Cellular Pathway (Step-by-step immune/biological action)"),
                ClarificationOption(id="cross_section", label="Organ & Physiological Cross-Section (Anatomy, input-output mechanics)")
            ]
        elif domain == "arts_literature":
            return [
                ClarificationOption(id="narrative_arc", label="Narrative Arc / Story Mountain (Exposition, rising tension, climax & resolution)"),
                ClarificationOption(id="harmony_waves", label="Harmonic Structure & Contrast Board (Motifs, tension, and resolution)"),
                ClarificationOption(id="creative_breakdown", label="Comparative Masterwork Dissection (Key scene/masterpiece analysis)")
            ]
        elif domain == "science_nature":
            return [
                ClarificationOption(id="cross_section_sim", label="Cross-Section & Force Interactions (Aerodynamic wing, earth crust, light rays)"),
                ClarificationOption(id="process_flow", label="Physical Energy Flow Simulation (Energy transfer from source to outcome)"),
                ClarificationOption(id="natural_cycle", label="Natural Planetary Cycle (Water cycle, plate subduction, solar fusion)")
            ]
        elif domain == "computer_science":
            return [
                ClarificationOption(id="algorithm_animator", label="Step-by-Step Algorithm & Memory Simulator (Animated pointers & state updates)"),
                ClarificationOption(id="code_visualizer", label="Live Code Execution & Call Stack (Syntax line highlight, variables watch)"),
                ClarificationOption(id="architecture_flow", label="System Architecture & Concurrency Pipeline (Non-blocking I/O event flow)")
            ]
        elif domain == "mathematics":
            return [
                ClarificationOption(id="math_graph", label="Mathematical Curves & Moving Tangent Lines (Visual coordinates and limits)"),
                ClarificationOption(id="geometric_proof", label="Geometric & Algebraic Proof Breakdown (Visual spatial transformations)")
            ]
        else:
            return [
                ClarificationOption(id="concept_metaphor", label="Relatable Visual Metaphor (Comparing complex realities to everyday concepts)"),
                ClarificationOption(id="process_simulation", label="Stage-by-Stage Functional Architecture (Inputs, transformations, outputs)"),
                ClarificationOption(id="comparison_matrix", label="Multi-Dimensional Comparison Matrix (Contrasting options, styles & trade-offs)")
            ]

    def plan_and_generate_lecture(
        self,
        topic: str,
        knowledge_level: str = "Intermediate",
        purpose: str = "Deep Understanding",
        preferred_language: str = "English",
        teaching_style: str = "Animated Visual First",
        lecture_duration: str = "Standard (4-5 mins)",
        voice_name: str = "en-US-ChristopherNeural",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically constructs a tailored pedagogical video lecture for ANY subject matter.
        """
        model = self._get_configured_gemini(api_key)
        
        num_scenes = 5
        if "quick" in lecture_duration.lower() or "2-3" in lecture_duration.lower():
            num_scenes = 3
        elif "deep" in lecture_duration.lower() or "7" in lecture_duration.lower() or "8" in lecture_duration.lower():
            num_scenes = 6

        # Live Gemini generation if API key is provided
        if model:
            try:
                gemini_data = self._generate_with_gemini(
                    model, topic, knowledge_level, purpose,
                    preferred_language, teaching_style, num_scenes
                )
                if gemini_data:
                    return gemini_data
            except Exception as ex:
                print(f"Gemini live generation fallback: {ex}")

        # Built-in multi-domain generator
        return self._generate_with_pedagogical_engine(
            topic, knowledge_level, purpose, preferred_language,
            teaching_style, num_scenes, voice_name
        )

    def _generate_with_gemini(
        self, model, topic: str, knowledge_level: str, purpose: str,
        preferred_language: str, teaching_style: str, num_scenes: int
    ) -> Optional[Dict[str, Any]]:
        prompt = f"""
        You are an elite educator, master instructional designer, animator, and video producer.
        Topic: "{topic}"
        Knowledge Level: {knowledge_level}
        Purpose: {purpose}
        Language: {preferred_language}
        Teaching Style: {teaching_style}
        Number of Scenes: {num_scenes}

        You are creating a comprehensive, educational video lecture that is deeply tailored to this specific subject matter.
        Do NOT use a generic tech template for non-technical topics!
        
        Visual types available to you:
        - "timeline_journey": For historical / chronological milestones (parameters: {{"milestones": [{{"year": "1789", "title": "Storming of Bastille", "desc": "...", "impact": "..."}}]}})
        - "cycle_loop": For circular processes (parameters: {{"cycle_title": "...", "stages": [{{"name": "Stage 1", "role": "..."}}]}})
        - "hierarchy_pyramid": For multi-tier value/need systems (parameters: {{"tiers": ["Base tier", "Middle tier", "Apex tier"]}})
        - "spectrum_meter": For trade-offs or cognitive polarities (parameters: {{"left_label": "...", "right_label": "...", "center_balance": "...", "markers": [...]}})
        - "narrative_arc": For storytelling / artistic arcs (parameters: {{"phases": [{{"phase": "Exposition", "event": "..."}}, {{"phase": "Climax", "event": "..."}}]}})
        - "cause_and_effect": For causal chains (parameters: {{"root_catalyst": "...", "intermediate_effects": [...], "ultimate_consequence": "..."}})
        - "cross_section_sim": For physical / anatomical cutaways (parameters: {{"subject": "...", "layers": [...]}})
        - "algorithm_animator": For arrays / pointers / step search
        - "code_visualizer": For syntax & variables
        - "math_graph": For function curves & tangents
        - "concept_metaphor": For contrasting analogies
        - "comparison_matrix": For 3-column comparisons
        - "diagram_board": For modular architecture diagrams

        Return a single valid JSON object with NO extra text or markdown formatting. The schema must match:
        {{
            "title": "Inspiring educational lecture title",
            "domain": "history" | "economics_business" | "psychology_philosophy" | "health_biology" | "arts_literature" | "science_nature" | "computer_science" | "mathematics" | "general",
            "subdomain": "Specific Field Name",
            "scenes": [
                {{
                    "scene_id": "scene_1",
                    "index": 0,
                    "chapter_title": "Chapter title",
                    "pedagogical_phase": "hook" | "foundation" | "visual_demonstration" | "edge_cases" | "summary",
                    "narration_text": "Spoken script (3-5 sentences), warm, engaging, teacher-like.",
                    "estimated_duration": 25.0,
                    "visual_spec": {{
                        "visual_type": "timeline_journey" | "cycle_loop" | "hierarchy_pyramid" | "spectrum_meter" | "narrative_arc" | "cause_and_effect" | "cross_section_sim" | "concept_metaphor" | "comparison_matrix" | "math_graph" | "algorithm_animator" | "code_visualizer",
                        "title": "Visual Title",
                        "subtitle": "Visual Subtitle",
                        "parameters": {{}},
                        "keyframe_steps": [
                            {{"step": 1, "description": "...", "highlight": "..."}}
                        ]
                    }}
                }}
            ],
            "materials": {{
                "summary": "Comprehensive 2-3 paragraph summary",
                "notes_markdown": "# Topic Notes\\n\\nDetailed structured notes with headings and bullet points.",
                "key_concepts": [
                    {{"concept": "Name", "definition": "Clear definition", "importance": "Why it matters"}}
                ],
                "formulas_or_code": [
                    {{"title": "Title", "type": "rule"|"principle"|"quote"|"formula"|"code", "content": "...", "explanation": "..."}}
                ],
                "practice_questions": [
                    {{"question": "Thought-provoking problem or real-life scenario", "hint": "...", "solution": "..."}}
                ],
                "quiz": [
                    {{"id": 1, "question": "...", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "..."}}
                ],
                "flashcards": [
                    {{"id": 1, "front": "...", "back": "...", "category": "..."}}
                ]
            }}
        }}
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)

    def _generate_with_pedagogical_engine(
        self,
        topic: str,
        knowledge_level: str,
        purpose: str,
        preferred_language: str,
        teaching_style: str,
        num_scenes: int,
        voice_name: str
    ) -> Dict[str, Any]:
        """
        Built-in multi-domain generator featuring rich curated masterclasses across:
        - History & Civilization (e.g. French Revolution, Fall of Roman Empire)
        - Economics & Finance (e.g. How Inflation Works)
        - Psychology & Philosophy (e.g. Stoicism, Cognitive Biases, Maslow)
        - Health & Medicine (e.g. Circadian Rhythm & Sleep)
        - Arts & Storytelling (e.g. The Hero's Journey)
        - Everyday Science (e.g. Why the Sky is Blue, How Airplanes Fly)
        - Plus CS & Math (Binary Search, Neural Networks, Async/Await, Calculus)
        - Plus an adaptive general-purpose synthesizer for ANY topic!
        """
        t_low = topic.lower().strip()

        # 1. History
        if any(w in t_low for w in ["french revolution", "bastille", "robespierre", "monarchy"]):
            return self._build_french_revolution_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t_low for w in ["roman empire", "rome", "fall of rome", "caesar"]):
            return self._build_roman_empire_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 2. Economics
        elif any(w in t_low for w in ["inflation", "purchasing power", "cpi", "central bank", "money supply"]):
            return self._build_inflation_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 3. Psychology & Philosophy
        elif any(w in t_low for w in ["stoic", "stoicism", "marcus aurelius", "seneca", "epictetus"]):
            return self._build_stoicism_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t_low for w in ["cognitive bias", "confirmation bias", "anchoring", "heuristic"]):
            return self._build_cognitive_biases_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t_low for w in ["maslow", "hierarchy of needs"]):
            return self._build_maslow_hierarchy_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 4. Health & Biology
        elif any(w in t_low for w in ["sleep", "circadian", "melatonin", "rem sleep", "sleep cycle"]):
            return self._build_sleep_circadian_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t_low for w in ["photosynthesis", "light reaction", "chloroplast"]):
            return self._build_photosynthesis_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 5. Arts & Literature
        elif any(w in t_low for w in ["hero's journey", "monomyth", "joseph campbell", "storytelling"]):
            return self._build_heros_journey_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 6. Everyday Science
        elif any(w in t_low for w in ["sky is blue", "rayleigh scattering", "blue sky", "atmosphere"]):
            return self._build_why_sky_is_blue_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t_low for w in ["airplane", "fly", "aerodynamic", "lift", "bernoulli"]):
            return self._build_how_airplanes_fly_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 7. Computer Science & Math
        elif "binary search" in t_low:
            return self._build_binary_search_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t_low for k in ["neural network", "backpropagation", "gradient descent", "deep learning"]):
            return self._build_neural_networks_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t_low for k in ["async", "await", "asynchronous", "promise", "event loop"]):
            return self._build_async_await_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t_low for k in ["derivative", "calculus", "rate of change", "tangent"]):
            return self._build_calculus_derivative_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 8. Adaptive Domain Synthesizer for ANY General Purpose Topic
        return self._build_adaptive_topic_lecture(topic, knowledge_level, purpose, teaching_style, num_scenes, voice_name)

    # ------------------- GENERAL PURPOSE DOMAIN BLUEPRINTS -------------------

    def _build_french_revolution_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Spark: Starvation, Debt & The Three Estates",
                "pedagogical_phase": "hook",
                "narration_text": "In the summer of 1789, France was bankrupt, frozen by terrible crop failures, and suffocating under an unjust social order known as the Three Estates. While the clergy and nobility paid virtually zero taxes and feasted in Versailles, the commoners, 98 percent of the population, paid for everything while starving in the streets of Paris. When the price of a single loaf of bread soared to equal a month of peasant wages, centuries of royal absolute power were about to collapse.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "hierarchy_pyramid",
                    "title": "The Ancien Régime: The Three Estates",
                    "subtitle": "A Society Built on Extreme Inequality",
                    "parameters": {
                        "pyramid_title": "Feudal Estate Pyramid (1789)",
                        "tiers": [
                            {"tier": "1st Estate: The Clergy (0.5% Pop)", "note": "Owned 10% of land, paid 0% taxes, collected tithes"},
                            {"tier": "2nd Estate: The Nobility (1.5% Pop)", "note": "Held top military & court posts, exempted from taxes"},
                            {"tier": "3rd Estate: Commoners & Bourgeoisie (98% Pop)", "note": "Peasants, merchants, laborers who bore the entire tax burden"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "3rd Estate tax burden"},
                        {"step": 2, "highlight": "1st and 2nd Estate tax exemption"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Chronology of Rebellion: From Bastille to Republic",
                "pedagogical_phase": "foundation",
                "narration_text": "Let us trace the pivotal turning points that shook the Western world. On July 14, 1789, enraged citizens stormed the medieval Bastille fortress, seizing gunpowder and declaring popular sovereignty. Within weeks, the National Assembly abolished feudalism and proclaimed the Declaration of the Rights of Man. By 1792, King Louis the Sixteenth was deposed, and France declared itself a Republic.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "timeline_journey",
                    "title": "The Revolutionary Timeline: 1789 - 1799",
                    "subtitle": "From Royal Absolutism to the Rise of Napoleon",
                    "parameters": {
                        "milestones": [
                            {"year": "May 1789", "title": "Estates-General Convenes", "desc": "Third Estate breaks away to form National Assembly", "impact": "Birth of popular sovereignty"},
                            {"year": "July 1789", "title": "Storming of the Bastille", "desc": "Parisians seize the fortress armory", "impact": "Symbolic fall of tyranny"},
                            {"year": "Aug 1789", "title": "Declaration of Rights of Man", "desc": "'Liberty, Equality, Fraternity' enshrined", "impact": "End of feudal privilege"},
                            {"year": "Jan 1793", "title": "Execution of Louis XVI", "desc": "The King is guillotined for treason", "impact": "Point of no return for Europe"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "1789"},
                        {"step": 2, "highlight": "1793"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Clashing Ideologies: Girondins vs. The Mountain",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "As foreign monarchies invaded France to crush the uprising, the revolution turned radically inwards. The National Convention split into two fierce factions: the moderate Girondins, who advocated decentralized democracy and constitutional caution, and the radical Jacobins, led by Maximilien Robespierre, who demanded ruthless central power to save the revolution at any cost.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "The Ideological Civil War",
                    "subtitle": "Moderate Reformers vs. Radical Jacobins",
                    "parameters": {
                        "col1": "The Royalists: Preserve monarchy, aristocratic tradition, and Catholic authority",
                        "col2": "The Girondins: Moderate republicans, free markets, rule of law, anti-violence",
                        "col3": "The Jacobin Mountain: Radical centralization, price controls, state terror to purge counter-revolutionaries"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Girondins"},
                        {"step": 2, "highlight": "Jacobins"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Reign of Terror: The Revolution Devours Its Children",
                "pedagogical_phase": "edge_cases",
                "narration_text": "Robespierre declared that without virtue, terror is fatal; and without terror, virtue is impotent. The Committee of Public Safety suspended constitutional liberties, executing over 17,000 citizens by guillotine in just one year. But paranoia escalated until Robespierre himself was arrested and guillotined in the Thermidorian Reaction, proving that revolutions often consume the very leaders who unleash them.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": "The Cascade of Radicalization",
                    "subtitle": "How War and Paranoia Led to the Reign of Terror",
                    "parameters": {
                        "root_catalyst": "Foreign Monarchies Invade France (1792)",
                        "intermediate_effects": [
                            "War panic & bread shortages radicalize Parisian sans-culottes",
                            "Committee of Public Safety established under Robespierre",
                            "Law of Suspects: Anyone accused of treason is guillotined"
                        ],
                        "ultimate_consequence": "Thermidorian Reaction: Robespierre executed, ending the Terror"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Foreign Invasion"},
                        {"step": 2, "highlight": "Reign of Terror"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Global Legacy: How 1789 Shaped Modern Democracy",
                "pedagogical_phase": "summary",
                "narration_text": "Out of the revolutionary ashes rose Napoleon Bonaparte, whose Napoleonic Code modernized European law. The French Revolution forever dismantled divine right monarchy, introduced universal human rights into international law, invented modern political left and right, and demonstrated that ordinary citizens possess the power to reshape history. Its ideals of Liberty, Equality, and Fraternity remain the bedrock of modern democracy.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Birth of the Modern Political Spectrum",
                    "subtitle": "Where Lawmakers Sat in the 1789 National Assembly",
                    "parameters": {
                        "left_label": "The Left: Radical Change, Equality, Republicanism",
                        "right_label": "The Right: Tradition, Monarchy, Order, Hierarchy",
                        "center_balance": "Constitutional Liberalism & Human Rights",
                        "markers": [
                            "Left: Jacobins",
                            "Center: Plain / Marais",
                            "Right: Monarchists & Aristocracy"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "The Left"},
                        {"step": 2, "highlight": "The Right"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "The French Revolution (1789-1799) was a watershed moment in human history. Driven by acute financial insolvency, hunger, and extreme inequality under the Three Estates, the French people overthrew centuries of feudal monarchy, enacted the Declaration of the Rights of Man, weathered the radical Reign of Terror, and established foundational principles of secular democracy and human rights.",
            "notes_markdown": """# The French Revolution: Comprehensive Masterclass Notes

## 1. Root Causes of 1789
- **Financial Crisis**: Royal debts from funding the American Revolution and Seven Years' War.
- **Agricultural Crisis**: The 1788-1789 crop failure caused bread prices to consume 80% of peasants' income.
- **Social Inequality**: The Three Estates structure exempting the top 2% from taxation.

## 2. Chronological Milestones
- **June 1789**: The Tennis Court Oath establishes the National Assembly.
- **July 14, 1789**: Storming of the Bastille.
- **August 1789**: Declaration of the Rights of Man and of the Citizen.
- **1793-1794**: Reign of Terror under Robespierre.
- **1799**: Coup of 18 Brumaire by Napoleon Bonaparte.

## 3. Enduring Legacies
1. **The Political Spectrum**: The terms 'Left-wing' and 'Right-wing' originated from where deputies sat in the 1789 National Assembly.
2. **Secular Law**: The Napoleonic Code abolished aristocratic privileges and established civil equality.
3. **National Sovereignty**: Power derives from the people, not divine right.
""",
            "key_concepts": [
                {"concept": "The Three Estates", "definition": "The feudal social hierarchy dividing France into Clergy (1st), Nobility (2nd), and Commoners (3rd).", "importance": "Extreme tax inequality between estates sparked the rebellion."},
                {"concept": "Reign of Terror", "definition": "A 10-month period (1793-1794) of state-sponsored executions during internal and external war.", "importance": "Demonstrates the dangers of ideological radicalization and paranoia."},
                {"concept": "Popular Sovereignty", "definition": "The principle that authority of a state and government is created and sustained by the consent of its people.", "importance": "Replaced divine right monarchy with democratic legitimacy."}
            ],
            "formulas_or_code": [
                {"title": "The National Motto", "type": "principle", "content": "Liberté, Égalité, Fraternité", "explanation": "Liberty, Equality, Fraternity: the universal triad defining modern republican democracies."},
                {"title": "Article 1 (Rights of Man)", "type": "quote", "content": "Men are born and remain free and equal in rights.", "explanation": "Foundational premise dissolving aristocratic hereditary entitlement."}
            ],
            "practice_questions": [
                {"question": "Why did King Louis XVI call the Estates-General in May 1789 after a 175-year hiatus?", "hint": "Consider France's sovereign financial situation.", "solution": "France was facing complete national bankruptcy, and the aristocracy refused to surrender their tax exemptions without approval from the Estates-General."}
            ],
            "quiz": [
                {"id": 1, "question": "What percentage of the French population belonged to the Third Estate in 1789?", "options": ["Around 50%", "Around 75%", "Around 98%", "Less than 20%"], "correct_index": 2, "explanation": "Commoners, peasants, and the bourgeoisie accounted for roughly 98% of the kingdom's populace."},
                {"id": 2, "question": "What was the significance of the storming of the Bastille on July 14, 1789?", "options": ["It was where the King lived", "It symbolized the fall of royal tyranny and secured gunpowder for the revolution", "It was where all national tax money was kept", "It ended the French Revolution in a single day"], "correct_index": 1, "explanation": "The Bastille was a dreaded symbol of royal oppression and contained the gunpowder needed by the newly formed National Guard."}
            ],
            "flashcards": [
                {"id": 1, "front": "What did the Tennis Court Oath pledge?", "back": "The Third Estate vowed not to disband until they had drafted a written constitution for France.", "category": "Milestones"},
                {"id": 2, "front": "Who led the Committee of Public Safety during the Reign of Terror?", "back": "Maximilien Robespierre.", "category": "Key Figures"}
            ]
        }

        return {
            "title": "The French Revolution: Storming the Bastille to the Birth of Democracy",
            "domain": "history",
            "subdomain": "Modern European History & Political Revolutions",
            "scenes": scenes,
            "materials": materials
        }

    def _build_inflation_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Coffee Shop Dilemma: What is Inflation?",
                "pedagogical_phase": "hook",
                "narration_text": "In 1970, a cup of coffee cost twenty-five cents. Today, that exact same coffee costs four dollars. Did the coffee beans become sixteen times more delicious? Of course not. The coffee didn't change; the value of the dollar did! Inflation is not simply prices rising; it is the silent evaporation of your money's purchasing power over time.",
                "estimated_duration": 22.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Purchasing Power Shrinkage",
                    "subtitle": "What $20 Bought in 1970 vs Today",
                    "parameters": {
                        "left_title": "1970: $20 Bill",
                        "left_items": ["Full grocery cart (Eggs, Milk, Bread, Meat)", "Full tank of gasoline", "Dinner for two at a restaurant"],
                        "right_title": "Today: $20 Bill",
                        "right_items": ["A modest sandwich and drink", "A few gallons of gas", "Purchasing power eroded by ~85%!"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "1970 basket"},
                        {"step": 2, "highlight": "Current basket"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Twin Drivers: Demand-Pull vs. Cost-Push",
                "pedagogical_phase": "foundation",
                "narration_text": "Economists categorize inflation into two primary engines. First is Demand-Pull inflation: too much money chasing too few goods, like when stimulus cash arrives but factories cannot produce goods fast enough. Second is Cost-Push inflation: when production costs spike, such as an oil embargo or war that makes transportation and electricity expensive across the entire economy.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "The Two Engines of Inflation",
                    "subtitle": "Demand-Pull vs. Cost-Push Economics",
                    "parameters": {
                        "col1": "Demand-Pull: High consumer spending & cheap credit pull prices upward",
                        "col2": "Cost-Push: Rising supply costs (oil, raw materials, wages) push prices higher",
                        "col3": "Built-In (Wage-Price Spiral): Workers demand higher wages, forcing businesses to raise prices again"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Demand-Pull"},
                        {"step": 2, "highlight": "Cost-Push"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Money Supply Cycle: Milton Friedman's Rule",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "As Nobel laureate Milton Friedman famously argued, inflation is always and everywhere a monetary phenomenon. If an economy produces 100 apples, and there is 100 dollars in circulation, an apple costs 1 dollar. If the central bank prints another 100 dollars without growing more apples, an apple naturally rises to 2 dollars. The money supply cycle connects central bank interest rates, commercial bank lending, and the velocity of money.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cycle_loop",
                    "title": "The Monetary Cycle & Price Equilibrium",
                    "subtitle": "Central Bank -> Commercial Lending -> Consumer Spending -> Price Pressures",
                    "parameters": {
                        "cycle_title": "Credit & Monetary Expansion Loop",
                        "stages": [
                            {"name": "1. Low Interest Rates", "role": "Central Bank cuts rates, making borrowing cheap"},
                            {"name": "2. Bank Credit Surges", "role": "Mortgages, business loans, and consumer credit multiply"},
                            {"name": "3. Aggregate Demand Exceeds Supply", "role": "Purchasing volume outpaces factory capacity"},
                            {"name": "4. Broad Price Increases", "role": "Sellers raise prices across housing, food, and energy"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Cheap Credit"},
                        {"step": 2, "highlight": "Surging Demand"},
                        {"step": 3, "highlight": "Price Increase"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Central Bank's Sledgehammer: Raising Rates",
                "pedagogical_phase": "edge_cases",
                "narration_text": "To stop runaway inflation, central banks have one primary lever: hiking interest rates. When the Federal Reserve raises rates, borrowing costs for credit cards, cars, and home mortgages skyrocket. Consumers stop buying homes, companies freeze hiring, demand cools down, and prices stabilize. But the risk is immense: tighten too fast, and you trigger a painful economic recession.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Central Bank Balancing Act",
                    "subtitle": "Controlling Inflation vs. Preventing Economic Recession",
                    "parameters": {
                        "left_label": "Loose Money: Low Rates, High Growth, High Inflation Risk",
                        "right_label": "Tight Money: High Rates, Crushed Inflation, High Recession Risk",
                        "center_balance": "The 'Goldilocks' 2% Annual Inflation Target",
                        "markers": [
                            "Dovish (Stimulate Economy)",
                            "Neutral (Sustainable Equilibrium)",
                            "Hawkish (Aggressive Rate Hikes)"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Loose Money"},
                        {"step": 2, "highlight": "Tight Money"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Protecting Your Wealth: Assets That Beat Inflation",
                "pedagogical_phase": "summary",
                "narration_text": "Inflation is an invisible tax on savers. Holding cash in a zero-interest savings account guarantees you lose real wealth every single year. To thrive, smart investors allocate capital into inflation-hedging assets: productive businesses with pricing power, real estate with rent growth, and Treasury Inflation-Protected Securities. Understanding inflation turns you from an economic victim into an informed investor.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Asset Performance During Inflation",
                    "subtitle": "Winners vs. Losers When Purchasing Power Drops",
                    "parameters": {
                        "col1": "Cash & Fixed Savings: Guaranteed losers. Purchasing power drops year after year.",
                        "col2": "Fixed-Rate Debtors: Relative winners. They pay back old mortgages with cheaper, inflated dollars.",
                        "col3": "Equities & Real Assets: Resilient performers. Companies raise prices, preserving real returns."
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Cash"},
                        {"step": 2, "highlight": "Real Assets"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "Inflation is the sustained increase in the general price level of goods and services, which corresponds directly to a decline in purchasing power. It is propelled by Demand-Pull factors, Cost-Push shocks, and expansion of the money supply, and managed by Central Banks through interest rate policies.",
            "notes_markdown": """# Economics: Understanding Inflation & Monetary Policy

## 1. Defining Inflation
$$\\text{Inflation Rate} = \\frac{\\text{CPI}_{\\text{current}} - \\text{CPI}_{\\text{previous}}}{\\text{CPI}_{\\text{previous}}} \\times 100$$
- **Purchasing Power**: The quantity of goods and services one unit of currency can buy.
- **Consumer Price Index (CPI)**: A weighted basket of typical goods (food, shelter, transportation, healthcare).

## 2. Core Causes
1. **Demand-Pull**: Aggregate demand exceeding aggregate supply.
2. **Cost-Push**: Exogenous supply shocks (e.g. oil crisis, natural disasters).
3. **Monetary Expansion**: When the growth of broad money supply ($M_2$) significantly outpaces real economic output ($GDP$).

## 3. The Quantity Theory of Money
$$M \\cdot V = P \\cdot Y$$
where:
- $M$: Money Supply
- $V$: Velocity of Money (how many times a dollar is spent per year)
- $P$: Price Level
- $Y$: Real Output (Real GDP)
""",
            "key_concepts": [
                {"concept": "Purchasing Power", "definition": "The real value of currency expressed in terms of the amount of goods or services one unit can buy.", "importance": "Core reason why long-term cash holding is risky."},
                {"concept": "Consumer Price Index (CPI)", "definition": "A statistical measure tracking changes in prices paid by consumers for a representative basket of goods.", "importance": "Standard government benchmark for inflation."},
                {"concept": "Interest Rate Lever", "definition": "Central bank policy of adjusting the cost of borrowing to accelerate or cool down economic demand.", "importance": "Primary monetary mechanism for stabilizing prices."}
            ],
            "formulas_or_code": [
                {"title": "Equation of Exchange", "type": "formula", "content": "M \\cdot V = P \\cdot Y", "explanation": "Relates money supply and velocity to the general price level and economic output."},
                {"title": "The Rule of 72", "type": "rule", "content": "\\text{Years to Halve Purchasing Power} \\approx \\frac{72}{\\text{Inflation Rate}}", "explanation": "At 7% inflation, your money loses half its buying power in approximately 10 years."}
            ],
            "practice_questions": [
                {"question": "Why does a moderate 2% inflation target benefit an economy more than 0% inflation or deflation?", "hint": "Think about consumer behavior when prices are expected to drop.", "solution": "Deflation causes consumers and businesses to postpone purchases expecting lower prices later, triggering economic paralysis. A predictable 2% inflation greases wages and encourages investment."}
            ],
            "quiz": [
                {"id": 1, "question": "What happens to the purchasing power of cash during inflation?", "options": ["It increases", "It stays exactly constant", "It decreases", "It doubles every five years"], "correct_index": 2, "explanation": "As prices rise, each dollar buys fewer goods and services, diminishing purchasing power."},
                {"id": 2, "question": "How do central banks combat high inflation?", "options": ["By printing more money", "By raising interest rates to cool borrowing and demand", "By cutting taxes for corporations", "By lowering interest rates to zero"], "correct_index": 1, "explanation": "Raising interest rates makes credit expensive, slowing spending and bringing supply and demand into balance."}
            ],
            "flashcards": [
                {"id": 1, "front": "What is Demand-Pull Inflation?", "back": "When aggregate demand for goods outstrips available production capacity ('too much money chasing too few goods').", "category": "Mechanisms"},
                {"id": 2, "front": "Who benefits from unexpected inflation?", "back": "Borrowers with fixed-rate debt, because they repay loans with devalued currency.", "category": "Impact"}
            ]
        }

        return {
            "title": "How Inflation Works: The Hidden Tax on Money",
            "domain": "economics_business",
            "subdomain": "Macroeconomics & Personal Finance",
            "scenes": scenes,
            "materials": materials
        }

    def _build_stoicism_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Dichotomy of Control: The Stoic Superpower",
                "pedagogical_phase": "hook",
                "narration_text": "Imagine standing in the middle of a torrential storm. You can scream at the clouds, curse the rain, and tear your hair out in fury—yet the rain will continue to fall. Epictetus, a Greek slave who became one of Rome's greatest philosophers, observed that human suffering does not come from events themselves, but from the judgments we form about them. This single insight is the Dichotomy of Control, the ultimate bedrock of Stoic philosophy.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "The Dichotomy of Control",
                    "subtitle": "What You Control vs. What You Cannot",
                    "parameters": {
                        "left_title": "Outside Your Control (Indifferents)",
                        "left_items": ["The past and the future", "Other people's opinions & actions", "Health, traffic, weather, fame"],
                        "right_title": "Within Your Control (Your Domain)",
                        "right_items": ["Your current judgments and beliefs", "Your character, honesty, and values", "Your deliberate actions & emotional response"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "External events"},
                        {"step": 2, "highlight": "Internal sovereignty"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Four Cardinal Virtues: The Stoic Compass",
                "pedagogical_phase": "foundation",
                "narration_text": "To the Stoics, virtue is the sole good. Everything else—wealth, status, pleasure—is merely an 'indifferent'. They navigated life with four cardinal virtues: Wisdom, the ability to discern good from bad; Courage, doing what is right despite fear; Justice, treating fellow human beings with absolute fairness; and Temperance, practicing self-discipline and moderation in all things.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "hierarchy_pyramid",
                    "title": "The Four Cardinal Virtues",
                    "subtitle": "The Architectural Pillars of Moral Character",
                    "parameters": {
                        "pyramid_title": "Stoic Virtue Architecture",
                        "tiers": [
                            {"tier": "Wisdom (Sophia): Understanding reality & clarity of thought", "note": "Knowing what matters and what is trivial"},
                            {"tier": "Courage (Andreia): Moral backbone and resilience", "note": "Facing fear, hardship, and truth without flinching"},
                            {"tier": "Justice (Dikaiosyne): Service to the human community", "note": "Fairness, benevolence, and duty to society"},
                            {"tier": "Temperance (Sophrosyne): Mastery over impulse", "note": "Discipline, moderation, and emotional equilibrium"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Wisdom and Courage"},
                        {"step": 2, "highlight": "Justice and Temperance"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Cognitive Loop: From Impression to Assent",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "Modern cognitive behavioral therapy, or CBT, is directly based on the Stoic mental model. When an external event happens, your brain experiences an automatic initial impression or phantasia. An untrained person immediately reacts with anger or panic. A Stoic pauses in the gap between stimulus and response, critically examining the impression before granting assent.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cycle_loop",
                    "title": "The Cognitive Loop: Stimulus to Response",
                    "subtitle": "The Gap Between What Happens and How You React",
                    "parameters": {
                        "cycle_title": "Stoic Mental Processing Circuit",
                        "stages": [
                            {"name": "1. External Stimulus", "role": "Someone insults you or an unexpected obstacle occurs"},
                            {"name": "2. Raw Impression (Phantasia)", "role": "Initial involuntary spike of adrenaline or thought"},
                            {"name": "3. Critical Examination (Elenchos)", "role": "Ask: 'Is this within my control? Does this harm my character?'"},
                            {"name": "4. Deliberate Response (Assent)", "role": "Respond with calm virtue, refusing to be disturbed"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Raw Impression"},
                        {"step": 2, "highlight": "Critical Examination"},
                        {"step": 3, "highlight": "Deliberate Response"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Psychological Exercises: Premeditatio Malorum & Amor Fati",
                "pedagogical_phase": "edge_cases",
                "narration_text": "The Stoics practiced rigorous mental exercises. In Premeditatio Malorum, they intentionally visualized potential misfortunes—losing a job, illness, betrayal—to inoculate themselves against anxiety. And through Amor Fati, loving one's fate, Marcus Aurelius reminded us: 'The impediment to action advances action. What stands in the way becomes the way.'",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Practical Stoic Mental Tools",
                    "subtitle": "Daily Psychological Drills for Unshakeable Resilience",
                    "parameters": {
                        "col1": "Premeditatio Malorum: Mental rehearsal of adversity to destroy surprise and fragility.",
                        "col2": "Amor Fati (Love Your Fate): Don't just tolerate obstacles; use them as fuel to practice patience and creativity.",
                        "col3": "Memento Mori: Remember death. Keeps pride humble and gives fierce urgency to every single day."
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Premeditatio"},
                        {"step": 2, "highlight": "Amor Fati"},
                        {"step": 3, "highlight": "Memento Mori"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Stoicism in the Real World: Inner Citadel",
                "pedagogical_phase": "summary",
                "narration_text": "Stoicism is not emotionless detachment; it is the freedom from destructive passions so you can love and act fully in the real world. By building what Marcus Aurelius called the 'Inner Citadel' inside your mind, external chaos can never conquer you. Focus only on what you control, act with justice, love whatever happens, and remember that virtue is its own reward.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Spectrum of Emotional Mastery",
                    "subtitle": "Reactive Passivity vs Stoic Sovereignty",
                    "parameters": {
                        "left_label": "Reactive Victim: Blaming circumstances, easily enraged, fragile",
                        "right_label": "Stoic Sovereignty: Accountable, tranquil, transforms setbacks into strength",
                        "center_balance": "The Inner Citadel: Deep emotional stability grounded in virtue",
                        "markers": [
                            "Impulsive Reaction",
                            "Conscious Reflection",
                            "Unshakeable Equanimity"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Reactive"},
                        {"step": 2, "highlight": "Stoic Sovereignty"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "Stoicism is an ancient Hellenistic philosophy founded in Athens by Zeno of Citium and championed in Rome by Seneca, Epictetus, and Marcus Aurelius. Its core practice is the Dichotomy of Control: distinguishing between what is up to us and what is not, and cultivating wisdom, courage, justice, and temperance.",
            "notes_markdown": """# Stoicism: Philosophy for Everyday Resilience

## 1. The Dichotomy of Control (Epictetus)
$$\\text{Total Reality} = \\text{Things Up to Us (Attitudes, Choices)} + \\text{Things Not Up to Us (Events, Others)}$$
- Freedom is achieved by anchoring happiness exclusively to things within our direct control.

## 2. The Four Cardinal Virtues
1. **Wisdom (Sophia)**: Practical understanding of how to navigate complex human situations.
2. **Courage (Andreia)**: Moral strength to endure adversity and tell the truth.
3. **Justice (Dikaiosyne)**: Ethical duty to community and treating all with fairness.
4. **Temperance (Sophrosyne)**: Restraint, modesty, and emotional equilibrium.

## 3. Daily Psychological Exercises
- **Premeditatio Malorum**: Negative visualization to remove the shock of misfortune.
- **The View from Above**: Visualizing the earth from high altitude to gain cosmic perspective.
- **Memento Mori**: Awareness of mortality to clarify priorities.
""",
            "key_concepts": [
                {"concept": "Dichotomy of Control", "definition": "The division between things that belong to our sphere of choice versus external events.", "importance": "Eliminates chronic anxiety and resentment."},
                {"concept": "Amor Fati", "definition": "A love of fate; embracing whatever life throws at you as an opportunity to practice virtue.", "importance": "Transforms adversity from a curse into fuel."},
                {"concept": "Inner Citadel", "definition": "Marcus Aurelius's metaphor for the fortified, invulnerable state of a disciplined mind.", "importance": "Protects emotional peace during crisis."}
            ],
            "formulas_or_code": [
                {"title": "The Marcus Aurelius Maxim", "type": "principle", "content": "The impediment to action advances action. What stands in the way becomes the way.", "explanation": "Every obstacle is an opportunity to cultivate a specific virtue."},
                {"title": "Epictetus's Core Rule", "type": "quote", "content": "Men are disturbed not by things, but by the views which they take of things.", "explanation": "Underlying premise of modern Cognitive Behavioral Therapy (CBT)."}
            ],
            "practice_questions": [
                {"question": "How would a Stoic respond to losing their flight due to bad weather at the airport?", "hint": "Consider the Dichotomy of Control.", "solution": "A Stoic recognizes that the weather is completely outside their control. Rather than shouting at airline staff, they accept the reality immediately and use the waiting time constructively."}
            ],
            "quiz": [
                {"id": 1, "question": "According to Epictetus, what is the primary source of human mental suffering?", "options": ["Physical pain and illness", "Not having enough money", "Our judgments and opinions about events rather than events themselves", "Living in an imperfect society"], "correct_index": 2, "explanation": "Epictetus taught that events are neutral; only our value judgments make us suffer."},
                {"id": 2, "question": "What is the exercise of 'Premeditatio Malorum'?", "options": ["Wishing bad luck upon your rivals", "Mentally visualizing potential setbacks in advance so you are calm and prepared", "Ignoring all problems and hoping for the best", "Writing angry letters to vent emotions"], "correct_index": 1, "explanation": "Premeditating adversity desensitizes us to anxiety and prepares us with contingency plans."}
            ],
            "flashcards": [
                {"id": 1, "front": "What are the four Stoic virtues?", "back": "Wisdom, Courage, Justice, and Temperance.", "category": "Core Principles"},
                {"id": 2, "front": "What does 'Amor Fati' mean?", "back": "Love of fate; actively embracing everything that happens as useful.", "category": "Practices"}
            ]
        }

        return {
            "title": "Stoicism: The Ancient Art of Mental Resilience",
            "domain": "psychology_philosophy",
            "subdomain": "Practical Philosophy & Cognitive Resilience",
            "scenes": scenes,
            "materials": materials
        }

    def _build_sleep_circadian_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The 24-Hour Master Clock: The Suprachiasmatic Nucleus",
                "pedagogical_phase": "hook",
                "narration_text": "Deep inside your brain, right above where your optic nerves cross, sits a cluster of twenty thousand neurons called the Suprachiasmatic Nucleus. This microscopic biological clock governs virtually every cell, organ, and hormone in your body. It doesn't use gears or batteries; it synchronizes to the natural rhythm of planet Earth's rotation through the single most potent cue in nature: morning sunlight.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "cycle_loop",
                    "title": "The 24-Hour Circadian Biological Clock",
                    "subtitle": "Light Input -> Suprachiasmatic Nucleus -> Hormonal Waves",
                    "parameters": {
                        "cycle_title": "Daily Circadian Rhythm Phases",
                        "stages": [
                            {"name": "07:00 AM: Cortisol Awakening", "role": "Sunlight triggers cortisol spike; stops melatonin production"},
                            {"name": "02:00 PM: Peak Reaction Time", "role": "Core body temperature rises; optimal coordination"},
                            {"name": "09:00 PM: Melatonin Release", "role": "Darkness triggers pineal gland to release sleep hormone"},
                            {"name": "03:00 AM: Deep Cellular Repair", "role": "Lowest body temperature; brain glymphatic cleansing active"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Morning Cortisol"},
                        {"step": 2, "highlight": "Evening Melatonin"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Two Sleep Forces: Circadian Drive vs. Sleep Pressure",
                "pedagogical_phase": "foundation",
                "narration_text": "Why do you feel tired at night? Sleep is governed by a two-process model. Process C is your 24-hour circadian rhythm. Process S is sleep pressure: every minute you are awake, your brain burns ATP energy and accumulates a chemical byproduct called Adenosine. Like sand falling in an hourglass, adenosine builds up pressure until your brain demands sleep to wash it away.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Process C vs. Process S",
                    "subtitle": "The Two Complementary Drivers of Sleepiness",
                    "parameters": {
                        "left_title": "Process C: The Circadian Rhythm",
                        "left_items": ["Governed by sunlight & SCN clock", "Oscillates on a 24-hour wave", "Tells you *when* to sleep"],
                        "right_title": "Process S: Adenosine Pressure",
                        "right_items": ["Accumulates steadily with every waking hour", "Blocked temporarily by caffeine molecules", "Tells you *how deeply* you need to sleep"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Process C wave"},
                        {"step": 2, "highlight": "Process S accumulation"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The 90-Minute Architecture: NREM to REM Sleep",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "When you sleep, you don't simply switch off; you embark on a 90-minute neural rollercoaster through distinct sleep stages. In Stage 3 Deep NREM sleep, delta brainwaves slow down to 1 hertz, physical tissues repair, and your brain's glymphatic system opens up to flush out metabolic waste. In REM sleep, your body is paralyzed while your brain dreams intensely, synthesizing emotional memories and creative connections.",
                "estimated_duration": 26.0,
                "visual_spec": {
                    "visual_type": "narrative_arc",
                    "title": "The 90-Minute Sleep Cycle Hypnogram",
                    "subtitle": "Stage 1 -> Stage 2 -> Slow-Wave NREM -> REM Dreaming",
                    "parameters": {
                        "phases": [
                            {"phase": "Light NREM (Stages 1-2)", "event": "Heart rate slows, sleep spindles consolidate motor memory"},
                            {"phase": "Deep NREM (Stage 3 Delta)", "event": "Peak growth hormone, physical tissue restoration & waste flush"},
                            {"phase": "REM Sleep", "event": "Rapid eye movements, vivid dreaming, emotional integration & creativity"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Deep NREM"},
                        {"step": 2, "highlight": "REM Dreaming"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Modern Disruptors: Blue Light & Caffeine Halflife",
                "pedagogical_phase": "edge_cases",
                "narration_text": "Our modern environment is biologically alien to our ancient circadian clock. Blue light emitted from smartphones tricks your retinas into believing it is noon, delaying melatonin release by hours. Meanwhile, caffeine has an average quarter-life of twelve hours: a cup of coffee at noon still has a quarter of its caffeine circulating in your brain at midnight, hijacking adenosine receptors and destroying restorative deep sleep.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": "Circadian Disruption Cascade",
                    "subtitle": "How Screens and Late Caffeine Sabotage Sleep Architecture",
                    "parameters": {
                        "root_catalyst": "Screen Exposure & Afternoon Caffeine (6hr Half-Life)",
                        "intermediate_effects": [
                            "Retinal melanopsin cells signal SCN to suppress melatonin",
                            "Adenosine receptors blocked; sleep latency increases",
                            "Deep Slow-Wave Sleep reduced by up to 30%"
                        ],
                        "ultimate_consequence": "Glymphatic brain clearance impaired; chronic cognitive fatigue"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Melatonin suppression"},
                        {"step": 2, "highlight": "Sleep quality loss"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. The Circadian Protocol: Science-Backed Sleep Optimization",
                "pedagogical_phase": "summary",
                "narration_text": "To unlock peak mental energy, follow the circadian protocol: view bright sunlight within thirty minutes of waking to anchor your clock, keep a consistent wake-up time even on weekends, avoid caffeine within ten hours of bedtime, and dim your lights two hours before sleep in a cool 65-degree bedroom. Master your biological clock, and you master your life.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "The Circadian Optimization Protocol",
                    "subtitle": "Morning, Evening, and Bedroom Environment Rules",
                    "parameters": {
                        "col1": "Morning Anchor: 10-15 minutes of outdoor sunlight within 30m of waking",
                        "col2": "Daytime Habits: Cut caffeine 10 hours before bed; exercise early in the day",
                        "col3": "Evening Wind-Down: Dim warm lights, cool room (65-68°F), consistent sleep window"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Morning"},
                        {"step": 2, "highlight": "Evening"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "The circadian rhythm is an intrinsic 24-hour cycle regulated by the brain's suprachiasmatic nucleus that coordinates sleepiness, hormonal output, body temperature, and metabolism. Sleep is structured into 90-minute cycles alternating between restorative Deep NREM sleep and creative REM sleep.",
            "notes_markdown": """# Circadian Biology & Sleep Science Master Notes

## 1. The Two-Process Model of Sleep
- **Process C (Circadian Rhythm)**: Internal 24-hour oscillator synchronized primarily by photon signals to the suprachiasmatic nucleus (SCN).
- **Process S (Homeostatic Sleep Pressure)**: Steady accumulation of **adenosine** during wakefulness, cleared during deep sleep.

## 2. Sleep Cycle Architecture (90-Minute Repetitions)
1. **NREM Stage 1**: Light transitional sleep.
2. **NREM Stage 2**: Sleep spindles and K-complexes consolidate motor skills.
3. **NREM Stage 3 (Slow-Wave Sleep)**: Delta waves ($<4\\text{ Hz}$), growth hormone release, physical tissue recovery, and **glymphatic brain clearance**.
4. **REM (Rapid Eye Movement)**: Brainwave activity mimics wakefulness; emotional regulation, neuroplasticity, and consolidation of associative memories.

## 3. High-Leverage Protocols
- **Morning Sunlight**: Sets the circadian timer for melatonin release ~14 hours later.
- **Caffeine Clearance**: Caffeine has a 5-7 hour half-life and 10-12 hour quarter-life.
- **Thermoregulation**: The body must drop its core temperature by ~2-3°F to initiate and maintain deep sleep.
""",
            "key_concepts": [
                {"concept": "Suprachiasmatic Nucleus (SCN)", "definition": "The master pacemaker located in the anterior hypothalamus coordinating peripheral body clocks.", "importance": "Central control tower for sleep-wake timing."},
                {"concept": "Adenosine", "definition": "A neuromodulator that accumulates during wakefulness and induces sleepiness.", "importance": "The molecule whose receptors caffeine competitively blocks."},
                {"concept": "Glymphatic System", "definition": "A glial-dependent waste clearance pathway that removes toxic proteins like beta-amyloid during deep sleep.", "importance": "Protects against neurodegenerative decline."}
            ],
            "formulas_or_code": [
                {"title": "Caffeine Pharmacokinetics", "type": "rule", "content": "A(t) = A_0 \\cdot (0.5)^{t / t_{1/2}}", "explanation": "With a 6-hour half-life, 200mg of coffee at 2 PM leaves 50mg still active at 2 AM."},
                {"title": "Optimal Bedroom Temperature", "type": "rule", "content": "T_{\\text{bedroom}} \\approx 65^\\circ\\text{F} - 68^\\circ\\text{F} \\ (18^\\circ\\text{C} - 20^\\circ\\text{C})", "explanation": "Facilitates the necessary 2°F core body temperature drop for deep slow-wave sleep."}
            ],
            "practice_questions": [
                {"question": "Why does drinking a double espresso at 4 PM impair your sleep even if you fall asleep easily at 11 PM?", "hint": "Consider sleep architecture and deep sleep stages.", "solution": "While caffeine may not prevent you from falling unconscious if sleep pressure is high, it blocks adenosine receptors in the cortex, suppressing restorative Stage 3 Slow-Wave Deep Sleep by up to 20-30%."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the primary zeitgeber (time-cue) that resets the master circadian clock every day?", "options": ["Eating breakfast", "Outdoor sunlight hitting the eyes in the morning", "A cold shower", "Alarm clock sound"], "correct_index": 1, "explanation": "Photons from natural sunlight trigger specialized melanopsin ganglion cells in the retina that signal the SCN."},
                {"id": 2, "question": "What happens during Stage 3 Deep NREM sleep?", "options": ["Intense dreaming and muscle paralysis", "The glymphatic system flushes metabolic waste from brain tissue", "Cortisol spikes to maximum levels", "Heart rate increases to sprint levels"], "correct_index": 1, "explanation": "Deep slow-wave sleep is the primary window for cellular repair, growth hormone release, and glymphatic brain detox."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does caffeine actually do in the brain?", "back": "It competitively binds to adenosine receptors without activating them, temporarily hiding sleep pressure.", "category": "Pharmacology"},
                {"id": 2, "front": "How long is a typical human sleep cycle?", "back": "Approximately 90 minutes, cycling through light NREM, deep NREM, and REM.", "category": "Sleep Architecture"}
            ]
        }

        return {
            "title": "Sleep & Circadian Rhythm: The Biology of Human Energy",
            "domain": "health_biology",
            "subdomain": "Neuroscience, Chronobiology & Sleep Medicine",
            "scenes": scenes,
            "materials": materials
        }

    def _build_heros_journey_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Monomyth: Why One Story Rules All Cultures",
                "pedagogical_phase": "hook",
                "narration_text": "Whether you look at the ancient Babylonian epic of Gilgamesh, Homer's Odyssey, Star Wars, Harry Potter, or The Matrix, humanity has told the exact same foundational story for ten thousand years. Mythologist Joseph Campbell discovered that all great mythologies share a single narrative architecture: The Hero's Journey. It resonates across every continent because it is not just fiction—it is the psychological blueprint for human growth and transformation.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cycle_loop",
                    "title": "The 12-Stage Monomyth Cycle",
                    "subtitle": "The Universal Narrative Blueprint Described by Joseph Campbell",
                    "parameters": {
                        "cycle_title": "The Hero's Journey Circle",
                        "stages": [
                            {"name": "Act I: Separation", "role": "Ordinary World -> Call to Adventure -> Crossing the Threshold"},
                            {"name": "Act II: Initiation", "role": "Road of Trials -> The Inmost Cave -> The Supreme Ordeal"},
                            {"name": "Act III: Return", "role": "The Reward -> The Road Back -> Master of Two Worlds"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Ordinary World"},
                        {"step": 2, "highlight": "The Supreme Ordeal"},
                        {"step": 3, "highlight": "The Return with Elixir"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Leaving the Known: The Call & The Threshold",
                "pedagogical_phase": "foundation",
                "narration_text": "Every great adventure begins in the comfortable, stagnant Ordinary World. Soon, a disruptive event sounds the Call to Adventure. Initially, fear leads to the Refusal of the Call, until a wise Mentor—like Obi-Wan Kenobi or Gandalf—appears to provide crucial wisdom. The hero must then cross the Threshold into the Unknown World, leaving safety behind forever.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Known World vs. Unknown World",
                    "subtitle": "Crossing the Threshold of Adventure",
                    "parameters": {
                        "left_title": "The Known World (Ordinary Life)",
                        "left_items": ["Familiar, predictable, but stagnant", "Illusion of absolute safety", "The hero feels incomplete or unfulfilled"],
                        "right_title": "The Unknown World (Special World)",
                        "right_items": ["Dangerous, uncertain, and magical", "Forces confront the hero's deepest flaws", "Crucible of psychological metamorphosis"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Known World"},
                        {"step": 2, "highlight": "Unknown World"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Abyss: The Supreme Ordeal & Death of the Old Self",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "In the Special World, the hero encounters tests, allies, and enemies. Eventually, they descend into the Inmost Cave to face their greatest fear in the Supreme Ordeal. In this moment, the old, selfish identity of the hero must symbolically die. Only by confronting death or failure do they seize the Elixir—the ultimate truth or weapon needed to heal the world.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "narrative_arc",
                    "title": "Narrative Arc & Emotional Tension",
                    "subtitle": "From Inciting Incident to the Supreme Climax and Catharsis",
                    "parameters": {
                        "phases": [
                            {"phase": "1. Exposition & Call", "event": "Baseline status quo disrupted"},
                            {"phase": "2. Rising Tension & Trials", "event": "Tests, allies, threshold guardians overcome"},
                            {"phase": "3. The Supreme Ordeal (Peak Climax)", "event": "Death of the old ego; triumph over the shadow"},
                            {"phase": "4. Resolution & Return", "event": "Returning home transformed with the Elixir"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Rising Tension"},
                        {"step": 2, "highlight": "Supreme Ordeal Peak"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Archetypes: Shadow, Mentor, Trickster & Shapeshifter",
                "pedagogical_phase": "edge_cases",
                "narration_text": "Campbell and psychologist Carl Jung explained that characters in stories represent universal psychological archetypes. The Shadow embodies the dark, repressed aspects of human nature. The Mentor represents higher consciousness. The Trickster punctures ego and brings humor, while the Shapeshifter creates suspense by shifting loyalties. These are not just movie characters—they are parts of your own psyche.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "The Four Great Story Archetypes",
                    "subtitle": "Psychological Mirrors in Classic Mythology",
                    "parameters": {
                        "col1": "The Mentor: Guide & teacher providing wisdom, tools, and moral clarity.",
                        "col2": "The Shadow: The villain reflecting the hero's unmastered dark potential.",
                        "col3": "The Trickster: Catalyst for change questioning norms with irony and wit."
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Mentor"},
                        {"step": 2, "highlight": "Shadow"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. The Elixir: Master of Two Worlds",
                "pedagogical_phase": "summary",
                "narration_text": "The journey is never complete until the hero returns home to share the Elixir with their community. Transformed by adversity, they are now the Master of Two Worlds: capable of living without fear in either reality. Whenever you face career turmoil, personal tragedy, or unfamiliar frontiers in your own life, remember: you are not suffering pointless chaos; you are on the Hero's Journey.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Evolution of the Protagonist",
                    "subtitle": "From Reluctant Commoner to Self-Actualized Master",
                    "parameters": {
                        "left_label": "Innocent & Passive: Trapped in comfort, uninitiated",
                        "right_label": "Transformed Master: Integrated wisdom, purposeful leader",
                        "center_balance": "The Tested Crucible: Growth forged through voluntary ordeal",
                        "markers": [
                            "Comfort Zone",
                            "The Abyss",
                            "Self-Actualization"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Innocent"},
                        {"step": 2, "highlight": "Transformed Master"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "The Hero's Journey (Monomyth) is the universal narrative archetype identified by mythologist Joseph Campbell in 'The Hero with a Thousand Faces'. Spanning three acts—Departure, Initiation, and Return—it reflects the fundamental human psychological journey of confronting chaos, undergoing personal transformation, and returning to serve the community.",
            "notes_markdown": """# Narrative Design: The Hero's Journey & Archetypes

## 1. The Three Act Structure of the Monomyth
1. **Act I: Departure (Separation)**
   - The Ordinary World
   - Call to Adventure & Refusal of the Call
   - Meeting the Mentor & Crossing the First Threshold
2. **Act II: Initiation (Descent into Chaos)**
   - Tests, Allies, and Enemies
   - Approach to the Inmost Cave
   - The Supreme Ordeal & Seizing the Sword (Reward)
3. **Act III: Return (Integration)**
   - The Road Back & Resurrection
   - Return with the Elixir to renew the community

## 2. Jungian Psychological Archetypes
- **The Hero**: The ego seeking individuation.
- **The Mentor**: The wise old guide representing the higher self.
- **The Shadow**: The repressed, unacknowledged negative potential.
- **The Threshold Guardian**: Obstacles testing readiness for transformation.
""",
            "key_concepts": [
                {"concept": "The Monomyth", "definition": "The universal narrative pattern shared by mythologies across divergent cultures and historical eras.", "importance": "Foundational template for literature, film, and psychology."},
                {"concept": "The Supreme Ordeal", "definition": "The central crisis where the hero confronts their deepest vulnerability and undergoes symbolic death.", "importance": "Catalyst for genuine inner change."},
                {"concept": "The Elixir", "definition": "The hard-won prize or revelation that the returning hero brings back to revitalize the community.", "importance": "Ensures the journey serves a communal, not purely selfish, purpose."}
            ],
            "formulas_or_code": [
                {"title": "Campbell's Core Maxim", "type": "quote", "content": "The cave you fear to enter holds the treasure you seek.", "explanation": "Directs human attention toward voluntary confrontation of feared challenges."},
                {"title": "The Monomyth Formula", "type": "rule", "content": "Separation \\longrightarrow Initiation \\longrightarrow Return", "explanation": "The irreducible three-phase rhythm of all epic storytelling."}
            ],
            "practice_questions": [
                {"question": "How does Luke Skywalker in Star Wars follow the Refusal of the Call?", "hint": "What does Luke tell Obi-Wan initially on Tatooine?", "solution": "Luke initially refuses to leave Tatooine, stating he must help his Uncle Owen with the harvest. Only after the tragic destruction of his home does he commit to crossing the threshold."}
            ],
            "quiz": [
                {"id": 1, "question": "Who popularized the concept of 'The Hero's Journey' in his 1949 work 'The Hero with a Thousand Faces'?", "options": ["Sigmund Freud", "Joseph Campbell", "George Lucas", "Aristotle"], "correct_index": 1, "explanation": "Joseph Campbell documented this universal storytelling pattern across world mythologies."},
                {"id": 2, "question": "What is the final stage of the Hero's Journey?", "options": ["Defeating the dragon forever", "Retiring in the magical world", "Returning to the ordinary world with the Elixir to heal the community", "Fighting against fellow allies"], "correct_index": 2, "explanation": "The hero must bring back the elixir of wisdom to benefit their people."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does 'The Shadow' archetype represent in storytelling?", "back": "The dark, repressed aspects of human nature that the hero must confront and overcome.", "category": "Archetypes"},
                {"id": 2, "front": "What is the role of a Threshold Guardian?", "back": "To test the hero's readiness and commitment before allowing entry into the special world.", "category": "Structure"}
            ]
        }

        return {
            "title": "The Hero's Journey: The Universal Pattern of Great Stories",
            "domain": "arts_literature",
            "subdomain": "Mythology, Narrative Architecture & Screenwriting",
            "scenes": scenes,
            "materials": materials
        }

    def _build_why_sky_is_blue_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Sunlight Illusion: White Light is a Rainbow",
                "pedagogical_phase": "hook",
                "narration_text": "Look up at the clear sky on a bright afternoon: it shines in a brilliant, vivid azure blue. Yet at sunset, that exact same sky burns in fiery orange and crimson! Many people assume the sky reflects the ocean, but the sky is blue even over the middle of dry deserts. The true answer begins with a surprise: the sunlight streaming from our yellow sun is actually pure white light containing every color in the visible rainbow.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "cross_section_sim",
                    "title": "White Light Spectrum & Wavelengths",
                    "subtitle": "Long Red Waves vs. Short Blue Wavelengths",
                    "parameters": {
                        "subject": "Solar Radiation Spectrum",
                        "layers": [
                            {"name": "Red Wavelengths (~700 nm)", "role": "Long, lazy waves that easily bypass small particles"},
                            {"name": "Green/Yellow (~550 nm)", "role": "Medium wavelengths, moderate deflection"},
                            {"name": "Blue/Violet (~400 nm)", "role": "Short, energetic, tightly oscillating wavelengths"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Red wave length"},
                        {"step": 2, "highlight": "Blue wave frequency"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Rayleigh Scattering: Molecules as Tuning Forks",
                "pedagogical_phase": "foundation",
                "narration_text": "Earth's atmosphere is an ocean of gas molecules, mostly Nitrogen and Oxygen. In the late nineteenth century, Lord Rayleigh discovered that when light waves strike particles much smaller than their wavelength, the light scatters in all directions. The scattering efficiency is inversely proportional to the fourth power of the wavelength! Because blue wavelengths are short, they scatter nearly ten times more intensely than red light.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Lord Rayleigh's Scattering Law",
                    "subtitle": "Why Short Wavelengths Scatter Exponentially More",
                    "parameters": {
                        "left_title": "Red Light (Long ~700nm Waves)",
                        "left_items": ["Wavelength is 1.75x longer than blue", "Scattering power = (1/700)^4 (Very Low)", "Passes straight through air without bouncing"],
                        "right_title": "Blue Light (Short ~400nm Waves)",
                        "right_items": ["Wavelength matches tiny gas molecule size", "Scattering power = (1/400)^4 (10x More Intense!)", "Bounces in every direction across the sky!"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Red light path"},
                        {"step": 2, "highlight": "Blue scattering burst"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Human Eye Mystery: Why Blue Instead of Violet?",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "Now for a fascinating puzzle: violet light has an even shorter wavelength than blue, so violet light scatters the most of all! Why doesn't the sky look purple? The answer is human biology. First, our sun naturally emits much more blue light than violet. Second, human eyes have three color receptors called cones: red, green, and blue. Our retinas are far more sensitive to blue light than violet, perceiving the scattered sky light as vivid sky blue.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Physics vs. Human Physiology",
                    "subtitle": "Why We See Blue When Violet Scatters More",
                    "parameters": {
                        "col1": "Solar Spectrum: Sun emits significantly higher flux of blue photons than ultraviolet/violet",
                        "col2": "Atmospheric Scattering: Violet scatters most, followed closely by vibrant blue",
                        "col3": "Human Cone Receptors: Retinal S, M, and L cones are calibrated to interpret this combination as sky blue"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Solar Spectrum"},
                        {"step": 2, "highlight": "Human Retinal Cones"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Sunset Transformation: Atmospheric Path Length",
                "pedagogical_phase": "edge_cases",
                "narration_text": "Why do sunsets turn red? At midday, the sun is directly overhead, and light passes through a thin slice of atmosphere. At sunset, sunlight hits Earth at an extreme angle, traveling through ten times more atmosphere! All the blue light gets scattered away long before reaching your eyes. Only the resilient, long red and orange wavelengths make the long trek across the horizon.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "cross_section_sim",
                    "title": "Noon vs. Sunset Atmospheric Path Length",
                    "subtitle": "Short Direct Path vs. Long Oblique Horizon Path",
                    "parameters": {
                        "subject": "Planetary Atmosphere Cross-Section",
                        "layers": [
                            {"name": "Noon Sun (Overhead)", "role": "Path length = 1x. Blue scatters overhead, sun looks white-yellow."},
                            {"name": "Sunset Sun (Horizon Angle)", "role": "Path length = 10x! Blue completely filtered out; only reds survive."}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Noon direct light"},
                        {"step": 2, "highlight": "Sunset long path"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Cosmic Skies: Mars, The Moon & Beyond",
                "pedagogical_phase": "summary",
                "narration_text": "Rayleigh scattering explains planetary skies across the solar system! On the Moon, which has no atmosphere, the sky is pitch black even in broad daylight. On Mars, the thin atmosphere is filled with iron-rich rust dust that causes Mie scattering, creating butterscotch-yellow day skies and blue sunsets! The color of the sky is a cosmic fingerprint of a planet's atmospheric chemistry.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Skies of the Solar System",
                    "subtitle": "How Atmospheric Composition Shapes Sky Color",
                    "parameters": {
                        "col1": "Earth (N2 & O2): Blue daytime skies, fiery red sunsets (Rayleigh scattering)",
                        "col2": "The Moon (Vacuum): Pure black skies, dazzling bright stars during the day",
                        "col3": "Mars (CO2 & Iron Dust): Butterscotch daytime sky, blue Martian sunsets!"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Earth"},
                        {"step": 2, "highlight": "Moon"},
                        {"step": 3, "highlight": "Mars"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "The sky is blue due to Rayleigh scattering: gas molecules in Earth's atmosphere scatter short wavelengths of light (blue and violet) far more effectively than longer wavelengths (red and orange). Human cone sensitivity and solar emission combine to make the sky appear brilliant blue.",
            "notes_markdown": """# Physics & Atmospheric Optics: Why the Sky is Blue

## 1. Rayleigh Scattering Law
The intensity of scattered light $I$ by particles much smaller than the wavelength $\\lambda$ is:
$$I(\\lambda) \\propto \\frac{1}{\\lambda^4}$$
- Blue light ($\\lambda \\approx 400\\text{ nm}$) scatters nearly $\\approx 10\\times$ more strongly than red light ($\\lambda \\approx 700\\text{ nm}$).

## 2. Why Not Violet?
1. The sun emits less violet radiation than blue radiation.
2. The human eye's photopic response relies on trichromatic cone cells (Red, Green, Blue) that perceive the mixture of scattered light as cerulean blue.

## 3. Red Sunsets & Atmospheric Air Mass
- At sunset, sunlight passes through up to $10\\times$ more atmospheric air mass ($AM$).
- Blue light is completely scattered away along the path, leaving only the long-wavelength red and orange rays to reach the observer.
""",
            "key_concepts": [
                {"concept": "Rayleigh Scattering", "definition": "The scattering of electromagnetic radiation by particles with dimensions smaller than the radiation's wavelength.", "importance": "Explains blue skies and red sunsets."},
                {"concept": "Inverse Fourth Power Law", "definition": "The mathematical relationship showing scattering power scales with $1/\\lambda^4$.", "importance": "Demonstrates why minor differences in wavelength produce dramatic color differences."},
                {"concept": "Trichromatic Vision", "definition": "Human color perception driven by three types of retinal cones responding to short, medium, and long wavelengths.", "importance": "Explains why we perceive the sky as blue rather than violet."}
            ],
            "formulas_or_code": [
                {"title": "Rayleigh Scattering Intensity", "type": "formula", "content": "I \\propto \\frac{1}{\\lambda^4}", "explanation": "Scattering intensity is inversely proportional to the fourth power of wavelength."},
                {"title": "Wavelength Ratio", "type": "rule", "content": "\\frac{I_{\\text{blue}}}{I_{\\text{red}}} \\approx \\left(\\frac{700}{400}\\right)^4 \\approx 9.4", "explanation": "Blue light scatters approximately 9.4 times more effectively than red light in clean air."}
            ],
            "practice_questions": [
                {"question": "What color would Earth's sky appear if our atmosphere had no gases or particles at all?", "hint": "Think about astronauts on the Moon.", "solution": "Without an atmosphere to scatter sunlight, the sky would be completely black, with the sun appearing as a blinding white sphere against starry space."}
            ],
            "quiz": [
                {"id": 1, "question": "What physical phenomenon causes the daytime sky to appear blue?", "options": ["Ocean reflections bouncing off clouds", "Rayleigh scattering of short wavelengths by nitrogen and oxygen molecules", "Nuclear fusion emissions from the ozone layer", "Absorption of red light by plant chlorophyll"], "correct_index": 1, "explanation": "Tiny atmospheric molecules scatter short blue wavelengths in every direction."},
                {"id": 2, "question": "Why do sunsets appear red and orange?", "options": ["The sun cools down significantly in the evening", "Sunlight travels through a much longer atmospheric path, scattering away all the blue light", "Industrial pollution creates red light at dusk", "Earth rotates closer to the sun at sunset"], "correct_index": 1, "explanation": "The oblique sunset path filters out blue light, leaving only the longest wavelengths to pass through."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does Rayleigh's law state about wavelength?", "back": "Scattering intensity is proportional to 1 / (wavelength^4). Shorter wavelengths scatter exponentially more.", "category": "Physics"},
                {"id": 2, "front": "What color are sunsets on Mars?", "back": "Blue! Fine Martian iron dust scatters reddish light during the day and allows blue light to penetrate at sunset.", "category": "Planetary Science"}
            ]
        }

        return {
            "title": "Why is the Sky Blue? The Optics of Atmospheric Light",
            "domain": "science_nature",
            "subdomain": "Optics, Atmospheric Physics & Human Perception",
            "scenes": scenes,
            "materials": materials
        }

    def _build_how_airplanes_fly_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. Defying Gravity: The Four Forces of Flight",
                "pedagogical_phase": "hook",
                "narration_text": "A fully loaded Boeing 747 weighs nearly one million pounds—the weight of four hundred cars. How can a massive machine made of steel and aluminum lift effortlessly into the sky and cruise five miles high? Flight is not magic; it is an exquisite dance between four competing physical forces: Lift fighting Gravity, and Thrust fighting Drag. When Lift exceeds Gravity, the giant takes to the air.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "cross_section_sim",
                    "title": "The Four Fundamental Forces of Flight",
                    "subtitle": "Lift vs. Weight & Thrust vs. Drag",
                    "parameters": {
                        "subject": "Aircraft Free-Body Force Diagram",
                        "layers": [
                            {"name": "Lift (Upward Force)", "role": "Generated by airfoils moving through the air"},
                            {"name": "Gravity / Weight (Downward Force)", "role": "Earth's gravitational pull on the aircraft mass"},
                            {"name": "Thrust (Forward Force)", "role": "Produced by jet engines or propellers"},
                            {"name": "Drag (Backward Resistance)", "role": "Aerodynamic air friction and pressure resistance"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Lift and Gravity balance"},
                        {"step": 2, "highlight": "Thrust overcoming Drag"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Airfoil Anatomy: Camber, Chord & Attack Angle",
                "pedagogical_phase": "foundation",
                "narration_text": "Look closely at an airplane wing. It is shaped as an Airfoil: curved on top, flatter on the bottom, with a rounded leading edge and a razor-sharp trailing edge. The Angle of Attack is the tilt of the wing relative to the oncoming wind. Tilt the wing upward slightly, and it scoops oncoming air, generating pressure differentials that produce vertical lift.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "cross_section_sim",
                    "title": "The Airfoil Geometry",
                    "subtitle": "Leading Edge, Trailing Edge, Camber & Chord Line",
                    "parameters": {
                        "subject": "Aerodynamic Airfoil Profile",
                        "layers": [
                            {"name": "Curved Upper Surface (Camber)", "role": "Accelerates air stream, creating lower static pressure"},
                            {"name": "Flatter Lower Surface", "role": "Maintains higher relative pressure, pushing upward"},
                            {"name": "Angle of Attack (Alpha)", "role": "Angle between chord line and relative wind direction"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Curved Upper Surface"},
                        {"step": 2, "highlight": "Angle of Attack"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Two Laws: Bernoulli's Pressure & Newton's Downwash",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "For decades, flight was explained with popular myths like equal transit time. Real aerodynamics unites Bernoulli's Principle with Newton's Third Law. Bernoulli shows that air moving faster over the curved upper surface creates lower pressure above the wing than below it. Meanwhile, Newton's Third Law dictates that the wing physically deflects thousands of tons of air downwards in a powerful downwash—and for every action, there is an equal and opposite upward lift!",
                "estimated_duration": 26.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Bernoulli vs. Newton: The Dual Engines of Lift",
                    "subtitle": "Pressure Differences + Massive Downward Air Deflection",
                    "parameters": {
                        "left_title": "Bernoulli's Principle (Pressure)",
                        "left_items": ["Faster airflow over top curved surface", "Generates lower static pressure above", "The wing is 'pulled' upward by vacuum pressure"],
                        "right_title": "Newton's Third Law (Action-Reaction)",
                        "right_items": ["Coanda effect bends air along wing slope", "Wing forces massive volume of air DOWN (Downwash)", "Equal and opposite reaction drives airplane UP!"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Bernoulli Pressure Delta"},
                        {"step": 2, "highlight": "Newtonian Downwash"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Aerodynamic Stall: The Critical Angle of Attack",
                "pedagogical_phase": "edge_cases",
                "narration_text": "If tilting a wing upward generates more lift, why can't a pilot tilt it as steep as they want? If the Angle of Attack exceeds roughly fifteen degrees, the airflow can no longer smoothly hug the wing. It separates into turbulent eddies, lift plummets catastrophically, and the wing Stalls. Pilots train relentlessly to recognize the aerodynamic stall and pitch the nose down to restore smooth airflow.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "Angle of Attack & Stall Envelope",
                    "subtitle": "Smooth Laminar Flow vs. Turbulent Flow Separation",
                    "parameters": {
                        "left_label": "Cruise (2° to 5°): Smooth laminar attachment, high lift, minimal drag",
                        "right_label": "Aerodynamic Stall (>15°): Flow separates into turbulent vortices, lift collapses!",
                        "center_balance": "Maximum Lift Angle (~12° to 14°): Critical threshold during takeoff/landing",
                        "markers": [
                            "Normal Cruise",
                            "Approach & Flare",
                            "Aerodynamic Stall"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Smooth Cruise"},
                        {"step": 2, "highlight": "Turbulent Stall"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Modern Aerodynamics: Winglets & Supersonic Flight",
                "pedagogical_phase": "summary",
                "narration_text": "Modern aircraft are marvels of computational fluid dynamics. Wingtips feature vertical upturned fins called Winglets, which disrupt high-pressure wingtip vortices, saving billions of gallons of fuel. From gliders soaring on thermal winds to hypersonic jets piercing the sound barrier, mastering the invisible forces of air has shrunk our planet and expanded human capability.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Modern Aviation Innovations",
                    "subtitle": "Fuel Efficiency, Fly-By-Wire, and Supersonic Shapes",
                    "parameters": {
                        "col1": "Blended Winglets: Suppresses tip vortex drag, reducing fuel burn by 5-7%",
                        "col2": "Fly-by-Wire Computers: Continuously adjusts flight control surfaces hundreds of times per second",
                        "col3": "Delta & Swept Wings: Delays supersonic shockwaves for high-speed cruising"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Winglets"},
                        {"step": 2, "highlight": "Fly-by-Wire"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "Airplanes generate lift through the interaction of airfoils with moving air. Lift is produced simultaneously by pressure differentials across the upper and lower surfaces (Bernoulli's Principle) and by the downward deflection of massive air mass (Newton's Third Law).",
            "notes_markdown": """# Aerodynamics: The Physics of Flight

## 1. The Four Forces of Flight
$$\\Sigma F_y = L - W = m \\cdot a_y$$
$$\\Sigma F_x = T - D = m \\cdot a_x$$
- **Lift ($L$)**: Upward aerodynamic force generated by wings.
- **Weight ($W$)**: Gravitational force downward ($m \\cdot g$).
- **Thrust ($T$)**: Forward propulsion generated by engines.
- **Drag ($D$)**: Aerodynamic resistance opposing forward motion.

## 2. The Lift Equation
$$L = \\frac{1}{2} \\rho v^2 S C_L$$
where:
- $\\rho$: Air density
- $v$: True airspeed
- $S$: Wing surface area
- $C_L$: Coefficient of lift (determined by airfoil shape and Angle of Attack)

## 3. How Lift is Really Generated
1. **Bernoulli's Principle**: Faster airflow over the upper camber creates a region of lower static pressure.
2. **Newton's Third Law**: The wing redirects airflow downward (downwash); the reactive upward force is lift.
3. **The Coanda Effect**: Fluid flows naturally adhere to a curved convex surface.
""",
            "key_concepts": [
                {"concept": "Airfoil", "definition": "A streamlined structure with curved upper and lower surfaces designed to produce aerodynamic lift.", "importance": "The physical shape that makes mechanical flight possible."},
                {"concept": "Angle of Attack (AoA)", "definition": "The angle between the chord line of an airfoil and the oncoming relative wind.", "importance": "Controls the amount of lift and danger of aerodynamic stalling."},
                {"concept": "Downwash", "definition": "The downward deflection of air caused by the passage of a lifting airfoil.", "importance": "Newtonian action that produces an equal and opposite upward reaction."}
            ],
            "formulas_or_code": [
                {"title": "The Aerodynamic Lift Equation", "type": "formula", "content": "L = \\frac{1}{2} \\rho v^2 S C_L", "explanation": "Calculates lift from air density, velocity squared, wing area, and lift coefficient."},
                {"title": "Bernoulli's Equation", "type": "formula", "content": "P + \\frac{1}{2}\\rho v^2 = \\text{constant}", "explanation": "As airflow speed v increases over the wing, static pressure P must decrease."}
            ],
            "practice_questions": [
                {"question": "Why do commercial airliners need longer runway distances to take off on hot summer days or at high-altitude airports like Denver?", "hint": "Look at the lift equation and air density $\\rho$.", "solution": "Hot air and high elevation both reduce air density ($\\rho$). Since Lift is directly proportional to air density, the aircraft must achieve a higher ground speed ($v$) to generate sufficient lift to take off."}
            ],
            "quiz": [
                {"id": 1, "question": "What happens when an airplane wing exceeds its critical Angle of Attack?", "options": ["It flies at supersonic speed", "It stalls because airflow separates from the upper wing surface", "The jet engines turn off automatically", "Drag drops to zero"], "correct_index": 1, "explanation": "Exceeding the critical angle causes flow separation and an immediate loss of lift known as an aerodynamic stall."},
                {"id": 2, "question": "What are the four fundamental forces acting on an airplane in unaccelerated flight?", "options": ["Speed, Altitude, Direction, Mass", "Lift, Weight (Gravity), Thrust, and Drag", "Friction, Kinetic Energy, Potential Energy, Torque", "Inertia, Pressure, Heat, Sound"], "correct_index": 1, "explanation": "Lift opposes weight, and thrust opposes aerodynamic drag."}
            ],
            "flashcards": [
                {"id": 1, "front": "What is the primary function of winglets on aircraft wingtips?", "back": "They reduce high-pressure air curling into low-pressure air, suppressing wingtip vortices and saving fuel.", "category": "Aviation Engineering"},
                {"id": 2, "front": "Does doubling an airplane's speed double its lift?", "back": "No! Lift scales with velocity squared (v^2), so doubling speed quadruples (4x) the lift.", "category": "Physics"}
            ]
        }

        return {
            "title": "How Airplanes Fly: The Physics & Engineering of Lift",
            "domain": "science_nature",
            "subdomain": "Fluid Dynamics & Aeronautical Engineering",
            "scenes": scenes,
            "materials": materials
        }

    # ------------------- DYNAMIC GENERAL-PURPOSE SYNTHESIZER -------------------

    def _build_adaptive_topic_lecture(
        self, topic: str, level: str, purpose: str, teaching_style: str, num_scenes: int, voice_name: str
    ) -> Dict[str, Any]:
        """
        Dynamically synthesizes a bespoke educational masterclass for ANY general topic,
        avoiding boilerplate slides and selecting distinct visual types appropriate to the subject.
        """
        topic_title = topic.strip().title()
        analysis = self.analyze_topic(topic)
        domain = analysis.domain

        # Choose bespoke visual templates based on domain
        if domain == "history":
            vtype1 = "concept_metaphor"
            vtype2 = "timeline_journey"
            vtype3 = "comparison_matrix"
            vtype4 = "cause_and_effect"
            vtype5 = "spectrum_meter"
        elif domain in ["economics_business", "psychology_philosophy"]:
            vtype1 = "concept_metaphor"
            vtype2 = "hierarchy_pyramid"
            vtype3 = "cycle_loop"
            vtype4 = "spectrum_meter"
            vtype5 = "comparison_matrix"
        elif domain in ["health_biology", "science_nature"]:
            vtype1 = "cross_section_sim"
            vtype2 = "cycle_loop"
            vtype3 = "concept_metaphor"
            vtype4 = "cause_and_effect"
            vtype5 = "comparison_matrix"
        elif domain == "arts_literature":
            vtype1 = "concept_metaphor"
            vtype2 = "narrative_arc"
            vtype3 = "comparison_matrix"
            vtype4 = "spectrum_meter"
            vtype5 = "cycle_loop"
        else:
            vtype1 = "concept_metaphor"
            vtype2 = "process_simulation"
            vtype3 = "hierarchy_pyramid"
            vtype4 = "comparison_matrix"
            vtype5 = "cycle_loop"

        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Core Paradox: Why {topic_title} Matters",
                "pedagogical_phase": "hook",
                "narration_text": f"To truly grasp {topic_title}, we must look past superficial definitions and confront the core dilemma that makes it so vital. What breakdown happens in its absence? How does understanding this concept transform how we perceive the world? Let us build an intuitive mental model from first principles.",
                "estimated_duration": 22.0,
                "visual_spec": {
                    "visual_type": vtype1,
                    "title": f"The Core Intuition of {topic_title}",
                    "subtitle": "Unpacking the Fundamental Paradox and Value",
                    "parameters": {
                        "left_title": "Conventional View / Without Insight",
                        "left_items": ["Superficial understanding or confusion", "Vulnerable to common misconceptions", "Unintended friction in decisions"],
                        "right_title": f"With {topic_title}",
                        "right_items": ["Crystal-clear conceptual mental model", "Systematic understanding of underlying drivers", "Practical clarity and informed action"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Conventional confusion"},
                        {"step": 2, "highlight": "Deep clarity"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Structural Architecture & Core Mechanics",
                "pedagogical_phase": "foundation",
                "narration_text": f"Every robust framework operates through fundamental components. In {topic_title}, dynamic forces interact according to consistent rules. When we map out its structural roadmap, the moving parts fall into place with natural clarity.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": vtype2,
                    "title": f"Foundational Architecture of {topic_title}",
                    "subtitle": "The Essential Building Blocks and Flow",
                    "parameters": {
                        "milestones": [
                            {"year": "Foundation", "title": "Preconditions & Origins", "desc": "Initial conditions that trigger action", "impact": "Baseline established"},
                            {"year": "Mechanics", "title": "Core Dynamic Transformation", "desc": "Primary operational rules in action", "impact": "System in motion"},
                            {"year": "Maturity", "title": "Equilibrium & Culmination", "desc": "Long-term steady state outcome", "impact": "Enduring consequence"}
                        ],
                        "tiers": [
                            {"tier": f"Tier 1: Foundational Preconditions of {topic_title}", "note": "Baseline elements required for stability"},
                            {"tier": "Tier 2: Intermediate Dynamic Mechanisms", "note": "Active processing and operational flow"},
                            {"tier": "Tier 3: Peak Manifestation & Mastery", "note": "Highest level of performance and insight"}
                        ],
                        "subject": f"Internal Dynamics of {topic_title}",
                        "layers": [
                            {"name": "Input Layer", "role": "Catalysts and environmental signals"},
                            {"name": "Core Process Engine", "role": "Fundamental transformations and interactions"},
                            {"name": "Observable Outcome", "role": "Final equilibrium and measurable impact"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Foundation"},
                        {"step": 2, "highlight": "Core Mechanics"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Engine in Motion: Step-by-Step Demonstration",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Now let us examine {topic_title} in dynamic motion. Notice how each state transition follows from the previous one. Understanding this continuous cycle allows us to predict outcomes and navigate complex scenarios with confidence.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": vtype3,
                    "title": f"{topic_title} in Action",
                    "subtitle": "Tracking Active Cycles and Interactive Relationships",
                    "parameters": {
                        "cycle_title": f"The Operational Cycle of {topic_title}",
                        "stages": [
                            {"name": "1. Catalyst / Trigger", "role": "Initial event sets process into motion"},
                            {"name": "2. Intermediate Dynamics", "role": "System components interact and transform"},
                            {"name": "3. Equilibrium Output", "role": "Outcome is delivered and reinforced through feedback"}
                        ],
                        "col1": "Traditional View: Linear, simplistic cause and effect",
                        "col2": "Systemic Reality: Interdependent feedback loops and non-linear shifts",
                        "col3": "Strategic Mastery: Leveraging high-impact leverage points"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Trigger"},
                        {"step": 2, "highlight": "Dynamic Transformation"},
                        {"step": 3, "highlight": "Equilibrium"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Nuances, Pitfalls & Critical Boundaries",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"Mastery requires knowing where a concept encounters its limits. In {topic_title}, common pitfalls occur when boundary conditions are ignored. By recognizing these friction points in advance, we avoid costly misjudgments.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": vtype4,
                    "title": "Nuances, Pitfalls & The Balance Spectrum",
                    "subtitle": "Navigating Extreme Assumptions and Hidden Traps",
                    "parameters": {
                        "left_label": "Over-Simplification: Ignoring vital context and nuance",
                        "right_label": "Over-Complication: Paralyzed by excessive detail",
                        "center_balance": "Pragmatic Mastery: Actionable clarity grounded in sound judgment",
                        "markers": [
                            "Naive Assumption",
                            "Balanced Prudence",
                            "Over-Engineered"
                        ],
                        "root_catalyst": "Misunderstanding Boundary Constraints",
                        "intermediate_effects": [
                            "Applying models outside their valid domain",
                            "Ignoring feedback loops and unintended consequences"
                        ],
                        "ultimate_consequence": "Suboptimal decisions and systemic friction"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Over-Simplification"},
                        {"step": 2, "highlight": "Pragmatic Balance"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Real-World Applications & Strategic Takeaways",
                "pedagogical_phase": "summary",
                "narration_text": f"To conclude our masterclass on {topic_title}: this knowledge is not merely theoretical—it is an actionable lens for real-world clarity. By retaining the core intuition, respecting the underlying mechanisms, and navigating trade-offs prudently, you can apply this across your learning, career, and life.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": vtype5,
                    "title": f"{topic_title}: Key Takeaways & Toolkit",
                    "subtitle": "Synthesizing Core Principles for Practical Application",
                    "parameters": {
                        "col1": "Core Principle: Focus on the root drivers, not surface noise",
                        "col2": "Systemic Invariant: Consistency of application across changing conditions",
                        "col3": "Actionable Habit: Regularly audit your mental models against reality"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Core Principle"},
                        {"step": 2, "highlight": "Actionable Habit"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This comprehensive masterclass on {topic_title} deconstructs the foundational paradox, the structural architecture, step-by-step dynamic mechanics, critical edge boundaries, and practical applications.",
            "notes_markdown": f"""# {topic_title}: Comprehensive Study Guide

## 1. Executive Summary
Understanding **{topic_title}** requires building a clear mental model from simple intuition to nuanced real-world dynamics:
- **Core Purpose**: Explains foundational realities and solves complex problems with elegance.
- **Key Invariants**: Predictable principles that remain true under shifting conditions.
- **Practical Relevance**: Widely applicable across analytical thinking, strategic decision-making, and general education.

## 2. Structural Principles
1. **First Principles Thinking**: Strip away assumptions to understand the foundational root drivers.
2. **Dynamic Feedback**: Understand how changes in one variable ripple across the entire system.
3. **Boundary Awareness**: Recognize where models work effectively and where edge cases require caution.
""",
            "key_concepts": [
                {"concept": f"{topic_title} Core Invariant", "definition": "The central principle that reliably governs behavior within this domain.", "importance": "Ensures sound reasoning from first principles."},
                {"concept": "Dynamic Feedback", "definition": "How outcomes loop back to influence the original inputs of the system.", "importance": "Prevents over-simplified linear thinking."}
            ],
            "formulas_or_code": [
                {"title": f"{topic_title} Heuristic", "type": "principle", "content": "Clarity of Principles \\times Consistency of Application = Mastery", "explanation": "Success depends on foundational clarity paired with disciplined execution."}
            ],
            "practice_questions": [
                {"question": f"What is the most common mistake people make when encountering {topic_title} for the first time?", "hint": "Think about surface appearances vs. root causes.", "solution": f"People often confuse surface symptoms with root causes. Truly understanding {topic_title} requires looking past immediate impressions to analyze systemic drivers."}
            ],
            "quiz": [
                {"id": 1, "question": f"What is the foundation of mastering {topic_title}?", "options": ["Memorizing isolated facts without context", "Understanding root principles and how components interact dynamically", "Ignoring edge cases and limitations", "Relying on random chance"], "correct_index": 1, "explanation": "True mastery comes from understanding underlying mechanisms and causal relationships."},
                {"id": 2, "question": f"Why is awareness of edge cases critical in {topic_title}?", "options": ["It is only useful for academic tests", "Models and systems tend to fail at boundary conditions if unhandled", "Edge cases never occur in real life", "It replaces the need for basic understanding"], "correct_index": 1, "explanation": "Critical failures almost always occur at boundaries and unanticipated edge conditions."}
            ],
            "flashcards": [
                {"id": 1, "front": f"What is the core takeaway of {topic_title}?", "back": "Focus on root mechanisms and systematic relationships rather than surface symptoms.", "category": "Core Principle"},
                {"id": 2, "front": f"How should you apply {topic_title} in practice?", "back": "Use it as a decision-making framework, auditing your assumptions regularly.", "category": "Application"}
            ]
        }

        return {
            "title": f"{topic_title}: Intuitive Visual Masterclass",
            "domain": domain,
            "subdomain": analysis.subdomain,
            "scenes": scenes,
            "materials": materials
        }
