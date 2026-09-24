/**
 * Main Application Orchestration Script for AI-Powered Video Lecture Generator
 */

let currentLecture = null;
let currentSceneIndex = 0;
let currentLectureTime = 0; // global seconds in lecture
let isPlaying = false;
let playbackSpeed = 1.0;
let showSubtitles = true;

// Audio elements
const sceneAudio = new Audio();
const bgMusicAudio = new Audio('/media/ambient_study.mp3');
bgMusicAudio.loop = true;
bgMusicAudio.volume = 0.08;

let visualRenderer = null;
let currentAnalysis = null;
let quizAnswers = {};
let currentCardIndex = 0;
let masteredCards = new Set();

document.addEventListener('DOMContentLoaded', () => {
  visualRenderer = new LectureVisualRenderer('interactiveCanvas');
  initEventListeners();
  loadRecentLectures();
  loadVoices();
});

function initEventListeners() {
  // Topic input & analysis
  const searchInput = document.getElementById('topicInput');
  const analyzeBtn = document.getElementById('analyzeBtn');

  analyzeBtn.addEventListener('click', () => {
    const topic = searchInput.value.trim();
    if (topic) analyzeTopic(topic);
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const topic = searchInput.value.trim();
      if (topic) analyzeTopic(topic);
    }
  });

  // Sample Topic Pills
  document.querySelectorAll('.topic-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const topic = pill.getAttribute('data-topic');
      searchInput.value = topic;
      analyzeTopic(topic);
    });
  });

  // Clarification drawer actions
  document.getElementById('startGenerateBtn').addEventListener('click', () => {
    startLectureGeneration();
  });

  document.getElementById('cancelClarificationBtn').addEventListener('click', () => {
    document.getElementById('clarificationDrawer').style.display = 'none';
  });

  // Player Controls
  const playPauseBtn = document.getElementById('playPauseBtn');
  playPauseBtn.addEventListener('click', togglePlayPause);

  document.getElementById('prevChapterBtn').addEventListener('click', jumpPrevChapter);
  document.getElementById('nextChapterBtn').addEventListener('click', jumpNextChapter);

  const speedSelect = document.getElementById('speedSelect');
  speedSelect.addEventListener('change', (e) => {
    playbackSpeed = parseFloat(e.target.value);
    sceneAudio.playbackRate = playbackSpeed;
  });

  const subtitleToggleBtn = document.getElementById('subtitleToggleBtn');
  subtitleToggleBtn.addEventListener('click', () => {
    showSubtitles = !showSubtitles;
    subtitleToggleBtn.style.color = showSubtitles ? '#38bdf8' : '#64748b';
    if (!showSubtitles && visualRenderer) {
      visualRenderer.currentSubtitle = "";
    }
  });

  const musicToggleBtn = document.getElementById('musicToggleBtn');
  musicToggleBtn.addEventListener('click', () => {
    if (bgMusicAudio.paused) {
      bgMusicAudio.play();
      musicToggleBtn.style.color = '#38bdf8';
    } else {
      bgMusicAudio.pause();
      musicToggleBtn.style.color = '#64748b';
    }
  });

  const fullscreenBtn = document.getElementById('fullscreenBtn');
  fullscreenBtn.addEventListener('click', toggleFullscreen);

  // Scrubber seeking
  const scrubber = document.getElementById('scrubberContainer');
  scrubber.addEventListener('click', onScrubberClick);

  // Mode switcher (Canvas vs Native Video)
  document.getElementById('modeCanvasBtn').addEventListener('click', () => switchPlayerMode('canvas'));
  document.getElementById('modeVideoBtn').addEventListener('click', () => switchPlayerMode('video'));

  // Audio events
  sceneAudio.addEventListener('timeupdate', onSceneAudioTimeUpdate);
  sceneAudio.addEventListener('ended', onSceneAudioEnded);

  // Keyboard shortcut (Space = Play/Pause)
  document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      togglePlayPause();
    }
  });

  // Materials Nav Tabs
  document.querySelectorAll('.mat-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mat-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.material-tab-pane').forEach(p => p.style.display = 'none');

      btn.classList.add('active');
      const targetPaneId = btn.getAttribute('data-pane');
      const pane = document.getElementById(targetPaneId);
      if (pane) pane.style.display = 'block';
    });
  });

  // Side Drawer Tabs (Transcript vs Chapters)
  document.querySelectorAll('.d-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.d-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.getAttribute('data-tab');
      document.getElementById('transcriptTab').style.display = (tab === 'transcript') ? 'flex' : 'none';
      document.getElementById('chaptersTab').style.display = (tab === 'chapters') ? 'flex' : 'none';
    });
  });

  // Flashcard flip & navigation
  const flashcardStage = document.getElementById('flashcardStage');
  if (flashcardStage) {
    flashcardStage.addEventListener('click', () => {
      const inner = document.getElementById('flashcardInner');
      inner.classList.toggle('flipped');
    });
  }

  document.getElementById('prevCardBtn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    navigateFlashcard(-1);
  });
  document.getElementById('nextCardBtn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    navigateFlashcard(1);
  });
  document.getElementById('masterCardBtn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    markFlashcardMastered();
  });

  // Download menu
  document.getElementById('downloadNotesBtn')?.addEventListener('click', downloadLectureNotes);
  document.getElementById('downloadVideoBtn')?.addEventListener('click', downloadLectureVideo);
  document.getElementById('renderVideoBtn')?.addEventListener('click', triggerVideoRender);

  // Settings Modal
  document.getElementById('settingsBtn')?.addEventListener('click', () => {
    document.getElementById('settingsModal').style.display = 'flex';
  });
  document.getElementById('closeSettingsBtn')?.addEventListener('click', () => {
    document.getElementById('settingsModal').style.display = 'none';
  });
  document.getElementById('saveSettingsBtn')?.addEventListener('click', saveSettings);
}

