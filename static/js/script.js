const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelector(".nav-links");

if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
        const isOpen = navLinks.classList.toggle("is-open");
        navToggle.setAttribute("aria-expanded", String(isOpen));
    });
}

const lessonDataNode = document.getElementById("lesson-data");
const trainer = document.querySelector("[data-trainer]");
const csrfToken = document.querySelector("meta[name='csrf-token']")?.getAttribute("content") || "";

function postJson(url, payload) {
    return fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(payload),
    }).catch(() => null);
}

if (lessonDataNode && trainer) {
    const lessons = JSON.parse(lessonDataNode.textContent);
    const lessonSelect = document.querySelector("[data-lesson-select]");
    const elements = {
        lessonLabel: trainer.querySelector("[data-lesson-label]"),
        lessonTitle: trainer.querySelector("[data-lesson-title]"),
        lessonCategory: trainer.querySelector("[data-lesson-category]"),
        lessonDifficulty: trainer.querySelector("[data-lesson-difficulty]"),
        currentStep: trainer.querySelector("[data-current-step]"),
        totalSteps: trainer.querySelector("[data-total-steps]"),
        remaining: trainer.querySelector("[data-remaining]"),
        overallBar: trainer.querySelector("[data-overall-bar]"),
        courseProgress: trainer.querySelector("[data-course-progress]"),
        courseBar: trainer.querySelector("[data-course-bar]"),
        unlockNote: trainer.querySelector("[data-unlock-note]"),
        xp: trainer.querySelector("[data-xp]"),
        eta: trainer.querySelector("[data-eta]"),
        accuracy: trainer.querySelector("[data-accuracy]"),
        streak: trainer.querySelector("[data-streak]"),
        lives: trainer.querySelector("[data-lives]"),
        shortcutLabel: trainer.querySelector("[data-shortcut-label]"),
        action: trainer.querySelector("[data-action]"),
        purpose: trainer.querySelector("[data-purpose]"),
        target: trainer.querySelector("[data-target]"),
        feedback: trainer.querySelector("[data-feedback]"),
        status: trainer.querySelector("[data-status]"),
        start: trainer.querySelector("[data-start]"),
        skip: trainer.querySelector("[data-skip]"),
        reset: trainer.querySelector("[data-reset]"),
        completion: trainer.querySelector("[data-completion]"),
        finalXp: trainer.querySelector("[data-final-xp]"),
        finalAccuracy: trainer.querySelector("[data-final-accuracy]"),
        finalSpeed: trainer.querySelector("[data-final-speed]"),
        finalTime: trainer.querySelector("[data-final-time]"),
        weakAreas: trainer.querySelector("[data-weak-areas]"),
        startQuiz: trainer.querySelector("[data-start-quiz]"),
        nextLesson: trainer.querySelector("[data-next-lesson]"),
        quiz: trainer.querySelector("[data-quiz]"),
        quizLabel: trainer.querySelector("[data-quiz-label]"),
        quizTask: trainer.querySelector("[data-quiz-task]"),
        quizTarget: trainer.querySelector("[data-quiz-target]"),
        quizFeedback: trainer.querySelector("[data-quiz-feedback]"),
        quizScore: trainer.querySelector("[data-quiz-score]"),
        quizAccuracy: trainer.querySelector("[data-quiz-accuracy]"),
        quizReaction: trainer.querySelector("[data-quiz-reaction]"),
        quizWrong: trainer.querySelector("[data-quiz-wrong]"),
        retryQuiz: trainer.querySelector("[data-retry-quiz]"),
        nextLessonQuiz: trainer.querySelector("[data-next-lesson-quiz]"),
    };

    let unlockedLessonIndex = 0;
    let completedShortcutTotal = 0;
    let state = createState(0);

    function createState(lessonIndex) {
        return {
            mode: "idle",
            lessonIndex,
            shortcutIndex: 0,
            quizIndex: 0,
            correct: 0,
            attempts: 0,
            streak: 0,
            lives: 3,
            xp: 0,
            startedAt: null,
            shortcutStartedAt: null,
            speeds: [],
            weakAreas: [],
            quizCorrect: 0,
            quizAttempts: 0,
            quizWrong: 0,
            quizStartedAt: null,
            quizTaskStartedAt: null,
            quizReactionTimes: [],
            practiceSaved: false,
            quizSaved: false,
        };
    }

    function highlightExpectedKeys(keys) {
        document.querySelectorAll(".key-cap").forEach((cap) => {
            cap.classList.remove("is-expected");
        });
        if (!keys) return;
        keys.forEach((key) => {
            const cleanKey = key.trim().toLowerCase();
            const cap = document.querySelector(`.key-cap[data-key="${cleanKey}"]`);
            if (cap) cap.classList.add("is-expected");
        });
    }

    function handleVisualKeydown(event) {
        let key = event.key.toLowerCase();
        if (key === " ") key = "space";
        
        if (event.ctrlKey) highlightPressed("control");
        if (event.altKey) highlightPressed("alt");
        if (event.shiftKey) highlightPressed("shift");
        if (event.metaKey) highlightPressed("meta");
        
        highlightPressed(key);
    }

    function handleVisualKeyup(event) {
        let key = event.key.toLowerCase();
        if (key === " ") key = "space";
        
        removePressed(key);
        if (!event.ctrlKey) removePressed("control");
        if (!event.altKey) removePressed("alt");
        if (!event.shiftKey) removePressed("shift");
        if (!event.metaKey) removePressed("meta");
    }

    function highlightPressed(key) {
        const cap = document.querySelector(`.key-cap[data-key="${key}"]`);
        if (cap) cap.classList.add("is-pressed");
    }

    function removePressed(key) {
        const cap = document.querySelector(`.key-cap[data-key="${key}"]`);
        if (cap) cap.classList.remove("is-pressed");
    }

    function currentLesson() {
        return lessons[state.lessonIndex];
    }

    function currentShortcut() {
        return currentLesson().shortcuts[state.shortcutIndex];
    }

    function currentQuizShortcut() {
        return currentLesson().shortcuts[state.quizIndex];
    }

    function totalCourseShortcuts() {
        return lessons.reduce((sum, lesson) => sum + lesson.shortcuts.length, 0);
    }

    function completedInCurrentLesson() {
        if (state.mode === "complete" || state.mode === "quiz" || state.mode === "quiz_result") return currentLesson().shortcuts.length;
        return state.shortcutIndex;
    }

    function renderLessonShell() {
        const lesson = currentLesson();
        elements.lessonLabel.textContent = `Lesson ${lesson.id} of ${lessons.length}`;
        elements.lessonTitle.textContent = lesson.title;
        elements.lessonCategory.textContent = lesson.category;
        elements.lessonDifficulty.textContent = lesson.difficulty;
        elements.totalSteps.textContent = String(lesson.shortcuts.length);
        renderProgress();
    }

    function renderCourseProgress() {
        const lessonCompleted = completedInCurrentLesson();
        const previousLessons = lessons
            .slice(0, state.lessonIndex)
            .reduce((sum, lesson) => sum + lesson.shortcuts.length, 0);
        const completed = Math.max(completedShortcutTotal, previousLessons + lessonCompleted);
        const progress = Math.min(100, Math.round((completed / totalCourseShortcuts()) * 100));
        elements.courseProgress.textContent = String(progress);
        elements.courseBar.style.width = `${progress}%`;
        elements.unlockNote.textContent =
            state.lessonIndex <= unlockedLessonIndex
                ? "This lesson is unlocked. Finish practice and quiz to unlock the next one."
                : "This lesson is previewable in the MVP, but unlocks after earlier lessons in production.";
    }

    function renderProgress() {
        const lesson = currentLesson();
        const total = lesson.shortcuts.length;
        const completed = completedInCurrentLesson();
        const progress = total ? Math.round((completed / total) * 100) : 0;
        const accuracy = state.attempts ? Math.round((state.correct / state.attempts) * 100) : 0;
        const remainingShortcuts = Math.max(total - completed, 0);
        const estimatedRemaining = state.mode === "idle"
            ? lesson.duration
            : Math.max(state.mode === "complete" || state.mode === "quiz_result" ? 0 : 1, Math.ceil((remainingShortcuts / Math.max(total, 1)) * lesson.duration));

        elements.currentStep.textContent = String(Math.min(state.shortcutIndex + 1, total));
        elements.remaining.textContent = String(remainingShortcuts);
        elements.overallBar.style.width = `${progress}%`;
        elements.xp.textContent = String(state.xp);
        elements.eta.textContent = `${estimatedRemaining} min`;
        elements.accuracy.textContent = `${accuracy}%`;
        elements.streak.textContent = String(state.streak);
        elements.lives.textContent = "❤️".repeat(Math.max(0, state.lives)) || "💔";
        elements.shortcutLabel.textContent = `Shortcut ${Math.min(state.shortcutIndex + 1, total)} of ${total}`;
        renderCourseProgress();
    }

    function renderShortcut() {
        const shortcut = currentShortcut();
        elements.action.textContent = shortcut.name;
        elements.purpose.textContent = `${shortcut.purpose} ${shortcut.when}`;
        elements.target.innerHTML = shortcut.combo.map((key) => `<kbd>${key}</kbd>`).join("");
        elements.feedback.textContent = "Press the shortcut on your keyboard.";
        elements.feedback.className = "trainer-feedback";
        elements.status.textContent = "Listening";
        state.shortcutStartedAt = Date.now();
        highlightExpectedKeys(shortcut.keys);
        renderProgress();
    }

    function resetLesson(lessonIndex = state.lessonIndex) {
        state = createState(lessonIndex);
        renderLessonShell();
        elements.action.textContent = "Ready to train";
        elements.purpose.textContent = "Click Start Lesson, then press the displayed shortcut.";
        elements.target.innerHTML = "<kbd>Start Lesson</kbd>";
        elements.feedback.textContent = "Your shortcut challenge will appear here.";
        elements.feedback.className = "trainer-feedback";
        elements.status.textContent = "Idle";
        elements.start.textContent = "Start Lesson";
        elements.start.disabled = false;
        elements.skip.disabled = true;
        elements.reset.disabled = true;
        elements.completion.hidden = true;
        elements.quiz.hidden = true;
        elements.startQuiz.disabled = false;
        elements.nextLesson.disabled = false;
        elements.retryQuiz.disabled = true;
        elements.nextLessonQuiz.disabled = true;
    }

    function normalizeEvent(event) {
        const keys = [];
        if (event.ctrlKey) keys.push("control");
        if (event.altKey) keys.push("alt");
        if (event.shiftKey) keys.push("shift");
        if (event.metaKey) keys.push("meta");

        let key = event.key.toLowerCase();
        if (key === " ") key = "space";
        if (!["control", "alt", "shift", "meta"].includes(key)) {
            keys.push(key);
        }
        return keys;
    }

    function arraysMatch(first, second) {
        return first.length === second.length && second.every((key) => first.includes(key));
    }

    function isPracticeCapturing() {
        return state.mode === "lesson" || state.mode === "quiz";
    }

    function quizTaskFor(shortcut) {
        const tasks = {
            "Copy": "Copy selected text.",
            "Paste": "Paste copied content.",
            "Cut": "Cut selected content.",
            "Undo": "Undo the last action.",
            "Redo": "Redo the last undone action.",
            "Find": "Find text in the current page or document.",
            "Replace": "Replace repeated text.",
            "Select All": "Select all content.",
            "Save": "Save the active document.",
            "New Tab": "Open a new tab.",
            "Reopen Closed Tab": "Reopen the tab you just closed.",
            "History": "Open browsing history.",
            "Downloads": "Open downloads.",
            "Bookmark Page": "Bookmark the current page.",
            "Open Recent File": "Open a file by name.",
        };
        return shortcut.task || tasks[shortcut.name] || shortcut.purpose;
    }

    function moveNext() {
        const lesson = currentLesson();
        if (state.shortcutIndex >= lesson.shortcuts.length - 1) {
            finishLesson();
            return;
        }
        state.shortcutIndex += 1;
        renderShortcut();
    }

    function finishLesson() {
        if (state.mode === "complete") return;
        state.mode = "complete";
        const totalTime = Math.max(1, Math.round((Date.now() - state.startedAt) / 1000));
        const averageSpeed = state.speeds.length
            ? Math.round(state.speeds.reduce((sum, value) => sum + value, 0) / state.speeds.length)
            : 0;
        const accuracy = state.attempts ? Math.round((state.correct / state.attempts) * 100) : 0;

        completedShortcutTotal = Math.max(
            completedShortcutTotal,
            lessons.slice(0, state.lessonIndex).reduce((sum, lesson) => sum + lesson.shortcuts.length, 0) + currentLesson().shortcuts.length
        );

        elements.status.textContent = "Complete";
        elements.feedback.textContent = "Lesson complete. Start the practical quiz when ready.";
        elements.start.disabled = true;
        elements.skip.disabled = true;
        elements.finalXp.textContent = String(state.xp);
        elements.finalAccuracy.textContent = `${accuracy}%`;
        elements.finalSpeed.textContent = `${averageSpeed}s`;
        elements.finalTime.textContent = `${totalTime}s`;
        elements.weakAreas.textContent = state.weakAreas.length ? [...new Set(state.weakAreas)].join(", ") : "None yet";
        elements.completion.hidden = false;
        elements.completion.classList.add("is-celebrating");
        window.setTimeout(() => elements.completion.classList.remove("is-celebrating"), 1200);
        if (!state.practiceSaved) {
            state.practiceSaved = true;
            postJson("/api/practice/result/", {
                lesson_order: currentLesson().id,
                lesson_db_id: currentLesson().db_id,
                completed_shortcuts: currentLesson().shortcuts.length,
                total_shortcuts: currentLesson().shortcuts.length,
                accuracy,
                average_speed_seconds: averageSpeed,
                xp_earned: state.xp,
                weak_areas: [...new Set(state.weakAreas)],
            });
        }
        renderProgress();
    }

    function startQuiz() {
        state.mode = "quiz";
        state.quizIndex = 0;
        state.quizCorrect = 0;
        state.quizAttempts = 0;
        state.quizWrong = 0;
        state.quizReactionTimes = [];
        state.quizStartedAt = Date.now();
        elements.completion.hidden = true;
        elements.quiz.hidden = false;
        elements.status.textContent = "Quiz";
        elements.retryQuiz.disabled = false;
        elements.nextLessonQuiz.disabled = true;
        renderQuizTask();
    }

    function renderQuizTask() {
        const shortcut = currentQuizShortcut();
        elements.quizLabel.textContent = `Practical Quiz ${state.quizIndex + 1} of ${currentLesson().shortcuts.length}`;
        elements.quizTask.textContent = quizTaskFor(shortcut);
        elements.quizTarget.textContent = "Press the shortcut for this task";
        elements.quizFeedback.textContent = "Waiting for your shortcut.";
        elements.quizFeedback.className = "trainer-feedback";
        state.quizTaskStartedAt = Date.now();
        highlightExpectedKeys([]);
        renderQuizStats();
    }

    function renderQuizStats() {
        const accuracy = state.quizAttempts ? Math.round((state.quizCorrect / state.quizAttempts) * 100) : 0;
        const reaction = state.quizReactionTimes.length
            ? Math.round((state.quizReactionTimes.reduce((sum, value) => sum + value, 0) / state.quizReactionTimes.length) * 10) / 10
            : 0;
        const speedBonus = Math.max(0, 100 - Math.round(reaction * 10));
        const score = Math.max(0, Math.round(accuracy * 0.75 + speedBonus * 0.25 - state.quizWrong * 4));
        elements.quizScore.textContent = String(score);
        elements.quizAccuracy.textContent = `${accuracy}%`;
        elements.quizReaction.textContent = `${reaction}s`;
        if (reaction > 0) {
            if (reaction < 1.0) {
                elements.quizReaction.style.color = "var(--success)";
            } else if (reaction < 2.0) {
                elements.quizReaction.style.color = "var(--amber)";
            } else {
                elements.quizReaction.style.color = "var(--danger)";
            }
        } else {
            elements.quizReaction.style.color = "inherit";
        }
        elements.quizWrong.textContent = String(state.quizWrong);
    }

    function finishQuiz() {
        if (state.mode === "quiz_result") return;
        state.mode = "quiz_result";
        const accuracy = state.quizAttempts ? Math.round((state.quizCorrect / state.quizAttempts) * 100) : 0;
        const reaction = state.quizReactionTimes.length
            ? Math.round((state.quizReactionTimes.reduce((sum, value) => sum + value, 0) / state.quizReactionTimes.length) * 10) / 10
            : 0;
        unlockedLessonIndex = Math.max(unlockedLessonIndex, Math.min(state.lessonIndex + 1, lessons.length - 1));
        elements.quizLabel.textContent = "Quiz Complete";
        elements.quizTask.textContent = `Score: ${elements.quizScore.textContent}`;
        elements.quizTarget.textContent = "Lesson skill verified";
        elements.quizFeedback.textContent = state.lessonIndex >= lessons.length - 1
            ? `Accuracy ${accuracy}%. Wrong attempts ${state.quizWrong}. Course complete.`
            : `Accuracy ${accuracy}%. Wrong attempts ${state.quizWrong}. Next lesson unlocked.`;
        elements.quizFeedback.className = "trainer-feedback is-correct";
        elements.retryQuiz.disabled = false;
        elements.nextLessonQuiz.disabled = false;
        elements.quiz.classList.add("is-celebrating");
        window.setTimeout(() => elements.quiz.classList.remove("is-celebrating"), 1200);
        if (!state.quizSaved) {
            state.quizSaved = true;
            postJson("/api/quiz/result/", {
                lesson_order: currentLesson().id,
                lesson_db_id: currentLesson().db_id,
                score: Number(elements.quizScore.textContent || 0),
                accuracy,
                reaction_time_seconds: reaction,
                wrong_attempts: state.quizWrong,
            });
        }
        renderProgress();
    }

    function handleLessonKeydown(event, pressed) {
        const shortcut = currentShortcut();
        const expected = shortcut.keys;

        if (pressed.length < expected.length) return;

        state.attempts += 1;
        if (arraysMatch(pressed, expected)) {
            const speed = Math.max(1, Math.round((Date.now() - state.shortcutStartedAt) / 1000));
            state.correct += 1;
            state.streak += 1;
            state.xp += 25 + Math.max(0, 5 - speed);
            state.speeds.push(speed);
            elements.feedback.textContent = "Correct. Moving to the next shortcut.";
            elements.feedback.className = "trainer-feedback is-correct";
            renderProgress();
            window.setTimeout(moveNext, 650);
        } else {
            state.streak = 0;
            state.lives = Math.max(0, state.lives - 1);
            state.weakAreas.push(shortcut.name);
            elements.feedback.textContent = `Try again. You pressed ${pressed.join(" + ").toUpperCase()}.`;
            elements.feedback.className = "trainer-feedback is-wrong";
            renderProgress();
        }
    }

    function handleQuizKeydown(pressed) {
        const shortcut = currentQuizShortcut();
        const expected = shortcut.keys;
        if (pressed.length < expected.length) return;

        state.quizAttempts += 1;
        const reaction = Math.max(0.2, Math.round(((Date.now() - state.quizTaskStartedAt) / 1000) * 10) / 10);
        state.quizReactionTimes.push(reaction);

        if (arraysMatch(pressed, expected)) {
            state.quizCorrect += 1;
            elements.quizFeedback.textContent = `Correct in ${reaction}s.`;
            elements.quizFeedback.className = "trainer-feedback is-correct";
            renderQuizStats();
            if (state.quizIndex >= currentLesson().shortcuts.length - 1) {
                window.setTimeout(finishQuiz, 650);
            } else {
                state.quizIndex += 1;
                window.setTimeout(renderQuizTask, 650);
            }
        } else {
            state.quizWrong += 1;
            elements.quizFeedback.textContent = `Wrong attempt: ${pressed.join(" + ").toUpperCase()}. Try the task again.`;
            elements.quizFeedback.className = "trainer-feedback is-wrong";
            renderQuizStats();
        }
    }

    function handleKeydown(event) {
        handleVisualKeydown(event);
        if (!isPracticeCapturing()) return;
        if (event.repeat) {
            event.preventDefault();
            event.stopPropagation();
            return;
        }

        const pressed = normalizeEvent(event);
        if (pressed.length === 0) return;

        event.preventDefault();
        event.stopPropagation();

        if (state.mode === "lesson") {
            handleLessonKeydown(event, pressed);
        } else if (state.mode === "quiz") {
            handleQuizKeydown(pressed);
        }
    }

    function goToNextLesson() {
        if (state.lessonIndex >= lessons.length - 1) {
            state.mode = "course_complete";
            elements.status.textContent = "Course Complete";
            elements.feedback.textContent = "All lessons are complete. Choose a lesson to review or reset manually.";
            elements.start.disabled = true;
            elements.skip.disabled = true;
            elements.reset.disabled = false;
            elements.nextLesson.disabled = true;
            elements.nextLessonQuiz.disabled = true;
            renderProgress();
            return;
        }
        const nextIndex = state.lessonIndex + 1;
        if (lessonSelect) lessonSelect.value = String(nextIndex);
        resetLesson(nextIndex);
    }

    elements.start.addEventListener("click", () => {
        state.mode = "lesson";
        state.startedAt = Date.now();
        elements.start.textContent = "Training";
        elements.start.disabled = true;
        elements.skip.disabled = false;
        elements.reset.disabled = false;
        elements.completion.hidden = true;
        elements.quiz.hidden = true;
        renderShortcut();
    });

    elements.skip.addEventListener("click", () => {
        if (state.mode !== "lesson") return;
        state.attempts += 1;
        state.streak = 0;
        state.lives = Math.max(0, state.lives - 1);
        state.weakAreas.push(currentShortcut().name);
        moveNext();
    });

    elements.reset.addEventListener("click", () => resetLesson());
    elements.startQuiz.addEventListener("click", startQuiz);
    elements.retryQuiz.addEventListener("click", startQuiz);
    elements.nextLesson.addEventListener("click", goToNextLesson);
    elements.nextLessonQuiz.addEventListener("click", goToNextLesson);

    if (lessonSelect) {
        lessonSelect.addEventListener("change", (event) => resetLesson(Number(event.target.value)));
    }

    document.addEventListener("keydown", handleKeydown, true);
    document.addEventListener("keyup", handleVisualKeyup, true);
    resetLesson(0);
}

