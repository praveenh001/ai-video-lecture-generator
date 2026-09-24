import os
import math
import subprocess
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

def get_ffmpeg_exe() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def load_fonts():
    """Loads modern Segoe UI and Consolas fonts with fallbacks."""
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 34)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
        font_body = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
        font_badge = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)
        font_code = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)
        font_subtitles = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_body = font_title
        font_badge = font_title
        font_code = font_title
        font_subtitles = font_title
    return {
        "title": font_title,
        "sub": font_sub,
        "body": font_body,
        "badge": font_badge,
        "code": font_code,
        "subtitle": font_subtitles
    }

class VisualEngine:
    def __init__(self, media_dir: str = "backend/media"):
        self.media_dir = media_dir
        self.videos_dir = os.path.join(media_dir, "videos")
        self.thumbs_dir = os.path.join(media_dir, "thumbnails")
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.thumbs_dir, exist_ok=True)
        self.fonts = load_fonts()

    def draw_base_canvas(self, width: int = 1280, height: int = 720) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        """Creates a modern dark gradient canvas with glowing accents."""
        img = Image.new("RGB", (width, height), (12, 16, 28))
        draw = ImageDraw.Draw(img)

        # Subtle vertical gradient
        for y in range(height):
            factor = y / height
            r = int(10 + factor * 12)
            g = int(14 + factor * 14)
            b = int(26 + factor * 22)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Soft top ambient glow
        draw.ellipse([(-200, -200), (600, 300)], fill=(20, 35, 65))
        draw.ellipse([(width - 500, -100), (width + 300, 400)], fill=(18, 45, 60))

        # Grid lines (fine dark tech style)
        for x in range(0, width, 80):
            draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 6), width=1)
        for y in range(0, height, 80):
            draw.line([(0, y), (width, y)], fill=(255, 255, 255, 6), width=1)

        return img, draw

    def render_scene_frame(
        self,
        scene: Dict[str, Any],
        step_idx: int = 0,
        subtitle_text: str = "",
        width: int = 1280,
        height: int = 720
    ) -> Image.Image:
        """
        Renders an ultra-clean educational frame for a given scene and step.
        """
        img, draw = self.draw_base_canvas(width, height)
        fonts = self.fonts

        # 1. Header Bar
        chapter_title = scene.get("chapter_title", "Educational Lecture")
        pedagogical_phase = scene.get("pedagogical_phase", "Foundation").upper()
        
        # Phase badge
        phase_colors = {
            "HOOK": ((245, 158, 11), (254, 243, 199)),
            "FOUNDATION": ((59, 130, 246), (219, 234, 254)),
            "VISUAL_DEMONSTRATION": ((16, 185, 129), (209, 250, 229)),
            "EDGE_CASES": ((236, 72, 153), (253, 231, 243)),
            "SUMMARY": ((139, 92, 246), (243, 232, 255))
        }
        bg_col, txt_col = phase_colors.get(pedagogical_phase, ((59, 130, 246), (255, 255, 255)))
        draw.rounded_rectangle([(60, 35), (200, 65)], radius=15, fill=bg_col)
        draw.text((80, 40), pedagogical_phase.replace("_", " "), fill=(255, 255, 255), font=fonts["badge"])

        # Chapter Title
        draw.text((220, 35), chapter_title, fill=(240, 244, 255), font=fonts["title"])

        # Visual Spec
        vspec = scene.get("visual_spec", {})
        vtype = vspec.get("visual_type", "diagram_board")
        vtitle = vspec.get("title", "")
        vsubtitle = vspec.get("subtitle", "")
        params = vspec.get("parameters", {})
        steps = vspec.get("keyframe_steps", [])
        current_step = steps[step_idx] if (steps and step_idx < len(steps)) else {}

        # Visual Header inside main container
        container_rect = [(60, 95), (width - 60, height - 120)]
        draw.rounded_rectangle(container_rect, radius=20, fill=(18, 24, 38), outline=(45, 58, 85), width=2)

        # Title of Visual
        draw.text((90, 115), vtitle, fill=(56, 189, 248), font=fonts["sub"])
        if vsubtitle:
            draw.text((90, 150), vsubtitle, fill=(148, 163, 184), font=fonts["body"])

        # 2. Render Specialized Visual Component
        if vtype == "algorithm_animator":
            self._render_algorithm_animator(draw, params, current_step, step_idx, fonts, container_rect)
        elif vtype == "code_visualizer":
            self._render_code_visualizer(draw, params, current_step, step_idx, fonts, container_rect)
        elif vtype == "math_graph":
            self._render_math_graph(draw, params, current_step, step_idx, fonts, container_rect)
        elif vtype == "concept_metaphor":
            self._render_concept_metaphor(draw, params, current_step, step_idx, fonts, container_rect)
        elif vtype == "process_simulation":
            self._render_process_simulation(draw, params, current_step, step_idx, fonts, container_rect)
        elif vtype == "comparison_matrix":
            self._render_comparison_matrix(draw, params, current_step, step_idx, fonts, container_rect)
        else:
            self._render_diagram_board(draw, params, current_step, step_idx, fonts, container_rect)

        # 3. Subtitles Pill at bottom
        sub_text = subtitle_text or scene.get("narration_text", "")
        if sub_text:
            if len(sub_text) > 110:
                sub_text = sub_text[:107] + "..."
            sub_w = int(draw.textlength(sub_text, font=fonts["subtitle"]))
            pill_left = max(60, (width - sub_w) // 2 - 30)
            pill_right = min(width - 60, (width + sub_w) // 2 + 30)
            draw.rounded_rectangle([(pill_left, height - 90), (pill_right, height - 40)], radius=15, fill=(5, 8, 16), outline=(60, 80, 115), width=1)
            draw.text((pill_left + 30, height - 80), sub_text, fill=(255, 255, 255), font=fonts["subtitle"])

        return img

    def _render_algorithm_animator(self, draw, params, step, step_idx, fonts, rect):
        """Draws interactive array visualization with pointers (Low, Mid, High), comparisons, and eliminations."""
        arr = params.get("array", [2, 5, 8, 12, 16, 23, 38, 56, 72, 91])
        target = params.get("target", 23)
        steps_list = params.get("steps", [])

        # Active state parameters
        active_step = steps_list[step_idx] if (steps_list and step_idx < len(steps_list)) else step
        low = active_step.get("low", 0)
        high = active_step.get("high", len(arr) - 1)
        mid = active_step.get("mid", (low + high) // 2)
        eliminated = active_step.get("eliminated", [])
        matched = active_step.get("matched", None)
        action_note = active_step.get("decision") or active_step.get("action") or f"Target = {target} | Search range: [{low}..{high}]"

        # Banner for current action
        draw.rounded_rectangle([(90, 195), (rect[1][0] - 30, 245)], radius=10, fill=(30, 41, 59), outline=(56, 189, 248), width=1)
        draw.text((110, 210), f"⚡ ACTION: {action_note}", fill=(254, 240, 138), font=fonts["body"])

        # Draw Array Elements
        n = len(arr)
        start_x = 90
        available_w = rect[1][0] - rect[0][0] - 60
        cell_w = min(100, (available_w - (n - 1) * 12) // n)
        cell_h = 90
        start_y = 310

        for i, val in enumerate(arr):
            cx = start_x + i * (cell_w + 12)
            cy = start_y
            
            # Determine color state
            is_elim = i in eliminated
            is_mid = (i == mid)
            is_match = (i == matched)

            if is_match:
                bg = (16, 185, 129) # Vibrant Emerald
                border = (52, 211, 153)
                text_col = (255, 255, 255)
            elif is_mid:
                bg = (99, 102, 241) # Vibrant Indigo
                border = (165, 180, 252)
                text_col = (255, 255, 255)
            elif is_elim:
                bg = (24, 30, 44) # Dimmed / Eliminated
                border = (40, 50, 70)
                text_col = (75, 85, 99)
            else:
                bg = (30, 41, 59) # Active Candidate
                border = (71, 85, 105)
                text_col = (241, 245, 249)

            draw.rounded_rectangle([(cx, cy), (cx + cell_w, cy + cell_h)], radius=12, fill=bg, outline=border, width=2)
            
            # Draw value text centered
            val_str = str(val)
            tw = draw.textlength(val_str, font=fonts["title"])
            draw.text((cx + (cell_w - tw) // 2, cy + 22), val_str, fill=text_col, font=fonts["title"])

            # Draw index below
            idx_str = f"[{i}]"
            iw = draw.textlength(idx_str, font=fonts["badge"])
            draw.text((cx + (cell_w - iw) // 2, cy + cell_h + 8), idx_str, fill=(100, 116, 139), font=fonts["badge"])

            # Pointer indicators above cell
            if i == low and not is_elim:
                draw.rounded_rectangle([(cx, cy - 45), (cx + cell_w // 2 - 2, cy - 20)], radius=6, fill=(14, 165, 233))
                draw.text((cx + 6, cy - 42), "LOW", fill=(255, 255, 255), font=fonts["badge"])
            if i == high and not is_elim:
                draw.rounded_rectangle([(cx + cell_w // 2 + 2, cy - 45), (cx + cell_w, cy - 20)], radius=6, fill=(244, 63, 94))
                draw.text((cx + cell_w // 2 + 6, cy - 42), "HIGH", fill=(255, 255, 255), font=fonts["badge"])
            if is_mid:
                draw.rounded_rectangle([(cx + 10, cy - 75), (cx + cell_w - 10, cy - 50)], radius=6, fill=(99, 102, 241))
                draw.text((cx + 16, cy - 72), "MID", fill=(255, 255, 255), font=fonts["badge"])

            # Crossed-out hash for eliminated
            if is_elim:
                draw.line([(cx + 10, cy + 10), (cx + cell_w - 10, cy + cell_h - 10)], fill=(239, 68, 68, 120), width=2)

        # Legend at bottom of visual container
        draw.text((90, 480), f"🎯 Target Search Value: {target}", fill=(255, 255, 255), font=fonts["sub"])
        draw.text((90, 520), f"Pointers: LOW = idx {low} | MID = idx {mid} (val {arr[mid]}) | HIGH = idx {high}", fill=(148, 163, 184), font=fonts["body"])

    def _render_code_visualizer(self, draw, params, step, step_idx, fonts, rect):
        """Draws syntax-styled code editor with active execution pointer and scope inspector."""
        code_str = params.get("code", "")
        lines = code_str.split("\n")
        lang = params.get("language", "python").upper()
        active_line_num = step.get("active_line", 2)
        variables = params.get("variables", {})

        # Editor frame
        ed_x = 90
        ed_y = 195
        ed_w = 720
        ed_h = 360
        draw.rounded_rectangle([(ed_x, ed_y), (ed_x + ed_w, ed_y + ed_h)], radius=12, fill=(15, 20, 32), outline=(51, 65, 85), width=2)

        # Editor header with dots
        draw.ellipse([(ed_x + 18, ed_y + 14), (ed_x + 30, ed_y + 26)], fill=(239, 68, 68))
        draw.ellipse([(ed_x + 36, ed_y + 14), (ed_x + 48, ed_y + 26)], fill=(234, 179, 8))
        draw.ellipse([(ed_x + 54, ed_y + 14), (ed_x + 66, ed_y + 26)], fill=(34, 197, 94))
        draw.text((ed_x + 85, ed_y + 12), f"main.{lang.lower()} - Active Execution", fill=(148, 163, 184), font=fonts["badge"])

        # Code lines
        line_y = ed_y + 45
        for idx, line in enumerate(lines[:12]):
            curr_num = idx + 1
            is_active = (curr_num == active_line_num)
            if is_active:
                draw.rectangle([(ed_x + 4, line_y - 2), (ed_x + ed_w - 4, line_y + 24)], fill=(30, 58, 110))
                draw.text((ed_x + 10, line_y), "▶", fill=(250, 204, 21), font=fonts["badge"])
            
            # Line number
            draw.text((ed_x + 30, line_y), f"{curr_num:2d}", fill=(100, 116, 139), font=fonts["code"])
            
            # Code line content
            line_color = (248, 250, 252)
            if "def " in line or "return " in line or "while " in line or "if " in line or "else:" in line or "for " in line:
                line_color = (192, 132, 252) # Keyword purple
            elif "import " in line:
                line_color = (251, 146, 60)
            elif "#" in line:
                line_color = (100, 116, 139) # Comment gray
            draw.text((ed_x + 70, line_y), line, fill=line_color, font=fonts["code"])
            line_y += 25

        # Side Panel: Variable Scope Watch & Stack
        var_x = ed_x + ed_w + 25
        var_w = rect[1][0] - var_x - 30
        draw.rounded_rectangle([(var_x, ed_y), (var_x + var_w, ed_y + ed_h)], radius=12, fill=(24, 30, 48), outline=(56, 189, 248), width=1)
        draw.text((var_x + 20, ed_y + 18), "🔍 VARIABLE SCOPE WATCH", fill=(56, 189, 248), font=fonts["badge"])

        vy = ed_y + 55
        scope_vars = step.get("scope", "low=0, high=9, mid=4")
        draw.text((var_x + 20, vy), f"State: {scope_vars}", fill=(254, 240, 138), font=fonts["body"])
        vy += 40

        for k, v in variables.items():
            draw.rounded_rectangle([(var_x + 15, vy), (var_x + var_w - 15, vy + 45)], radius=8, fill=(15, 23, 42))
            draw.text((var_x + 25, vy + 12), f"{k}:", fill=(148, 163, 184), font=fonts["body"])
            draw.text((var_x + 120, vy + 12), str(v), fill=(52, 211, 153), font=fonts["title"])
            vy += 55

    def _render_math_graph(self, draw, params, step, step_idx, fonts, rect):
        """Draws coordinate system, mathematical curve f(x), tangent/secant lines and formulas."""
        ox = 320
        oy = 440
        scale_x = 75
        scale_y = 18

        # Draw grid & axes
        draw.line([(ox - 200, oy), (ox + 350, oy)], fill=(71, 85, 105), width=2) # X axis
        draw.line([(ox, oy + 80), (ox, oy - 230)], fill=(71, 85, 105), width=2) # Y axis
        draw.text((ox + 360, oy - 10), "x", fill=(148, 163, 184), font=fonts["sub"])
        draw.text((ox - 10, oy - 250), "y", fill=(148, 163, 184), font=fonts["sub"])

        # Plot f(x) = x^2 curve
        pts = []
        for xi in range(-120, 240, 4):
            x_val = xi / scale_x
            y_val = x_val ** 2
            px = ox + int(x_val * scale_x)
            py = oy - int(y_val * scale_y)
            pts.append((px, py))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(56, 189, 248), width=3)

        # Plot point x0 = 2 -> f(2) = 4
        x0_px = ox + int(2.0 * scale_x)
        x0_py = oy - int(4.0 * scale_y)
        draw.ellipse([(x0_px - 6, x0_py - 6), (x0_px + 6, x0_py + 6)], fill=(244, 63, 94))
        draw.text((x0_px - 45, x0_py - 25), "(2, 4)", fill=(255, 255, 255), font=fonts["badge"])

        # Tangent line at (2, 4) with slope m = 4
        t_pt1 = (x0_px - 80, x0_py + int(80 * (4.0 * scale_y / scale_x)))
        t_pt2 = (x0_px + 80, x0_py - int(80 * (4.0 * scale_y / scale_x)))
        draw.line([t_pt1, t_pt2], fill=(250, 204, 21), width=3)
        draw.text((t_pt2[0] + 10, t_pt2[1] - 10), "Tangent: Slope = 4", fill=(250, 204, 21), font=fonts["badge"])

        # Math formula card on the right
        card_x = ox + 420
        card_y = 195
        card_w = rect[1][0] - card_x - 30
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + 350)], radius=15, fill=(24, 30, 48), outline=(56, 189, 248), width=2)
        draw.text((card_x + 20, card_y + 20), "📐 THE CALCULUS DERIVATIVE", fill=(56, 189, 248), font=fonts["badge"])
        draw.text((card_x + 20, card_y + 60), "f'(x) = lim_{h -> 0} [f(x+h) - f(x)] / h", fill=(254, 240, 138), font=fonts["body"])
        draw.text((card_x + 20, card_y + 110), "For f(x) = x²:", fill=(255, 255, 255), font=fonts["sub"])
        draw.text((card_x + 20, card_y + 150), "• f'(x) = 2x", fill=(52, 211, 153), font=fonts["title"])
        draw.text((card_x + 20, card_y + 205), "At x = 2: Slope = 2(2) = 4.0", fill=(241, 245, 249), font=fonts["body"])
        draw.text((card_x + 20, card_y + 250), "Instantaneous Rate of Change!", fill=(148, 163, 184), font=fonts["sub"])

    def _render_concept_metaphor(self, draw, params, step, step_idx, fonts, rect):
        """Draws comparative visual cards contrasting two concepts or metaphors."""
        left_title = params.get("left_title") or params.get("left_label") or "Traditional / Without"
        right_title = params.get("right_title") or params.get("right_label") or "Optimized / With Concept"
        left_items = params.get("left_items", ["High overhead", "Slow linear execution"])
        right_items = params.get("right_items", ["Logarithmic speed", "Divide and conquer"])

        card_w = (rect[1][0] - rect[0][0] - 80) // 2
        card_h = 350
        cy = 195

        # Left Card (Without / Traditional)
        lx = rect[0][0] + 30
        draw.rounded_rectangle([(lx, cy), (lx + card_w, cy + card_h)], radius=15, fill=(30, 25, 35), outline=(239, 68, 68), width=2)
        draw.rounded_rectangle([(lx + 20, cy + 20), (lx + 160, cy + 50)], radius=8, fill=(239, 68, 68))
        draw.text((lx + 32, cy + 25), "INEFFICIENT", fill=(255, 255, 255), font=fonts["badge"])
        draw.text((lx + 20, cy + 65), left_title, fill=(254, 202, 202), font=fonts["sub"])
        iy = cy + 120
        for it in left_items:
            draw.text((lx + 25, iy), f"❌  {it}", fill=(226, 232, 240), font=fonts["body"])
            iy += 45

        # Right Card (With Concept / Superior)
        rx = lx + card_w + 20
        draw.rounded_rectangle([(rx, cy), (rx + card_w, cy + card_h)], radius=15, fill=(20, 35, 35), outline=(16, 185, 129), width=2)
        draw.rounded_rectangle([(rx + 20, cy + 20), (rx + 160, cy + 50)], radius=8, fill=(16, 185, 129))
        draw.text((rx + 36, cy + 25), "OPTIMIZED", fill=(255, 255, 255), font=fonts["badge"])
        draw.text((rx + 20, cy + 65), right_title, fill=(167, 243, 208), font=fonts["sub"])
        iy = cy + 120
        for it in right_items:
            draw.text((rx + 25, iy), f"✅  {it}", fill=(226, 232, 240), font=fonts["body"])
            iy += 45

    def _render_process_simulation(self, draw, params, step, step_idx, fonts, rect):
        """Draws multi-stage pipeline flow with dynamic pulse highlight."""
        stages = params.get("stages") or params.get("components") or [
            {"name": "1. Input Request", "role": "Incoming event received"},
            {"name": "2. Core Processing", "role": "Transformation applied"},
            {"name": "3. Result Delivery", "role": "Value returned to client"}
        ]
        
        num_s = len(stages)
        cw = min(280, (rect[1][0] - rect[0][0] - (num_s + 1) * 30) // num_s)
        ch = 260
        cy = 230

        for i, s in enumerate(stages):
            sx = rect[0][0] + 30 + i * (cw + 30)
            is_active = (i == (step_idx % num_s))
            
            border = (56, 189, 248) if is_active else (51, 65, 85)
            bg = (30, 58, 95) if is_active else (20, 26, 40)
            
            draw.rounded_rectangle([(sx, cy), (sx + cw, cy + ch)], radius=15, fill=bg, outline=border, width=3 if is_active else 1)
            
            badge_title = f"STAGE {i+1}"
            draw.rounded_rectangle([(sx + 15, cy + 15), (sx + 110, cy + 42)], radius=6, fill=(56, 189, 248) if is_active else (71, 85, 105))
            draw.text((sx + 24, cy + 20), badge_title, fill=(255, 255, 255), font=fonts["badge"])

            name = s.get("name", f"Stage {i+1}")
            desc = s.get("role") or s.get("desc") or ""
            draw.text((sx + 15, cy + 60), name, fill=(248, 250, 252), font=fonts["sub"])
            draw.text((sx + 15, cy + 110), desc, fill=(148, 163, 184), font=fonts["body"])

            # Arrow to next stage
            if i < num_s - 1:
                ax = sx + cw + 8
                draw.text((ax, cy + 110), "➔", fill=(56, 189, 248) if is_active else (71, 85, 105), font=fonts["title"])

    def _render_comparison_matrix(self, draw, params, step, step_idx, fonts, rect):
        """Draws 3 comparison columns."""
        cols = [
            params.get("col1", "Baseline Approach"),
            params.get("col2", "Balanced Standard"),
            params.get("col3", "Optimized Approach")
        ]
        cw = (rect[1][0] - rect[0][0] - 80) // 3
        cy = 205
        ch = 330
        for i, col_text in enumerate(cols):
            cx = rect[0][0] + 25 + i * (cw + 20)
            draw.rounded_rectangle([(cx, cy), (cx + cw, cy + ch)], radius=12, fill=(22, 28, 44), outline=(71, 85, 105), width=1)
            draw.rounded_rectangle([(cx + 15, cy + 15), (cx + 120, cy + 45)], radius=6, fill=(99, 102, 241))
            draw.text((cx + 25, cy + 20), f"COLUMN {i+1}", fill=(255, 255, 255), font=fonts["badge"])
            # Wrap text
            words = col_text.split(":")
            hdr = words[0]
            body = ":".join(words[1:]) if len(words) > 1 else words[0]
            draw.text((cx + 15, cy + 65), hdr, fill=(56, 189, 248), font=fonts["sub"])
            draw.text((cx + 15, cy + 115), body.strip(), fill=(203, 213, 225), font=fonts["body"])

    def _render_diagram_board(self, draw, params, step, step_idx, fonts, rect):
        """Default diagram board."""
        draw.text((rect[0][0] + 40, 220), "📌 Core Architectural Components", fill=(255, 255, 255), font=fonts["sub"])
        elements = params.get("elements") or params.get("layers") or ["Foundational Concept", "Transformation Invariant", "Final Output"]
        ey = 280
        for elem in elements:
            label = elem if isinstance(elem, str) else elem.get("name", "Component")
            draw.rounded_rectangle([(rect[0][0] + 40, ey), (rect[1][0] - 40, ey + 50)], radius=8, fill=(30, 41, 59), outline=(56, 189, 248), width=1)
            draw.text((rect[0][0] + 60, ey + 14), f"• {label}", fill=(241, 245, 249), font=fonts["body"])
            ey += 65

    def render_scene_video(self, scene: Dict[str, Any], audio_path: str, output_path: str) -> str:
        """
        Renders an MP4 video clip for a single scene with animated frames and synchronized audio.
        """
        ffmpeg_exe = get_ffmpeg_exe()
        duration = scene.get("actual_duration") or scene.get("estimated_duration") or 15.0
        steps = scene.get("visual_spec", {}).get("keyframe_steps", [])
        num_steps = max(1, len(steps))

        # Generate frames
        with tempfile.TemporaryDirectory() as tmpdir:
            fps = 2  # 2 frames per second is lightweight and smooth for instructional slide steps
            total_frames = max(2, int(duration * fps))

            for f_idx in range(total_frames):
                # Calculate active step index proportionally
                step_idx = min(num_steps - 1, int((f_idx / total_frames) * num_steps))
                # Determine active subtitle text
                sub_text = ""
                cur_time = f_idx / fps
                for sub in scene.get("subtitles", []):
                    # sub can be SubtitleItem or dict
                    st = sub.start if hasattr(sub, "start") else sub.get("start", 0)
                    en = sub.end if hasattr(sub, "end") else sub.get("end", 999)
                    txt = sub.text if hasattr(sub, "text") else sub.get("text", "")
                    if st <= cur_time <= en:
                        sub_text = txt
                        break

                img = self.render_scene_frame(scene, step_idx=step_idx, subtitle_text=sub_text)
                img.save(os.path.join(tmpdir, f"frame_{f_idx:05d}.png"))

            # Run ffmpeg to compile frames + audio
            cmd = [
                ffmpeg_exe, "-y",
                "-r", str(fps),
                "-i", os.path.join(tmpdir, "frame_%05d.png"),
                "-i", audio_path,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        return output_path

    def render_full_lecture_video(
        self,
        lecture_data: Dict[str, Any],
        ambient_audio_path: Optional[str] = "backend/media/ambient_study.mp3"
    ) -> str:
        """
        Renders full continuous lecture MP4 video stitching all scene clips.
        """
        lecture_id = lecture_data.get("id", "lecture")
        final_video_name = f"lecture_{lecture_id}.mp4"
        final_video_path = os.path.join(self.videos_dir, final_video_name)

        scenes = lecture_data.get("scenes", [])
        if not scenes:
            return ""

        ffmpeg_exe = get_ffmpeg_exe()
        rendered_scene_paths = []

        with tempfile.TemporaryDirectory() as tmpdir:
            for idx, sc in enumerate(scenes):
                sc_id = sc.get("scene_id", f"scene_{idx}")
                audio_rel = sc.get("audio_url", f"/media/audio/{sc_id}.mp3")
                audio_abs = os.path.join("backend", audio_rel.lstrip("/"))
                if not os.path.exists(audio_abs):
                    # fallback
                    audio_abs = os.path.join("backend/media/audio", f"{sc_id}.mp3")

                scene_video_file = os.path.join(tmpdir, f"scene_{idx}.mp4")
                self.render_scene_video(sc, audio_abs, scene_video_file)
                rendered_scene_paths.append(scene_video_file)

            # Create concat list file
            concat_txt = os.path.join(tmpdir, "concat.txt")
            with open(concat_txt, "w") as f:
                for sv in rendered_scene_paths:
                    f.write(f"file '{sv.replace(os.sep, '/')}'\n")

            # Concat scenes
            temp_stitched = os.path.join(tmpdir, "stitched.mp4")
            cmd_concat = [
                ffmpeg_exe, "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_txt,
                "-c", "copy",
                temp_stitched
            ]
            subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            # Mix ambient study music ducked if exists
            if ambient_audio_path and os.path.exists(ambient_audio_path):
                cmd_mix = [
                    ffmpeg_exe, "-y",
                    "-i", temp_stitched,
                    "-stream_loop", "-1", "-i", ambient_audio_path,
                    "-filter_complex", "[1:a]volume=0.08[bg];[0:a][bg]amix=inputs=2:duration=first[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    final_video_path
                ]
                subprocess.run(cmd_mix, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                import shutil
                shutil.copy(temp_stitched, final_video_path)

        return f"/media/videos/{final_video_name}"