// ------------------- TOPIC ANALYSIS & CLARIFICATION -------------------

async function analyzeTopic(topic) {
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-sm"></span> Analyzing...`;

  try {
    const res = await fetch('/api/analyze-topic', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic,
        api_key: localStorage.getItem('gemini_api_key') || null
      })
    });

    if (!res.ok) throw new Error("Analysis failed");
    currentAnalysis = await res.json();
    renderClarificationDrawer(currentAnalysis);
  } catch (err) {
    console.error(err);
    alert("Could not analyze topic. Please try again.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `✨ Analyze Topic`;
  }
}

function renderClarificationDrawer(data) {
  document.getElementById('drawerTopicTitle').textContent = `Educational Blueprint: "${data.topic}"`;
  document.getElementById('drawerDomainBadge').textContent = (data.domain || 'General').toUpperCase();
  document.getElementById('drawerOverviewText').textContent = data.overview;

  const container = document.getElementById('questionsContainer');
  container.innerHTML = '';

  data.clarification_questions.forEach(q => {
    const block = document.createElement('div');
    block.className = 'question-block';

    const lbl = document.createElement('span');
    lbl.className = 'question-label';
    lbl.textContent = q.question;
    block.appendChild(lbl);

    const stack = document.createElement('div');
    stack.className = 'options-stack';

    q.options.forEach((opt, idx) => {
      const label = document.createElement('label');
      label.className = `option-radio-label ${opt.id === q.default_value ? 'selected' : ''}`;
      label.innerHTML = `
        <input type="radio" name="${q.id}" value="${opt.id}" ${opt.id === q.default_value ? 'checked' : ''}>
        <div>
          <strong>${opt.label.split('(')[0]}</strong>
          <span style="display:block; font-size:0.78rem; color:#94a3b8;">${opt.label.includes('(') ? '(' + opt.label.split('(')[1] : ''}</span>
        </div>
      `;
      label.querySelector('input').addEventListener('change', () => {
        stack.querySelectorAll('.option-radio-label').forEach(l => l.classList.remove('selected'));
        label.classList.add('selected');
      });
      stack.appendChild(label);
    });

    block.appendChild(stack);
    container.appendChild(block);
  });

  const drawer = document.getElementById('clarificationDrawer');
  drawer.style.display = 'block';
  drawer.scrollIntoView({ behavior: 'smooth' });
}