const library = document.querySelector("[data-library]");

if (library) {
    const search = document.querySelector("[data-library-search]");
    const filters = Array.from(document.querySelectorAll("[data-filter]"));
    const sort = document.querySelector("[data-library-sort]");
    const empty = document.querySelector("[data-library-empty]");
    const favFilterBtn = document.querySelector("[data-filter-favorites]");
    const favFilterText = document.querySelector("[data-fav-text]");
    const cards = Array.from(library.querySelectorAll(".shortcut-library-card"));

    let favorites = JSON.parse(localStorage.getItem("shortcut_favorites") || "[]");
    let favoritesOnly = false;

    cards.forEach((card) => {
        const starBtn = card.querySelector(".favorite-btn");
        if (starBtn) {
            const id = starBtn.dataset.shortcutId;
            if (favorites.includes(id)) {
                starBtn.textContent = "★";
                starBtn.style.color = "var(--amber)";
                starBtn.classList.add("is-active");
            }
            
            starBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                const isFav = starBtn.classList.toggle("is-active");
                if (isFav) {
                    starBtn.textContent = "★";
                    starBtn.style.color = "var(--amber)";
                    if (!favorites.includes(id)) favorites.push(id);
                } else {
                    starBtn.textContent = "☆";
                    starBtn.style.color = "var(--muted)";
                    favorites = favorites.filter((favId) => favId !== id);
                }
                localStorage.setItem("shortcut_favorites", JSON.stringify(favorites));
                if (favoritesOnly) filterLibrary();
            });
        }
    });

    function filterLibrary() {
        const query = (search.value || "").toLowerCase();
        const activeFilters = Object.fromEntries(filters.map((filter) => [filter.dataset.filter, filter.value.toLowerCase()]));
        let visible = 0;

        cards.forEach((card) => {
            const text = card.textContent.toLowerCase();
            const starBtn = card.querySelector(".favorite-btn");
            const isFav = starBtn ? starBtn.classList.contains("is-active") : false;
            
            const matchesSearch = !query || text.includes(query);
            const matchesApp = !activeFilters.app || card.dataset.apps.includes(activeFilters.app);
            const matchesCategory = !activeFilters.category || card.dataset.category === activeFilters.category;
            const matchesDifficulty = !activeFilters.difficulty || card.dataset.difficulty === activeFilters.difficulty;
            const matchesFav = !favoritesOnly || isFav;
            
            card.hidden = !(matchesSearch && matchesApp && matchesCategory && matchesDifficulty && matchesFav);
            if (!card.hidden) visible += 1;
        });
        if (empty) empty.hidden = visible !== 0;
    }

    function sortLibrary() {
        const mode = sort?.value || "name";
        const sorted = [...cards].sort((a, b) => {
            if (mode === "saved") return Number(b.dataset.saved) - Number(a.dataset.saved);
            if (mode === "difficulty") return a.dataset.difficulty.localeCompare(b.dataset.difficulty);
            return a.dataset.name.localeCompare(b.dataset.name);
        });
        sorted.forEach((card) => library.appendChild(card));
        filterLibrary();
    }

    if (favFilterBtn) {
        favFilterBtn.addEventListener("click", () => {
            favoritesOnly = !favoritesOnly;
            favFilterBtn.style.background = favoritesOnly ? "rgba(216, 138, 25, 0.14)" : "var(--surface)";
            favFilterBtn.style.borderColor = favoritesOnly ? "var(--amber)" : "var(--line)";
            if (favFilterText) favFilterText.textContent = favoritesOnly ? "All" : "Favorites";
            filterLibrary();
        });
    }

    search.addEventListener("input", filterLibrary);
    filters.forEach((filter) => filter.addEventListener("change", filterLibrary));
    if (sort) sort.addEventListener("change", sortLibrary);
    sortLibrary();
}
