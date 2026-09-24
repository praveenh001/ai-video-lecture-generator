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

    def classify_topic_archetype(self, topic: str) -> Dict[str, str]:
        t = topic.lower().strip()

        def has_any(keywords):
            return any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in keywords)

        # 1. Countries, Civilizations, Nations, Cultures
        country_words = [
            "india", "bharat", "japan", "egypt", "china", "rome", "greece", "russia", "america", "usa",
            "united states", "britain", "england", "france", "germany", "persia", "italy", "spain",
            "brazil", "mexico", "canada", "australia", "turkey", "israel", "korea", "africa", "civilization",
            "country", "nation"
        ]
        if has_any(country_words):
            return {
                "archetype": "country_civilization",
                "domain": "history",
                "subdomain": "Civilizations, Culture & Geopolitics",
                "recommended_style": "Chronological Epochs & Cultural Heritage Journey"
            }

        # 2. Historical Epochs & Turning Points (Evaluated before science to avoid 'revolution' matching 'evolution')
        history_words = [
            "revolution", "war", "battle", "treaty", "cold war", "renaissance", "medieval", "crusade",
            "colonial", "independence", "revolt", "empire", "dynasty", "monarchy", "bastille", "robespierre",
            "ancient egypt", "mesopotamia", "feudal"
        ]
        if has_any(history_words):
            return {
                "archetype": "historical_epoch",
                "domain": "history",
                "subdomain": "World History & Turning Points",
                "recommended_style": "Chronological Timeline Journeys & Causal Cascades"
            }

        # 3. Programming & Code (Word boundaries prevent 'oop' matching 'loops' or 'rest' matching 'interest')
        code_words = [
            "python", "javascript", "java", "c++", "golang", "rust", "typescript", "swift", "kotlin",
            "exception", "try except", "stack trace", "pointer", "syntax", "decorator", "generator",
            "async", "await", "promise", "concurrency", "multithreading", "recursion", "oop",
            "object oriented", "react", "fastapi", "flask", "django", "node.js", "docker", "kubernetes",
            "git", "memory leak", "garbage collection", "compiler", "interpreter", "debugging",
            "api", "rest api", "sql query", "database index"
        ]
        if has_any(code_words) or ("code" in t and "dress code" not in t) or ("error" in t and "trial and error" not in t):
            return {
                "archetype": "programming_code",
                "domain": "computer_science",
                "subdomain": "Software Engineering & Programming Languages",
                "recommended_style": "Code Execution Walkthrough & Call Stack Inspection"
            }

        # 4. Economics & Finance
        econ_words = [
            "inflation", "stock market", "stocks", "economy", "economics", "purchasing power", "cpi",
            "interest rate", "central bank", "monetary policy", "supply and demand", "money supply",
            "crypto", "bitcoin", "blockchain", "venture capital", "trade deficit", "banking", "gdp",
            "recession", "liquidity", "fiscal policy", "monopoly"
        ]
        if has_any(econ_words):
            return {
                "archetype": "economics_finance",
                "domain": "economics_business",
                "subdomain": "Economics, Markets & Finance",
                "recommended_style": "Market Equilibrium Curves & Money Flow Cycles"
            }

        # 5. Psychology, Philosophy & Mental Models
        psy_words = [
            "stoic", "stoicism", "philosophy", "psychology", "cognitive bias", "bias", "maslow",
            "habit", "habits", "habit loop", "dopamine", "mindset", "plato", "aristotle", "socrates",
            "nietzsche", "marcus aurelius", "seneca", "epictetus", "behavior", "freud", "ego", "emotion",
            "happiness", "existentialism", "ethics", "mental model", "decision making"
        ]
        if has_any(psy_words):
            return {
                "archetype": "psychology_philosophy",
                "domain": "psychology_philosophy",
                "subdomain": "Cognitive Psychology & Philosophy",
                "recommended_style": "Cognitive Feedback Loops & Hierarchy Pyramids"
            }

        # 6. Health, Biology & Physiology
        bio_words = [
            "sleep", "circadian", "circadian rhythm", "melatonin", "rem sleep", "photosynthesis",
            "immune system", "immunity", "virus", "bacteria", "heart", "cardiovascular", "brain",
            "neuron", "neurotransmitter", "fasting", "intermittent fasting", "diet", "nutrition",
            "cancer", "blood", "organ", "exercise", "hormone", "insulin", "dna", "rna", "genetics",
            "cell", "cellular", "mitochondria", "biology"
        ]
        if has_any(bio_words):
            return {
                "archetype": "health_biology",
                "domain": "health_biology",
                "subdomain": "Health Sciences & Human Biology",
                "recommended_style": "Biological Pathway Simulations & Rhythm Cycles"
            }

        # 7. Algorithms & Mathematics
        math_words = [
            "binary search", "search algorithm", "sorting", "sort", "quicksort", "mergesort",
            "data structure", "tree", "binary tree", "graph", "dynamic programming", "hash table",
            "calculus", "derivative", "integral", "matrix", "linear algebra", "neural network",
            "deep learning", "gradient descent", "backpropagation", "probability", "statistics",
            "algorithm", "vectors"
        ]
        if has_any(math_words):
            return {
                "archetype": "algorithm_math",
                "domain": "computer_science" if any(w in t for w in ["search", "sort", "graph", "tree", "neural", "programming"]) else "mathematics",
                "subdomain": "Algorithms, Systems & Applied Mathematics",
                "recommended_style": "Interactive Step-by-Step Simulator & Mathematical Curves"
            }

        # 8. Everyday Science & Physics
        science_words = [
            "sky is blue", "rayleigh scattering", "airplane", "airplanes", "fly", "aerodynamics",
            "lift", "bernoulli", "earthquake", "weather", "ocean", "climate", "space", "gravity",
            "energy", "physics", "solar", "black hole", "evolution", "atom", "quantum", "quantum computing",
            "light", "relativity", "thermodynamics"
        ]
        if has_any(science_words):
            return {
                "archetype": "everyday_science",
                "domain": "science_nature",
                "subdomain": "Natural Sciences & Phenomenon Exploration",
                "recommended_style": "Physical Cross-Sections & Force Dynamic Simulations"
            }

        # 9. Arts, Literature & Storytelling
        arts_words = [
            "hero's journey", "heros journey", "monomyth", "storytelling", "literature", "writing",
            "narrative", "poetry", "novel", "music", "harmony", "musical", "cinema", "film",
            "theatre", "painting", "aesthetic", "creative writing"
        ]
        if has_any(arts_words):
            return {
                "archetype": "arts_literature",
                "domain": "arts_literature",
                "subdomain": "Arts, Humanities & Narrative Architecture",
                "recommended_style": "Narrative Arc Curves & Aesthetic Harmony Boards"
            }

        # Default general
        return {
            "archetype": "general",
            "domain": "general",
            "subdomain": "General Knowledge & Analytical Thinking",
            "recommended_style": "Visual Metaphor & Conceptual Blueprint"
        }

    def analyze_topic(self, topic: str, api_key: Optional[str] = None) -> TopicAnalysisResponse:
        classified = self.classify_topic_archetype(topic)
        domain = classified["domain"]
        subdomain = classified["subdomain"]
        arch = classified["archetype"]
        recommended_style = classified["recommended_style"]

        model = self._get_configured_gemini(api_key)
        t_clean = topic.strip().title()

        if arch == "country_civilization":
            overview_text = f"An immersive educational masterclass on {t_clean}: exploring its civilizational antiquity and spiritual/divine heritage, golden epochs of science and arts, historic struggle for independence, constitutional democracy, and modern rising influence on the global stage."
        elif arch == "programming_code":
            overview_text = f"A hands-on, practical software engineering masterclass on {t_clean}: deconstructing the core language syntax, tracing execution and call stacks step-by-step, avoiding critical runtime pitfalls, and mastering production-grade patterns."
        elif arch == "historical_epoch":
            overview_text = f"A dramatic historical journey through {t_clean}: tracing the underlying catalysts, pivotal turning points, clashing factions, and the enduring global consequences that shape the world today."
        elif arch == "economics_finance":
            overview_text = f"A practical economic exploration of {t_clean}: demystifying market forces, supply and demand equilibrium, monetary policy cycles, and actionable strategies for navigating financial realities."
        elif arch == "psychology_philosophy":
            overview_text = f"A transformative psychological and philosophical study of {t_clean}: examining foundational mental models, cognitive feedback loops, common human blind spots, and daily practices for resilience."
        elif arch == "health_biology":
            overview_text = f"A science-backed biological exploration of {t_clean}: unraveling physiological mechanisms, cellular pathways, circadian and hormonal rhythms, and evidence-based protocols for human health."
        elif arch == "arts_literature":
            overview_text = f"A creative exploration of {t_clean}: analyzing narrative structures, harmonic principles, iconic masterworks, and universal archetypes that touch the human spirit."
        elif arch == "everyday_science":
            overview_text = f"An illuminating scientific investigation into {t_clean}: explaining everyday natural phenomena through fundamental physical laws, cross-sections, and dynamic force simulations."
        elif arch == "algorithm_math":
            overview_text = f"A rigorous computational and mathematical masterclass on {t_clean}: building intuitive mental models, animated state transitions, coordinate geometry curves, and asymptotic complexity boundaries."
        else:
            overview_text = f"A structured educational masterclass on {t_clean}: building a clear mental model from intuitive first principles to dynamic demonstrations, critical edge cases, and real-world applications."

        style_options = self._get_style_options_for_archetype(arch, domain)
        questions = [
            ClarificationQuestion(
                id="knowledge_level",
                question=f"What is your current familiarity with {t_clean}?",
                options=[
                    ClarificationOption(id="beginner", label="Beginner (Focus on clear visual intuition, engaging stories, zero jargon)"),
                    ClarificationOption(id="intermediate", label="Intermediate (Core mechanisms, cause-and-effect, practical depth)"),
                    ClarificationOption(id="advanced", label="Advanced (Nuanced trade-offs, theoretical rigor, edge conditions)")
                ],
                default_value="intermediate"
            ),
            ClarificationQuestion(
                id="purpose",
                question="What is your primary learning goal?",
                options=self._get_purpose_options_for_archetype(arch),
                default_value="conceptual"
            ),
            ClarificationQuestion(
                id="teaching_style",
                question="Which visual teaching style helps you learn best?",
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

        if model:
            try:
                prompt = f"""
                Analyze the educational topic: "{topic}".
                Respond in valid JSON only with keys:
                - "domain": string (history, economics_business, psychology_philosophy, health_biology, arts_literature, science_nature, computer_science, mathematics, or general)
                - "subdomain": string
                - "overview": concise 2-sentence instructional summary specifically tailored to "{topic}"
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

    def _get_purpose_options_for_archetype(self, arch: str) -> List[ClarificationOption]:
        if arch == "country_civilization":
            return [
                ClarificationOption(id="cultural_history", label="Civilizational & Spiritual Heritage (Antiquity, philosophy, traditions)"),
                ClarificationOption(id="modern_geopolitics", label="Modern Nation & Global Power (Democracy, economy, technology, society)"),
                ClarificationOption(id="general_overview", label="Complete Masterclass (From ancient roots to modern global leader)")
            ]
        elif arch == "programming_code":
            return [
                ClarificationOption(id="coding_interview", label="Coding Interviews & LeetCode (Core patterns, edge cases, error recovery)"),
                ClarificationOption(id="production_engineering", label="Production Engineering (Writing clean, resilient, debuggable code)"),
                ClarificationOption(id="syntax_mastery", label="Syntax & Mental Model (Understanding the language engine completely)")
            ]
        elif arch == "economics_finance":
            return [
                ClarificationOption(id="financial_literacy", label="Personal Wealth & Financial Protection (Inflation, assets, investing)"),
                ClarificationOption(id="academic_macro", label="Macroeconomics & Policy (Central banking, money supply, market cycles)")
            ]
        elif arch == "historical_epoch":
            return [
                ClarificationOption(id="historical_causes", label="Causes, Turning Points & Global Consequence (From sparks to treaties)"),
                ClarificationOption(id="societal_impact", label="Human Experience & Societal Transformation (People, rights, and legacy)")
            ]
        elif arch == "psychology_philosophy":
            return [
                ClarificationOption(id="self_mastery", label="Personal Growth & Daily Resilience (Mindset, emotional balance, habits)"),
                ClarificationOption(id="theoretical_depth", label="Philosophical & Psychological Frameworks (Deep mental models & theory)")
            ]
        elif arch == "health_biology":
            return [
                ClarificationOption(id="health_protocols", label="Actionable Longevity & Vitality Protocols (Sleep, nutrition, habits)"),
                ClarificationOption(id="cellular_science", label="Cellular & Physiological Science (Mechanisms, pathways, pathways)")
            ]
        elif arch == "algorithm_math":
            return [
                ClarificationOption(id="interview_prep", label="Technical Problem Solving & Interviews (Complexity, invariants, patterns)"),
                ClarificationOption(id="math_intuition", label="Visual Mathematical Intuition (Geometrical and coordinate insights)")
            ]
        else:
            return [
                ClarificationOption(id="conceptual", label="Deep Conceptual Intuition (Build a rock-solid mental model)"),
                ClarificationOption(id="practical", label="Practical Real-World Application (Apply directly in life, decisions, or career)"),
                ClarificationOption(id="academic", label="Academic Mastery & Exams (Key definitions, proofs, structured analysis)")
            ]

    def _get_style_options_for_archetype(self, arch: str, domain: str) -> List[ClarificationOption]:
        if arch == "country_civilization":
            return [
                ClarificationOption(id="epochs_timeline", label="Chronological Epochs & Timeline (Antiquity to modern renaissance)"),
                ClarificationOption(id="cultural_mosaic", label="Cultural, Spiritual & Constitutional Mosaic (Philosophies, unity in diversity)"),
                ClarificationOption(id="geopolitical_rise", label="Civilizational Rise & Global Impact (Science, trade, diaspora, future)")
            ]
        elif arch == "programming_code":
            return [
                ClarificationOption(id="code_flow", label="Live Syntax Execution & Call Stack Trace (Line-by-line pointer & variables watch)"),
                ClarificationOption(id="hierarchy_tree", label="Exception / Class Hierarchy Tree (Understanding inheritance & categories)"),
                ClarificationOption(id="crash_recovery", label="Crash vs. Graceful Recovery Comparison (Clean code vs antipatterns)")
            ]
        elif arch == "historical_epoch":
            return [
                ClarificationOption(id="timeline", label="Chronological Timeline & Turning Points (Visual chronological roadmap)"),
                ClarificationOption(id="cause_effect", label="Cause-and-Effect Cascade (Tracking catalysts to lasting global ripple effects)"),
                ClarificationOption(id="opposing_forces", label="Clashing Factions Matrix (Comparing motivations and strategies)")
            ]
        elif arch == "economics_finance":
            return [
                ClarificationOption(id="market_equilibrium", label="Market Dynamics & Equilibrium Shift (Dynamic supply/demand curves)"),
                ClarificationOption(id="money_cycle", label="Economic Money Flow Cycle (Tracking capital between households, banks & markets)"),
                ClarificationOption(id="spectrum_tradeoff", label="Trade-off & Policy Spectrum (Inflation vs. Unemployment, Risk vs. Reward)")
            ]
        elif arch == "psychology_philosophy":
            return [
                ClarificationOption(id="pyramid_hierarchy", label="Structural Hierarchy (Multi-tier pyramid like Maslow's or value systems)"),
                ClarificationOption(id="cognitive_loop", label="Cognitive Feedback Loop (Trigger -> Thought -> Emotion -> Habit Action)"),
                ClarificationOption(id="metaphor_allegory", label="Philosophical Allegory Board (Concrete spatial analogies for abstract truths)")
            ]
        elif arch == "health_biology":
            return [
                ClarificationOption(id="biological_cycle", label="Circadian / Bio-Rhythm Cycle (Tracking hormones, energy & bodily phases)"),
                ClarificationOption(id="cellular_pathway", label="Microscopic Defense / Cellular Pathway (Step-by-step immune/biological action)"),
                ClarificationOption(id="cross_section", label="Organ & Physiological Cross-Section (Anatomy, input-output mechanics)")
            ]
        elif arch == "arts_literature":
            return [
                ClarificationOption(id="narrative_arc", label="Narrative Arc / Story Mountain (Exposition, rising tension, climax & resolution)"),
                ClarificationOption(id="creative_breakdown", label="Comparative Masterwork Dissection (Key scene/masterpiece analysis)")
            ]
        elif arch == "everyday_science":
            return [
                ClarificationOption(id="cross_section_sim", label="Cross-Section & Force Interactions (Aerodynamic wing, earth crust, light rays)"),
                ClarificationOption(id="process_flow", label="Physical Energy Flow Simulation (Energy transfer from source to outcome)")
            ]
        elif arch == "algorithm_math":
            return [
                ClarificationOption(id="algorithm_animator", label="Step-by-Step Algorithm & Memory Simulator (Animated pointers & state updates)"),
                ClarificationOption(id="math_graph", label="Mathematical Curves & Moving Tangent Lines (Visual coordinates and limits)")
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
        model = self._get_configured_gemini(api_key)
        
        num_scenes = 5
        if "quick" in lecture_duration.lower() or "2-3" in lecture_duration.lower():
            num_scenes = 3
        elif "deep" in lecture_duration.lower() or "7" in lecture_duration.lower() or "8" in lecture_duration.lower():
            num_scenes = 6

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

        return self._generate_with_pedagogical_engine(
            topic, knowledge_level, purpose, preferred_language,
            teaching_style, num_scenes, voice_name
        )

    def _generate_with_gemini(
        self, model, topic: str, knowledge_level: str, purpose: str,
        preferred_language: str, teaching_style: str, num_scenes: int
    ) -> Optional[Dict[str, Any]]:
        prompt = f"""
        You are a world-class educator, master instructional designer, animator, and video producer.
        Topic: "{topic}"
        Knowledge Level: {knowledge_level}
        Purpose: {purpose}
        Language: {preferred_language}
        Teaching Style: {teaching_style}
        Number of Scenes: {num_scenes}

        You are creating an exceptional educational video lecture specifically tailored to "{topic}".
        CRITICAL RULES:
        - If the topic is a Country/Civilization (e.g. "India"), dive into authentic history, spiritual/philosophical heritage, cultural epochs, independence struggles, democracy, and modern achievements!
        - If the topic is a Programming concept (e.g. "Exception in Python"), show REAL code examples (e.g. try/except/else/finally), trace execution line by line, explain stack unwinding, show common built-in exceptions, and production best practices!
        - Do NOT use generic placeholder words like "The Core Invariant" or "Dynamic Transformation" on non-technical topics!
        - Every scene must be substantive, factual, engaging, and pedagogically rich.

        Return valid JSON only matching the standard lecture schema with title, domain, subdomain, scenes, and materials.
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
        t = topic.lower().strip()
        classified = self.classify_topic_archetype(topic)
        arch = classified["archetype"]

        # 1. SPECIFIC TOPIC: INDIA (Country, Civilization, Divine Heritage, History)
        if re.search(r'\bindia\b', t) or re.search(r'\bbharat\b', t):
            return self._build_india_civilization_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 2. SPECIFIC TOPIC: EXCEPTION IN PYTHON (Code, Syntax, Stack Unwinding, Best Practices)
        if any(w in t for w in ["exception in python", "python exception", "python error", "try except python", "exceptions in python"]):
            return self._build_python_exceptions_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 3. Other Core Curated Masterclasses
        if "binary search" in t:
            return self._build_binary_search_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t for w in ["french revolution", "bastille", "robespierre"]):
            return self._build_french_revolution_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t for w in ["inflation", "purchasing power", "cpi", "money supply"]):
            return self._build_inflation_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t for w in ["stoic", "stoicism", "marcus aurelius", "seneca", "epictetus"]):
            return self._build_stoicism_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t for w in ["sleep", "circadian", "melatonin", "rem sleep"]):
            return self._build_sleep_circadian_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t for w in ["hero's journey", "heros journey", "monomyth", "storytelling"]):
            return self._build_heros_journey_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t for w in ["sky is blue", "rayleigh scattering", "blue sky"]):
            return self._build_why_sky_is_blue_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(w in t for w in ["airplane", "fly", "aerodynamic", "lift", "bernoulli"]):
            return self._build_how_airplanes_fly_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t for k in ["neural network", "backpropagation", "gradient descent", "deep learning"]):
            return self._build_neural_networks_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t for k in ["async", "await", "asynchronous", "promise", "event loop"]):
            return self._build_async_await_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t for k in ["derivative", "calculus", "rate of change", "tangent"]):
            return self._build_calculus_derivative_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif "photosynthesis" in t:
            return self._build_photosynthesis_lecture(knowledge_level, purpose, num_scenes, voice_name)

        # 4. Archetype-Aware Specialized Generators for Any of the N Situations:
        if arch == "country_civilization":
            return self._build_generic_country_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "programming_code":
            return self._build_generic_programming_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "historical_epoch":
            return self._build_generic_history_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "economics_finance":
            return self._build_generic_economics_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "psychology_philosophy":
            return self._build_generic_psychology_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "health_biology":
            return self._build_generic_biology_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "everyday_science":
            return self._build_generic_science_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "algorithm_math":
            return self._build_generic_algorithm_math_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        elif arch == "arts_literature":
            return self._build_generic_arts_lecture(topic, knowledge_level, purpose, num_scenes, voice_name)
        else:
            return self._build_adaptive_topic_lecture(topic, knowledge_level, purpose, teaching_style, num_scenes, voice_name)

    def _build_india_civilization_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Sacred Cradle: Antiquity & Spiritual Roots",
                "pedagogical_phase": "hook",
                "narration_text": "India is not merely a nation; it is one of humanity's oldest continuous living civilizations, spanning over five thousand years. Along the fertile banks of the Indus and the sacred Saraswati rivers, advanced planned cities like Harappa and Mohenjo-daro thrived with sophisticated metallurgy and civic drainage. From these ancient soils arose profound spiritual traditions: Sanatana Dharma, the poetic philosophy of the Vedas, the introspective depth of the Upanishads, and the timeless moral paths of Buddhism and Jainism. Here, truth was recognized as one, expressed in myriad forms.",
                "estimated_duration": 26.0,
                "visual_spec": {
                    "visual_type": "hierarchy_pyramid",
                    "title": "Ancient Spiritual & Philosophical Foundations",
                    "subtitle": "The Intellectual & Metaphysical Heritage of Ancient India",
                    "parameters": {
                        "pyramid_title": "Vedic & Philosophical Heritage",
                        "tiers": [
                            {"tier": "Moksha & Self-Realization (The Upanishads)", "note": "Ultimate liberation through spiritual realization (Aham Brahmasmi)"},
                            {"tier": "Dharma & Ethical Living (The Epics & Gita)", "note": "Righteous duty, moral action without attachment to fruits (Nishkama Karma)"},
                            {"tier": "Spiritual Diversity: Buddhism, Jainism, Darshanas", "note": "Ahimsa (non-violence), Yoga, Vedanta, Nyaya, and Samkhya systems"},
                            {"tier": "Indus Valley Civilization (~3300 - 1300 BCE)", "note": "Urban grid cities, standardized weights, maritime commerce, bronze mastery"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Indus Valley Foundation"},
                        {"step": 2, "highlight": "Vedic & Philosophical Heritage"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Epochs of Enlightenment: Maurya, Gupta & Cultural Synthesis",
                "pedagogical_phase": "foundation",
                "narration_text": "Across centuries, great dynasties united the subcontinent in scholarship and architectural grandeur. Emperor Ashoka of the Maurya Empire renounced war after Kalinga, carving edicts of peace, religious tolerance, and animal welfare upon stone pillars across Asia. Under the Gupta Golden Age, Indian mathematicians invented the decimal system and the concept of zero, while astronomers like Aryabhata calculated the solar year. Universities like Nalanda welcomed thousands of scholars from China to Greece, making India the intellectual beacon of the ancient world.",
                "estimated_duration": 27.0,
                "visual_spec": {
                    "visual_type": "timeline_journey",
                    "title": "The Golden Epochs of Classical India",
                    "subtitle": "From Ancient Empires to Global Intellectual Influence",
                    "parameters": {
                        "milestones": [
                            {"year": "321 - 185 BCE", "title": "Mauryan Empire & Ashoka", "desc": "Pan-Indian unification; Ashokan Edicts spread Buddhist ethics of Ahimsa", "impact": "Universal moral governance"},
                            {"year": "320 - 550 CE", "title": "Gupta Empire (Golden Age)", "desc": "Aryabhata invents zero & decimal place-value; Kalidasa's classical Sanskrit poetry", "impact": "Foundations of modern mathematics"},
                            {"year": "427 - 1197 CE", "title": "Nalanda University", "desc": "World's premier residential university with 10,000 students and massive library", "impact": "Global hub of Buddhist & secular study"},
                            {"year": "9th - 13th Cent", "title": "Chola Maritime Empire", "desc": "Magnificent Brihadeeswarar bronze & stone temples; naval trade to Southeast Asia", "impact": "Cultural diaspora across Indochina"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Mauryan Empire"},
                        {"step": 2, "highlight": "Gupta Golden Age"},
                        {"step": 3, "highlight": "Nalanda & Cholas"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Crucible of Freedom: Colonial Struggle to 1947",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "By the eighteenth century, European colonial expansion culminated in the British East India Company and the British Raj, which systematically exploited India's textiles and wealth. But the spirit of India rose in resistance. From the brave rebellion of 1857 to the revolutionary bravery of Bhagat Singh, Netaji Subhas Chandra Bose's Indian National Army, and Mahatma Gandhi's mass non-violent Satyagraha, millions mobilized. On the midnight of August 15, 1947, as Jawaharlal Nehru declared, India awoke to life and freedom.",
                "estimated_duration": 26.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": "The Freedom Movement & The Dawn of Independence",
                    "subtitle": "How Colonial Resistance Forged a Sovereign Republic",
                    "parameters": {
                        "root_catalyst": "British Colonial Exploitation & The Revolt of 1857",
                        "intermediate_effects": [
                            "Birth of Indian National Congress (1885) and Swadeshi economic boycott",
                            "Mahatma Gandhi's Non-Violent Satyagraha, Salt March & Quit India Movement",
                            "Netaji Subhas Chandra Bose & The Indian National Army challenge British military power"
                        ],
                        "ultimate_consequence": "Midnight of August 15, 1947: Sovereign Independence; Constitution ratified in 1950"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Revolt of 1857"},
                        {"step": 2, "highlight": "Satyagraha & INA"},
                        {"step": 3, "highlight": "Independence 1947"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Unity in Diversity: The Constitutional Tapestry",
                "pedagogical_phase": "edge_cases",
                "narration_text": "What makes modern India truly miraculous is its constitutional achievement. Architected by Dr. B. R. Ambedkar, the Indian Constitution established the world's largest sovereign democracy. Within one single nation live twenty-eight states, twenty-two officially recognized languages, and every major world religion—Hinduism, Islam, Christianity, Sikhism, Buddhism, and Jainism. Despite immense complexity, India thrives not by enforcing conformity, but by celebrating Unity in Diversity as its sacred national creed.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "The Pluralistic Mosaic of the Republic",
                    "subtitle": "Democracy, Linguistic Richness & Spiritual Coexistence",
                    "parameters": {
                        "col1": "World's Largest Democracy: 1.4 billion people, 900+ million voters, peaceful constitutional transitions of power",
                        "col2": "Linguistic & Cultural Tapestry: 22 Eighth Schedule languages, classical literatures (Tamil, Sanskrit, Kannada, Telugu)",
                        "col3": "Spiritual Synthesis: Birthplace of Hinduism, Buddhism, Jainism, Sikhism; thriving home of Islam, Christianity, Zoroastrianism"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Democracy"},
                        {"step": 2, "highlight": "Linguistic Tapestry"},
                        {"step": 3, "highlight": "Spiritual Synthesis"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Modern India: Space, Digital Revolution & Global Horizon",
                "pedagogical_phase": "summary",
                "narration_text": "Today, India stands as a vibrant global powerhouse where ancient heritage meets twenty-first-century innovation. With ISRO's Chandrayaan landing on the lunar South Pole, a revolutionary digital public infrastructure powering billions of instant UPI transactions, and a young demographic driving global technology and entrepreneurship, India continues its civilizational mission. Guided by the timeless motto 'Vasudhaiva Kutumbakam'—the world is one family—India shines as a beacon of democracy, culture, and progress.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Civilizational Synthesis of Modern India",
                    "subtitle": "Ancient Timeless Wisdom Harmonizing with Cutting-Edge Innovation",
                    "parameters": {
                        "left_label": "Timeless Spiritual Wisdom: Yoga, Ayurveda, Vedanta, Ahimsa",
                        "right_label": "High-Tech Frontier: ISRO Space Exploration, Digital Public Infrastructure, AI Leadership",
                        "center_balance": "Vasudhaiva Kutumbakam: 'The World is One Family' Guided by Democratic Values",
                        "markers": [
                            "Vedic Heritage",
                            "World's Largest Democracy",
                            "Global Innovation Leader"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Spiritual Heritage"},
                        {"step": 2, "highlight": "High-Tech Frontier"},
                        {"step": 3, "highlight": "Vasudhaiva Kutumbakam"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "India (Bharat) is one of the world's oldest and most profound continuous civilizations. Spanning the ancient Indus Valley, the philosophical depths of the Vedas and Upanishads, golden classical empires, a heroic non-violent freedom struggle, and the world's largest constitutional democracy, India harmoniously bridges ancient spiritual wisdom with modern technological leadership in space, digital infrastructure, and global affairs.",
            "notes_markdown": """# India: Comprehensive Civilizational & National Study Notes

## 1. Antiquity & The Vedic Heritage
- **Indus Valley Civilization (~3300 - 1300 BCE)**: Advanced planned urban centers at Harappa, Mohenjo-daro, and Dholavira with standardized brick architecture, water management, and extensive international trade.
- **The Vedic Tradition & Philosophy**: The composition of the Rigveda, Samaveda, Yajurveda, and Atharvaveda, progressing to the **Upanishads**, which explored the fundamental nature of reality (*Brahman*) and the self (*Atman*).
- **Core Spiritual Concepts**:
  - *Dharma*: Cosmic order, moral duty, and ethical action.
  - *Karma*: The law of cause and effect governing actions.
  - *Ahimsa*: Non-violence and reverence for all living beings, championed by Mahavira and Gautama Buddha.

## 2. Classical Golden Empires
1. **The Maurya Empire (321 - 185 BCE)**: Unified under Chandragupta Maurya and Chanakya (author of the *Arthashastra*). Emperor Ashoka embraced Buddhism after the Kalinga war, carving edicts of tolerance and ethics across Asia.
2. **The Gupta Golden Age (320 - 550 CE)**: Remarkable mathematical breakthroughs including the formalization of zero as a number, decimal place-value, and trigonometry by mathematicians like **Aryabhata** and **Varahamihira**.
3. **Nalanda University**: Premier residential center of global learning hosting scholars from across the Silk Road.
4. **Southern Dynasties (Cholas, Pandyas, Pallavas)**: Renowned for exquisite Dravidian temple architecture, bronze sculpture, and trans-oceanic trade networks.

## 3. The Freedom Struggle & Independence
- **Colonial Era**: British East India Company hegemony followed by direct British Crown rule (British Raj) after the historic **Revolt of 1857**.
- **The National Movement**:
  - *Mahatma Gandhi*: Championed mass non-violent resistance (*Satyagraha*), leading the Non-Cooperation Movement, Salt March (1930), and Quit India Movement (1942).
  - *Netaji Subhas Chandra Bose*: Established the Indian National Army (Azad Hind Fauj) to militarily challenge British rule.
  - *Revolutionary Heroes*: Bhagat Singh, Chandrashekhar Azad, Rani Lakshmibai.
- **Midnight of August 15, 1947**: India attained sovereign independence, celebrated in Jawaharlal Nehru's historic 'Tryst with Destiny' address.

## 4. The Republic of India
- **The Constitution (Adopted Nov 26, 1949; in effect Jan 26, 1950)**: Drafted under the chairmanship of **Dr. B. R. Ambedkar**, creating a Sovereign, Socialist, Secular, Democratic Republic.
- **Unity in Diversity**: 28 States, 8 Union Territories, 22 Eighth Schedule languages, and a multi-religious secular constitutional fabric.
- **Modern Milestones**:
  - **Space Leadership (ISRO)**: Successful Chandrayaan-3 lunar south-pole landing and Aditya-L1 solar mission.
  - **Digital Public Infrastructure (India Stack)**: Unified Payments Interface (UPI) facilitating billions of real-time transactions monthly.
""",
            "key_concepts": [
                {"concept": "Unity in Diversity", "definition": "The philosophical and constitutional principle that diverse ethnic, linguistic, and religious communities coexist in harmonious shared citizenship.", "importance": "Foundational bedrock of the Indian Republic."},
                {"concept": "Ahimsa", "definition": "The ancient ethical doctrine of non-violence in thought, word, and deed, central to Hinduism, Buddhism, and Jainism.", "importance": "Inspired Mahatma Gandhi's freedom movement and modern global civil rights struggles."},
                {"concept": "Vasudhaiva Kutumbakam", "definition": "A Sanskrit phrase from the Maha Upanishad meaning 'The World is One Family'.", "importance": "Guides India's cultural diplomacy and global humanitarian outlook."}
            ],
            "formulas_or_code": [
                {"title": "The National Motto", "type": "quote", "content": "Satyameva Jayate (Truth Alone Triumphs)", "explanation": "From the Mundaka Upanishad, inscribed at the base of the Lion Capital of Ashoka."},
                {"title": "Universal Ethical Invariant", "type": "principle", "content": "Vasudhaiva Kutumbakam (The World is One Family)", "explanation": "Core philosophical orientation recognizing the common bond of all humanity."}
            ],
            "practice_questions": [
                {"question": "How did Emperor Ashoka's governance after the Kalinga war represent a paradigm shift in political philosophy?", "hint": "Think about the transition from conquest by arms to conquest by righteousness.", "solution": "Ashoka renounced military conquest (Digvijaya) and adopted conquest by moral righteousness (Dharmavijaya), inscribing edicts mandating medical care for humans and animals, environmental conservation, and mutual religious respect across his vast empire."}
            ],
            "quiz": [
                {"id": 1, "question": "Who served as the principal architect and Chairman of the Drafting Committee of the Indian Constitution?", "options": ["Mahatma Gandhi", "Dr. B. R. Ambedkar", "Jawaharlal Nehru", "Sardar Vallabhbhai Patel"], "correct_index": 1, "explanation": "Dr. Bhimrao Ramji Ambedkar chaired the Drafting Committee that framed the Constitution of India."},
                {"id": 2, "question": "What groundbreaking mathematical contribution flourished during the Gupta Golden Age of India?", "options": ["The invention of the abacus", "The formalization of zero and decimal place-value system", "Calculus limits", "Binary electronics"], "correct_index": 1, "explanation": "Indian mathematicians like Aryabhata developed the decimal system and the operational concept of zero, which revolutionized global mathematics."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does the national motto 'Satyameva Jayate' mean and where does it originate?", "back": "It means 'Truth Alone Triumphs' and originates from the ancient Mundaka Upanishad.", "category": "National Symbols"},
                {"id": 2, "front": "When did the Constitution of India come into full effect?", "back": "January 26, 1950, celebrated nationwide as Republic Day.", "category": "Constitution"}
            ]
        }

        return {
            "title": "India: The Epic Journey of a Continuous Civilization",
            "domain": "history",
            "subdomain": "Civilizations, Culture & Geopolitics",
            "scenes": scenes,
            "materials": materials
        }

    def _build_python_exceptions_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Production Crash: Syntax Errors vs. Runtime Exceptions",
                "pedagogical_phase": "hook",
                "narration_text": "Imagine writing a banking script or web server. If your code has a syntax error like a missing parenthesis, Python detects it before running a single line. But what happens when your code is syntactically flawless, yet a user inputs zero as a divisor, or a database connection suddenly drops? Without exception handling, Python panics, halts execution immediately, and crashes with an ugly traceback. Exception handling is the vital safety net that transforms fatal crashes into resilient, graceful recovery.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Syntax Error vs. Runtime Exception",
                    "subtitle": "Compile-Time Parsing vs. Runtime Unexpected Conditions",
                    "parameters": {
                        "left_title": "SyntaxError (Fatal Parser Halt)",
                        "left_items": ["Missing colon, mismatched brackets, typos", "Caught before code begins executing", "Cannot be handled at runtime with try/except"],
                        "right_title": "Exceptions (Recoverable Runtime Events)",
                        "right_items": ["ZeroDivisionError, KeyError, FileNotFoundError", "Occurs while code is actively executing", "Can be caught, recovered from, and cleanly resolved!"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "SyntaxError parse failure"},
                        {"step": 2, "highlight": "Runtime Exception handling"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Four Pillars: try, except, else, and finally",
                "pedagogical_phase": "foundation",
                "narration_text": "Python's exception handling engine is built upon four keywords. Inside the try block, you place code that might fail. The except block catches specific error types and executes fallback logic. Many developers forget the else block: it executes strictly if no exception was raised in the try block! And finally is the unbreakable guarantee: it runs no matter what happens, whether an exception occurred, was caught, or even if the function returned early.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": "The Full try-except-else-finally Suite",
                    "subtitle": "Complete Four-Keyword Error Handling Anatomy",
                    "parameters": {
                        "language": "python",
                        "code": "def process_account_file(filename):\n    file = None\n    try:\n        # 1. Dangerous operation: File I/O\n        file = open(filename, 'r')\n        data = file.read()\n    except FileNotFoundError as err:\n        # 2. Recovery logic for missing file\n        print(f'Warning: {filename} missing. Using defaults.')\n        return {}\n    else:\n        # 3. Runs ONLY if try succeeded with zero errors\n        print('File successfully read without exceptions!')\n        return parse_data(data)\n    finally:\n        # 4. ALWAYS runs: Crucial resource cleanup\n        if file:\n            file.close()\n            print('Cleanup: File closed safely.')",
                        "highlights": [
                            {"line": 3, "label": "try block: contains code that might fail"},
                            {"line": 7, "label": "except block: catches specific error"},
                            {"line": 11, "label": "else block: runs strictly on success"},
                            {"line": 15, "label": "finally block: always guaranteed to run"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 3, "scope": "Entering try block"},
                        {"step": 2, "active_line": 7, "scope": "Catching FileNotFoundError"},
                        {"step": 3, "active_line": 15, "scope": "Finally cleanup guaranteed"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Stack Unwinding: How Exceptions Travel Up the Call Stack",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "When an exception occurs deep inside a nested function, Python initiates Stack Unwinding. Let's watch: main calls calculate, which calls divide. When divide attempts ten divided by zero, a ZeroDivisionError object is instantiated. Divide has no try block, so Python terminates divide and pops it off the stack! It jumps up to calculate; no handler exists there either. Finally, it arrives back at main, finds a matching except block, and handles the error gracefully without crashing your server.",
                "estimated_duration": 26.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": "Call Stack Unwinding in Action",
                    "subtitle": "How Exceptions Bubble Up Across Nested Functions",
                    "parameters": {
                        "language": "python",
                        "code": "def divide(a, b):\n    return a / b  # <-- ZeroDivisionError raised here!\n\ndef calculate(x, y):\n    return divide(x, y)  # Unwinds up call stack\n\ndef main():\n    try:\n        result = calculate(10, 0)\n    except ZeroDivisionError as e:\n        print(f'Caught at top level: {e}')\n        result = 0\n    return result",
                        "highlights": [
                            {"line": 2, "label": "Error occurs in deepest leaf function"},
                            {"line": 5, "label": "Stack frame popped: bubbles up"},
                            {"line": 9, "label": "Target except block catches and recovers!"}
                        ],
                        "variables": {"a": 10, "b": 0, "active_error": "ZeroDivisionError", "stack_depth": "main -> calculate -> divide"}
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 2, "scope": "divide(10, 0) raises error"},
                        {"step": 2, "active_line": 5, "scope": "calculate frame unwound"},
                        {"step": 3, "active_line": 9, "scope": "main catches ZeroDivisionError"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Exception Class Hierarchy & Custom Exceptions",
                "pedagogical_phase": "edge_cases",
                "narration_text": "In Python, all exceptions are standard object-oriented classes organized in a strict inheritance tree. At the very root sits BaseException, followed by Exception. When you write except LookupError, Python will catch both IndexError and KeyError because they are child subclasses! To write professional code, you can define your own custom exceptions by inheriting from Exception, allowing your application to signal domain-specific business logic errors.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "hierarchy_pyramid",
                    "title": "The Python Built-In Exception Tree",
                    "subtitle": "BaseException -> Exception -> Specific Subclasses",
                    "parameters": {
                        "pyramid_title": "Python Exception Class Hierarchy",
                        "tiers": [
                            {"tier": "BaseException (SystemExit, KeyboardInterrupt)", "note": "Root class. Should almost NEVER be caught directly in application code!"},
                            {"tier": "Exception (Standard Application Errors)", "note": "Root for all non-system-exiting errors; base class for user custom exceptions"},
                            {"tier": "ArithmeticError (ZeroDivisionError, OverflowError)", "note": "Mathematical failures during runtime arithmetic"},
                            {"tier": "LookupError (KeyError, IndexError)", "note": "Dictionary key missing or list index out of bounds"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "BaseException & SystemExit"},
                        {"step": 2, "highlight": "Exception Subclasses"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Production Best Practices: Antipatterns vs. Clean Code",
                "pedagogical_phase": "summary",
                "narration_text": "Let us conclude with the golden rules of production error handling. The cardinal sin of Python programming is the bare except pass: catching every error silently and doing nothing. This masks critical bugs, keyboard interrupts, and memory errors! Instead, follow three principles: catch only the specific exceptions you anticipate, preserve error contexts using the raise keyword, and prefer context managers with the with statement for automatic resource cleanup.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Production Best Practices vs Antipatterns",
                    "subtitle": "Writing Robust, Maintainable Error Handling",
                    "parameters": {
                        "col1": "The Silent Killer (Antipattern): 'except: pass'. Masks typos, breaks debugging, swallows KeyboardInterrupt.",
                        "col2": "Specific & Informative: 'except (KeyError, ValueError) as err:'. Explicitly handle expected failures with logging.",
                        "col3": "Pythonic Resource Cleanup: Use 'with open(...) as f:' context managers instead of manual try/finally close."
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Antipattern"},
                        {"step": 2, "highlight": "Specific Exception"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "Exception handling in Python provides a structured mechanism for detecting and recovering from runtime errors without crashing the program. Through try, except, else, and finally blocks, call stack unwinding, and object-oriented exception hierarchies, Python programs maintain reliability, data integrity, and clean resource management.",
            "notes_markdown": """# Python Exception Handling: Complete Engineering Guide

## 1. Syntax vs. Exception
- **SyntaxError**: Detected during parsing before execution begins (e.g. `if x = 5:`).
- **Exception**: Occurs during runtime when syntactically valid code encounters an impossible state (e.g. dividing by zero, file not found, network timeout).

## 2. The Four Keyword Blocks
```python
try:
    # Code that may raise an exception
    value = database.fetch(user_id)
except UserNotFoundError as e:
    # Code executed if specific exception occurs
    logger.warning(f"User {user_id} not found: {e}")
    value = default_user()
else:
    # Executed ONLY if try block completed with NO exceptions
    logger.info("Data fetched successfully")
finally:
    # ALWAYS executed regardless of success, exception, or early return
    database.close_connection()
```

## 3. The Exception Class Hierarchy
```
BaseException
 ├── SystemExit
 ├── KeyboardInterrupt
 └── Exception
      ├── ArithmeticError
      │    └── ZeroDivisionError
      ├── LookupError
      │    ├── IndexError
      │    └── KeyError
      ├── ValueError
      └── TypeError
```

## 4. Defining Custom Exceptions
```python
class InsufficientFundsError(Exception):
    def __init__(self, balance: float, amount: float):
        self.balance = balance
        self.amount = amount
        super().__init__(f"Cannot withdraw ${amount}; balance is only ${balance}")

# Usage:
def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientFundsError(balance, amount)
    return balance - amount
```
""",
            "key_concepts": [
                {"concept": "Stack Unwinding", "definition": "The process by which the Python runtime terminates active function call frames in reverse order until a matching except block is located.", "importance": "Allows high-level functions to handle errors originating in deep helper functions."},
                {"concept": "Bare Except Antipattern", "definition": "Writing `except:` without an exception type, which catches `BaseException` including `KeyboardInterrupt` and `SystemExit`.", "importance": "Dangerous bug masking practice; always catch `Exception` or specific subtypes."},
                {"concept": "Context Manager (`with` statement)", "definition": "A language construct implementing `__enter__` and `__exit__` methods that guarantees cleanup even when exceptions occur.", "importance": "Pythonic alternative to verbose try/finally blocks."}
            ],
            "formulas_or_code": [
                {"title": "Re-raising Exceptions", "type": "code", "content": "try:\n    perform_action()\nexcept Exception as err:\n    log_error(err)\n    raise  # Re-raises current exception preserving original traceback", "explanation": "Preserves original stack trace when logging and propagating."},
                {"title": "Custom Exception Class", "type": "code", "content": "class CustomError(Exception):\n    pass", "explanation": "Standard idiomatic way to create domain-specific application exceptions."}
            ],
            "practice_questions": [
                {"question": "In a `try-except-else-finally` block, if the `try` block executes `return 10`, does the `finally` block still execute?", "hint": "Consider the guaranteed nature of the `finally` keyword.", "solution": "Yes! The `finally` block is guaranteed to run before the function returns to the caller, even when early return statements are executed inside the `try` or `except` blocks."}
            ],
            "quiz": [
                {"id": 1, "question": "When does the `else` block execute in a Python try/except construct?", "options": ["Whenever an exception is caught", "Only when the try block completes with zero exceptions", "Always right before the finally block", "Only when a syntax error occurs"], "correct_index": 1, "explanation": "The else block executes strictly if no exception was raised in the try block."},
                {"id": 2, "question": "Why is writing `except Exception:` considered better than writing a bare `except:`?", "options": ["It runs 10x faster", "It prevents accidentally catching SystemExit and KeyboardInterrupt (Ctrl+C)", "It automatically writes to log files", "It is required by the Python compiler"], "correct_index": 1, "explanation": "A bare except catches BaseException, which intercepts critical system signals like KeyboardInterrupt and SystemExit, preventing the user from stopping the program."}
            ],
            "flashcards": [
                {"id": 1, "front": "What is the difference between IndexError and KeyError?", "back": "IndexError occurs when accessing a sequence with an out-of-range integer index; KeyError occurs when looking up a non-existent key in a dictionary.", "category": "Built-in Exceptions"},
                {"id": 2, "front": "What does the 'finally' block guarantee?", "back": "It guarantees execution under all circumstances, even after errors, caught exceptions, or early return statements.", "category": "Control Flow"}
            ]
        }

        return {
            "title": "Exception Handling in Python: Writing Crash-Proof Code",
            "domain": "computer_science",
            "subdomain": "Software Engineering & Python Runtime",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_country_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        country_name = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. Origins & Ancient Heritage of {country_name}",
                "pedagogical_phase": "hook",
                "narration_text": f"Every nation tells a story of human adaptation, culture, and survival. To truly understand {country_name}, we must journey back to its geographical cradle and earliest inhabitants. Natural rivers, mountains, and coastlines shaped its early trade and spiritual traditions, laying the cultural bedrock that survives to this day.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "hierarchy_pyramid",
                    "title": f"The Cultural & Geographic Foundations of {country_name}",
                    "subtitle": "Geographic Cradle, Early Peoples & Cultural Identity",
                    "parameters": {
                        "pyramid_title": f"{country_name} Civilizational Bedrock",
                        "tiers": [
                            {"tier": "Spiritual Ethos & Cultural Traditions", "note": "Enduring values, folklore, and community identity"},
                            {"tier": "Early Settlements & Ancient Kingdoms", "note": "First unified governance and legal systems"},
                            {"tier": "Geographical Landscape & Rivers", "note": "Topography, fertile valleys, and natural trade routes"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Geographical landscape"},
                        {"step": 2, "highlight": "Early kingdoms"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": f"2. Golden Ages & Historical Epochs",
                "pedagogical_phase": "foundation",
                "narration_text": f"Across the centuries, {country_name} passed through defining historical epochs. From formative classical dynasties to transformative golden ages of arts, architecture, and commerce, these pivotal eras forged the national character and connected its people to the broader global stage.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "timeline_journey",
                    "title": f"Historical Epochs of {country_name}",
                    "subtitle": "From Ancient Foundations to Modern Era",
                    "parameters": {
                        "milestones": [
                            {"year": "Classical Era", "title": "Formation & Antiquity", "desc": "Establishment of early national identity and commerce", "impact": "Foundational unity"},
                            {"year": "Golden Age", "title": "Cultural & Architectural Flourishing", "desc": "Peak literature, scholarship, and trade influence", "impact": "Lasting monuments & arts"},
                            {"year": "Modern Transition", "title": "Nation-State Consolidation", "desc": "Entering the modern industrial and geopolitical world", "impact": "Sovereignty & institutions"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Classical Era"},
                        {"step": 2, "highlight": "Golden Age"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Crucible: Struggles, Wars & Independence",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"No society evolves without struggle. {country_name} has weathered external invasions, internal conflicts, and major political revolutions. How its citizens overcame these existential trials reveals the resilience and solidarity that define the nation today.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": "Historical Turning Points & National Resilience",
                    "subtitle": "Catalysts of Transformation and Rebirth",
                    "parameters": {
                        "root_catalyst": f"Major Historical Crucible / Reform in {country_name}",
                        "intermediate_effects": [
                            "Mobilization of citizen movements and military defense",
                            "Restructuring of political and constitutional institutions"
                        ],
                        "ultimate_consequence": "Emergence of modern sovereign governance and national pride"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Historical Crucible"},
                        {"step": 2, "highlight": "Sovereign Governance"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": f"4. Society, Culture & Pluralism in {country_name}",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"Look inside modern {country_name} and you find a vibrant human tapestry. Its language, regional traditions, festivals, and culinary heritage demonstrate how diverse communities unite under a common identity, balancing historical traditions with rapid modernization.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": f"The Cultural & Social Pillars of {country_name}",
                    "subtitle": "Language, Regional Diversity & National Institutions",
                    "parameters": {
                        "col1": "Linguistic & Cultural Heritage: Regional dialects, arts, music, and culinary traditions",
                        "col2": "Social & Civic Fabric: Community values, educational institutions, and public life",
                        "col3": "Economic Drivers: Industry, agriculture, technological innovation, and trade"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Cultural Heritage"},
                        {"step": 2, "highlight": "Civic Fabric"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": f"5. Modern {country_name} on the Global Stage",
                "pedagogical_phase": "summary",
                "narration_text": f"Today, {country_name} plays an active role in international diplomacy, global trade, science, and cultural exchange. By drawing strength from its rich history while embracing the future, {country_name} continues to inspire and contribute to humanity's collective journey.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": f"{country_name} in the 21st Century",
                    "subtitle": "Preserving Ancient Heritage while Driving Modern Innovation",
                    "parameters": {
                        "left_label": "Historical Roots: Heritage, traditional arts, foundational values",
                        "right_label": "Global Horizon: Technological advancement, international trade, diplomacy",
                        "center_balance": "National Synthesis: Dynamic modern society grounded in deep history",
                        "markers": [
                            "Ancient Heritage",
                            "National Institutions",
                            "Global Leadership"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Historical Roots"},
                        {"step": 2, "highlight": "Global Horizon"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This educational masterclass explores {country_name}: its civilizational origins and geography, golden classical eras, historical struggles and independence, cultural and social pluralism, and its modern role on the global stage.",
            "notes_markdown": f"""# {country_name}: History, Culture & Modern Society

## 1. Geographic & Ancient Foundations
- The geographic environment, rivers, and coastlines that shaped early settlement in {country_name}.
- Spiritual, philosophical, and folk traditions that formed the bedrock of communal life.

## 2. Defining Historical Eras
- Classical governance and early legal codes.
- Flourishing of architecture, literature, and trade during golden epochs.
- Modern transitions toward democratic sovereignty and constitutional governance.

## 3. Society & Global Contribution
- Pluralism, language, arts, and culinary traditions.
- Contributions to world diplomacy, science, and the global economy.
""",
            "key_concepts": [
                {"concept": f"{country_name} Civilizational Identity", "definition": "The enduring collective values, historical continuity, and shared cultural ethos of the nation.", "importance": "Unifies diverse regional traditions."},
                {"concept": "Cultural Synthesis", "definition": "The blending of historical heritage with contemporary innovations and global connections.", "importance": "Drives dynamic social and economic development."}
            ],
            "formulas_or_code": [
                {"title": "Civilizational Invariant", "type": "principle", "content": "Historical Roots + Pluralistic Unity = National Resilience", "explanation": "How nations sustain longevity across centuries of global change."}
            ],
            "practice_questions": [
                {"question": f"How has geography influenced the cultural and economic development of {country_name}?", "hint": "Consider natural borders, waterways, and trade routes.", "solution": f"Natural geography in {country_name} determined agricultural centers, trade connections with neighboring regions, and protected cultural continuity across historical epochs."}
            ],
            "quiz": [
                {"id": 1, "question": f"What forms the foundational bedrock of {country_name}'s cultural continuity?", "options": ["Isolation from all trade", "Deep historical heritage, shared values, and cultural traditions", "Constant total abandonment of the past", "Random chance without institutions"], "correct_index": 1, "explanation": "Nations endure through shared cultural heritage, resilient institutions, and adaptive unity."},
                {"id": 2, "question": f"Why is understanding the historical epochs of {country_name} important today?", "options": ["It is only useful for ancient history exams", "Modern social, legal, and cultural institutions are rooted in historical developments", "History has no bearing on current affairs", "To memorize dates without context"], "correct_index": 1, "explanation": "Contemporary culture, legal systems, and national identity are directly shaped by historical milestones."}
            ],
            "flashcards": [
                {"id": 1, "front": f"What is a primary characteristic of {country_name}'s social fabric?", "back": "A dynamic balance between cherished historical traditions and modern global innovation.", "category": "Culture"},
                {"id": 2, "front": f"How do historical challenges shape {country_name}?", "back": "Overcoming adversity builds institutional resilience and reinforces shared national solidarity.", "category": "History"}
            ]
        }

        return {
            "title": f"{country_name}: History, Heritage & Modern Civilization",
            "domain": "history",
            "subdomain": "Civilizations, Culture & Geopolitics",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_programming_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        tech_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Core Problem: Why We Need {tech_title}",
                "pedagogical_phase": "hook",
                "narration_text": f"Every great programming feature exists to solve a real engineering pain point. Without {tech_title}, code becomes fragile, difficult to maintain, and prone to silent failures. By understanding the exact software problem it eliminates, the syntax and mechanics will make immediate intuitive sense.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"The Engineering Problem Behind {tech_title}",
                    "subtitle": "Fragile Ad-Hoc Code vs. Robust Structured Patterns",
                    "parameters": {
                        "left_title": f"Without {tech_title}",
                        "left_items": ["Brittle, error-prone boilerplate", "Difficult to debug or scale", "Uncontrolled runtime side-effects"],
                        "right_title": f"With {tech_title}",
                        "right_items": ["Clean, idiomatic syntax", "Predictable execution and state flow", "Robust, production-grade maintainability"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Brittle boilerplate"},
                        {"step": 2, "highlight": "Robust pattern"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Syntax & Mechanics: The Core Anatomy",
                "pedagogical_phase": "foundation",
                "narration_text": f"Let us examine the exact syntax structure. Notice how the language constructs establish clear boundaries. Each keyword and parameter plays a distinct role in orchestrating how data and execution flow through your application.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": f"{tech_title} Syntax & Structure",
                    "subtitle": "Idiomatic Implementation & Language Rules",
                    "parameters": {
                        "language": "python",
                        "code": f"# Demonstrating {tech_title}\ndef execute_pattern(data):\n    # 1. Setup preconditions\n    if not data:\n        raise ValueError('Invalid input data')\n        \n    # 2. Core construct in action\n    result = process_data(data)\n    \n    # 3. Clean return of processed state\n    return result",
                        "highlights": [
                            {"line": 2, "label": "Define idiomatic function signature"},
                            {"line": 4, "label": "Input validation & error boundary"},
                            {"line": 8, "label": "Core construct invocation"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 2, "scope": "Function entry"},
                        {"step": 2, "active_line": 4, "scope": "Validation check"},
                        {"step": 3, "active_line": 8, "scope": "Core execution"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Live Execution Trace & Memory Scope",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Now let us watch the code execute line by line. Notice how variables transform in memory and how control flow transitions between scopes. Tracking this runtime behavior demystifies what the interpreter or compiler is doing behind the scenes.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": "Interactive Execution & Variable Watch",
                    "subtitle": "Step-by-Step State Changes During Runtime",
                    "parameters": {
                        "language": "python",
                        "code": f"# Runtime Tracing for {tech_title}\nitems = [10, 20, 30]\ntotal = 0\n\nfor item in items:\n    total += item\n    print(f'Active item: {{item}}, Running total: {{total}}')\n\nreturn total",
                        "highlights": [
                            {"line": 2, "label": "State initialized in scope"},
                            {"line": 5, "label": "Loop iteration & accumulator update"},
                            {"line": 8, "label": "Final state returned"}
                        ],
                        "variables": {"active_item": 20, "running_total": 30, "items_remaining": 1}
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 2, "scope": "total=0"},
                        {"step": 2, "active_line": 6, "scope": "total=30"},
                        {"step": 3, "active_line": 8, "scope": "return total=60"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Edge Cases, Pitfalls & Hidden Traps",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"Experienced software engineers are defined by how they handle the edge cases. What happens when inputs are null, resources are exhausted, or concurrency conflicts occur? Knowing these traps ensures your software remains rock-solid in production.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Common Antipatterns vs. Production Best Practices",
                    "subtitle": f"Writing Resilient, Maintainable {tech_title}",
                    "parameters": {
                        "col1": "Common Trap: Ignoring boundary conditions and unhandled null/empty inputs",
                        "col2": "Defensive Pattern: Explicit validation, clear error boundaries, and self-documenting types",
                        "col3": "Performance Tip: Minimize unnecessary allocations and release resources promptly"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Common Trap"},
                        {"step": 2, "highlight": "Defensive Pattern"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Production Architecture & Real-World Use",
                "pedagogical_phase": "summary",
                "narration_text": f"To master {tech_title}, integrate it into your everyday architectural toolkit. By favoring clarity over cleverness, enforcing invariants, and writing self-explanatory code, you build software that is both elegant and durable.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Production Engineering Summary",
                    "subtitle": "Key Takeaways for Professional Codebases",
                    "parameters": {
                        "col1": "Readability First: Code is read far more often than it is written",
                        "col2": "Resource Safety: Always guarantee cleanup via context managers or finalizers",
                        "col3": "Testability: Structure functions to be purely deterministic and easily tested"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Readability"},
                        {"step": 2, "highlight": "Resource Safety"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This software engineering masterclass on {tech_title} covers core syntax, execution mechanics, call stack and memory scope behavior, critical edge cases, and production-grade best practices.",
            "notes_markdown": f"""# {tech_title}: Software Engineering Guide

## 1. Executive Summary
Understanding **{tech_title}** requires mastering both its mental model and syntax:
- **Core Purpose**: Eliminates fragile ad-hoc code in favor of robust, idiomatic patterns.
- **Runtime Mechanics**: Predictable execution, stack management, and scope isolation.
- **Production Standard**: Defensive validation, explicit error boundaries, and resource safety.

## 2. Best Practices Checklist
1. Validate inputs early at boundary interfaces.
2. Ensure all external resources (sockets, files, connections) are cleanly finalized.
3. Write expressive, self-documenting code with meaningful names.
""",
            "key_concepts": [
                {"concept": f"{tech_title} Idiom", "definition": "The standard, community-accepted way to structure this pattern cleanly.", "importance": "Ensures codebase consistency and readability."},
                {"concept": "Resource Cleanup", "definition": "Guaranteeing that memory, handles, and connections are released even under failure.", "importance": "Prevents catastrophic memory and connection leaks in servers."}
            ],
            "formulas_or_code": [
                {"title": "The Golden Rule of Software Design", "type": "principle", "content": "Clarity > Cleverness; Explicit > Implicit", "explanation": "Code should clearly communicate intent without hidden side effects."}
            ],
            "practice_questions": [
                {"question": f"What is the most critical advantage of applying {tech_title} correctly?", "hint": "Think about debugging, maintainability, and production stability.", "solution": f"Applying {tech_title} correctly prevents unexpected runtime crashes, isolates failures cleanly, and makes the codebase readable and maintainable for team members."}
            ],
            "quiz": [
                {"id": 1, "question": f"What should be the primary consideration when implementing {tech_title}?", "options": ["Writing the shortest, most cryptic code possible", "Clear readability, explicit error boundaries, and resource safety", "Ignoring edge cases to save time", "Using global variables everywhere"], "correct_index": 1, "explanation": "Maintainable software prioritizes readability, safety, and clear boundaries."},
                {"id": 2, "question": f"Why is handling edge cases essential in {tech_title}?", "options": ["It is only needed for toy exercises", "Production systems almost always fail at boundary inputs if unhandled", "Edge cases never happen in real life", "It can be safely ignored"], "correct_index": 1, "explanation": "Real-world failures happen at boundaries: network dropouts, null inputs, and unexpected states."}
            ],
            "flashcards": [
                {"id": 1, "front": f"What is the golden rule when writing {tech_title}?", "back": "Clarity is superior to cleverness; always write code that communicates intent explicitly.", "category": "Clean Code"},
                {"id": 2, "front": "Why is resource finalization critical?", "back": "To avoid leaking system handles, file descriptors, or memory pools during runtime.", "category": "Architecture"}
            ]
        }

        return {
            "title": f"Mastering {tech_title}: Core Mechanics & Production Patterns",
            "domain": "computer_science",
            "subdomain": "Software Engineering & Architecture",
            "scenes": scenes,
            "materials": materials
        }

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

    def _build_binary_search_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Dictionary Dilemma: Linear vs Logarithmic",
                "pedagogical_phase": "hook",
                "narration_text": "Imagine opening a 1,000-page dictionary to find the word 'Quantum'. If you started from page 1 and flipped page by page, you would waste tremendous time checking 500 pages. Instead, you naturally flip right to the middle. If you see words starting with 'M', you know immediately that 'Q' must be in the right half, instantly discarding 500 pages in a single move. This intuitive division is the exact power of Binary Search.",
                "estimated_duration": 22.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Search Strategy Comparison",
                    "subtitle": "Linear Page-by-Page vs. Binary Division",
                    "parameters": {
                        "metaphor": "dictionary_search",
                        "left_label": "Linear Search: O(N)",
                        "left_items": ["Page 1: A", "Page 2: B", "Page 3: C", "...", "Page 500: Target Found (500 steps)"],
                        "right_label": "Binary Search: O(log N)",
                        "right_items": ["Open middle (Page 500)", "Target 'Q' > 'M' -> Discard 1-500", "Open middle of remainder", "Found in ~10 steps!"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "1,000 pages search space established", "highlight": "entire_space"},
                        {"step": 2, "description": "Dividing search space in half", "highlight": "middle_split"},
                        {"step": 3, "description": "Discarding 500 pages instantly", "highlight": "eliminated_half"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Invariant: Sorted Arrays & Three Pointers",
                "pedagogical_phase": "foundation",
                "narration_text": "Binary search has one non-negotiable prerequisite: the array must be sorted. Without order, division is impossible. We maintain three key pointers: Low at the start of our search window, High at the end, and Mid right in the center. The formula is simple: Mid equals Low plus High minus Low divided by two, avoiding integer overflow. In each step, we inspect only the element at Mid.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "algorithm_animator",
                    "title": "Three-Pointer Architecture",
                    "subtitle": "Tracking Low, Mid, and High on a Sorted Array",
                    "parameters": {
                        "algorithm_type": "array_search",
                        "array": [2, 5, 8, 12, 16, 23, 38, 56, 72, 91],
                        "target": 23,
                        "low": 0,
                        "high": 9,
                        "mid": 4,
                        "state_label": "Initial State: Target = 23"
                    },
                    "keyframe_steps": [
                        {"step": 1, "low": 0, "high": 9, "mid": 4, "action": "Calculate mid = 0 + (9-0)//2 = 4", "val": 16, "status": "active"},
                        {"step": 2, "low": 0, "high": 9, "mid": 4, "action": "Compare array[mid] (16) vs Target (23)", "val": 16, "status": "comparing"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Elimination Engine: Step-by-Step Execution",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "Let us watch the algorithm in motion. We are searching for 23. Mid points to index 4, which holds the value 16. Since 16 is strictly less than 23, our target cannot possibly exist anywhere from index 0 to 4. We eliminate the entire left half! We shift Low to Mid plus one, which is index 5. Now our new window is from index 5 to 9. We recalculate Mid to index 7, which holds 56. 56 is greater than 23, so we eliminate the right half! Finally, Low and High converge on index 5, value 23. Target found in just three comparisons!",
                "estimated_duration": 29.0,
                "visual_spec": {
                    "visual_type": "algorithm_animator",
                    "title": "Live Binary Search Execution",
                    "subtitle": "Target: 23 in [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]",
                    "parameters": {
                        "algorithm_type": "array_search",
                        "array": [2, 5, 8, 12, 16, 23, 38, 56, 72, 91],
                        "target": 23,
                        "steps": [
                            {
                                "step_num": 1,
                                "low": 0,
                                "high": 9,
                                "mid": 4,
                                "mid_val": 16,
                                "comparison": "16 < 23 (Target is larger)",
                                "decision": "Eliminate left window [0..4], Move low = mid + 1",
                                "eliminated": [0, 1, 2, 3, 4]
                            },
                            {
                                "step_num": 2,
                                "low": 5,
                                "high": 9,
                                "mid": 7,
                                "mid_val": 56,
                                "comparison": "56 > 23 (Target is smaller)",
                                "decision": "Eliminate right window [7..9], Move high = mid - 1",
                                "eliminated": [0, 1, 2, 3, 4, 7, 8, 9]
                            },
                            {
                                "step_num": 3,
                                "low": 5,
                                "high": 6,
                                "mid": 5,
                                "mid_val": 23,
                                "comparison": "23 == 23 (Match Found!)",
                                "decision": "Return index 5 successfully!",
                                "eliminated": [0, 1, 2, 3, 4, 6, 7, 8, 9],
                                "matched": 5
                            }
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "low": 0, "high": 9, "mid": 4, "msg": "Mid is 16. Target 23 > 16. Discard left."},
                        {"step": 2, "low": 5, "high": 9, "mid": 7, "msg": "Mid is 56. Target 23 < 56. Discard right."},
                        {"step": 3, "low": 5, "high": 6, "mid": 5, "msg": "Mid is 23. Match found at index 5!"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Clean Code Implementation & Variable Watch",
                "pedagogical_phase": "edge_cases",
                "narration_text": "Here is the canonical Python implementation. Notice the while loop condition: while low is less than or equal to high. That 'less than or equal' is crucial for arrays with an odd length or single elements. Inside the loop, if array at mid matches target, we return mid. If the target is greater, we search the right sub-array. Otherwise, we search the left. If low crosses high without a match, we return minus one.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": "Python Binary Search Implementation",
                    "subtitle": "Iterative Implementation with While Loop",
                    "parameters": {
                        "language": "python",
                        "code": "def binary_search(arr, target):\n    low = 0\n    high = len(arr) - 1\n    \n    while low <= high:\n        mid = low + (high - low) // 2\n        \n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n            \n    return -1",
                        "highlights": [
                            {"line": 2, "label": "Initialize pointers: low=0, high=9"},
                            {"line": 5, "label": "Loop invariant: low <= high"},
                            {"line": 6, "label": "Safe mid calculation avoiding overflow"},
                            {"line": 8, "label": "Base case: match found"},
                            {"line": 10, "label": "Target in right half: low = mid + 1"},
                            {"line": 12, "label": "Target in left half: high = mid - 1"},
                            {"line": 14, "label": "Exhausted search space: return -1"}
                        ],
                        "variables": {"low": 5, "high": 6, "mid": 5, "target": 23, "return": 5}
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 2, "scope": "low=0, high=9"},
                        {"step": 2, "active_line": 6, "scope": "mid=4 (arr[4]=16)"},
                        {"step": 3, "active_line": 10, "scope": "low updated to 5"},
                        {"step": 4, "active_line": 8, "scope": "arr[5]==23 -> return 5"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Time Complexity: Why O(log N) Changes Everything",
                "pedagogical_phase": "summary",
                "narration_text": "The logarithmic efficiency of binary search is staggering. For an array of 1 million items, linear search would take on average 500,000 checks. Binary search takes at most 20 checks. For 4 billion items, the entire internet population, binary search finds any user in just 32 operations. It turns an impossible problem into an instantaneous lookup. Remember: sorted input, three pointers, eliminate half each step.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "math_graph",
                    "title": "Computational Scale: O(N) vs O(log N)",
                    "subtitle": "Number of Operations as Input Size (N) Grows",
                    "parameters": {
                        "curve_type": "complexity_comparison",
                        "x_label": "Input Elements (N)",
                        "y_label": "Operations Required",
                        "data_points": [
                            {"n": "16", "linear": 16, "binary": 4},
                            {"n": "1,024", "linear": 1024, "binary": 10},
                            {"n": "1,000,000", "linear": 1000000, "binary": 20},
                            {"n": "4,000,000,000", "linear": 4000000000, "binary": 32}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Plotting linear line O(N)", "highlight": "linear_curve"},
                        {"step": 2, "description": "Plotting flat logarithmic curve O(log N)", "highlight": "log_curve"}
                    ]
                }
            }
        ]

        if num_scenes == 3:
            scenes = [scenes[0], scenes[2], scenes[4]]
            for i, s in enumerate(scenes):
                s["index"] = i

        materials = {
            "summary": "Binary Search is a foundational divide-and-conquer algorithm that locates an element in a sorted collection in O(log n) logarithmic time. By repeatedly examining the middle element and discarding the non-viable half of the search space, it reduces a problem of billions of elements to a handful of comparisons.",
            "notes_markdown": """# Binary Search: Complete Masterclass Notes

## 1. Core Principle
Binary Search locates a target value within a **sorted array** by halving the search space each step.
- **Time Complexity**:
  - Best Case: $O(1)$ (target located at initial mid)
  - Average Case: $O(\\log n)$
  - Worst Case: $O(\\log n)$
- **Space Complexity**:
  - Iterative: $O(1)$ auxiliary space
  - Recursive: $O(\\log n)$ call stack space

## 2. The 3 Pointer Pattern
```python
def binary_search(arr: list[int], target: int) -> int:
    low = 0
    high = len(arr) - 1
    
    while low <= high:
        # Avoid integer overflow (in languages like C++/Java)
        mid = low + (high - low) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1  # Target is in the right half
        else:
            high = mid - 1 # Target is in the left half
            
    return -1  # Target not found
```

## 3. Essential Edge Cases
1. **Empty Array**: `len(arr) == 0` returns `-1`.
2. **Single Element**: Verified correctly because `low <= high` uses `<=` instead of `<`.
3. **Target Smaller Than Minimum**: `high` moves to `-1`, terminating properly.
4. **Target Greater Than Maximum**: `low` exceeds `len(arr)-1`, terminating properly.
5. **Duplicates**: Standard binary search returns any valid match index. For first/last occurrence, adjust pointer without early return.
""",
            "key_concepts": [
                {"concept": "Sorted Invariant", "definition": "The array must be ordered; without sorting, eliminating halves is mathematically invalid.", "importance": "Prerequisite for algorithm correctness."},
                {"concept": "Search Space Halving", "definition": "Discarding $\\frac{N}{2}$ candidate items in every comparison step.", "importance": "Provides $O(\\log N)$ exponential reduction in computation."},
                {"concept": "Integer Overflow Guard", "definition": "Calculating `mid = low + (high - low) // 2` rather than `(low + high) // 2`.", "importance": "Prevents arithmetic overflow in 32-bit integer systems."}
            ],
            "formulas_or_code": [
                {"title": "Logarithmic Steps Formula", "type": "formula", "content": "k = \\lceil \\log_2(N) \\rceil", "explanation": "Maximum number of iterations required to find target or determine absence in an array of size N."},
                {"title": "Midpoint Calculation", "type": "code", "content": "mid = low + (high - low) // 2", "explanation": "Calculates midpoint index safely within bounds."}
            ],
            "practice_questions": [
                {"question": "How many comparisons does Binary Search take in the worst case for an array with 1,048,576 elements?", "hint": "Calculate log base 2 of 2^20.", "solution": "Since 1,048,576 = 2^20, Binary Search requires at most 20 comparisons plus 1 final check, so at most 21 operations."},
                {"question": "What happens if we mistakenly write `while low < high:` instead of `while low <= high:`?", "hint": "Consider a single-element array like [5] with target 5.", "solution": "With low < high, a single-element array (where low == high == 0) will skip the loop entirely and return -1 without checking the target."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the primary prerequisite for Binary Search to function correctly?", "options": ["Array must contain unique elements", "Array must be sorted", "Array length must be an even power of 2", "Elements must all be positive integers"], "correct_index": 1, "explanation": "Binary search fundamentally relies on order so that comparing the midpoint guarantees which half can be discarded."},
                {"id": 2, "question": "What is the worst-case time complexity of Binary Search on an array of size N?", "options": ["O(1)", "O(N)", "O(log N)", "O(N log N)"], "correct_index": 2, "explanation": "Halving the search space each step produces a logarithmic time complexity of O(log N)."},
                {"id": 3, "question": "Why is `mid = low + (high - low) // 2` preferred over `mid = (low + high) // 2` in many programming languages?", "options": ["It computes faster on the CPU", "It prevents 32-bit integer overflow when low + high exceeds 2^31 - 1", "It handles negative numbers better", "It is required by the Python interpreter"], "correct_index": 1, "explanation": "In statically typed languages like C, C++, and Java, low + high can overflow the maximum signed 32-bit integer, resulting in a negative index."}
            ],
            "flashcards": [
                {"id": 1, "front": "What is the time complexity of Binary Search?", "back": "O(log N) in both average and worst case; O(1) in best case.", "category": "Complexity"},
                {"id": 2, "front": "Why is the loop condition 'while low <= high' and not '<'?", "back": "To allow checking the final remaining element when low and high converge on the same index.", "category": "Implementation"},
                {"id": 3, "front": "What is the auxiliary space complexity of iterative binary search?", "back": "O(1) constant auxiliary space, as only low, high, and mid pointers are stored.", "category": "Memory"}
            ]
        }

        return {
            "title": "Mastering Binary Search: Intuition, Algorithm & Complexity",
            "domain": "computer_science",
            "subdomain": "Algorithms & Data Structures",
            "scenes": scenes,
            "materials": materials
        }

    def _build_neural_networks_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Artificial Neuron: Inputs, Weights & Biases",
                "pedagogical_phase": "hook",
                "narration_text": "How can a computer recognize a handwritten digit, translate languages, or drive a car? At the heart of deep learning is a surprisingly simple mathematical building block: the artificial neuron. Just like biological synapses, it takes multiple input signals, scales each by an adjustable weight, adds an internal bias, and passes the sum through an activation function.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "process_simulation",
                    "title": "The Perceptron Architecture",
                    "subtitle": "Weighted Inputs Summed and Activated",
                    "parameters": {
                        "inputs": ["x1: Pixel Brightness", "x2: Edge Angle", "x3: Contrast"],
                        "weights": ["w1 = 0.8", "w2 = -0.4", "w3 = 1.2"],
                        "summation": "z = Σ(wi · xi) + b",
                        "activation": "a = σ(z) = 1 / (1 + e^-z)",
                        "output": "Probability: 0.94 (Digit '7')"
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Signals flow into input dendrites"},
                        {"step": 2, "description": "Weighted linear combination computed"},
                        {"step": 3, "description": "Non-linear activation fires"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Forward Propagation: From Pixels to Predictions",
                "pedagogical_phase": "foundation",
                "narration_text": "When we stack hundreds of these neurons into layers, we form a deep neural network. Information flows strictly forward. The input layer takes raw data, hidden layers extract increasingly abstract features like edges, textures, and object shapes, and the output layer outputs probabilities via the Softmax function.",
                "estimated_duration": 22.0,
                "visual_spec": {
                    "visual_type": "diagram_board",
                    "title": "Deep Neural Network Architecture",
                    "subtitle": "Input Layer -> Hidden Layers -> Output Layer",
                    "parameters": {
                        "layers": [
                            {"name": "Input Layer", "nodes": 4, "role": "Raw Features"},
                            {"name": "Hidden Layer 1", "nodes": 6, "role": "Low-level Edges"},
                            {"name": "Hidden Layer 2", "nodes": 6, "role": "High-level Shapes"},
                            {"name": "Output Layer", "nodes": 2, "role": "Classification"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Input pulse enters network"},
                        {"step": 2, "description": "Hidden activations compute"},
                        {"step": 3, "description": "Output prediction emitted"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Loss Landscape: Measuring Mistake",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "Initially, all weights are random, so the network makes wild guesses. To train it, we define a Loss Function, like Cross-Entropy or Mean Squared Error. The Loss measures how wrong the prediction is. Picture a mountainous 3D terrain: the height of each mountain represents error. Our goal is to descend the mountains to reach the lowest possible valley.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "math_graph",
                    "title": "3D Loss Landscape & Valley of Convergence",
                    "subtitle": "Minimizing Error via Gradient Vector",
                    "parameters": {
                        "curve_type": "loss_surface",
                        "x_axis": "Weight 1",
                        "y_axis": "Loss (Error)",
                        "formula": "L(w) = (y_pred - y_true)^2"
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "High error starting position"},
                        {"step": 2, "description": "Calculating steepest slope"},
                        {"step": 3, "description": "Stepping down toward global minimum"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Backpropagation & The Chain Rule",
                "pedagogical_phase": "edge_cases",
                "narration_text": "Here is the breakthrough: Backpropagation. Using calculus and the chain rule of derivatives, we compute the gradient: how much did each individual weight contribute to the final error? We propagate this error backward from output to input, updating every weight in the opposite direction of the gradient scaled by a learning rate.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": "Gradient Descent Weight Update Rule",
                    "subtitle": "The Mathematical Engine of Learning",
                    "parameters": {
                        "language": "python",
                        "code": "# Backpropagation Step\nfor epoch in range(num_epochs):\n    # 1. Forward Pass\n    y_pred = model.forward(X)\n    loss = criterion(y_pred, y_true)\n    \n    # 2. Backward Pass (Chain Rule)\n    loss.backward()\n    \n    # 3. Parameter Update: w = w - lr * grad\n    with torch.no_grad():\n        for param in model.parameters():\n            param -= learning_rate * param.grad\n            param.grad.zero_()",
                        "highlights": [
                            {"line": 4, "label": "Forward pass prediction"},
                            {"line": 8, "label": "Compute gradients via chain rule"},
                            {"line": 13, "label": "Nudge weights downhill by learning rate"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 4, "scope": "Computing forward activations"},
                        {"step": 2, "active_line": 8, "scope": "Error gradients propagating backwards"},
                        {"step": 3, "active_line": 13, "scope": "Weights updated downhill"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Training in Action & Overfitting",
                "pedagogical_phase": "summary",
                "narration_text": "After millions of micro-adjustments, the network converges. But beware of overfitting: if the model simply memorizes the training data without learning generalized patterns, it will fail in the real world. Techniques like dropout, regularization, and batch normalization keep our neural network robust, enabling modern AI models to generalize remarkably.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Generalization vs Overfitting",
                    "subtitle": "Finding the Optimal Model Complexity",
                    "parameters": {
                        "col1": "Underfitting (High Bias): Model is too simple, fails to capture trend",
                        "col2": "Balanced (Optimal): Smooth decision boundary, high test accuracy",
                        "col3": "Overfitting (High Variance): Fits noise, fails on new unseen data"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Underfitting"},
                        {"step": 2, "highlight": "Balanced"},
                        {"step": 3, "highlight": "Overfitting"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "Neural Networks learn by combining linear transformations with non-linear activations. Through forward propagation, predictions are made; through loss calculation and backpropagation using the calculus chain rule, gradients are passed backward to iteratively update weights using gradient descent.",
            "notes_markdown": """# Neural Networks & Backpropagation: Core Lecture Notes

## 1. Mathematical Anatomy of a Single Neuron
A neuron computes:
$$z = \\sum_{i=1}^{n} w_i x_i + b = \\mathbf{w}^T \\mathbf{x} + b$$
$$a = \\sigma(z)$$
where:
- $\\mathbf{x}$: Input feature vector
- $\\mathbf{w}$: Learned weights vector
- $b$: Bias term
- $\\sigma$: Non-linear activation function (ReLU, Sigmoid, GELU)

## 2. The Backpropagation Algorithm
To minimize loss $L$, we compute partial derivatives $\\frac{\\partial L}{\\partial w_{ij}}$ via the Chain Rule:
$$\\frac{\\partial L}{\\partial w} = \\frac{\\partial L}{\\partial a} \\cdot \\frac{\\partial a}{\\partial z} \\cdot \\frac{\\partial z}{\\partial w}$$

## 3. Gradient Descent Parameter Update
$$w \\leftarrow w - \\eta \\cdot \\frac{\\partial L}{\\partial w}$$
where $\\eta$ represents the **learning rate**.
""",
            "key_concepts": [
                {"concept": "Non-Linear Activation", "definition": "Functions like ReLU ($f(x) = \\max(0, x)$) that enable networks to approximate non-linear boundary functions.", "importance": "Without non-linearities, any deep network collapses mathematically into a single linear matrix."},
                {"concept": "Gradient Descent", "definition": "An iterative optimization algorithm that steps in the opposite direction of the gradient to minimize the loss.", "importance": "Core optimization mechanism powering all deep learning models."},
                {"concept": "Learning Rate", "definition": "Hyperparameter determining the step size taken downhill during gradient descent.", "importance": "Too high causes divergence; too low causes sluggish or trapped training."}
            ],
            "formulas_or_code": [
                {"title": "Weight Update Rule", "type": "formula", "content": "w_{t+1} = w_t - \\eta \\nabla L(w_t)", "explanation": "Updates parameter weights downhill along the negative gradient."},
                {"title": "ReLU Activation", "type": "formula", "content": "f(x) = \\max(0, x)", "explanation": "Most popular activation function, avoids vanishing gradient problem for positive inputs."}
            ],
            "practice_questions": [
                {"question": "Why can't a multi-layer neural network with only linear activation functions solve the XOR problem?", "hint": "Consider the composition of linear transformations.", "solution": "A composition of linear functions is always strictly linear. The XOR problem requires a non-linear decision boundary, which is impossible without non-linear activations."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the primary role of the activation function in a neural network?", "options": ["Speed up floating point arithmetic", "Introduce non-linearity so the network can learn complex patterns", "Normalize weights to sum to one", "Prevent memory leaks in GPU tensors"], "correct_index": 1, "explanation": "Without non-linear activation functions, a network of any depth is mathematically equivalent to a single linear layer."},
                {"id": 2, "question": "What mathematical principle underpins backpropagation?", "options": ["Pythagorean theorem", "The Calculus Chain Rule", "Fourier transform", "Markov chains"], "correct_index": 1, "explanation": "Backpropagation computes partial derivatives through composite functions using the chain rule of calculus."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does the gradient vector point towards?", "back": "The direction of steepest increase of the loss function.", "category": "Calculus"},
                {"id": 2, "front": "Why do we subtract the gradient during weight updates?", "back": "Because we want to minimize error, so we move in the opposite direction (steepest descent).", "category": "Optimization"}
            ]
        }

        return {
            "title": "Neural Networks & Backpropagation: Visualizing How AI Learns",
            "domain": "computer_science",
            "subdomain": "Artificial Intelligence & Machine Learning",
            "scenes": scenes,
            "materials": materials
        }

    def _build_async_await_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Restaurant Chef: Synchronous vs Asynchronous",
                "pedagogical_phase": "hook",
                "narration_text": "Imagine a chef in a restaurant kitchen. In a synchronous world, the chef puts bread in the toaster and stands completely frozen, doing nothing for three minutes until the toast pops up. Customers starve while the kitchen sits idle! In an asynchronous kitchen, the chef drops the bread into the toaster, immediately starts chopping vegetables, and only comes back to grab the toast when a chime rings. This non-blocking concurrency is what async and await deliver to software.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "The Chef Kitchen Metaphor",
                    "subtitle": "Blocking I/O vs. Non-Blocking Event-Driven Concurrency",
                    "parameters": {
                        "left_title": "Synchronous (Blocking)",
                        "left_items": ["Wait for Toaster (3m idle)", "Wait for Water to Boil (5m idle)", "Cook Stew: Total 15 mins wasted"],
                        "right_title": "Async / Event Loop (Non-blocking)",
                        "right_items": ["Start Toaster -> Delegate to Timer", "Chop Veggies concurrently", "Grab toast upon event notification!"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Blocking freeze"},
                        {"step": 2, "highlight": "Async delegation"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Event Loop Architecture",
                "pedagogical_phase": "foundation",
                "narration_text": "Under the hood, single-threaded runtimes like Python asyncio or Node.js utilize an Event Loop. The Call Stack runs your JavaScript or Python code line by line. When an I/O operation like a database query or network request occurs, it is handed off to the OS background pool. The main thread never freezes; it continues handling user clicks or other requests, checking the Task Queue whenever the stack is clear.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "process_simulation",
                    "title": "Event Loop & Task Queue Cycle",
                    "subtitle": "Call Stack -> Web APIs / OS Kernel -> Callback Queue",
                    "parameters": {
                        "components": [
                            {"name": "Call Stack", "desc": "Current execution frame"},
                            {"name": "OS / Web API", "desc": "Handling network socket I/O"},
                            {"name": "Task Queue", "desc": "Completed callbacks waiting"},
                            {"name": "Event Loop", "desc": "Continuously pumping tasks into stack"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Call stack encounters await fetch()"},
                        {"step": 2, "description": "Network request offloaded to background"},
                        {"step": 3, "description": "Task queue notifies event loop on completion"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Code Anatomy: async def and await",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "Writing asynchronous code used to mean messy callback hell. The async and await keywords make asynchronous code read like clean synchronous code. Declaring async def defines a coroutine. When you write await, execution pauses at that exact line and releases the thread. When the awaited operation completes, execution resumes smoothly with the returned value.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": "Async/Await in Action (Python Asyncio)",
                    "subtitle": "Suspending and Resuming Coroutines",
                    "parameters": {
                        "language": "python",
                        "code": "import asyncio\n\nasync def fetch_user_data(user_id):\n    print(f'Fetching user {user_id}...')\n    # Non-blocking pause: thread released!\n    await asyncio.sleep(2) \n    return {'id': user_id, 'name': 'Alex'}\n\nasync def main():\n    # Run multiple tasks concurrently with gather\n    results = await asyncio.gather(\n        fetch_user_data(1),\n        fetch_user_data(2)\n    )\n    print(results)\n\nasyncio.run(main())",
                        "highlights": [
                            {"line": 3, "label": "Defines an async coroutine"},
                            {"line": 6, "label": "await pauses function without blocking thread"},
                            {"line": 11, "label": "Runs both I/O operations simultaneously in parallel time!"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 3, "scope": "Coroutine registered"},
                        {"step": 2, "active_line": 6, "scope": "Thread yields control during sleep"},
                        {"step": 3, "active_line": 11, "scope": "Gather resolves in 2s total instead of 4s!"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Common Pitfalls: Blocking the Loop",
                "pedagogical_phase": "edge_cases",
                "narration_text": "The number one mistake developers make is running CPU-heavy operations inside an async function. If you calculate Fibonacci or run an image filter on the event loop, you block every other user connected to your server! For CPU-heavy work, offload to a worker process or thread pool. Async is strictly designed for I/O-bound operations.",
                "estimated_duration": 22.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "I/O Bound vs CPU Bound",
                    "subtitle": "Choosing the Right Concurrency Tool",
                    "parameters": {
                        "col1": "I/O Bound (Network, DB, Disk): Perfect for Async/Await & Event Loop",
                        "col2": "CPU Bound (Video encoding, ML, Encryption): Requires Multi-Processing / ThreadPool",
                        "col3": "Golden Rule: Never call time.sleep() or sync DB drivers in async def"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "I/O Bound"},
                        {"step": 2, "highlight": "CPU Bound"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Real-World Power: High Throughput Servers",
                "pedagogical_phase": "summary",
                "narration_text": "By eliminating idle thread memory, frameworks like FastAPI and Node.js can handle tens of thousands of concurrent websocket and HTTP connections on a single machine. Async and await provide clean syntax, high efficiency, and modern scalability. Code synchronously, execute asynchronously.",
                "estimated_duration": 21.0,
                "visual_spec": {
                    "visual_type": "math_graph",
                    "title": "Server Concurrency Throughput",
                    "subtitle": "Thread-per-request vs. Asynchronous Event-Driven Architecture",
                    "parameters": {
                        "x_axis": "Concurrent Connections (Thousands)",
                        "y_axis": "RAM Usage (MB)",
                        "data_points": [
                            {"c": "1k", "threaded": "1,000 MB (1MB per thread)", "async": "35 MB"},
                            {"c": "10k", "threaded": "10,000 MB (Crash)", "async": "80 MB"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Thread stack memory explosion"},
                        {"step": 2, "description": "Flat lightweight async coroutine footprint"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "Async/Await enables asynchronous, non-blocking programming with clean, sequential syntax. An Event Loop coordinates operations by running code on a call stack while offloading I/O-bound tasks to operating system background handlers.",
            "notes_markdown": """# Async / Await & Concurrency Master Notes

## 1. Why Non-Blocking Concurrency?
Traditional thread-per-connection models incur ~1-8 MB RAM per thread and high context-switching overhead.
Async event-driven architectures handle tens of thousands of concurrent I/O connections on a single thread by yielding during network wait times.

## 2. Key Terminology
- **Coroutine**: A specialized function that can pause execution via `await` and resume later without blocking the thread.
- **Event Loop**: The central loop checking the call stack and dispatching callbacks from the completed task queue.
- **Task**: A scheduled coroutine wrapped for concurrent execution.

## 3. Python Asyncio Best Practices
```python
import asyncio

async def fetch_item(item_id: int):
    # Simulating non-blocking network request
    await asyncio.sleep(1)
    return f"Item {item_id}"

async def main():
    # Run multiple tasks concurrently in parallel time
    items = await asyncio.gather(
        fetch_item(1),
        fetch_item(2),
        fetch_item(3)
    )
    print(items) # Completes in 1 second, NOT 3 seconds!

asyncio.run(main())
```
""",
            "key_concepts": [
                {"concept": "Event Loop", "definition": "A single-threaded loop that monitors and schedules execution of tasks and callbacks.", "importance": "Heart of non-blocking I/O in Python and JavaScript."},
                {"concept": "Coroutine", "definition": "A function defined with `async def` whose execution can be suspended at `await` points.", "importance": "Allows human-readable sequential code for async workflows."},
                {"concept": "Gather / Promise.all", "definition": "Utility that launches multiple coroutines concurrently and waits for all to finish.", "importance": "Drastically reduces wall-clock time for multiple independent I/O tasks."}
            ],
            "formulas_or_code": [
                {"title": "Concurrent Execution", "type": "code", "content": "results = await asyncio.gather(*tasks)", "explanation": "Executes list of coroutines concurrently."}
            ],
            "practice_questions": [
                {"question": "If you call `time.sleep(5)` inside an `async def` endpoint in FastAPI, what happens?", "hint": "Think about the single-threaded event loop.", "solution": "It blocks the entire thread and event loop for 5 seconds, freezing requests from all other users during that interval. Use `await asyncio.sleep(5)` instead."}
            ],
            "quiz": [
                {"id": 1, "question": "What does the `await` keyword do when encountered in a coroutine?", "options": ["Spawns a new OS background thread", "Pauses the coroutine and yields control back to the event loop", "Stops the entire Python interpreter until finished", "Deletes the task from memory"], "correct_index": 1, "explanation": "Await suspends the current coroutine, allowing the event loop to execute other ready tasks while waiting for I/O."},
                {"id": 2, "question": "When should you NOT use async/await?", "options": ["When querying a remote PostgreSQL database", "When downloading 50 URLs via HTTP", "When executing a heavy CPU-bound image convolution filter", "When waiting for a webhook response"], "correct_index": 2, "explanation": "Heavy CPU tasks block the event loop; they must be offloaded to worker processes or a ProcessPoolExecutor."}
            ],
            "flashcards": [
                {"id": 1, "front": "What is the difference between concurrency and parallelism?", "back": "Concurrency is dealing with lots of things at once (structure); parallelism is doing lots of things at once (hardware execution).", "category": "Core Principle"},
                {"id": 2, "front": "Does `async def` create a new OS thread?", "back": "No! It runs on the same thread within the event loop cooperative scheduling.", "category": "Architecture"}
            ]
        }

        return {
            "title": "Async / Await Explained: Concurrency, Event Loops & Clean Code",
            "domain": "computer_science",
            "subdomain": "Software Engineering & Concurrency",
            "scenes": scenes,
            "materials": materials
        }

    def _build_calculus_derivative_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. The Speedometer Paradox: Instantaneous Rate of Change",
                "pedagogical_phase": "hook",
                "narration_text": "If you drive a car from home to school, you can easily calculate your average speed: total distance divided by total time. But at the exact moment you glance at your speedometer, it reads exactly 60 miles per hour. How can you have speed at a single, frozen instant when zero distance is traversed over zero time? Zero divided by zero is undefined! Resolving this paradox is the very birth of calculus and the derivative.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "The Speedometer Paradox",
                    "subtitle": "Average Speed vs. Instantaneous Velocity",
                    "parameters": {
                        "left_title": "Average Speed",
                        "left_items": ["Δx / Δt", "Total Distance / Total Time", "Easy to calculate over an interval"],
                        "right_title": "Instantaneous Speed",
                        "right_items": ["At exact time t = 2.000s", "Distance = 0, Time = 0 -> 0/0 ??", "Solved by the concept of Limits!"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Interval measurement"},
                        {"step": 2, "highlight": "Instantaneous point"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Secant Line & The Moving Point",
                "pedagogical_phase": "foundation",
                "narration_text": "Let us place this on a Cartesian coordinate plane. Consider a curve f of x. If we pick two points on the curve separated by a horizontal distance h, the line connecting them is called a secant line. Its slope is rise over run: f of x plus h minus f of x, all divided by h. This gives the average rate of change over the window h.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "math_graph",
                    "title": "Secant Line on Function f(x) = x²",
                    "subtitle": "Connecting (x, f(x)) to (x+h, f(x+h))",
                    "parameters": {
                        "curve": "f(x) = x^2",
                        "x0": 2,
                        "h": 1.5,
                        "formula": "Slope = [f(x+h) - f(x)] / h"
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Points (2, 4) and (3.5, 12.25) plotted"},
                        {"step": 2, "description": "Secant line drawn with slope = 5.5"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Taking the Limit: Secant Becomes Tangent",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "Now, let us watch the magic of calculus. We shrink the distance h closer and closer to zero. As h drops from 1 to 0.1 to 0.001, the second point slides down the curve. The secant line pivots smoothly until, at the limit where h approaches zero, it touches the curve at exactly one point. It transforms into the Tangent Line! The slope of this tangent line is the exact derivative at that point.",
                "estimated_duration": 27.0,
                "visual_spec": {
                    "visual_type": "math_graph",
                    "title": "Dynamic Limit Convergence",
                    "subtitle": "Watch the Secant Morph into a Tangent Line as h -> 0",
                    "parameters": {
                        "curve": "f(x) = x^2",
                        "x0": 2,
                        "h_steps": [1.5, 0.8, 0.3, 0.05, 0.001],
                        "tangent_slope": 4.0
                    },
                    "keyframe_steps": [
                        {"step": 1, "h": 1.5, "slope": 5.5, "label": "h = 1.5 (Secant)"},
                        {"step": 2, "h": 0.5, "slope": 4.5, "label": "h = 0.5 (Closing in)"},
                        {"step": 3, "h": 0.01, "slope": 4.01, "label": "h -> 0 (Tangent slope = 4.0)"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Formal Definition & Power Rule",
                "pedagogical_phase": "edge_cases",
                "narration_text": "This brings us to the formal definition of the derivative: f prime of x equals the limit as h approaches zero of f of x plus h minus f of x over h. If we plug in f of x equals x squared, the algebra simplifies to two x plus h. As h approaches zero, what remains is simply two x. At x equals two, the slope is exactly four! This leads directly to the famous Power Rule: the derivative of x to the n is n times x to the n minus one.",
                "estimated_duration": 26.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": "Algebraic Limit Walkthrough & Power Rule",
                    "subtitle": "Step-by-Step Expansion of (x+h)²",
                    "parameters": {
                        "language": "latex",
                        "code": "% Limit Definition of Derivative\nf'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}\n\n% For f(x) = x^2:\nf'(x) = \\lim_{h \\to 0} \\frac{(x+h)^2 - x^2}{h}\n      = \\lim_{h \\to 0} \\frac{x^2 + 2xh + h^2 - x^2}{h}\n      = \\lim_{h \\to 0} \\frac{2xh + h^2}{h}\n      = \\lim_{h \\to 0} (2x + h)\n      = 2x\n\n% Power Rule:\n\\frac{d}{dx}[x^n] = n \\cdot x^{n-1}",
                        "highlights": [
                            {"line": 2, "label": "The universal limit definition"},
                            {"line": 6, "label": "Cancelling out x² terms"},
                            {"line": 8, "label": "Dividing out h eliminates 0/0 indeterminate form!"},
                            {"line": 10, "label": "Final clean derivative 2x"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 2, "scope": "Universal Definition"},
                        {"step": 2, "active_line": 8, "scope": "h cancelled out"},
                        {"step": 3, "active_line": 13, "scope": "General Power Rule"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Real-World Applications: Optimization & AI",
                "pedagogical_phase": "summary",
                "narration_text": "Derivatives are not just textbook exercises; they power our modern world. In physics, the derivative of position is velocity, and the derivative of velocity is acceleration. In business, marginal cost is the derivative of total cost. And in machine learning, derivatives tell algorithms how to optimize billions of weights. The derivative gives us the power to optimize anything that changes.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Everyday Derivatives in Action",
                    "subtitle": "Physics, Finance, and Artificial Intelligence",
                    "parameters": {
                        "col1": "Physics: Position -> Velocity (dx/dt) -> Acceleration (d²x/dt²)",
                        "col2": "Economics: Profit Optimization where Marginal Revenue = Marginal Cost (dProfit/dQ = 0)",
                        "col3": "Machine Learning: Gradient Descent updates weights using partial derivatives"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Physics"},
                        {"step": 2, "highlight": "Economics"},
                        {"step": 3, "highlight": "Machine Learning"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "The derivative is the fundamental mathematical tool for measuring instantaneous rate of change. By taking the limit of secant line slopes as the interval shrinks to zero, the derivative yields the exact slope of the tangent line to a curve at any point.",
            "notes_markdown": """# Calculus: The Derivative & Instantaneous Change

## 1. The Limit Definition of the Derivative
For any continuous function $f(x)$, its derivative $f'(x)$ is defined as:
$$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$

## 2. Geometric Interpretation
- The secant line connects $(x, f(x))$ and $(x+h, f(x+h))$ with slope:
  $$m_{\\text{secant}} = \\frac{f(x+h) - f(x)}{h}$$
- As $h \\to 0$, the secant line rotates into the **tangent line** at $x$, whose slope is $f'(x)$.

## 3. Essential Differentiation Rules
1. **Power Rule**: $\\frac{d}{dx}[x^n] = n x^{n-1}$
2. **Constant Multiple Rule**: $\\frac{d}{dx}[c \\cdot f(x)] = c \\cdot f'(x)$
3. **Sum / Difference Rule**: $\\frac{d}{dx}[f(x) \\pm g(x)] = f'(x) \\pm g'(x)$
4. **Product Rule**: $\\frac{d}{dx}[f \\cdot g] = f' g + f g'$
5. **Chain Rule**: $\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)$
""",
            "key_concepts": [
                {"concept": "Tangent Line", "definition": "A straight line that touches a smooth curve at a single point, matching the curve's instantaneous direction.", "importance": "Geometric representation of the derivative."},
                {"concept": "Limit ($h \\to 0$)", "definition": "The mathematical operation allowing us to evaluate behavior arbitrarily close to zero without dividing by zero.", "importance": "Overcomes the 0/0 indeterminacy paradox."},
                {"concept": "Instantaneous Rate of Change", "definition": "The rate at which a variable changes at a single precise instant in time.", "importance": "Differentiates modern calculus from basic average arithmetic."}
            ],
            "formulas_or_code": [
                {"title": "Limit Definition of Derivative", "type": "formula", "content": "f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}", "explanation": "The fundamental mathematical foundation of differentiation."},
                {"title": "Power Rule", "type": "formula", "content": "\\frac{d}{dx}[x^n] = n x^{n-1}", "explanation": "Quick shortcut formula for differentiating polynomials."}
            ],
            "practice_questions": [
                {"question": "Find the derivative of $f(x) = 3x^4 - 5x^2 + 7$.", "hint": "Apply the power rule to each term independently.", "solution": "f'(x) = 3(4x^3) - 5(2x) + 0 = 12x^3 - 10x."}
            ],
            "quiz": [
                {"id": 1, "question": "What geometric feature of a function curve does the derivative $f'(a)$ represent?", "options": ["The area under the curve from 0 to a", "The slope of the tangent line at x = a", "The maximum y-value of the curve", "The distance from the origin to (a, f(a))"], "correct_index": 1, "explanation": "The derivative at a point is precisely the slope of the tangent line to the curve at that point."},
                {"id": 2, "question": "What is the derivative of $f(x) = x^3$ using the Power Rule?", "options": ["3x", "x^2", "3x^2", "3x^3"], "correct_index": 2, "explanation": "By the power rule d/dx[x^n] = n * x^(n-1), so d/dx[x^3] = 3x^2."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does a derivative equal to zero ($f'(x) = 0$) signify?", "back": "A horizontal tangent line, indicating a potential local maximum, local minimum, or saddle point.", "category": "Calculus"},
                {"id": 2, "front": "What is the derivative of a constant number $c$?", "back": "0, because a constant does not change (rate of change is zero).", "category": "Rules"}
            ]
        }

        return {
            "title": "Calculus: Intuition, Limits & The Power of The Derivative",
            "domain": "mathematics",
            "subdomain": "Calculus & Analysis",
            "scenes": scenes,
            "materials": materials
        }

    def _build_photosynthesis_lecture(self, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": "1. Solar Energy into Chemical Life: The Global Engine",
                "pedagogical_phase": "hook",
                "narration_text": "Every breath of oxygen you take, and virtually every calorie of food consumed by living things on Earth, traces back to a single biological miracle: photosynthesis. Plants, algae, and cyanobacteria harvest photons emitted by the sun 93 million miles away and lock that radiant energy into stable sugar molecules. Let us journey inside the leaf to see how this biochemical factory operates.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": "Photosynthesis: The Biosphere's Energy Converter",
                    "subtitle": "Sunlight + Water + Carbon Dioxide -> Glucose + Oxygen",
                    "parameters": {
                        "inputs": ["Sunlight (Photons)", "Water (H2O via Roots)", "Carbon Dioxide (CO2 via Stomata)"],
                        "engine": "Chloroplast (Thylakoid & Stroma)",
                        "outputs": ["Glucose (C6H12O6 Food)", "Oxygen (O2 Released to Atmosphere)"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Photons and water absorbed"},
                        {"step": 2, "description": "Energy captured in chloroplast"},
                        {"step": 3, "description": "Oxygen released and glucose synthesized"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Inside the Chloroplast: The Two-Stage Process",
                "pedagogical_phase": "foundation",
                "narration_text": "Inside plant cells lie disc-shaped organelles called chloroplasts. Photosynthesis is split into two distinct stages: the Light-Dependent Reactions, which occur in coin-like membrane stacks called Thylakoids, and the Light-Independent Reactions, known as the Calvin Cycle, which occur in the surrounding fluid called the Stroma.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "process_simulation",
                    "title": "Chloroplast Architecture: Two Linked Stages",
                    "subtitle": "Light Reactions (Thylakoid) <-> Calvin Cycle (Stroma)",
                    "parameters": {
                        "stage1": "Light Reactions: Uses Light + H2O -> Produces ATP + NADPH + O2",
                        "link": "Energy shuttle: ATP and NADPH transfer energy across the membrane",
                        "stage2": "Calvin Cycle: Uses CO2 + ATP + NADPH -> Produces Glucose Sugar"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Thylakoid Light Absorption"},
                        {"step": 2, "highlight": "ATP/NADPH Energy Shuttle"},
                        {"step": 3, "highlight": "Stroma Calvin Cycle Synthesis"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Light Reactions: Splitting Water with Light",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": "Let us zoom into the thylakoid membrane. Sunlight strikes chlorophyll in Photosystem II, exciting electrons to a high energy state. To replace these lost electrons, the plant splits water molecules, H2O, into hydrogen ions and oxygen gas. This is why plants release oxygen! As excited electrons tumble down the electron transport chain, they pump protons across the membrane, driving the ATP Synthase turbine like a microscopic hydroelectric dam.",
                "estimated_duration": 28.0,
                "visual_spec": {
                    "visual_type": "diagram_board",
                    "title": "Electron Transport Chain & ATP Synthase",
                    "subtitle": "Splitting Water and Generating ATP via Proton Gradient",
                    "parameters": {
                        "elements": [
                            "Photosystem II (Photons excite electrons)",
                            "Water Splitting: 2 H2O -> 4 H+ + O2 + 4e-",
                            "Cytochrome b6f (Proton Pump)",
                            "Photosystem I (NADPH Production)",
                            "ATP Synthase (Rotary Molecular Motor)"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Photon strikes chlorophyll"},
                        {"step": 2, "description": "H2O split into oxygen"},
                        {"step": 3, "description": "Proton gradient spins ATP Synthase"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Calvin Cycle: Fixing Air into Food",
                "pedagogical_phase": "edge_cases",
                "narration_text": "Now in the stroma, the plant uses that newly formed ATP and NADPH to perform Carbon Fixation. The enzyme RuBisCO, the most abundant protein on Earth, captures carbon dioxide from the air and fuses it into a five-carbon sugar. Through a continuous cyclic chain of transformations, high-energy three-carbon sugars are produced, which combine to form glucose and starch.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "process_simulation",
                    "title": "The Calvin Cycle (Dark Reactions)",
                    "subtitle": "Carbon Fixation via RuBisCO in the Stroma",
                    "parameters": {
                        "cycle_phases": [
                            "Phase 1: Carbon Fixation (CO2 + RuBP catalyzed by RuBisCO)",
                            "Phase 2: Reduction (ATP and NADPH convert 3-PGA into G3P sugar)",
                            "Phase 3: Regeneration (Remaining G3P regenerated back into RuBP)"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "CO2 fixation by RuBisCO"},
                        {"step": 2, "description": "Reduction with ATP/NADPH energy"},
                        {"step": 3, "description": "G3P sugar exits to form glucose"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Why Photosynthesis Shapes Our Climate & Future",
                "pedagogical_phase": "summary",
                "narration_text": "Without photosynthesis, Earth would have no breathable oxygen atmosphere and no protective ozone layer. Understanding this mechanism is vital today: by studying photosynthesis, scientists are developing artificial leaves, drought-resistant crops, and enhanced carbon capture technologies to fight climate change. Nature's solar panel is the ultimate blueprint for sustainable energy.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Ecological & Technological Impact",
                    "subtitle": "Natural Cycle vs. Next-Gen Bioengineering",
                    "parameters": {
                        "col1": "Atmospheric Balance: Consumes CO2, supplies planetary O2 and ozone layer",
                        "col2": "Food Web Foundation: Primary producer supporting all animal life",
                        "col3": "Artificial Photosynthesis: Engineering solar cells to produce hydrogen fuel"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Atmosphere"},
                        {"step": 2, "highlight": "Biosphere"},
                        {"step": 3, "highlight": "Future tech"}
                    ]
                }
            }
        ]

        materials = {
            "summary": "Photosynthesis is the biological process by which plants, algae, and cyanobacteria convert light energy into chemical energy stored in glucose. It occurs in two connected phases: the Light Reactions in the thylakoid membrane and the Calvin Cycle in the stroma.",
            "notes_markdown": """# Photosynthesis: Complete Educational Study Notes

## 1. Overall Chemical Equation
$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{Light Energy} \\longrightarrow \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$

## 2. Stage Comparison
| Feature | Light-Dependent Reactions | Calvin Cycle (Light-Independent) |
| :--- | :--- | :--- |
| **Location** | Thylakoid Membrane | Stroma (Fluid) |
| **Input** | Light, $\\text{H}_2\\text{O}$, NADP+, ADP | $\\text{CO}_2$, ATP, NADPH |
| **Output** | $\\text{O}_2$ (byproduct), ATP, NADPH | G3P (Glucose precursor), ADP, NADP+ |
| **Key Enzyme** | ATP Synthase, Cytochrome $b_6f$ | RuBisCO (Ribulose-1,5-bisphosphate carboxylase) |
""",
            "key_concepts": [
                {"concept": "Thylakoid Membrane", "definition": "Internal membrane discs within chloroplasts where photon absorption and water-splitting occur.", "importance": "Site of the light reactions."},
                {"concept": "RuBisCO", "definition": "The enzyme responsible for fixing atmospheric CO2 onto organic molecules.", "importance": "The critical gateway enzyme connecting inorganic carbon to the biological food chain."},
                {"concept": "Photolysis", "definition": "The light-driven chemical decomposition of water molecules into hydrogen ions, electrons, and oxygen.", "importance": "Source of Earth's atmospheric oxygen."}
            ],
            "formulas_or_code": [
                {"title": "Water Splitting Photolysis Equation", "type": "formula", "content": "2 \\text{H}_2\\text{O} \\longrightarrow 4\\text{H}^+ + 4e^- + \\text{O}_2", "explanation": "Replaces lost electrons in Photosystem II while releasing oxygen."}
            ],
            "practice_questions": [
                {"question": "What is the ultimate source of electrons that replace those lost by chlorophyll in Photosystem II?", "hint": "Think about what is consumed to release oxygen gas.", "solution": "Water molecules (H2O) are split by photolysis, providing electrons to Photosystem II."}
            ],
            "quiz": [
                {"id": 1, "question": "Where do the light-independent reactions (Calvin Cycle) take place inside the chloroplast?", "options": ["Outer chloroplast membrane", "Thylakoid lumen", "Stroma", "Mitochondrial matrix"], "correct_index": 2, "explanation": "The Calvin cycle takes place in the stroma, the fluid-filled space surrounding the thylakoids."},
                {"id": 2, "question": "What molecule is released as a byproduct during the light reactions of photosynthesis?", "options": ["Carbon dioxide", "Oxygen (O2)", "Glucose", "Methane"], "correct_index": 1, "explanation": "Oxygen gas is released as a byproduct when water is split to donate electrons."}
            ],
            "flashcards": [
                {"id": 1, "front": "What two high-energy molecules link the light reactions to the Calvin cycle?", "back": "ATP and NADPH.", "category": "Biochemistry"},
                {"id": 2, "front": "What is the primary function of chlorophyll?", "back": "To absorb blue and red wavelengths of light and transfer photon energy to electrons.", "category": "Pigments"}
            ]
        }

        return {
            "title": "Photosynthesis: How Plants Power Life on Earth",
            "domain": "science",
            "subdomain": "Cellular Biology & Bioenergetics",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_history_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        epoch_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Gathering Storm: Catalysts of {epoch_title}",
                "pedagogical_phase": "hook",
                "narration_text": f"Historical turning points do not emerge from a vacuum. Long before {epoch_title} shook the world, underlying socioeconomic pressures, shifting power dynamics, and philosophical ideas were silently colliding. Understanding these root catalysts reveals why a transformation became inevitable.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": f"Root Catalysts & Tensions Leading to {epoch_title}",
                    "subtitle": "The Social, Economic and Ideological Seeds of Change",
                    "parameters": {
                        "root_catalyst": f"Structural Inequities & Systemic Strains in Pre-{epoch_title}",
                        "intermediate_effects": [
                            "Emergence of new philosophical and political ideals",
                            "Economic hardship, institutional decay, or military friction",
                            "A sudden sparking incident that shattered public tolerance"
                        ],
                        "ultimate_consequence": f"The Outbreak and Irreversible Ignition of {epoch_title}"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Systemic Strains"},
                        {"step": 2, "highlight": "Ideological Awakening"},
                        {"step": 3, "highlight": "The Spark"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Pivotal Moments & Chronological Turning Points",
                "pedagogical_phase": "foundation",
                "narration_text": f"As events rapidly unfolded, history accelerated through critical milestones. Each battle, treaty, and popular proclamation redefined what was possible, sweeping away old orders and testing the courage of those involved.",
                "estimated_duration": 26.0,
                "visual_spec": {
                    "visual_type": "timeline_journey",
                    "title": f"Key Turning Points of {epoch_title}",
                    "subtitle": "Chronological Roadmap of Pivotal Historical Milestones",
                    "parameters": {
                        "milestones": [
                            {"year": "Stage 1", "title": "The Awakening & Spark", "desc": "Initial uprising, manifesto, or geopolitical realignment", "impact": "Breaks the status quo"},
                            {"year": "Stage 2", "title": "Escalation & Crisis", "desc": "Direct confrontation, intense conflict, and national mobilization", "impact": "High-stakes struggle"},
                            {"year": "Stage 3", "title": "The Climax", "desc": "Decisive battle, revolution victory, or institutional overthrow", "impact": "Irreversible shift of power"},
                            {"year": "Stage 4", "title": "New Order Established", "desc": "Treaty ratification, constitution drafting, and sovereign stabilization", "impact": "Foundation for modern era"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "The Awakening"},
                        {"step": 2, "highlight": "The Climax"},
                        {"step": 3, "highlight": "New Order"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Clashing Ideologies & Competing Factions",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Behind every historical epoch were real human beings with competing visions for society. Examining the key factions, their ideological motivations, and the compromises they made allows us to see this conflict with balanced historical empathy.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Competing Factions & Ideologies",
                    "subtitle": "Contrasting Visions for Society, Governance and Power",
                    "parameters": {
                        "col1": "The Traditional Order: Vested interests defending established hierarchy, monarchy, or empires",
                        "col2": "The Reformers / Revolutionaries: Mobilized populations demanding sovereignty, liberty, and rights",
                        "col3": "The Emerging Compromise: Pragmatic institutions formed in the crucible of post-crisis peace"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Traditional Order"},
                        {"step": 2, "highlight": "Revolutionaries"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. The Human Toll & Unintended Consequences",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"Great historical transformations rarely follow a simple linear path. Often, radicalization, economic disruption, and innocent suffering accompanied the upheaval, serving as a sobering reminder of the complex consequences of political fracture.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": "Intended Goals vs. Historical Realities",
                    "subtitle": "Weighing Idealism against Practical and Human Consequences",
                    "parameters": {
                        "root_catalyst": "Radical Upheaval & Breakdown of Law and Order",
                        "intermediate_effects": [
                            "Civil instability and economic hyper-volatility",
                            "Rise of factional rivalry and emergency powers"
                        ],
                        "ultimate_consequence": "eventual realization that lasting stability requires institutional checks and balances"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Breakdown of Law"},
                        {"step": 2, "highlight": "Institutional Checks"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": f"5. The Living Legacy of {epoch_title}",
                "pedagogical_phase": "summary",
                "narration_text": f"Centuries later, the echoes of {epoch_title} still reverberate across our laws, borders, and modern concepts of human rights. By studying this defining epoch, we gain profound perspective on the fragility and resilience of human civilization.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": f"The Enduring Global Legacy of {epoch_title}",
                    "subtitle": "From Historical Turmoil to Modern Societal Principles",
                    "parameters": {
                        "left_label": "Historical Context: Feudalism, autocratic rule, and systemic oppression",
                        "right_label": "Modern Consequence: Constitutional governance, human rights, and popular sovereignty",
                        "center_balance": "Historical Synthesis: Understanding the price and responsibility of freedom",
                        "markers": [
                            "Systemic Collapse",
                            "Democratic Awakening",
                            "Global Blueprint"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Historical Context"},
                        {"step": 2, "highlight": "Modern Consequence"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"A comprehensive historical masterclass on {epoch_title}: examining its deep-seated root catalysts, key chronological milestones, clashing political factions, human costs, and lasting global legacy.",
            "notes_markdown": f"""# {epoch_title}: Masterclass Historical Notes

## 1. Context & Catalysts
- Long-term economic strains, social inequality, and institutional decay.
- The role of circulating ideas, manifestos, and changing public consciousness.

## 2. Chronological Milestones
- **The Initial Spark**: The event that crossed the point of no return.
- **The Peak Conflict**: Military engagements, popular revolts, or legislative decrees.
- **The Resolution**: Treaties, constitutional frameworks, and new balances of power.

## 3. Enduring Legacy
- How modern sovereign democracy, civic rights, and international law trace back to this pivotal epoch.
""",
            "key_concepts": [
                {"concept": "Historical Catalyst", "definition": "A critical event or condition that accelerates social transformation beyond peaceful containment.", "importance": "Explains why revolutions or wars happen at specific moments."},
                {"concept": "Institutional Legacy", "definition": "The enduring laws, treaties, and political structures left in the wake of major historical events.", "importance": "Continues to shape contemporary governance."}
            ],
            "formulas_or_code": [
                {"title": "The Iron Law of Historical Change", "type": "principle", "content": "Unaddressed systemic inequality + Compelling alternative vision = Inevitable upheaval", "explanation": "Why societies that refuse timely reform face eventual dramatic restructuring."}
            ],
            "practice_questions": [
                {"question": f"What was the most consequential long-term outcome of {epoch_title} for modern society?", "hint": "Think about human rights, legal equality, and national sovereignty.", "solution": f"{epoch_title} demonstrated that political power ultimately derives from the consent of the governed, setting historical precedents for constitutional limits on authority."}
            ],
            "quiz": [
                {"id": 1, "question": f"Why is studying the root causes of {epoch_title} more informative than only memorizing battle dates?", "options": ["Battles are not real", "Understanding underlying socioeconomic forces helps identify similar vulnerabilities in modern societies", "Dates change over time", "It is easier to guess causes"], "correct_index": 1, "explanation": "History's true value lies in understanding why human societies fracture and how sustainable peace is achieved."}
            ],
            "flashcards": [
                {"id": 1, "front": f"What lesson does {epoch_title} offer to modern governance?", "back": "Institutions must proactively address public grievances and protect individual rights to avoid destabilization.", "category": "Historical Analysis"}
            ]
        }

        return {
            "title": f"{epoch_title}: Turning Points that Shaped the World",
            "domain": "history",
            "subdomain": "World History & Turning Points",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_economics_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        econ_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Core Economic Reality of {econ_title}",
                "pedagogical_phase": "hook",
                "narration_text": f"Every dollar, transaction, and resource allocation in human society is guided by fundamental economic incentives. To understand {econ_title}, we must cut through confusing jargon and observe how everyday people, businesses, and governments make decisions under conditions of scarcity.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"Demystifying {econ_title}",
                    "subtitle": "Scarcity, Incentives and Real-World Value",
                    "parameters": {
                        "left_title": "The Conventional Intuition",
                        "left_items": ["Assuming prices and markets are arbitrary", "Viewing wealth purely as printed paper", "Ignoring delayed second-order effects"],
                        "right_title": "The Economic Reality",
                        "right_items": ["Incentives determine behavior across markets", "Value is subjective, dynamic, and scarcity-driven", "Every policy intervention carries invisible trade-offs"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Conventional Intuition"},
                        {"step": 2, "highlight": "Economic Reality"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Market Forces & Dynamic Equilibrium",
                "pedagogical_phase": "foundation",
                "narration_text": f"At the heart of {econ_title} lies market dynamics: when supply changes, or buyer preferences shift, price acts as an information signal. Watch how equilibrium adjusts continuously like a self-correcting organism, balancing production with human demand.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cross_section_sim",
                    "title": "The Dynamic Market Equilibrium",
                    "subtitle": "How Price Signals Balance Buyer Demand and Producer Supply",
                    "parameters": {
                        "chamber_top": "High Demand Zone: Drives upward price signals, attracting investment",
                        "chamber_middle": "Market Equilibrium: Where willingness to pay equals marginal cost of production",
                        "chamber_bottom": "Supply Surplus Zone: Forces downward price discounting to clear inventory"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Equilibrium point"},
                        {"step": 2, "highlight": "Supply-Demand Shift"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Capital & Money Flow Cycle",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Money is not static; it is a circulating bloodstream. In this dynamic flow, households supply labor and spend income, businesses innovate and hire, and central banks modulate interest rates. Let's trace how {econ_title} ripples across this entire macroeconomic cycle.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cycle_loop",
                    "title": "The Macroeconomic Circulation Loop",
                    "subtitle": "Tracking Value and Capital Movement across Society",
                    "parameters": {
                        "loop_title": "Economic Flow Cycle",
                        "stages": [
                            {"stage": "1. Household Income & Consumption", "desc": "Earned wages allocated between immediate consumption and savings"},
                            {"stage": "2. Financial Intermediation & Banking", "desc": "Savings pooled into capital investments, loans, and business expansion"},
                            {"stage": "3. Production of Goods & Services", "desc": "Enterprises create tangible output, hiring talent and purchasing materials"},
                            {"stage": "4. Revenue & Value Realization", "desc": "Sales revenue returned to suppliers, employees, and reinvested equity"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Household Allocation"},
                        {"step": 2, "highlight": "Capital Investment"},
                        {"step": 3, "highlight": "Value Realization"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Trade-Offs & Policy Dilemmas",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"In economics, there are no pure solutions—only trade-offs. Stimulating growth can spark inflation, while aggressive cooling can trigger recessions. Navigating {econ_title} requires balancing risk against reward across time horizons.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Policy Trade-Off Spectrum",
                    "subtitle": "Navigating Conflicting Goals in Economic Decision-Making",
                    "parameters": {
                        "left_label": "Loose Monetary Stance: Fast growth, cheap credit, higher inflation risks",
                        "right_label": "Tight Monetary Stance: Price stability, strong currency, slower immediate growth",
                        "center_balance": "Sustainable Neutral Rate: Real productive growth without asset bubbles",
                        "markers": [
                            "Expansionary",
                            "Neutral Equilibrium",
                            "Contractionary"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Expansionary Risks"},
                        {"step": 2, "highlight": "Neutral Equilibrium"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Practical Application: Navigating Real-World Markets",
                "pedagogical_phase": "summary",
                "narration_text": f"How do you apply these principles to your own financial life and career? By distinguishing nominal prices from real purchasing power, diversifying risks, and understanding where we stand in the economic cycle, you can make clear-headed decisions in an uncertain world.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Actionable Financial Principles",
                    "subtitle": "Protecting Value and Capitalizing on Economic Cycles",
                    "parameters": {
                        "col1": "Focus on Real Purchasing Power: Nominal wage increases mean little if goods rise faster",
                        "col2": "Own Productive Assets: Equities, real property, and high-demand skills compound over time",
                        "col3": "Maintain Liquidity Reserves: Having an emergency buffer prevents selling assets at market bottoms"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Purchasing Power"},
                        {"step": 2, "highlight": "Productive Assets"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This economics masterclass analyzes {econ_title}: unpacking market price signals, the circular flow of capital, policy trade-off spectrums, and actionable strategies for preserving real wealth.",
            "notes_markdown": f"""# {econ_title}: Comprehensive Economics Guide

## 1. Core Principles
- **Scarcity & Choice**: Resources are limited; every choice involves an opportunity cost.
- **Price as Information**: Prices coordinate millions of independent buyers and sellers without centralized command.

## 2. The Macro Cycle
- Capital flows between households, financial institutions, and productive enterprises.
- Central bank policies impact the cost of borrowing and currency velocity.

## 3. Practical Wealth Rules
1. Distinguish between nominal and real (inflation-adjusted) returns.
2. Invest in productive assets that produce genuine economic output.
3. Understand debt cycles and maintain financial resilience.
""",
            "key_concepts": [
                {"concept": "Opportunity Cost", "definition": "The loss of potential gain from other alternatives when one alternative is chosen.", "importance": "The foundation of all rational economic decision-making."},
                {"concept": "Price Elasticity", "definition": "How responsive buyers or sellers are to a change in the price of a good.", "importance": "Dictates market behavior during supply or demand shocks."}
            ],
            "formulas_or_code": [
                {"title": "The Real Return Equation", "type": "formula", "content": "Real Return ≈ Nominal Return - Inflation Rate - Fees/Taxes", "explanation": "The true increase in purchasing power after accounting for dollar devaluation."}
            ],
            "practice_questions": [
                {"question": f"Why does printing more currency fail to permanently increase real national wealth in the context of {econ_title}?", "hint": "Think about the total quantity of goods and services produced.", "solution": "Wealth consists of the real goods, infrastructure, food, and services available, not the pieces of paper representing them. Increasing currency supply without increasing output simply bids up prices across the board."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the primary role of prices in a market economy?", "options": ["To make items expensive", "To act as decentralized information signals coordinating supply and demand", "To ensure government taxes are paid", "To prevent all foreign trade"], "correct_index": 1, "explanation": "Prices signal scarcity and abundance, directing resources to where they are most urgently needed."}
            ],
            "flashcards": [
                {"id": 1, "front": "What is the difference between nominal and real value?", "back": "Nominal value is expressed in raw currency figures; real value is adjusted for changes in purchasing power (inflation).", "category": "Core Economics"}
            ]
        }

        return {
            "title": f"Understanding {econ_title}: Economics, Markets & Money",
            "domain": "economics_business",
            "subdomain": "Economics, Markets & Finance",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_psychology_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        psy_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Architecture of the Mind: Why {psy_title} Matters",
                "pedagogical_phase": "hook",
                "narration_text": f"The human brain evolved to survive in ancestral savannas, not to navigate twenty-first-century digital overload. Because of this evolutionary mismatch, our automatic emotional reactions frequently misdirect our actions. By studying {psy_title}, we pull back the curtain on our subconscious programming.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"Subconscious Instinct vs. Conscious Clarity in {psy_title}",
                    "subtitle": "Evolutionary Wiring vs. Intentional Living",
                    "parameters": {
                        "left_title": "The Automatic Default (System 1)",
                        "left_items": ["Impulsive emotional triggers", "Cognitive biases and threat hypersensitivity", "Short-term dopamine seeking"],
                        "right_title": "The Intentional Mind (System 2)",
                        "right_items": ["Rational metacognition and reflection", "Long-term values alignment", "Emotional regulation and deliberate choice"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Automatic Default"},
                        {"step": 2, "highlight": "Intentional Mind"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Cognitive Feedback Loop",
                "pedagogical_phase": "foundation",
                "narration_text": f"Every thought, emotional reaction, and habitual behavior operates within a circular feedback loop. An environmental trigger sparks an automated interpretation, which floods our physiology with emotion, driving an action that reinforces the original neural circuit.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cycle_loop",
                    "title": "The Psychological Feedback Cycle",
                    "subtitle": "Trigger -> Cognitive Appraisal -> Emotion -> Behavioral Reinforcement",
                    "parameters": {
                        "loop_title": "The Mind-Behavior Cycle",
                        "stages": [
                            {"stage": "1. Environmental Trigger", "desc": "A sensory event, notification, or social interaction occurs"},
                            {"stage": "2. Cognitive Appraisal", "desc": "The mind automatically assigns meaning: safe, threatening, or rewarding"},
                            {"stage": "3. Neurochemical Emotion", "desc": "Dopamine, cortisol, or adrenaline shifts internal bodily state"},
                            {"stage": "4. Habitual Action & Feedback", "desc": "Behavior executed; dopamine reward reinforces the neural pathway"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Environmental Trigger"},
                        {"step": 2, "highlight": "Cognitive Appraisal"},
                        {"step": 3, "highlight": "Behavioral Reinforcement"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Hierarchy of Psychological Needs & Values",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Human psychological well-being is organized into foundational layers. Without safety and belonging, self-actualization remains out of reach. Let us map out how {psy_title} integrates into our core human hierarchy.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "hierarchy_pyramid",
                    "title": f"The Structural Hierarchy of {psy_title}",
                    "subtitle": "Foundational Survival to Higher Transcendent Purpose",
                    "parameters": {
                        "pyramid_title": "Psychological Hierarchy",
                        "tiers": [
                            {"tier": "Purpose & Self-Actualization", "note": "Meaningful contribution, creative expression, and moral integrity"},
                            {"tier": "Autonomy & Psychological Mastery", "note": "Competence, emotional self-regulation, and internal locus of control"},
                            {"tier": "Social Belonging & Trust", "note": "Secure relationships, community bonds, and vulnerability"},
                            {"tier": "Physiological & Mental Baseline", "note": "Sleep, nutrition, physical safety, and calm nervous system"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Physiological Baseline"},
                        {"step": 2, "highlight": "Autonomy & Mastery"},
                        {"step": 3, "highlight": "Self-Actualization"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Cognitive Biases & Blind Spots",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"No human mind is immune to blind spots. From confirmation bias—seeking only what confirms our prejudices—to catastrophic thinking and sunk-cost fallacies, awareness of these distortions is the true beginning of wisdom.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Cognitive Distortions vs. Mental Clarity",
                    "subtitle": "Recognizing and Overcoming Human Blind Spots",
                    "parameters": {
                        "col1": "Confirmation Bias: Only absorbing data that agrees with your pre-existing narrative",
                        "col2": "Emotional Reasoning: Believing that because an anxiety feels intense, a catastrophe must be true",
                        "col3": "Metacognitive Reframing: Observing thoughts like clouds without being controlled by them"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Confirmation Bias"},
                        {"step": 2, "highlight": "Metacognitive Reframing"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Daily Practice & Psychological Resilience",
                "pedagogical_phase": "summary",
                "narration_text": f"Philosophy and psychology are not spectator sports; they are daily practices. By pausing between stimulus and response, choosing conscious reframing, and cultivating grateful self-awareness, we transform {psy_title} into lived resilience and flourishing.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Spectrum of Psychological Resilience",
                    "subtitle": "Moving from Reactive Vulnerability to Antifragile Strength",
                    "parameters": {
                        "left_label": "Reactive Stance: Buffeted by external circumstances, blaming outside forces",
                        "right_label": "Antifragile Mastery: Using adversity as fuel for psychological growth and wisdom",
                        "center_balance": "Stoic Groundedness: Clear boundary between what you control and what you do not",
                        "markers": [
                            "Vulnerability",
                            "Emotional Balance",
                            "Antifragile Resilience"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Reactive Stance"},
                        {"step": 2, "highlight": "Antifragile Mastery"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This psychology and philosophical masterclass deconstructs {psy_title}: exploring evolutionary cognitive wiring, habit feedback loops, structural needs hierarchies, cognitive bias mitigation, and daily resilience.",
            "notes_markdown": f"""# {psy_title}: Psychological & Philosophical Guide

## 1. Foundational Concepts
- **System 1 vs. System 2**: Fast, emotional, automatic processing versus slow, logical, reflective deliberation.
- **The Space Between Stimulus & Response**: Freedom lies in cultivating the pause before reacting.

## 2. The Cognitive Loop
1. **Trigger**: External or internal prompt.
2. **Appraisal**: The narrative the mind constructs.
3. **Affect**: Somatic emotional activation.
4. **Behavior**: The action that solidifies the neural circuit.

## 3. Daily Resilience Protocols
- Practice metacognition: watch thoughts without judging them.
- Separate what is within your voluntary control from what is not.
""",
            "key_concepts": [
                {"concept": "Metacognition", "definition": "The capacity to observe, analyze, and regulate one's own thought processes.", "importance": "Breaks destructive automated cognitive loops."},
                {"concept": "Internal Locus of Control", "definition": "The psychological belief that one's decisions and effort determine life outcomes, rather than luck or external fate.", "importance": "Strongly correlated with mental health, resilience, and achievement."}
            ],
            "formulas_or_code": [
                {"title": "Viktor Frankl's Principle", "type": "principle", "content": "Between stimulus and response there is a space. In that space is our power to choose our response.", "explanation": "The ultimate foundation of human psychological freedom."}
            ],
            "practice_questions": [
                {"question": f"How can someone break an unhelpful automated thought loop related to {psy_title}?", "hint": "Think about the pause between stimulus and response.", "solution": "By labeling the emotional surge without immediate action ('I notice I am feeling anxiety'), questioning the underlying cognitive appraisal, and deliberately choosing a constructive response."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the key difference between automatic emotional reactions and conscious deliberation?", "options": ["There is no difference", "Emotional reactions are fast and evolutionary; deliberation is slow, conscious, and values-aligned", "Emotions are always correct", "Deliberation causes depression"], "correct_index": 1, "explanation": "Evolutionary System 1 prioritizes fast survival shortcuts, whereas System 2 allows thoughtful alignment with long-term goals."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does 'Metacognition' mean?", "back": "Thinking about thinking: the ability to observe one's own mental states objectively.", "category": "Cognitive Science"}
            ]
        }

        return {
            "title": f"Mastering {psy_title}: Psychology, Mindset & Resilience",
            "domain": "psychology_philosophy",
            "subdomain": "Cognitive Psychology & Philosophy",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_biology_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        bio_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Marvel of Life: Why {bio_title} Evolved",
                "pedagogical_phase": "hook",
                "narration_text": f"Life on Earth has refined its biochemical machinery over billions of years of natural selection. In {bio_title}, nature solved a profound physical challenge: how to capture energy, defend against microscopic invaders, or maintain cellular homeostasis against the laws of entropy.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"The Evolutionary Engineering of {bio_title}",
                    "subtitle": "Biological Solutions to Fundamental Physical Problems",
                    "parameters": {
                        "left_title": "The Physical Challenge",
                        "left_items": ["Entropy and cellular decay", "Fluctuating external environmental stresses", "Energy scarcity and microscopic pathogens"],
                        "right_title": "The Biological Innovation",
                        "right_items": ["Self-healing cellular membranes and enzymes", "Precision molecular signaling cascades", "Dynamic homeostasis maintaining optimal internal equilibrium"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Physical Challenge"},
                        {"step": 2, "highlight": "Biological Innovation"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Anatomical Structure & Cellular Cross-Section",
                "pedagogical_phase": "foundation",
                "narration_text": f"Let us zoom into the microscopic cutaway. Notice how specialized organelles and membranes are positioned with architectural precision. Each receptor, ion channel, and enzyme carries out targeted chemical transformations with near-perfect fidelity.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cross_section_sim",
                    "title": "Microscopic Cellular Architecture",
                    "subtitle": "Organelles, Selective Membranes and Biochemical Chambers",
                    "parameters": {
                        "chamber_top": "Extracellular Matrix: Signaling ligands, nutrients, and immune checkpoints",
                        "chamber_middle": "Semi-Permeable Lipid Bilayer: Dynamic protein channels and voltage-gated pumps",
                        "chamber_bottom": "Intracellular Cytoplasm: Mitochondria energy production, ribosome translation, and enzyme cascades"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Extracellular Matrix"},
                        {"step": 2, "highlight": "Lipid Bilayer"},
                        {"step": 3, "highlight": "Intracellular Cytoplasm"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Dynamic Pathways & Physiological Cycles",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Biology is never static; it is an orchestrated biochemical dance. As biochemical inputs trigger receptors, intracellular messengers cascade through the system, switching genes on or off and cycling metabolites into usable cellular fuel.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cycle_loop",
                    "title": "The Biochemical Signaling Pathway",
                    "subtitle": "Receptor Activation -> Second Messengers -> Cellular Response",
                    "parameters": {
                        "loop_title": "Physiological Cascade",
                        "stages": [
                            {"stage": "1. Receptor Binding", "desc": "Ligand or photon docks with membrane protein"},
                            {"stage": "2. Second Messenger Cascade", "desc": "cAMP, calcium ions, or kinase phosphorylation amplifies signal"},
                            {"stage": "3. Nuclear Transcription", "desc": "Transcription factors activate specific genetic programs"},
                            {"stage": "4. Negative Feedback Reset", "desc": "Phosphatases and receptor internalization restore basal sensitivity"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Receptor Binding"},
                        {"step": 2, "highlight": "Signal Amplification"},
                        {"step": 3, "highlight": "Negative Feedback"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Disruptions, Diseases & Immunological Defenses",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"When this delicate equilibrium is stressed by chronic inflammation, genetic mutations, or environmental toxins, disease manifests. Understanding these failure modes has unlocked miraculous therapies in modern medicine, from targeted immunotherapy to gene editing.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": "Homeostasis vs. Pathological Disruption",
                    "subtitle": "How Stressors Compromise Cellular Balance and How Defenses Respond",
                    "parameters": {
                        "root_catalyst": "External Stressor / Genetic Mutation / Toxic Influx",
                        "intermediate_effects": [
                            "Mitochondrial oxidative stress and inflammatory cytokine surge",
                            "Mobilization of innate and adaptive immune cell defenses"
                        ],
                        "ultimate_consequence": "Cellular repair and adaptation, or chronic pathology requiring medical intervention"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Oxidative Stress"},
                        {"step": 2, "highlight": "Immune Mobilization"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Human Health & Evidence-Based Protocols",
                "pedagogical_phase": "summary",
                "narration_text": f"How can we optimize our own biology in light of {bio_title}? By respecting our natural evolutionary rhythms—prioritizing restorative sleep, nutrient-dense nutrition, physical movement, and managing chronic stressors—we harmonize with millions of years of biological wisdom.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Evidence-Based Biological Optimization",
                    "subtitle": "Translating Cellular Insights into Daily Health Protocols",
                    "parameters": {
                        "col1": "Circadian Synchronization: Align light exposure, meals, and rest with natural solar rhythms",
                        "col2": "Cellular Stress Adaptation (Hormesis): Exercise and thermal changes spur mitochondrial biogenesis",
                        "col3": "Metabolic & Immune Care: Eliminate chronic systemic inflammation through whole-food nutrition"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Circadian Synchronization"},
                        {"step": 2, "highlight": "Hormesis Adaptation"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This human biology and health masterclass investigates {bio_title}: mapping evolutionary purposes, microscopic cellular anatomy, biochemical signaling cascades, disease vulnerabilities, and evidence-based health protocols.",
            "notes_markdown": f"""# {bio_title}: Biological & Physiological Study Notes

## 1. Principles of Cellular Life
- **Homeostasis**: The active maintenance of a stable internal environment despite external fluctuations.
- **Biochemical Specificity**: Lock-and-key interactions between enzymes, receptors, and substrates.

## 2. Signaling & Pathways
- Receptor phosphorylation, second-messenger amplification, and targeted gene expression.
- Feedback inhibition: how biological systems prevent runaway reactions.

## 3. Practical Health Implications
- The power of **hormesis**: mild biological stressors (exercise, temperature) trigger cellular repair mechanisms.
- Protecting cellular integrity through restorative sleep, micronutrients, and hydration.
""",
            "key_concepts": [
                {"concept": "Homeostasis", "definition": "The self-regulating process by which biological systems maintain internal stability while adjusting to changing external conditions.", "importance": "The core prerequisite for life itself."},
                {"concept": "Hormesis", "definition": "A biological phenomenon whereby a beneficial effect results from exposure to low doses of an otherwise stressful agent (e.g., exercise, cold, fasting).", "importance": "Drives cellular resilience and longevity."}
            ],
            "formulas_or_code": [
                {"title": "The Biological Invariant", "type": "principle", "content": "Structure Dictates Function; Homeostasis Preserves Life", "explanation": "The shape of proteins determines what they do; feedback loops keep the organism alive."}
            ],
            "practice_questions": [
                {"question": f"Why is negative feedback so prevalent in biological regulation related to {bio_title}?", "hint": "Think about what happens when a thermostat never turns off.", "solution": "Negative feedback ensures that once an optimal level is achieved, the pathway automatically slows down, preventing toxic accumulation or energy waste."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the primary function of cellular homeostasis?", "options": ["To stop all chemical reactions", "To maintain stable, life-supporting internal conditions despite changing environments", "To double body weight every week", "To eliminate the need for oxygen"], "correct_index": 1, "explanation": "Homeostasis dynamically balances temperature, pH, fluid levels, and energy."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does 'Hormesis' describe in biology?", "back": "The process where mild, controlled stressors trigger positive adaptive repair in cells.", "category": "Physiology"}
            ]
        }

        return {
            "title": f"The Science of {bio_title}: Cellular Mechanics & Human Health",
            "domain": "health_biology",
            "subdomain": "Health Sciences & Human Biology",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_science_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        sci_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Natural Mystery of {sci_title}",
                "pedagogical_phase": "hook",
                "narration_text": f"Look closely at the natural world, and familiar everyday sights suddenly reveal profound physical mysteries. Why does {sci_title} behave the way it does? By stripping away preconceived notions, we discover that the universe operates according to breathtakingly elegant mathematical and physical laws.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"Observing {sci_title}: From Intuition to Physics",
                    "subtitle": "Everyday Observation vs. Fundamental Physical Reality",
                    "parameters": {
                        "left_title": "The Surface Observation",
                        "left_items": ["Appears simple or taken for granted", "Intuitive assumptions often contradict nature", "Conceals invisible forces at work"],
                        "right_title": "The Underlying Physics",
                        "right_items": ["Governed by conservation of energy and momentum", "Emerges from atomic and quantum interactions", "Universal laws apply from the laboratory to deep space"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Surface Observation"},
                        {"step": 2, "highlight": "Underlying Physics"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Cross-Section & Force Dynamics",
                "pedagogical_phase": "foundation",
                "narration_text": f"Let us examine the physical cross-section. Observe the opposing forces: gravity pulling downward, pressure gradients pushing outward, and electromagnetic fields directing energy. When these vector forces interact, dynamic equilibrium is established.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cross_section_sim",
                    "title": "Cross-Section & Dynamic Force Equilibrium",
                    "subtitle": "Visualizing Interacting Vectors, Pressure and Energy Gradients",
                    "parameters": {
                        "chamber_top": "High-Potential Field: Inward pressure or gravitational potential",
                        "chamber_middle": "The Interaction Boundary: Wave interference, refraction, or kinetic transfer",
                        "chamber_bottom": "Equilibrium Base: Dispersed radiation, stabilized matter, or ground state"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "High Potential Field"},
                        {"step": 2, "highlight": "Interaction Boundary"},
                        {"step": 3, "highlight": "Equilibrium Base"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. The Governing Scientific Law",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Behind this phenomenon lies an unbreakable law of nature. Whether it is thermodynamics, Maxwell's electromagnetism, or Newton's mechanics, nature calculates outcomes with mathematical certainty. Let us track the cause-and-effect relationship.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "cause_and_effect",
                    "title": "The Fundamental Physical Mechanism",
                    "subtitle": "Input Stimulus -> Atomic/Wave Interaction -> Observable Phenomenon",
                    "parameters": {
                        "root_catalyst": f"Energy Influx or Gravitational/Atomic Stimulus in {sci_title}",
                        "intermediate_effects": [
                            "Conservation laws dictate redistribution of momentum and energy",
                            "Wave frequency shifts, thermal excitation, or particle acceleration"
                        ],
                        "ultimate_consequence": f"The Observable Natural Phenomenon of {sci_title}"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Energy Influx"},
                        {"step": 2, "highlight": "Wave/Particle Action"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Extreme Boundaries & Quantum Paradoxes",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"What happens when we push {sci_title} to extreme limits—approaching absolute zero, traveling near the speed of light, or compressing matter inside a neutron star? At these boundaries, classical intuition shatters, paving the way for relativity and quantum physics.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Spectrum of Physical Extremes",
                    "subtitle": "From Classical Everyday Scales to Relativistic Boundaries",
                    "parameters": {
                        "left_label": "Microscopic Quantum Domain: Wave-particle duality, uncertainty, tunneling",
                        "right_label": "Cosmological Extremes: General relativity, curved spacetime, singularity",
                        "center_balance": "Classical Mechanics: Predictable everyday physics at human scales",
                        "markers": [
                            "Quantum Scale",
                            "Everyday Realm",
                            "Relativistic Universe"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Quantum Domain"},
                        {"step": 2, "highlight": "Everyday Realm"},
                        {"step": 3, "highlight": "Relativistic Universe"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Human Engineering & Modern Technology",
                "pedagogical_phase": "summary",
                "narration_text": f"The ultimate triumph of understanding {sci_title} is using it to engineer a better world. From semiconductors and lasers to spaceflight and medical imaging, mastering this scientific principle allows humanity to transform nature's laws into transformative technology.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "From Natural Principle to Human Innovation",
                    "subtitle": "How Scientific Discovery Drives Breakthrough Engineering",
                    "parameters": {
                        "col1": "Natural Law: Fundamental behavior observed in nature and experimentally verified",
                        "col2": "Engineering Innovation: Harnessing the principle inside specialized hardware or sensors",
                        "col3": "Global Impact: Modern computing, satellite communication, clean energy, and health"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Natural Law"},
                        {"step": 2, "highlight": "Engineering Innovation"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This natural sciences and physics masterclass demystifies {sci_title}: exploring physical cutaways, vector force interactions, fundamental conservation laws, extreme relativistic boundaries, and engineering innovations.",
            "notes_markdown": f"""# {sci_title}: Fundamental Physics & Science Notes

## 1. Physical Principles
- **Conservation Laws**: Energy, momentum, and mass are conserved through all physical interactions.
- **Equilibrium & Forces**: Net force equals zero in steady state; unbalanced forces drive acceleration.

## 2. Microscopic vs. Macroscopic
- How subatomic behaviors combine to produce large-scale observable phenomena.
- Boundary conditions at extreme temperatures, pressures, and velocities.

## 3. Engineering Applications
- Translating theoretical physics into real-world sensors, engines, and digital technologies.
""",
            "key_concepts": [
                {"concept": "Conservation of Energy", "definition": "The law stating that energy cannot be created or destroyed, only transformed from one form to another.", "importance": "The universal bedrock of all physical science."},
                {"concept": "Vector Equilibrium", "definition": "A state where opposing physical forces balance each other out, resulting in zero net acceleration.", "importance": "Explains stability in structures, celestial orbits, and fluids."}
            ],
            "formulas_or_code": [
                {"title": "Fundamental Conservation Principle", "type": "formula", "content": "ΔE_system = Q - W (First Law of Thermodynamics)", "explanation": "The change in internal energy equals heat added minus work done."}
            ],
            "practice_questions": [
                {"question": f"Why is understanding the physical laws behind {sci_title} essential for engineering modern technologies?", "hint": "Consider predictability and materials science.", "solution": "Without precise mathematical models of physical forces and energy transfer, engineers cannot design reliable circuits, aerospace vehicles, or medical devices."}
            ],
            "quiz": [
                {"id": 1, "question": "What happens when opposing forces acting on a physical system are completely balanced?", "options": ["The system explodes", "The system achieves dynamic equilibrium with zero net acceleration", "Time stops", "Gravity ceases to exist"], "correct_index": 1, "explanation": "Balanced forces result in equilibrium, maintaining constant velocity or rest."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does conservation of energy guarantee?", "back": "Energy in an isolated system can never be created or destroyed, only transformed between states.", "category": "Physics"}
            ]
        }

        return {
            "title": f"The Physics of {sci_title}: Natural Laws & Scientific Marvels",
            "domain": "science_nature",
            "subdomain": "Natural Sciences & Phenomenon Exploration",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_algorithm_math_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        math_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Problem Space & Bottleneck of {math_title}",
                "pedagogical_phase": "hook",
                "narration_text": f"In mathematics and computer science, brilliance lies in efficiency. Without {math_title}, problems that should take milliseconds would take billions of years to compute! By formulating the problem rigorously, we unlock a structured path to optimal solutions.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"The Computational Challenge in {math_title}",
                    "subtitle": "Brute Force Inefficiency vs. Algorithmic Elegance",
                    "parameters": {
                        "left_title": "Brute Force Approach",
                        "left_items": ["O(N^2) or exponential blowup", "Exhaustive, redundant recalculation", "Fails catastrophically at scale"],
                        "right_title": f"The {math_title} Solution",
                        "right_items": ["Optimal mathematical invariants", "Pruning unnecessary search space", "Scales smoothly to millions of inputs"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Brute Force Inefficiency"},
                        {"step": 2, "highlight": "Algorithmic Elegance"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. Step-by-Step State Simulator",
                "pedagogical_phase": "foundation",
                "narration_text": f"Let us watch the algorithm execute step by step. Notice how pointers track the active boundary, invariant conditions are preserved, and search space contracts exponentially with each decision.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "algorithm_animator",
                    "title": "Interactive State & Memory Simulator",
                    "subtitle": "Pointer Movements, State Updates and Invariant Maintenance",
                    "parameters": {
                        "array": [2, 5, 8, 12, 16, 23, 38, 56, 72, 91],
                        "active_indices": [3, 4],
                        "target": 16,
                        "pointers": {"low": 0, "mid": 4, "high": 9},
                        "explanation": f"State updated: invariant satisfied for {math_title}"
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_pointer": "low", "highlight": "State initialized"},
                        {"step": 2, "active_pointer": "mid", "highlight": "Invariant comparison"},
                        {"step": 3, "active_pointer": "high", "highlight": "Search space halved"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Mathematical Coordinates & Curve Representation",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Now let us visualize the mathematical function. Notice the relationship between the independent variable and the rate of change. By graphing the function, the geometric meaning becomes unmistakably clear.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "math_graph",
                    "title": "Mathematical Curve & Tangent Limits",
                    "subtitle": "Coordinate Geometry, Function Curves and Slope Evolution",
                    "parameters": {
                        "function_type": "polynomial",
                        "curve_equation": "f(x) = x^2 - 4x + 6",
                        "tangent_point": {"x": 2, "y": 2, "slope": 0},
                        "domain_range": [-2, 6],
                        "asymptotes": []
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Function Curve plotted"},
                        {"step": 2, "highlight": "Tangent point at minimum (x=2)"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Time & Space Complexity Boundaries",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"Rigorous analysis demands understanding the limits. What is the worst-case Big-O runtime? How much auxiliary memory is required? Evaluating these boundaries proves whether an algorithm is ready for hyperscale deployment.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Complexity Boundaries: Best vs Worst Case",
                    "subtitle": "Asymptotic Performance Across Data Distributions",
                    "parameters": {
                        "col1": "Best Case: O(1) or optimal shortcut when inputs match ideal preconditions",
                        "col2": "Average Case: Stable, predictable asymptotic execution across random data",
                        "col3": "Worst Case / Edge Trap: Pathological inputs (e.g. reverse sorted) and memory limits"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Best Case"},
                        {"step": 2, "highlight": "Worst Case"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Clean Production Implementation",
                "pedagogical_phase": "summary",
                "narration_text": f"To conclude, let us inspect an idiomatic, battle-tested implementation. Notice the absence of off-by-one errors, the clean boundary checks, and the self-documenting structure that makes this algorithm production-grade.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "code_visualizer",
                    "title": f"Production Implementation of {math_title}",
                    "subtitle": "Battle-Tested, Idiomatic Algorithm Code",
                    "parameters": {
                        "language": "python",
                        "code": "def solve_algorithm(items):\n    # 1. Base condition check\n    if not items:\n        return None\n    \n    # 2. Initialize pointers / state\n    left, right = 0, len(items) - 1\n    \n    # 3. Core invariant loop\n    while left <= right:\n        mid = (left + right) // 2\n        if evaluate_condition(items[mid]):\n            return items[mid]\n        left += 1\n        \n    return None",
                        "highlights": [
                            {"line": 2, "label": "Precondition boundary check"},
                            {"line": 6, "label": "Pointer initialization"},
                            {"line": 9, "label": "Safe integer midpoint calculation"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "active_line": 2, "scope": "Validation"},
                        {"step": 2, "active_line": 9, "scope": "Core evaluation"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This mathematical and algorithmic masterclass deconstructs {math_title}: formulating computational efficiency, step-by-step memory simulation, coordinate curve graphing, Big-O complexity analysis, and idiomatic production code.",
            "notes_markdown": f"""# {math_title}: Algorithm & Applied Math Guide

## 1. Mathematical Foundation
- **Invariants**: Conditions that remain true throughout every iteration of the algorithm.
- **Asymptotic Analysis**: Measuring growth rate of computational work as input size $N$ approaches infinity.

## 2. Complexity Matrix
- **Time Complexity**: Best, Average, and Worst-case bounds (Big-O).
- **Space Complexity**: Memory footprint and auxiliary cache overhead.

## 3. Implementation Checklist
- Prevent off-by-one bugs in loop termination conditions.
- Handle empty, single-element, and duplicate edge inputs cleanly.
""",
            "key_concepts": [
                {"concept": "Loop Invariant", "definition": "A formal property that holds true before and after each iteration of a loop, used to prove algorithmic correctness.", "importance": "Guarantees bug-free code logic."},
                {"concept": "Big-O Notation", "definition": "A mathematical notation that describes the limiting behavior of a function when the argument tends towards a particular value or infinity.", "importance": "Universal standard for evaluating algorithmic scalability."}
            ],
            "formulas_or_code": [
                {"title": "Asymptotic Dominance", "type": "formula", "content": "O(1) < O(log N) < O(N) < O(N log N) < O(N^2) < O(2^N)", "explanation": "The fundamental hierarchy of computational complexity."}
            ],
            "practice_questions": [
                {"question": f"Why is preserving the loop invariant so essential in implementing {math_title}?", "hint": "Think about edge case errors and termination guarantees.", "solution": "Preserving the loop invariant guarantees that at termination, the algorithm has either found the correct result or proven that no solution exists within the search space."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the primary reason developers analyze Big-O complexity?", "options": ["To make code look complicated", "To predict how memory and runtime will scale as data grows to millions of items", "To satisfy the compiler", "To avoid writing unit tests"], "correct_index": 1, "explanation": "Big-O reveals whether an algorithm will remain fast or crash servers under production scale."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does a loop invariant guarantee?", "back": "That a key correctness condition remains unbroken before, during, and after loop execution.", "category": "Algorithm Theory"}
            ]
        }

        return {
            "title": f"Mastering {math_title}: Algorithmic Elegance & Mathematical Rigor",
            "domain": "computer_science" if "algorithm" in topic.lower() or "search" in topic.lower() or "tree" in topic.lower() else "mathematics",
            "subdomain": "Algorithms, Systems & Applied Mathematics",
            "scenes": scenes,
            "materials": materials
        }

    def _build_generic_arts_lecture(self, topic: str, level: str, purpose: str, num_scenes: int, voice_name: str) -> Dict[str, Any]:
        arts_title = topic.strip().title()
        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Creative Spark & Emotional Core of {arts_title}",
                "pedagogical_phase": "hook",
                "narration_text": f"Art is the lie that enables us to realize the truth. Behind every enduring narrative, melody, or visual composition lies a fundamental human longing. To understand {arts_title}, we must explore how creators distill universal emotional truths into structured artistic form.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"The Creative Tension in {arts_title}",
                    "subtitle": "Raw Human Emotion vs. Disciplined Artistic Craft",
                    "parameters": {
                        "left_title": "The Raw Human Experience",
                        "left_items": ["Unconscious desires, vulnerabilities, and fears", "Chaos of daily reality", "The hunger for meaning and connection"],
                        "right_title": "The Masterful Artistic Form",
                        "right_items": ["Harmonic structure, rhythm, and pacing", "Archetypal character arcs and symbolic motifs", "Cathartic resolution that touches the human spirit"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Raw Experience"},
                        {"step": 2, "highlight": "Artistic Form"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Narrative Arc & Dramatic Tension Mountain",
                "pedagogical_phase": "foundation",
                "narration_text": f"Notice how storytelling and artistic compositions mimic the natural heartbeat of human tension. Beginning in the ordinary world, tension steadily climbs through progressive complications until reaching an intense, transformative climax.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "narrative_arc",
                    "title": "The Dramatic Tension Arc",
                    "subtitle": "Exposition -> Inciting Incident -> Rising Action -> Climax -> Resolution",
                    "parameters": {
                        "arc_stages": [
                            {"stage": "Exposition", "tension": 15, "desc": "Establishment of the ordinary world and flawed status quo"},
                            {"stage": "Inciting Incident", "desc": "The catalyst that disrupts life and demands action", "tension": 35},
                            {"stage": "Rising Action", "tension": 65, "desc": "Escalating stakes, tests of character, and mounting complications"},
                            {"stage": "The Climax", "tension": 95, "desc": "The ultimate confrontation; point of no return"},
                            {"stage": "Resolution & Catharsis", "tension": 25, "desc": "Integration of lessons; the transformed new world"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Inciting Incident"},
                        {"step": 2, "highlight": "The Climax"},
                        {"step": 3, "highlight": "Resolution"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Archetypes & Psychological Depth",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Why do certain characters and symbols resonate across cultures? Carl Jung identified them as archetypes: universal figures stored in humanity's collective unconscious. Understanding these figures gives your artistic analysis immense psychological depth.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "hierarchy_pyramid",
                    "title": "The Archetypal Architecture of Art",
                    "subtitle": "Universal Figures of the Collective Unconscious",
                    "parameters": {
                        "pyramid_title": "Artistic & Character Archetypes",
                        "tiers": [
                            {"tier": "The Transcendent Whole", "note": "Integration of the Shadow, Anima/Animus, and Individuation"},
                            {"tier": "The Mentor & Herald", "note": "Wise guides providing the supernatural aid or catalyst call"},
                            {"tier": "The Shadow & Antagonist", "note": "Represents the unacknowledged fears and repressed traits"},
                            {"tier": "The Protagonist / Seeker", "note": "The relatable, flawed avatar of the audience embarking on the journey"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "The Protagonist"},
                        {"step": 2, "highlight": "The Shadow"},
                        {"step": 3, "highlight": "The Transcendent Whole"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Masterwork Dissection: Techniques of the Greats",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"Let us dissect how master creators deploy motif, juxtaposition, and silence. Great art is distinguished not just by what is presented, but by what is deliberately withheld, inviting the audience's imagination to complete the canvas.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Techniques of Master Craftsmanship",
                    "subtitle": "Contrasting Amateur Tropes with Enduring Masterworks",
                    "parameters": {
                        "col1": "Subtext vs. Exposition: Show, don't tell; trust the audience to infer emotional truths",
                        "col2": "Pacing & Negative Space: Pauses and silence amplify emotional impact far more than noise",
                        "col3": "Thematic Unity: Every scene, dialogue, and brushstroke serves a central governing idea"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Subtext"},
                        {"step": 2, "highlight": "Negative Space"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": f"5. The Timeless Resonance of {arts_title}",
                "pedagogical_phase": "summary",
                "narration_text": f"Great art outlives the civilizations that gave it birth. By mastering {arts_title}, whether as a creator, critic, or passionate observer, you connect with the sacred human tradition of turning mortal experience into immortal beauty.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "spectrum_meter",
                    "title": "The Spectrum of Artistic Impact",
                    "subtitle": "From Ephemeral Entertainment to Timeless Cultural Monument",
                    "parameters": {
                        "left_label": "Ephemeral Entertainment: Temporary distraction quickly forgotten",
                        "right_label": "Immortal Masterwork: Shapes language, worldview, and human consciousness across generations",
                        "center_balance": "Cultivated Craft: Resonant work executed with technical excellence and heart",
                        "markers": [
                            "Distraction",
                            "Resonant Craft",
                            "Timeless Masterwork"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Ephemeral"},
                        {"step": 2, "highlight": "Timeless Masterwork"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This arts and humanities masterclass explores {arts_title}: deconstructing the creative spark, the narrative tension curve, archetypal psychology, masterwork craftsmanship, and timeless cultural impact.",
            "notes_markdown": f"""# {arts_title}: Masterclass Arts & Literature Notes

## 1. The Core Artistic Invariant
- **Form Follows Emotion**: Technical structures (rhythm, lighting, prose) exist to amplify emotional resonance.
- **The Power of Subtext**: The unsaid carries more weight than explicit dialogue.

## 2. Structural Principles
- **The Tension Curve**: Exposition, inciting incident, rising action, climax, and catharsis.
- **Archetypal Resonance**: Universal patterns that mirror the collective human psyche.

## 3. The Craftsman's Rulebook
1. Kill your darlings: ruthlessly cut elements that do not serve thematic unity.
2. Value negative space: silence gives notes their power; pauses give words their weight.
""",
            "key_concepts": [
                {"concept": "Catharsis", "definition": "The purification and purgation of emotions (especially pity and fear) through dramatic art.", "importance": "Provides psychological renewal and empathy for audiences."},
                {"concept": "Subtext", "definition": "The implicit or underlying meaning of a literary or theatrical work, distinct from the literal text.", "importance": "Creates depth, tension, and realistic dialogue."}
            ],
            "formulas_or_code": [
                {"title": "The Golden Rule of Storytelling", "type": "principle", "content": "Specific Details + Universal Truth = Enduring Resonance", "explanation": "The more truthfully specific the human experience, the more universally it is felt."}
            ],
            "practice_questions": [
                {"question": f"Why does understanding the dramatic tension arc improve both the creation and analysis of {arts_title}?", "hint": "Think about audience engagement and emotional payoff.", "solution": "The tension arc mirrors the natural psychological rhythm of expectation, struggle, and relief, ensuring the audience remains emotionally invested until the final catharsis."}
            ],
            "quiz": [
                {"id": 1, "question": "What is the primary function of dramatic subtext in masterwork literature or cinema?", "options": ["To confuse the audience", "To convey deep emotional truth through unspoken implications and behavioral clues", "To hide spelling errors", "To make scenes longer"], "correct_index": 1, "explanation": "Subtext creates emotional authenticity by acknowledging that humans rarely state their rawest desires directly."}
            ],
            "flashcards": [
                {"id": 1, "front": "What does 'Catharsis' mean in dramatic theory?", "back": "The emotional release and purification experienced by the audience at a story's climax.", "category": "Literary Theory"}
            ]
        }

        return {
            "title": f"The Art of {arts_title}: Narrative Architecture & Creative Mastery",
            "domain": "arts_literature",
            "subdomain": "Arts, Humanities & Narrative Architecture",
            "scenes": scenes,
            "materials": materials
        }

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