// ------------------- FULL LECTURE GENERATION -------------------

async function startLectureGeneration() {
  const topic = currentAnalysis ? currentAnalysis.topic : document.getElementById('topicInput').value.trim();
  if (!topic) return;

  // Collect user clarification preferences
  const knowledgeLevel = document.querySelector('input[name="knowledge_level"]:checked')?.value || 'intermediate';
  const purpose = document.querySelector('input[name="purpose"]:checked')?.value || 'interview';
  const teachingStyle = document.querySelector('input[name="teaching_style"]:checked')?.value || 'anim_sim';
  const duration = document.querySelector('input[name="lecture_duration"]:checked')?.value || 'standard';
  const voice = document.getElementById('voiceSelect')?.value || localStorage.getItem('default_voice') || 'en-US-ChristopherNeural';

  document.getElementById('clarificationDrawer').style.display = 'none';
  showProgressOverlay();

  try {
    updateProgressStep(1);
    const res = await fetch('/api/generate-lecture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic,
        knowledge_level: knowledgeLevel,
        purpose: purpose,
        teaching_style: teachingStyle,
        lecture_duration: duration,
        voice_name: voice,
        api_key: localStorage.getItem('gemini_api_key') || null
      })
    });

    if (!res.ok) throw new Error("Generation failed");
    updateProgressStep(3);
    const lecture = await res.json();
    updateProgressStep(5);

    setTimeout(() => {
      hideProgressOverlay();
      loadLectureIntoWorkspace(lecture);
      loadRecentLectures();
    }, 600);

  } catch (err) {
    console.error(err);
    hideProgressOverlay();
    alert("Generation encountered an error: " + err.message);
  }
}

function showProgressOverlay() {
  document.getElementById('progressOverlay').style.display = 'block';
  document.getElementById('progressOverlay').scrollIntoView({ behavior: 'smooth' });
}

function hideProgressOverlay() {
  document.getElementById('progressOverlay').style.display = 'none';
}

function updateProgressStep(stepNum) {
  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`pStep${i}`);
    if (!el) continue;
    if (i < stepNum) {
      el.className = 'step-row completed';
      el.querySelector('.step-icon').textContent = '✅';
    } else if (i === stepNum) {
      el.className = 'step-row active';
      el.querySelector('.step-icon').textContent = '⏳';
    } else {
      el.className = 'step-row';
      el.querySelector('.step-icon').textContent = '○';
    }
  }
}

// ------------------- WORKSPACE & CINEMA PLAYER -------------------

function loadLectureIntoWorkspace(lecture) {
  currentLecture = lecture;
  currentSceneIndex = 0;
  currentLectureTime = 0;
  isPlaying = false;

  // Header info
  document.getElementById('lectureMainTitle').textContent = lecture.title;
  document.getElementById('lectureTopicMeta').textContent = `Topic: ${lecture.topic}`;
  document.getElementById('lectureDomainMeta').textContent = (lecture.domain || 'general').toUpperCase();
  document.getElementById('lectureLevelMeta').textContent = lecture.knowledge_level;
  document.getElementById('totalDurationDisplay').textContent = formatTime(lecture.total_duration);

  // Render chapters and transcript
  renderChaptersList(lecture.scenes);
  renderTranscriptList(lecture.scenes);
  renderChapterTicksOnScrubber(lecture.scenes, lecture.total_duration);

  // Populate materials
  renderMaterials(lecture.materials);
  renderSceneStudio(lecture.scenes);

  // Setup first scene
  loadScene(0, false);

  // Setup native video player if video already rendered
  const nativePlayer = document.getElementById('nativeVideoPlayer');
  if (lecture.video_url) {
    nativePlayer.src = lecture.video_url;
    document.getElementById('renderVideoBtn').textContent = "✓ MP4 Video Ready";
  } else {
    nativePlayer.removeAttribute('src');
    document.getElementById('renderVideoBtn').textContent = "🎬 Render MP4 Video";
  }

  // Show workspace
  const workspace = document.getElementById('cinemaWorkspace');
  workspace.style.display = 'block';
  workspace.scrollIntoView({ behavior: 'smooth' });
}

