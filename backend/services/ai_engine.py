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
            # Try gemini-2.0-flash, gemini-1.5-flash
            try:
                return genai.GenerativeModel("gemini-2.0-flash")
            except Exception:
                return genai.GenerativeModel("gemini-1.5-flash")
        return None

    def analyze_topic(self, topic: str, api_key: Optional[str] = None) -> TopicAnalysisResponse:
        """
        Analyzes a topic to determine its domain, pedagogical structure,
        and provide intelligent clarification questions.
        """
        topic_lower = topic.lower().strip()
        model = self._get_configured_gemini(api_key)

        # Domain heuristic detection
        domain = "general"
        subdomain = "General Knowledge"
        
        if any(w in topic_lower for w in ["search", "sort", "algorithm", "tree", "graph", "dp", "dynamic programming", "hash", "array", "linked list", "recursion", "dijkstra", "binary"]):
            domain = "computer_science"
            subdomain = "Algorithms & Data Structures"
        elif any(w in topic_lower for w in ["python", "javascript", "react", "fastapi", "async", "await", "promise", "api", "database", "sql", "thread", "memory", "pointer", "oop", "class"]):
            domain = "computer_science"
            subdomain = "Software Engineering & Programming"
        elif any(w in topic_lower for w in ["calculus", "derivative", "integral", "matrix", "linear algebra", "bayes", "probability", "statistics", "geometry", "trigonometry", "equation", "eigen"]):
            domain = "mathematics"
            subdomain = "Mathematics & Calculus"
        elif any(w in topic_lower for w in ["neural", "backpropagation", "transformer", "attention", "machine learning", "deep learning", "gradient descent", "ai", "llm", "cnn", "rnn"]):
            domain = "computer_science"
            subdomain = "Artificial Intelligence & Machine Learning"
        elif any(w in topic_lower for w in ["physics", "quantum", "gravity", "thermodynamics", "cell", "photosynthesis", "dna", "chemistry", "atom", "molecule", "biology", "optics"]):
            domain = "science"
            subdomain = "Natural Sciences & Physics"

        # Default recommended style based on domain
        style_map = {
            "computer_science": "Interactive Code & Algorithm Simulation",
            "mathematics": "Mathematical Curve & Formula Walkthrough",
            "science": "Process Flow & Animated Simulation",
            "general": "Animated Visual First"
        }
        recommended_style = style_map.get(domain, "Animated Visual First")

        questions = [
            ClarificationQuestion(
                id="knowledge_level",
                question="What is your current familiarity with this topic?",
                options=[
                    ClarificationOption(id="beginner", label="Beginner (Focus on visual intuition, simple analogies, zero jargon)"),
                    ClarificationOption(id="intermediate", label="Intermediate (Practical implementation, core mechanics, real use cases)"),
                    ClarificationOption(id="advanced", label="Advanced (Rigorous edge cases, time/space trade-offs, architecture)")
                ],
                default_value="intermediate"
            ),
            ClarificationQuestion(
                id="purpose",
                question="What is your primary goal for this lecture?",
                options=[
                    ClarificationOption(id="interview", label="Coding / Technical Interview Prep (Focus on optimal approach & complexity)"),
                    ClarificationOption(id="academic", label="Academic Exam & Homework (Theoretical clarity & step-by-step proofs)"),
                    ClarificationOption(id="practical", label="Practical Engineering (Production code, patterns, building real systems)"),
                    ClarificationOption(id="conceptual", label="Curiosity & Conceptual Intuition (Clear mental models & visual metaphors)")
                ],
                default_value="interview" if domain == "computer_science" else "conceptual"
            ),
            ClarificationQuestion(
                id="teaching_style",
                question="Which visual teaching style helps you learn best?",
                options=[
                    ClarificationOption(id="anim_sim", label="Step-by-step Algorithm / Process Simulator (Dynamic animated state updates)"),
                    ClarificationOption(id="code_flow", label="Code Execution Walkthrough (Line-by-line highlight, variables watch window)"),
                    ClarificationOption(id="math_curves", label="Mathematical Curves & Animated Equations (Visual coordinate plots)"),
                    ClarificationOption(id="concept_metaphor", label="Visual Metaphor & Architecture Diagrams (Intuitive spatial illustrations)")
                ],
                default_value="anim_sim" if domain == "computer_science" else "concept_metaphor"
            ),
            ClarificationQuestion(
                id="lecture_duration",
                question="Desired lecture length?",
                options=[
                    ClarificationOption(id="quick", label="Quick Concept (3 scenes, ~2-3 minutes)"),
                    ClarificationOption(id="standard", label="Standard Lesson (5 scenes, ~4-5 minutes)"),
                    ClarificationOption(id="deep", label="Comprehensive Deep Dive (7 scenes, ~7-9 minutes)")
                ],
                default_value="standard"
            )
        ]

        overview_text = f"We will construct an instructional video lecture on '{topic}'. The lesson will cover foundational principles, a live animated visualization demonstrating the core mechanism, complexity and trade-offs, and practical real-world applications."

        # If LLM model is available, refine analysis with live model
        if model:
            try:
                prompt = f"""
                Analyze the educational topic: "{topic}".
                Respond in valid JSON format only with these keys:
                - "domain": string (computer_science, mathematics, science, engineering, or general)
                - "subdomain": string
                - "overview": concise 2-sentence instructional summary
                - "recommended_level": "Beginner", "Intermediate", or "Advanced"
                - "recommended_style": string describing the best visual explanation technique
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
        Plans the lecture structure, scenes, visual specifications, scripts,
        and learning materials.
        """
        model = self._get_configured_gemini(api_key)
        
        # Determine scene count based on requested duration
        num_scenes = 5
        if "quick" in lecture_duration.lower() or "2-3" in lecture_duration.lower():
            num_scenes = 3
        elif "deep" in lecture_duration.lower() or "7" in lecture_duration.lower() or "8" in lecture_duration.lower():
            num_scenes = 6

        # Try generating via Gemini if key is provided and valid
        if model:
            try:
                gemini_data = self._generate_with_gemini(
                    model, topic, knowledge_level, purpose,
                    preferred_language, teaching_style, num_scenes
                )
                if gemini_data:
                    return gemini_data
            except Exception as ex:
                print(f"Gemini full generation error: {ex}. Using built-in pedagogical generator.")

        # Built-in Pedagogical Generation Engine with rich domain blueprints
        return self._generate_with_pedagogical_engine(
            topic, knowledge_level, purpose, preferred_language,
            teaching_style, num_scenes, voice_name
        )

    def _generate_with_gemini(
        self, model, topic: str, knowledge_level: str, purpose: str,
        preferred_language: str, teaching_style: str, num_scenes: int
    ) -> Optional[Dict[str, Any]]:
        prompt = f"""
        You are a world-class instructional designer, master educator, animator, and video producer.
        Topic: "{topic}"
        Knowledge Level: {knowledge_level}
        Purpose: {purpose}
        Language: {preferred_language}
        Teaching Style: {teaching_style}
        Number of Scenes: {num_scenes}

        You must design a complete, pedagogical video lecture that teaches through intuitive step-by-step visual animation (NOT static slides!).
        
        Available visual types:
        1. "algorithm_animator": Step-by-step state changes on data structures (array, pointers, search space elimination, trees, nodes).
        2. "code_visualizer": Syntax-highlighted code with animated execution pointer line, call stack, variables watch window, and simulated console output.
        3. "math_graph": Function curves, axes, coordinate points, tangent lines, animated slope, LaTeX formulas.
        4. "process_simulation": Multi-step flow diagram with animated signals/packets moving between nodes.
        5. "concept_metaphor": Concrete visual analogy cards comparing everyday concepts to technical reality.
        6. "comparison_matrix": Side-by-side feature comparison with animated indicators.

        Return a single valid JSON object with NO extra text or markdown formatting. The schema must match:
        {{
            "title": "Clear educational lecture title",
            "domain": "computer_science" | "mathematics" | "science" | "engineering" | "general",
            "subdomain": "string",
            "scenes": [
                {{
                    "scene_id": "scene_1",
                    "index": 0,
                    "chapter_title": "1. Hook & Intuition",
                    "pedagogical_phase": "hook",
                    "narration_text": "engaging 3-5 sentence spoken script written for a natural human voice. Clear, enthusiastic, teacher-like.",
                    "estimated_duration": 25.0,
                    "visual_spec": {{
                        "visual_type": "concept_metaphor" | "algorithm_animator" | "code_visualizer" | "math_graph" | "process_simulation",
                        "title": "Visual Title",
                        "subtitle": "Visual Subtitle",
                        "parameters": {{}},
                        "keyframe_steps": [
                            {{"step": 1, "description": "initial state", "highlight": "element"}},
                            {{"step": 2, "description": "active operation", "highlight": "element"}}
                        ]
                    }}
                }}
            ],
            "materials": {{
                "summary": "2-3 paragraph comprehensive summary of the lecture",
                "notes_markdown": "# Topic Notes\\n\\nStructured detailed markdown notes with bullet points and code/math.",
                "key_concepts": [
                    {{"concept": "Name", "definition": "Clear definition", "importance": "Why it matters"}}
                ],
                "formulas_or_code": [
                    {{"title": "Title", "type": "code"|"formula"|"rule", "content": "snippet or formula", "explanation": "how it works"}}
                ],
                "practice_questions": [
                    {{"question": "Problem statement", "hint": "Useful hint", "solution": "Full walkthrough"}}
                ],
                "quiz": [
                    {{"id": 1, "question": "Question?", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "Why A is correct."}}
                ],
                "flashcards": [
                    {{"id": 1, "front": "Concept / Question", "back": "Answer / Key takeaway", "category": "Core Principle"}}
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
        data = json.loads(text)
        return data

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
        Built-in high-fidelity instructional engine with dedicated blueprints for
        Algorithms, Programming, Mathematics, AI/ML, and Science.
        """
        topic_clean = topic.strip()
        t_low = topic_clean.lower()

        # Check for specialized blueprints
        if "binary search" in t_low:
            return self._build_binary_search_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t_low for k in ["neural network", "backpropagation", "gradient descent", "deep learning"]):
            return self._build_neural_networks_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t_low for k in ["async", "await", "asynchronous", "promise", "event loop"]):
            return self._build_async_await_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t_low for k in ["derivative", "calculus", "rate of change", "tangent"]):
            return self._build_calculus_derivative_lecture(knowledge_level, purpose, num_scenes, voice_name)
        elif any(k in t_low for k in ["photosynthesis", "light reaction", "chloroplast"]):
            return self._build_photosynthesis_lecture(knowledge_level, purpose, num_scenes, voice_name)
        else:
            return self._build_adaptive_topic_lecture(topic_clean, knowledge_level, purpose, teaching_style, num_scenes, voice_name)

    # ------------------- SPECIFIC RICH BLUEPRINTS -------------------

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

    def _build_adaptive_topic_lecture(
        self, topic: str, level: str, purpose: str, teaching_style: str, num_scenes: int, voice_name: str
    ) -> Dict[str, Any]:
        """
        Generates an adaptive, highly structured pedagogical lecture for any arbitrary topic.
        """
        title = f"{topic}: Intuitive Visual Masterclass"
        domain = "general"
        if any(w in topic.lower() for w in ["code", "algorithm", "data", "python", "software", "api", "network", "web"]):
            domain = "computer_science"
        elif any(w in topic.lower() for w in ["math", "formula", "matrix", "geometry", "probability", "algebra"]):
            domain = "mathematics"
        elif any(w in topic.lower() for w in ["physics", "biology", "chemistry", "space", "energy"]):
            domain = "science"

        scenes = [
            {
                "scene_id": "scene_1",
                "index": 0,
                "chapter_title": f"1. The Core Intuition: Why {topic} Matters",
                "pedagogical_phase": "hook",
                "narration_text": f"Welcome! To truly understand {topic}, we must start not with definitions or formulas, but with the fundamental problem it solves. Why do we need it? What breaks in its absence? By picturing this through an intuitive mental model, everything that follows will feel natural rather than memorized.",
                "estimated_duration": 22.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"The Foundational Intuition of {topic}",
                    "subtitle": "Connecting Everyday Intuition to Technical Reality",
                    "parameters": {
                        "left_title": "Without This Principle",
                        "left_items": ["High inefficiency or ambiguity", "Manual, fragile processes", "Difficult to scale or optimize"],
                        "right_title": f"With {topic}",
                        "right_items": ["Elegant, predictable structure", "Automated, scalable efficiency", "Clear mental clarity"]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "The problem setting"},
                        {"step": 2, "description": "The elegant solution"}
                    ]
                }
            },
            {
                "scene_id": "scene_2",
                "index": 1,
                "chapter_title": "2. The Underlying Mechanism: Core Architecture",
                "pedagogical_phase": "foundation",
                "narration_text": f"Now let us examine the fundamental mechanics that make {topic} work. At its base, it operates through a clear set of invariant rules. Signals, data, or concepts flow predictably from one stage to the next, maintaining consistency and purpose.",
                "estimated_duration": 24.0,
                "visual_spec": {
                    "visual_type": "process_simulation",
                    "title": f"{topic} Operational Pipeline",
                    "subtitle": "Stage-by-Stage Functional Architecture",
                    "parameters": {
                        "stages": [
                            {"name": "Stage 1: Input & Setup", "role": "Gathering preconditions"},
                            {"name": "Stage 2: Core Transformation", "role": "Applying primary rules & invariants"},
                            {"name": "Stage 3: Validation & Output", "role": "Delivering consistent results"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Stage 1"},
                        {"step": 2, "highlight": "Stage 2"},
                        {"step": 3, "highlight": "Stage 3"}
                    ]
                }
            },
            {
                "scene_id": "scene_3",
                "index": 2,
                "chapter_title": "3. Step-by-Step Walkthrough in Action",
                "pedagogical_phase": "visual_demonstration",
                "narration_text": f"Let us observe a concrete demonstration. Watch how state transitions occur step-by-step. Each action directly addresses the objective, eliminating uncertainty and producing verifiable outcomes.",
                "estimated_duration": 25.0,
                "visual_spec": {
                    "visual_type": "algorithm_animator" if domain == "computer_science" else "diagram_board",
                    "title": f"Live Demonstration of {topic}",
                    "subtitle": "Tracking Dynamic State Transitions",
                    "parameters": {
                        "steps": [
                            {"step": 1, "state": "Initial Condition", "note": "Establishing baseline parameters"},
                            {"step": 2, "state": "Active Execution", "note": "Processing central invariant"},
                            {"step": 3, "state": "Convergence", "note": "Reached target outcome"}
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "description": "Initial parameters set"},
                        {"step": 2, "description": "Active transformation"},
                        {"step": 3, "description": "Final result verified"}
                    ]
                }
            },
            {
                "scene_id": "scene_4",
                "index": 3,
                "chapter_title": "4. Edge Cases, Nuances & Common Traps",
                "pedagogical_phase": "edge_cases",
                "narration_text": f"Experienced practitioners know that mastery lies in understanding the edge cases. Where does {topic} encounter limits? What trade-offs between speed, complexity, and memory must we navigate? Being aware of these pitfalls prevents critical failures.",
                "estimated_duration": 23.0,
                "visual_spec": {
                    "visual_type": "comparison_matrix",
                    "title": "Nuances, Pitfalls & Trade-Offs",
                    "subtitle": "Best Practices for Real-World Scenarios",
                    "parameters": {
                        "col1": "Common Pitfall: Misunderstanding initial boundary conditions",
                        "col2": "Trade-off: Simplicity vs. Maximum Performance",
                        "col3": "Best Practice: Verify invariants continuously"
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Pitfall"},
                        {"step": 2, "highlight": "Trade-off"},
                        {"step": 3, "highlight": "Best Practice"}
                    ]
                }
            },
            {
                "scene_id": "scene_5",
                "index": 4,
                "chapter_title": "5. Real-World Applications & Key Takeaways",
                "pedagogical_phase": "summary",
                "narration_text": f"To wrap up our lesson: {topic} is a powerful concept that transforms how we solve complex challenges. By keeping the core intuition, the underlying mechanism, and the key trade-offs in mind, you are fully equipped to apply this in your studies and practical work.",
                "estimated_duration": 22.0,
                "visual_spec": {
                    "visual_type": "concept_metaphor",
                    "title": f"{topic}: Key Educational Takeaways",
                    "subtitle": "Summary of Core Principles and Applications",
                    "parameters": {
                        "takeaways": [
                            "Intuition first: Understand the problem before the implementation",
                            "Respect invariants: Consistency at every step guarantees success",
                            "Consider trade-offs: Balance elegance with practical efficiency"
                        ]
                    },
                    "keyframe_steps": [
                        {"step": 1, "highlight": "Intuition"},
                        {"step": 2, "highlight": "Invariants"},
                        {"step": 3, "highlight": "Application"}
                    ]
                }
            }
        ]

        materials = {
            "summary": f"This comprehensive lecture on {topic} breaks down the foundational intuition, step-by-step mechanics, critical edge cases, and real-world practical applications to ensure thorough conceptual mastery.",
            "notes_markdown": f"""# {topic}: Comprehensive Masterclass Notes

## 1. Executive Summary
Understanding **{topic}** requires building a solid mental model from simple to advanced concepts:
- **Core Purpose**: Solving fundamental challenges with clarity and speed.
- **Key Invariants**: Predictable rules that govern behavior throughout execution.
- **Scope & Applicability**: Widely utilized across modern engineering, science, and analytical domains.

## 2. Structural Principles
1. **Foundation**: Setting clear preconditions.
2. **Execution**: Systematic transformation with minimal friction.
3. **Verification**: Ensuring results meet all necessary constraints.
""",
            "key_concepts": [
                {"concept": f"{topic} Core Invariant", "definition": "The defining mathematical or architectural rule that remains true throughout the lifecycle.", "importance": "Guarantees system correctness."},
                {"concept": "State Transition", "definition": "Moving safely from an initial state through intermediate phases to a target outcome.", "importance": "Provides transparent traceability."}
            ],
            "formulas_or_code": [
                {"title": f"{topic} Paradigm Rule", "type": "rule", "content": "Invariant(State_t) == True for all t", "explanation": "Ensures every intermediate state satisfies foundational requirements."}
            ],
            "practice_questions": [
                {"question": f"What is the single most critical reason to apply {topic} in practice?", "hint": "Think about efficiency, predictability, and safety.", "solution": f"Applying {topic} creates a structured, verifiable approach that prevents errors, scales predictably, and optimizes resource utilization."}
            ],
            "quiz": [
                {"id": 1, "question": f"What is the first step when implementing or analyzing {topic}?", "options": ["Jump straight to advanced edge cases", "Establish clear foundational preconditions and invariants", "Ignore performance trade-offs", "Random trial and error"], "correct_index": 1, "explanation": "Establishing clear baseline preconditions ensures all downstream transformations are sound."},
                {"id": 2, "question": f"Why is understanding the edge cases of {topic} essential?", "options": ["It is only needed for academic exams", "Systems typically fail at boundary conditions if unhandled", "Edge cases do not affect real-world outcomes", "It replaces the need for the core mechanism"], "correct_index": 1, "explanation": "Failures and unexpected behavior almost always occur at boundaries and edge cases."}
            ],
            "flashcards": [
                {"id": 1, "front": f"What is the primary benefit of {topic}?", "back": "Providing structured, predictable, and optimized outcomes for complex problems.", "category": "Core Principle"},
                {"id": 2, "front": f"How should one approach learning {topic}?", "back": "By understanding the intuitive problem first, then mastering the rigorous mechanism and edge cases.", "category": "Pedagogy"}
            ]
        }

        return {
            "title": title,
            "domain": domain,
            "subdomain": "Educational Concepts",
            "scenes": scenes,
            "materials": materials
        }
