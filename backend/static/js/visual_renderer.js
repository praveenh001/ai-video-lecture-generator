/**
 * 60 FPS Interactive Dynamic Visual Stage & Instructional Animation Engine
 * Synchronizes real-time visuals, algorithm state changes, code walkthroughs,
 * and math curves with neural audio playback.
 */

class LectureVisualRenderer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.currentScene = null;
    this.currentStepIdx = 0;
    this.currentSubtitle = "";
    this.animTime = 0;
    this.pulsePhase = 0;
    this.rafId = null;

    // Handle high DPI displays
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    this.startAnimationLoop();
  }

  resizeCanvas() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = (rect.width || 1280) * dpr;
    this.canvas.height = ((rect.width || 1280) * (9 / 16)) * dpr;
    this.scale = (rect.width || 1280) / 1280 * dpr;
  }

  startAnimationLoop() {
    const loop = (timestamp) => {
      this.animTime = timestamp * 0.001;
      this.pulsePhase = (Math.sin(this.animTime * 3) + 1) * 0.5;
      this.render();
      this.rafId = requestAnimationFrame(loop);
    };
    this.rafId = requestAnimationFrame(loop);
  }

  setScene(scene, currentSceneTime = 0) {
    this.currentScene = scene;
    if (!scene) return;

    const steps = scene.visual_spec?.keyframe_steps || [];
    const duration = scene.actual_duration || scene.estimated_duration || 15;

    // Compute active step based on currentSceneTime
    if (steps.length > 0) {
      const stepDuration = duration / steps.length;
      const calculatedIdx = Math.min(steps.length - 1, Math.floor(currentSceneTime / stepDuration));
      this.currentStepIdx = calculatedIdx;
    } else {
      this.currentStepIdx = 0;
    }

    // Compute active subtitle
    this.currentSubtitle = "";
    if (scene.subtitles && scene.subtitles.length > 0) {
      for (const sub of scene.subtitles) {
        if (currentSceneTime >= sub.start && currentSceneTime <= sub.end) {
          this.currentSubtitle = sub.text;
          break;
        }
      }
    }
  }

  render() {
    const ctx = this.ctx;
    const w = 1280;
    const h = 720;

    ctx.save();
    ctx.scale(this.scale, this.scale);

    // 1. Background Gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
    bgGrad.addColorStop(0, '#0a0e1a');
    bgGrad.addColorStop(1, '#131b2e');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // Subtle background grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 60) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 60) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    if (!this.currentScene) {
      // Idle screen
      this.renderIdleScreen(ctx, w, h);
      ctx.restore();
      return;
    }

    const scene = this.currentScene;
    const vspec = scene.visual_spec || {};
    const vtype = vspec.visual_type || 'diagram_board';
    const params = vspec.parameters || {};
    const steps = vspec.keyframe_steps || [];
    const activeStep = steps[this.currentStepIdx] || {};

    // 2. Header Bar
    this.renderHeader(ctx, scene, w);

    // 3. Central Visual Container
    const cX = 60, cY = 100, cW = w - 120, cH = h - 210;
    ctx.fillStyle = 'rgba(18, 24, 38, 0.85)';
    ctx.strokeStyle = 'rgba(70, 90, 135, 0.4)';
    ctx.lineWidth = 2;
    this.roundRect(ctx, cX, cY, cW, cH, 16, true, true);

    // Visual Titles
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 24px Outfit, Inter, sans-serif';
    ctx.fillText(vspec.title || 'Instructional Visualization', cX + 30, cY + 38);

    if (vspec.subtitle) {
      ctx.fillStyle = '#94a3b8';
      ctx.font = '16px Inter, sans-serif';
      ctx.fillText(vspec.subtitle, cX + 30, cY + 68);
    }

    // 4. Delegate to specialized animator
    switch (vtype) {
      case 'algorithm_animator':
        this.renderAlgorithmAnimator(ctx, params, activeStep, cX, cY, cW, cH);
        break;
      case 'code_visualizer':
        this.renderCodeVisualizer(ctx, params, activeStep, cX, cY, cW, cH);
        break;
      case 'math_graph':
        this.renderMathGraph(ctx, params, activeStep, cX, cY, cW, cH);
        break;
      case 'concept_metaphor':
        this.renderConceptMetaphor(ctx, params, activeStep, cX, cY, cW, cH);
        break;
      case 'process_simulation':
        this.renderProcessSimulation(ctx, params, activeStep, cX, cY, cW, cH);
        break;
      case 'comparison_matrix':
        this.renderComparisonMatrix(ctx, params, activeStep, cX, cY, cW, cH);
        break;
      default:
        this.renderDiagramBoard(ctx, params, activeStep, cX, cY, cW, cH);
        break;
    }

    // 5. Subtitle Pill
    this.renderSubtitles(ctx, w, h);

    ctx.restore();
  }

  renderIdleScreen(ctx, w, h) {
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 36px Outfit, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('AI Video Lecture Generator', w / 2, h / 2 - 20);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '18px Inter, sans-serif';
    ctx.fillText('Enter any topic above to create an animated, instructional masterclass.', w / 2, h / 2 + 25);
    ctx.textAlign = 'left';
  }

  renderHeader(ctx, scene, w) {
    const phase = (scene.pedagogical_phase || 'Foundation').toUpperCase();
    const colors = {
      HOOK: '#f59e0b',
      FOUNDATION: '#38bdf8',
      VISUAL_DEMONSTRATION: '#10b981',
      EDGE_CASES: '#ec4899',
      SUMMARY: '#8b5cf6'
    };
    const phaseColor = colors[phase] || '#38bdf8';

    // Badge
    ctx.fillStyle = phaseColor;
    this.roundRect(ctx, 60, 40, 160, 32, 16, true, false);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 13px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(phase.replace('_', ' '), 140, 61);
    ctx.textAlign = 'left';

    // Title
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 26px Outfit, sans-serif';
    ctx.fillText(scene.chapter_title || '', 240, 64);
  }

  // Specialized: Algorithm & Array Animator
  renderAlgorithmAnimator(ctx, params, step, cX, cY, cW, cH) {
    const arr = params.array || [2, 5, 8, 12, 16, 23, 38, 56, 72, 91];
    const target = params.target || 23;
    const stepsList = params.steps || [];

    const activeData = stepsList[this.currentStepIdx] || step;
    const low = activeData.low !== undefined ? activeData.low : 0;
    const high = activeData.high !== undefined ? activeData.high : arr.length - 1;
    const mid = activeData.mid !== undefined ? activeData.mid : Math.floor((low + high) / 2);
    const eliminated = activeData.eliminated || [];
    const matched = activeData.matched !== undefined ? activeData.matched : null;

    const actionText = activeData.decision || activeData.action || `Target = ${target} | Current Window: [${low}..${high}]`;

    // Action banner with pulsating highlight
    ctx.fillStyle = 'rgba(30, 41, 59, 0.9)';
    ctx.strokeStyle = `rgba(56, 189, 248, ${0.4 + this.pulsePhase * 0.4})`;
    ctx.lineWidth = 1.5;
    this.roundRect(ctx, cX + 30, cY + 90, cW - 60, 44, 8, true, true);

    ctx.fillStyle = '#fef08a';
    ctx.font = 'bold 15px Inter, sans-serif';
    ctx.fillText(`⚡ ACTION: ${actionText}`, cX + 45, cY + 118);

    // Draw Array Cells
    const n = arr.length;
    const startX = cX + 30;
    const availW = cW - 60;
    const cellW = Math.min(85, Math.floor((availW - (n - 1) * 10) / n));
    const cellH = 80;
    const startY = cY + 200;

    for (let i = 0; i < n; i++) {
      const cx = startX + i * (cellW + 10);
      const cy = startY;
      const isElim = eliminated.includes(i);
      const isMid = (i === mid);
      const isMatch = (i === matched);

      let bg = '#1e293b';
      let border = '#475569';
      let txtCol = '#f8fafc';

      if (isMatch) {
        bg = '#10b981';
        border = '#34d399';
        txtCol = '#ffffff';
      } else if (isMid) {
        bg = '#6366f1';
        border = '#a5b4fc';
        txtCol = '#ffffff';
      } else if (isElim) {
        bg = '#0f172a';
        border = '#1e293b';
        txtCol = '#475569';
      }

      ctx.fillStyle = bg;
      ctx.strokeStyle = border;
      ctx.lineWidth = isMid || isMatch ? 3 : 1.5;
      this.roundRect(ctx, cx, cy, cellW, cellH, 10, true, true);

      // Value
      ctx.fillStyle = txtCol;
      ctx.font = 'bold 24px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(String(arr[i]), cx + cellW / 2, cy + 50);

      // Index
      ctx.fillStyle = '#64748b';
      ctx.font = '13px Consolas, monospace';
      ctx.fillText(`[${i}]`, cx + cellW / 2, cy + cellH + 20);

      // Pointers (LOW, HIGH, MID) with floating animation
      const floatY = Math.sin(this.animTime * 4 + i) * 3;

      if (i === low && !isElim) {
        ctx.fillStyle = '#0ea5e9';
        this.roundRect(ctx, cx, cy - 35 + floatY, cellW / 2 - 2, 22, 4, true, false);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillText('L', cx + (cellW / 2 - 2) / 2, cy - 20 + floatY);
      }
      if (i === high && !isElim) {
        ctx.fillStyle = '#f43f5e';
        this.roundRect(ctx, cx + cellW / 2 + 2, cy - 35 + floatY, cellW / 2 - 2, 22, 4, true, false);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillText('H', cx + cellW / 2 + 2 + (cellW / 2 - 2) / 2, cy - 20 + floatY);
      }
      if (isMid) {
        ctx.fillStyle = '#818cf8';
        this.roundRect(ctx, cx + 5, cy - 65 + floatY, cellW - 10, 24, 6, true, false);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.fillText('MID', cx + cellW / 2, cy - 49 + floatY);
      }

      // Eliminated diagonal line
      if (isElim) {
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx + 8, cy + 8);
        ctx.lineTo(cx + cellW - 8, cy + cellH - 8);
        ctx.stroke();
      }
    }

    ctx.textAlign = 'left';

    // Summary footer
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 18px Outfit, sans-serif';
    ctx.fillText(`Target Value: ${target}`, cX + 30, cY + cH - 35);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '15px Inter, sans-serif';
    ctx.fillText(`Pointer indices: LOW = ${low}, MID = ${mid}, HIGH = ${high}`, cX + 220, cY + cH - 35);
  }

  // Specialized: Code Visualizer & Execution Pointer
  renderCodeVisualizer(ctx, params, step, cX, cY, cW, cH) {
    const code = params.code || "def solve():\n    pass";
    const lines = code.split('\n');
    const activeLine = step.active_line || 1;
    const scope = step.scope || "initial state";

    const edX = cX + 30;
    const edY = cY + 90;
    const edW = cW * 0.65;
    const edH = cH - 110;

    // Code Window
    ctx.fillStyle = '#0b0f19';
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1.5;
    this.roundRect(ctx, edX, edY, edW, edH, 10, true, true);

    // Window Dots
    ctx.fillStyle = '#ef4444';
    ctx.beginPath(); ctx.arc(edX + 20, edY + 18, 5, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath(); ctx.arc(edX + 36, edY + 18, 5, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#10b981';
    ctx.beginPath(); ctx.arc(edX + 52, edY + 18, 5, 0, Math.PI * 2); ctx.fill();

    ctx.fillStyle = '#64748b';
    ctx.font = '12px Inter, sans-serif';
    ctx.fillText('algorithm.py - Execution Tracer', edX + 75, edY + 22);

    let curY = edY + 50;
    for (let i = 0; i < Math.min(10, lines.length); i++) {
      const lineNum = i + 1;
      const isCurrent = (lineNum === activeLine);

      if (isCurrent) {
        ctx.fillStyle = 'rgba(56, 189, 248, 0.15)';
        ctx.fillRect(edX + 4, curY - 14, edW - 8, 24);

        ctx.fillStyle = '#facc15';
        ctx.font = 'bold 14px Consolas, monospace';
        ctx.fillText('▶', edX + 12, curY + 2);
      }

      ctx.fillStyle = '#64748b';
      ctx.font = '13px Consolas, monospace';
      ctx.fillText(String(lineNum).padStart(2, ' '), edX + 28, curY + 2);

      let col = '#e2e8f0';
      const text = lines[i];
      if (/def |return |while |if |elif |else:/.test(text)) col = '#c084fc';
      else if (/#/.test(text)) col = '#64748b';

      ctx.fillStyle = col;
      ctx.fillText(text, edX + 58, curY + 2);
      curY += 24;
    }

    // Side Inspector: Scope & Memory
    const insX = edX + edW + 20;
    const insW = cW - edW - 50;
    ctx.fillStyle = '#111827';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1;
    this.roundRect(ctx, insX, edY, insW, edH, 10, true, true);

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 14px Inter, sans-serif';
    ctx.fillText('VARIABLE SCOPE', insX + 16, edY + 28);

    ctx.fillStyle = '#fef08a';
    ctx.font = '13px Consolas, monospace';
    ctx.fillText(scope, insX + 16, edY + 65);
  }

  // Specialized: Math Graph & Tangent / Secant Convergence
  renderMathGraph(ctx, params, step, cX, cY, cW, cH) {
    const oX = cX + 250;
    const oY = cY + cH - 80;
    const scaleX = 55;
    const scaleY = 14;

    // Axes
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(oX - 160, oY);
    ctx.lineTo(oX + 300, oY); // X
    ctx.moveTo(oX, oY + 50);
    ctx.lineTo(oX, oY - 220); // Y
    ctx.stroke();

    ctx.fillStyle = '#94a3b8';
    ctx.font = '14px Inter, sans-serif';
    ctx.fillText('x', oX + 310, oY + 5);
    ctx.fillText('f(x)', oX - 30, oY - 225);

    // Plot Curve f(x) = x^2
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 3;
    ctx.beginPath();
    let first = true;
    for (let xi = -100; xi <= 220; xi += 4) {
      const xVal = xi / scaleX;
      const yVal = xVal * xVal;
      const px = oX + xVal * scaleX;
      const py = oY - yVal * scaleY;
      if (first) { ctx.moveTo(px, py); first = false; }
      else { ctx.lineTo(px, py); }
    }
    ctx.stroke();

    // Tangent Line at x = 2
    const x0 = 2;
    const y0 = 4;
    const px0 = oX + x0 * scaleX;
    const py0 = oY - y0 * scaleY;

    ctx.fillStyle = '#f43f5e';
    ctx.beginPath();
    ctx.arc(px0, py0, 6, 0, Math.PI * 2);
    ctx.fill();

    // Animated Tangent pivoting
    const slope = 4.0;
    ctx.strokeStyle = '#facc15';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(px0 - 80, py0 + 80 * (slope * scaleY / scaleX));
    ctx.lineTo(px0 + 80, py0 - 80 * (slope * scaleY / scaleX));
    ctx.stroke();

    // Formula Card on right
    const cardX = oX + 360;
    const cardY = cY + 90;
    const cardW = cW - (cardX - cX) - 30;
    ctx.fillStyle = '#111827';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1.5;
    this.roundRect(ctx, cardX, cardY, cardW, cH - 110, 12, true, true);

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 16px Outfit, sans-serif';
    ctx.fillText('📐 THE DERIVATIVE', cardX + 20, cardY + 35);

    ctx.fillStyle = '#fef08a';
    ctx.font = '14px Consolas, monospace';
    ctx.fillText("f'(x) = lim (h->0) [f(x+h) - f(x)] / h", cardX + 20, cardY + 70);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 22px Outfit, sans-serif';
    ctx.fillText("f'(x) = 2x", cardX + 20, cardY + 120);

    ctx.fillStyle = '#10b981';
    ctx.font = '15px Inter, sans-serif';
    ctx.fillText("At x = 2: Tangent Slope = 4.0", cardX + 20, cardY + 160);
  }

  // Specialized: Concept Metaphor
  renderConceptMetaphor(ctx, params, step, cX, cY, cW, cH) {
    const cardW = (cW - 80) / 2;
    const cardH = cH - 120;
    const cardY = cY + 90;

    const leftTitle = params.left_title || params.left_label || "Traditional / Without";
    const rightTitle = params.right_title || params.right_label || "Optimized / With Concept";
    const leftItems = params.left_items || ["High overhead", "Slow linear execution"];
    const rightItems = params.right_items || ["Exponential speed", "Divide and conquer"];

    // Left Card
    ctx.fillStyle = 'rgba(40, 20, 30, 0.7)';
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1.5;
    this.roundRect(ctx, cX + 30, cardY, cardW, cardH, 12, true, true);

    ctx.fillStyle = '#ef4444';
    ctx.font = 'bold 18px Outfit, sans-serif';
    ctx.fillText(leftTitle, cX + 50, cardY + 40);

    let lY = cardY + 80;
    for (const item of leftItems) {
      ctx.fillStyle = '#f87171';
      ctx.font = '15px Inter, sans-serif';
      ctx.fillText(`❌ ${item}`, cX + 50, lY);
      lY += 35;
    }

    // Right Card
    const rX = cX + 50 + cardW;
    ctx.fillStyle = 'rgba(20, 45, 35, 0.7)';
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1.5;
    this.roundRect(ctx, rX, cardY, cardW, cardH, 12, true, true);

    ctx.fillStyle = '#10b981';
    ctx.font = 'bold 18px Outfit, sans-serif';
    ctx.fillText(rightTitle, rX + 20, cardY + 40);

    let rY = cardY + 80;
    for (const item of rightItems) {
      ctx.fillStyle = '#34d399';
      ctx.font = '15px Inter, sans-serif';
      ctx.fillText(`✅ ${item}`, rX + 20, rY);
      rY += 35;
    }
  }

  // Specialized: Process Simulation & Energy Pulses
  renderProcessSimulation(ctx, params, step, cX, cY, cW, cH) {
    const stages = params.stages || params.components || [
      { name: "Input", role: "Incoming Event" },
      { name: "Transform", role: "Rule Execution" },
      { name: "Result", role: "Output Dispatched" }
    ];
    const n = stages.length;
    const cardW = Math.min(260, Math.floor((cW - (n + 1) * 30) / n));
    const cardH = 200;
    const cardY = cY + 110;

    for (let i = 0; i < n; i++) {
      const sX = cX + 30 + i * (cardW + 30);
      const isCur = (i === (this.currentStepIdx % n));

      ctx.fillStyle = isCur ? 'rgba(30, 58, 95, 0.9)' : 'rgba(20, 26, 40, 0.8)';
      ctx.strokeStyle = isCur ? '#38bdf8' : '#334155';
      ctx.lineWidth = isCur ? 2.5 : 1;
      this.roundRect(ctx, sX, cardY, cardW, cardH, 12, true, true);

      // Stage Tag
      ctx.fillStyle = isCur ? '#38bdf8' : '#64748b';
      ctx.font = 'bold 12px Inter, sans-serif';
      ctx.fillText(`STAGE ${i + 1}`, sX + 18, cardY + 30);

      // Name
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 18px Outfit, sans-serif';
      ctx.fillText(stages[i].name || `Stage ${i + 1}`, sX + 18, cardY + 65);

      // Role
      ctx.fillStyle = '#94a3b8';
      ctx.font = '14px Inter, sans-serif';
      ctx.fillText(stages[i].role || stages[i].desc || '', sX + 18, cardY + 105);

      // Animated energy packet between stages
      if (i < n - 1) {
        const arrowX = sX + cardW + 8;
        ctx.fillStyle = '#38bdf8';
        ctx.font = '22px sans-serif';
        ctx.fillText('➔', arrowX, cardY + cardH / 2);
      }
    }
  }

  // Specialized: Comparison Matrix
  renderComparisonMatrix(ctx, params, step, cX, cY, cW, cH) {
    const cols = [
      params.col1 || "Baseline",
      params.col2 || "Balanced",
      params.col3 || "Optimized"
    ];
    const cWidth = (cW - 80) / 3;
    const cHeight = cH - 110;
    const cardY = cY + 90;

    for (let i = 0; i < 3; i++) {
      const x = cX + 30 + i * (cWidth + 10);
      ctx.fillStyle = 'rgba(20, 26, 42, 0.85)';
      ctx.strokeStyle = (i === this.currentStepIdx % 3) ? '#38bdf8' : '#334155';
      ctx.lineWidth = 1.5;
      this.roundRect(ctx, x, cardY, cWidth, cHeight, 10, true, true);

      ctx.fillStyle = '#818cf8';
      ctx.font = 'bold 12px Inter, sans-serif';
      ctx.fillText(`COLUMN ${i + 1}`, x + 15, cardY + 30);

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 16px Outfit, sans-serif';
      const text = cols[i];
      const parts = text.split(':');
      ctx.fillText(parts[0], x + 15, cardY + 65);

      if (parts[1]) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px Inter, sans-serif';
        ctx.fillText(parts[1].trim(), x + 15, cardY + 105);
      }
    }
  }

  // Specialized: Diagram Board
  renderDiagramBoard(ctx, params, step, cX, cY, cW, cH) {
    const elements = params.elements || params.layers || ["Core Invariant", "Dynamic Transform", "Optimal Output"];
    let ey = cY + 110;
    for (const elem of elements) {
      const text = typeof elem === 'string' ? elem : (elem.name || 'Component');
      ctx.fillStyle = 'rgba(30, 41, 59, 0.8)';
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1;
      this.roundRect(ctx, cX + 40, ey, cW - 80, 50, 8, true, true);

      ctx.fillStyle = '#f8fafc';
      ctx.font = '16px Inter, sans-serif';
      ctx.fillText(`• ${text}`, cX + 60, ey + 32);
      ey += 65;
    }
  }

  renderSubtitles(ctx, w, h) {
    if (!this.currentSubtitle) return;

    ctx.font = 'bold 20px Inter, sans-serif';
    const textWidth = ctx.measureText(this.currentSubtitle).width;
    const pillW = Math.min(w - 120, textWidth + 50);
    const pillH = 46;
    const pillX = (w - pillW) / 2;
    const pillY = h - 85;

    ctx.fillStyle = 'rgba(5, 8, 16, 0.9)';
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
    ctx.lineWidth = 1;
    this.roundRect(ctx, pillX, pillY, pillW, pillH, 23, true, true);

    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText(this.currentSubtitle, w / 2, pillY + 30);
    ctx.textAlign = 'left';
  }

  roundRect(ctx, x, y, width, height, radius, fill, stroke) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    if (fill) ctx.fill();
    if (stroke) ctx.stroke();
  }
}