function loadScene(index, autoPlay = true) {
  if (!currentLecture || index < 0 || index >= currentLecture.scenes.length) return;
  currentSceneIndex = index;
  const scene = currentLecture.scenes[index];

  // Set audio source
  sceneAudio.src = scene.audio_url;
  sceneAudio.playbackRate = playbackSpeed;

  // Update canvas
  if (visualRenderer) {
    visualRenderer.setScene(scene, 0);
  }

  // Highlight chapter and transcript
  highlightActiveChapter(index);

  if (autoPlay) {
    sceneAudio.play().then(() => {
      isPlaying = true;
      updatePlayPauseIcon();
      if (bgMusicAudio.paused) bgMusicAudio.play();
    }).catch(e => console.warn(e));
  } else {
    isPlaying = false;
    updatePlayPauseIcon();
  }
}

function togglePlayPause() {
  if (!currentLecture) return;
  if (isPlaying) {
    sceneAudio.pause();
    bgMusicAudio.pause();
    isPlaying = false;
  } else {
    sceneAudio.play().then(() => {
      isPlaying = true;
      bgMusicAudio.play();
    }).catch(e => console.warn(e));
  }
  updatePlayPauseIcon();
}

function updatePlayPauseIcon() {
  const btn = document.getElementById('playPauseBtn');
  btn.textContent = isPlaying ? '⏸' : '▶';
}

function onSceneAudioTimeUpdate() {
  if (!currentLecture || !currentLecture.scenes[currentSceneIndex]) return;

  const sceneTime = sceneAudio.currentTime;
  const scene = currentLecture.scenes[currentSceneIndex];

  // Compute global lecture time
  let precedingDuration = 0;
  for (let i = 0; i < currentSceneIndex; i++) {
    precedingDuration += currentLecture.scenes[i].actual_duration || currentLecture.scenes[i].estimated_duration || 15;
  }
  currentLectureTime = precedingDuration + sceneTime;

  // Update time display
  document.getElementById('currentTimeDisplay').textContent = formatTime(currentLectureTime);

  // Update scrubber fill
  const total = currentLecture.total_duration || 1;
  const pct = Math.min(100, (currentLectureTime / total) * 100);
  document.getElementById('scrubberFill').style.width = `${pct}%`;

  // Update Visual Renderer with current scene time
  if (visualRenderer) {
    visualRenderer.setScene(scene, sceneTime);
  }

  // Update transcript cue highlight
  highlightActiveTranscriptCue(currentLectureTime);
}

function onSceneAudioEnded() {
  if (!currentLecture) return;
  if (currentSceneIndex < currentLecture.scenes.length - 1) {
    loadScene(currentSceneIndex + 1, true);
  } else {
    // Finished lecture
    isPlaying = false;
    updatePlayPauseIcon();
    bgMusicAudio.pause();
  }
}

function onScrubberClick(e) {
  if (!currentLecture || !currentLecture.total_duration) return;
  const rect = e.currentTarget.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const ratio = Math.max(0, Math.min(1, clickX / rect.width));
  const targetTime = ratio * currentLecture.total_duration;
  seekToGlobalTime(targetTime);
}

function seekToGlobalTime(targetTime) {
  if (!currentLecture) return;
  let accumulated = 0;
  for (let i = 0; i < currentLecture.scenes.length; i++) {
    const sc = currentLecture.scenes[i];
    const dur = sc.actual_duration || sc.estimated_duration || 15;
    if (targetTime <= accumulated + dur || i === currentLecture.scenes.length - 1) {
      const sceneOffset = Math.max(0, targetTime - accumulated);
      if (currentSceneIndex !== i) {
        currentSceneIndex = i;
        sceneAudio.src = sc.audio_url;
      }
      sceneAudio.currentTime = sceneOffset;
      if (isPlaying) sceneAudio.play();
      highlightActiveChapter(i);
      return;
    }
    accumulated += dur;
  }
}

function jumpPrevChapter() {
  if (currentSceneIndex > 0) loadScene(currentSceneIndex - 1, isPlaying);
}

function jumpNextChapter() {
  if (currentLecture && currentSceneIndex < currentLecture.scenes.length - 1) {
    loadScene(currentSceneIndex + 1, isPlaying);
  }
}

function switchPlayerMode(mode) {
  const canvas = document.getElementById('interactiveCanvas');
  const video = document.getElementById('nativeVideoPlayer');
  const btnC = document.getElementById('modeCanvasBtn');
  const btnV = document.getElementById('modeVideoBtn');

  if (mode === 'canvas') {
    canvas.style.display = 'block';
    video.style.display = 'none';
    video.pause();
    btnC.classList.add('active');
    btnV.classList.remove('active');
  } else {
    canvas.style.display = 'none';
    video.style.display = 'block';
    sceneAudio.pause();
    isPlaying = false;
    updatePlayPauseIcon();
    btnC.classList.remove('active');
    btnV.classList.add('active');
    if (currentLecture && currentLecture.video_url && !video.src) {
      video.src = currentLecture.video_url;
    }
  }
}

function toggleFullscreen() {
  const elem = document.getElementById('cinemaPlayer');
  if (!document.fullscreenElement) {
    elem.requestFullscreen().catch(err => alert(err.message));
  } else {
    document.exitFullscreen();
  }
}

// ------------------- SIDE DRAWER (CHAPTERS & TRANSCRIPT) -------------------

function renderChaptersList(scenes) {
  const list = document.getElementById('chaptersList');
  list.innerHTML = '';

  let cumTime = 0;
  scenes.forEach((sc, idx) => {
    const item = document.createElement('div');
    item.className = `chapter-item ${idx === 0 ? 'active-chapter' : ''}`;
    item.id = `chapItem_${idx}`;

    const dur = sc.actual_duration || sc.estimated_duration || 15;
    item.innerHTML = `
      <div class="chap-info">
        <h4>${sc.chapter_title}</h4>
        <span>${formatTime(cumTime)} • ${sc.pedagogical_phase.toUpperCase()}</span>
      </div>
      <span style="font-size:0.85rem; color:#38bdf8;">${formatTime(dur)}</span>
    `;

    const targetTime = cumTime;
    item.addEventListener('click', () => {
      seekToGlobalTime(targetTime);
    });

    list.appendChild(item);
    cumTime += dur;
  });
}

function highlightActiveChapter(activeIdx) {
  document.querySelectorAll('.chapter-item').forEach((it, idx) => {
    if (idx === activeIdx) it.classList.add('active-chapter');
    else it.classList.remove('active-chapter');
  });
}

function renderTranscriptList(scenes) {
  const list = document.getElementById('transcriptList');
  list.innerHTML = '';

  let cumTime = 0;
  scenes.forEach((sc, sIdx) => {
    if (sc.subtitles && sc.subtitles.length > 0) {
      sc.subtitles.forEach((sub, subIdx) => {
        const cue = document.createElement('div');
        cue.className = 'transcript-cue';
        cue.setAttribute('data-time', cumTime + sub.start);
        cue.id = `cue_${sIdx}_${subIdx}`;
        cue.innerHTML = `
          <span class="cue-timestamp">${formatTime(cumTime + sub.start)}</span>
          <p>${sub.text}</p>
        `;
        cue.addEventListener('click', () => {
          seekToGlobalTime(cumTime + sub.start);
        });
        list.appendChild(cue);
      });
    } else {
      const cue = document.createElement('div');
      cue.className = 'transcript-cue';
      cue.setAttribute('data-time', cumTime);
      cue.innerHTML = `
        <span class="cue-timestamp">${formatTime(cumTime)}</span>
        <p>${sc.narration_text}</p>
      `;
      cue.addEventListener('click', () => seekToGlobalTime(cumTime));
      list.appendChild(cue);
    }
    cumTime += sc.actual_duration || sc.estimated_duration || 15;
  });
}

function highlightActiveTranscriptCue(currentTime) {
  const cues = document.querySelectorAll('.transcript-cue');
  let activeCue = null;
  cues.forEach(cue => {
    const t = parseFloat(cue.getAttribute('data-time'));
    if (t <= currentTime + 0.5) {
      activeCue = cue;
    }
  });

  cues.forEach(c => c.classList.remove('active-cue'));
  if (activeCue) {
    activeCue.classList.add('active-cue');
    // Smooth auto scroll within transcript list
    activeCue.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function renderChapterTicksOnScrubber(scenes, totalDuration) {
  const layer = document.getElementById('chapterTicksLayer');
  layer.innerHTML = '';
  if (!totalDuration) return;

  let cumTime = 0;
  scenes.forEach(sc => {
    const pct = (cumTime / totalDuration) * 100;
    if (pct > 0 && pct < 100) {
      const tick = document.createElement('div');
      tick.className = 'chapter-tick';
      tick.style.left = `${pct}%`;
      layer.appendChild(tick);
    }
    cumTime += sc.actual_duration || sc.estimated_duration || 15;
  });
}

// ------------------- LEARNING MATERIALS HUB -------------------

function renderMaterials(materials) {
  if (!materials) return;

  // 1. Lecture Notes (Markdown to HTML)
  const notesContainer = document.getElementById('notesContent');
  if (materials.notes_markdown) {
    notesContainer.innerHTML = formatSimpleMarkdown(materials.notes_markdown);
  }

  // 2. Key Concepts
  const conceptsContainer = document.getElementById('conceptsContainer');
  conceptsContainer.innerHTML = '';
  (materials.key_concepts || []).forEach(kc => {
    const card = document.createElement('div');
    card.className = 'concept-card';
    card.innerHTML = `
      <h4>${kc.concept}</h4>
      <p>${kc.definition}</p>
      <span class="importance-badge">💡 ${kc.importance}</span>
    `;
    conceptsContainer.appendChild(card);
  });

  // 3. Interactive Quiz
  const quizContainer = document.getElementById('quizContainer');
  quizContainer.innerHTML = '';
  quizAnswers = {};
  (materials.quiz || []).forEach((q, qIdx) => {
    const card = document.createElement('div');
    card.className = 'quiz-card';
    card.id = `quizCard_${q.id}`;

    let optsHtml = '';
    q.options.forEach((opt, oIdx) => {
      optsHtml += `
        <button class="quiz-option-btn" data-qid="${q.id}" data-oidx="${oIdx}">
          ${String.fromCharCode(65 + oIdx)}. ${opt}
        </button>
      `;
    });

    card.innerHTML = `
      <div class="quiz-question-num">Question ${qIdx + 1} of ${materials.quiz.length}</div>
      <div class="quiz-question-text">${q.question}</div>
      <div class="quiz-options-list">${optsHtml}</div>
      <div class="quiz-explanation-box" id="exp_${q.id}" style="display:none;"></div>
    `;

    card.querySelectorAll('.quiz-option-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        onQuizOptionSelected(q, parseInt(btn.getAttribute('data-oidx')), card);
      });
    });

    quizContainer.appendChild(card);
  });

  // 4. Flashcards
  currentCardIndex = 0;
  masteredCards.clear();
  renderCurrentFlashcard();

  // 5. Practice Questions
  const practiceContainer = document.getElementById('practiceContainer');
  practiceContainer.innerHTML = '';
  (materials.practice_questions || []).forEach((pq, pIdx) => {
    const block = document.createElement('div');
    block.className = 'concept-card';
    block.innerHTML = `
      <h4 style="color:#ffffff;">Problem ${pIdx + 1}: ${pq.question}</h4>
      <p style="color:#fef08a;">💡 Hint: ${pq.hint}</p>
      <details style="margin-top:0.8rem; cursor:pointer;">
        <summary style="color:#38bdf8; font-weight:600;">View Step-by-Step Solution</summary>
        <div style="background:#070a12; padding:1rem; border-radius:6px; margin-top:0.5rem; font-size:0.9rem;">
          ${pq.solution}
        </div>
      </details>
    `;
    practiceContainer.appendChild(block);
  });
}

function onQuizOptionSelected(questionObj, chosenIdx, cardElem) {
  const isCorrect = (chosenIdx === questionObj.correct_index);
  const btns = cardElem.querySelectorAll('.quiz-option-btn');

  btns.forEach((b, idx) => {
    b.disabled = true;
    if (idx === questionObj.correct_index) {
      b.classList.add('correct');
    } else if (idx === chosenIdx && !isCorrect) {
      b.classList.add('wrong');
    }
  });

  const expBox = cardElem.querySelector('.quiz-explanation-box');
  expBox.style.display = 'block';
  expBox.innerHTML = `
    <strong>${isCorrect ? '✅ Correct!' : '❌ Incorrect'}</strong>
    <p style="margin-top:0.4rem;">${questionObj.explanation}</p>
  `;
}

function renderCurrentFlashcard() {
  const cards = currentLecture?.materials?.flashcards || [];
  if (!cards.length) return;

  const card = cards[currentCardIndex];
  document.getElementById('cardCategory').textContent = card.category;
  document.getElementById('cardFrontText').textContent = card.front;
  document.getElementById('cardBackText').textContent = card.back;
  document.getElementById('cardProgressDisplay').textContent = `Card ${currentCardIndex + 1} of ${cards.length}`;

  const inner = document.getElementById('flashcardInner');
  inner.classList.remove('flipped');
}

function navigateFlashcard(delta) {
  const cards = currentLecture?.materials?.flashcards || [];
  if (!cards.length) return;
  currentCardIndex = (currentCardIndex + delta + cards.length) % cards.length;
  renderCurrentFlashcard();
}

function markFlashcardMastered() {
  masteredCards.add(currentCardIndex);
  document.getElementById('masteredCountDisplay').textContent = `Mastered: ${masteredCards.size}`;
  navigateFlashcard(1);
}

// ------------------- SCENE STUDIO & REGENERATION -------------------

function renderSceneStudio(scenes) {
  const container = document.getElementById('scenesStudioList');
  container.innerHTML = '';

  scenes.forEach((sc, idx) => {
    const card = document.createElement('div');
    card.className = 'scene-card-item';
    card.innerHTML = `
      <div class="scene-header-row">
        <span class="scene-num-badge">SCENE ${idx + 1}</span>
        <h4 style="flex:1; margin-left:1rem; font-size:1.05rem;">${sc.chapter_title}</h4>
        <span class="badge-tag" style="color:#38bdf8;">${sc.visual_spec.visual_type}</span>
      </div>
      <div class="scene-script-box">
        <strong>Narration Script:</strong>
        <p style="margin-top:0.3rem; color:#cbd5e1;">${sc.narration_text}</p>
      </div>
      <div class="scene-meta-row">
        <span>Duration: ${formatTime(sc.actual_duration || sc.estimated_duration)}</span>
        <button class="btn-secondary" onclick="openSceneEditModal(${idx})" style="padding:0.4rem 0.8rem; font-size:0.8rem;">
          ✏️ Edit & Regenerate Scene
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

function openSceneEditModal(sceneIndex) {
  const sc = currentLecture.scenes[sceneIndex];
  document.getElementById('editSceneIndex').value = sceneIndex;
  document.getElementById('editSceneTitle').value = sc.chapter_title;
  document.getElementById('editSceneNarration').value = sc.narration_text;
  document.getElementById('editSceneVisualType').value = sc.visual_spec.visual_type;
  document.getElementById('sceneEditModal').style.display = 'flex';
}

document.getElementById('closeSceneEditBtn')?.addEventListener('click', () => {
  document.getElementById('sceneEditModal').style.display = 'none';
});

document.getElementById('submitRegenerateSceneBtn')?.addEventListener('click', async () => {
  const idx = parseInt(document.getElementById('editSceneIndex').value);
  const title = document.getElementById('editSceneTitle').value;
  const script = document.getElementById('editSceneNarration').value;
  const vtype = document.getElementById('editSceneVisualType').value;

  const btn = document.getElementById('submitRegenerateSceneBtn');
  btn.disabled = true;
  btn.textContent = "Regenerating...";

  try {
    const res = await fetch(`/api/lectures/${currentLecture.id}/scenes/${idx}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scene_index: idx,
        chapter_title: title,
        narration_text: script,
        visual_type: vtype,
        voice_name: currentLecture.voice_name
      })
    });

    if (!res.ok) throw new Error("Scene regeneration failed");
    const updatedLecture = await res.json();
    document.getElementById('sceneEditModal').style.display = 'none';
    loadLectureIntoWorkspace(updatedLecture);
    alert(`Scene ${idx + 1} successfully regenerated and synchronized!`);
  } catch (err) {
    console.error(err);
    alert("Could not regenerate scene: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Regenerate Scene";
  }
});

// ------------------- DOWNLOADS & RENDERING -------------------

async function triggerVideoRender() {
  if (!currentLecture) return;
  const btn = document.getElementById('renderVideoBtn');
  btn.disabled = true;
  btn.textContent = "⏳ Rendering MP4 Video (FFmpeg)...";

  try {
    const res = await fetch(`/api/lectures/${currentLecture.id}/render-video`, { method: 'POST' });
    const data = await res.json();
    if (data.video_url) {
      currentLecture.video_url = data.video_url;
      document.getElementById('nativeVideoPlayer').src = data.video_url;
      btn.textContent = "✓ MP4 Video Ready";
      alert("MP4 Video successfully rendered! You can now watch it or download the video file.");
    }
  } catch (err) {
    console.error(err);
    alert("Video rendering encountered an error: " + err.message);
  } finally {
    btn.disabled = false;
  }
}

function downloadLectureVideo() {
  if (!currentLecture) return;
  if (currentLecture.video_url) {
    const a = document.createElement('a');
    a.href = currentLecture.video_url;
    a.download = `${currentLecture.topic}_lecture.mp4`;
    a.click();
  } else {
    if (confirm("The MP4 video has not been rendered on the server yet. Would you like to render it now?")) {
      triggerVideoRender();
    }
  }
}

function downloadLectureNotes() {
  if (!currentLecture || !currentLecture.materials) return;
  const md = currentLecture.materials.notes_markdown || `# ${currentLecture.title}`;
  const blob = new Blob([md], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentLecture.topic}_notes.md`;
  a.click();
  URL.revokeObjectURL(url);
}

// ------------------- RECENT LECTURES & VOICES -------------------

async function loadRecentLectures() {
  try {
    const res = await fetch('/api/lectures');
    const lectures = await res.json();
    const container = document.getElementById('recentLecturesList');
    if (!container) return;
    container.innerHTML = '';

    lectures.slice(0, 5).forEach(l => {
      const item = document.createElement('div');
      item.className = 'chapter-item';
      item.innerHTML = `
        <div class="chap-info">
          <h4>${l.title}</h4>
          <span>${l.created_at} • ${formatTime(l.total_duration)}</span>
        </div>
        <button class="btn-secondary" style="padding:0.35rem 0.7rem; font-size:0.75rem;">Open</button>
      `;
      item.addEventListener('click', async () => {
        const fullRes = await fetch(`/api/lectures/${l.id}`);
        const fullLec = await fullRes.json();
        loadLectureIntoWorkspace(fullLec);
      });
      container.appendChild(item);
    });
  } catch (e) {
    console.warn(e);
  }
}

async function loadVoices() {
  try {
    const res = await fetch('/api/voices');
    const voices = await res.json();
    const select = document.getElementById('voiceSelect');
    if (!select) return;
    select.innerHTML = '';
    voices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = v.name;
      select.appendChild(opt);
    });
  } catch (e) {
    console.warn(e);
  }
}

function saveSettings() {
  const geminiKey = document.getElementById('settingGeminiKey').value.trim();
  if (geminiKey) localStorage.setItem('gemini_api_key', geminiKey);
  const defVoice = document.getElementById('settingVoiceSelect').value;
  if (defVoice) localStorage.setItem('default_voice', defVoice);
  document.getElementById('settingsModal').style.display = 'none';
  alert("Settings saved successfully!");
}

// ------------------- UTILITIES -------------------

function formatTime(seconds) {
  if (isNaN(seconds)) return "00:00";
  const s = Math.floor(seconds);
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function formatSimpleMarkdown(md) {
  return md
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
    .replace(/\n\n/gim, '<br/><br/>');
}
