// Application State
let isDemoMode = false;

// DOM Elements
const modeToggle = document.getElementById("mode-toggle");
const modeToggleIndicator = modeToggle.querySelector("span");
const modeTextApi = modeToggle.previousElementSibling;
const modeTextDemo = modeToggle.nextElementSibling;

const languageSelect = document.getElementById("language-select");
const loadSampleBtn = document.getElementById("load-sample-btn");
const codeInput = document.getElementById("code-input");
const submitBtn = document.getElementById("submit-btn");
const btnSpinner = document.getElementById("btn-spinner");
const btnText = document.getElementById("btn-text");

const resultsContainer = document.getElementById("results-container");
const historyContainer = document.getElementById("history-container");

// Sample code snippet for quick testing
const SAMPLE_PYTHON = `import sqlite3

def get_user_data(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Insecure query using direct string formatting
    query = f"SELECT * FROM accounts WHERE id = '{user_id}'"
    cursor.execute(query)
    return cursor.fetchall()
`;

// Initialize Event Listeners
document.addEventListener("DOMContentLoaded", () => {
    loadSampleBtn.addEventListener("click", () => {
        codeInput.value = SAMPLE_PYTHON;
    });

    modeToggle.addEventListener("click", toggleDemoMode);
    submitBtn.addEventListener("click", handleCodeReview);

    // Initial fetch of persisted reviews
    loadReviewHistory();
});

// Toggle between Live API Mode and Demo/Mock Mode
function toggleDemoMode() {
    isDemoMode = !isDemoMode;

    if (isDemoMode) {
        modeToggle.classList.remove("bg-slate-600");
        modeToggle.classList.add("bg-amber-600");
        modeToggleIndicator.classList.remove("translate-x-1");
        modeToggleIndicator.classList.add("translate-x-6");

        modeTextApi.classList.replace("text-slate-300", "text-slate-500");
        modeTextDemo.classList.replace("text-amber-400/50", "text-amber-400");
    } else {
        modeToggle.classList.remove("bg-amber-600");
        modeToggle.classList.add("bg-slate-600");
        modeToggleIndicator.classList.remove("translate-x-6");
        modeToggleIndicator.classList.add("translate-x-1");

        modeTextApi.classList.replace("text-slate-500", "text-slate-300");
        modeTextDemo.classList.replace("text-amber-400", "text-amber-400/50");
    }
}

// Main Submission Handler
async function handleCodeReview() {
    const code = codeInput.value.trim();
    const language = languageSelect.value;

    if (!code) {
        alert("Please enter or paste source code before submitting.");
        return;
    }

    setLoadingState(true);

    if (isDemoMode) {
        // Mock Mode: Client-side simulation, zero backend/database contamination
        setTimeout(() => {
            const mockResponse = {
                id: null,
                language: language,
                created_at: null,
                issues: [
                    {
                        issue_type: "SQL Injection Vulnerability",
                        severity: "High",
                        description: "Direct f-string formatting in SQL query allows arbitrary SQL execution.",
                        suggestion: "cursor.execute('SELECT * FROM accounts WHERE id = ?', (user_id,))"
                    },
                    {
                        issue_type: "Resource Leak",
                        severity: "Medium",
                        description: "Database connection is not closed or wrapped in a context manager.",
                        suggestion: "with sqlite3.connect('users.db') as conn:\n    ..."
                    }
                ]
            };
            renderFindings(mockResponse, true);
            setLoadingState(false);
        }, 600);
        return;
    }

    // Live API Mode: Sends code to FastAPI backend
    try {
        const response = await fetch("/review", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, language })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        renderFindings(data, false);
        await loadReviewHistory(); // Refresh history panel with new DB record
    } catch (error) {
        renderError(error.message);
    } finally {
        setLoadingState(false);
    }
}

// Render Findings Cards
function renderFindings(data, isSimulated) {
    resultsContainer.className = "flex-grow bg-slate-800 rounded-lg border border-slate-700 p-4 overflow-y-auto max-h-[460px] flex flex-col gap-4 text-left";
    resultsContainer.innerHTML = "";

    // Simulated Notice Banner
    if (isSimulated) {
        const demoBanner = document.createElement("div");
        demoBanner.className = "bg-amber-950/40 border border-amber-600/50 text-amber-300 text-xs px-3 py-2 rounded-md font-mono";
        demoBanner.textContent = "[DEMO MODE] Client-simulated review. Record was not saved to SQLite.";
        resultsContainer.appendChild(demoBanner);
    } else if (data.id) {
        const dbBadge = document.createElement("div");
        dbBadge.className = "bg-slate-900 border border-slate-700 text-slate-400 text-xs px-3 py-1.5 rounded-md flex justify-between";
        dbBadge.innerHTML = `<span>Persisted Record: <strong class="text-emerald-400">#${data.id}</strong></span><span>${new Date(data.created_at).toLocaleString()}</span>`;
        resultsContainer.appendChild(dbBadge);
    }

    // Zero Issues Found State
    if (!data.issues || data.issues.length === 0) {
        const cleanState = document.createElement("div");
        cleanState.className = "h-full flex flex-col justify-center items-center text-center p-6";
        cleanState.innerHTML = `
            <div class="h-12 w-12 rounded-full bg-emerald-950/50 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-3 text-xl font-bold">✓</div>
            <p class="text-slate-200 font-semibold">No Vulnerabilities Detected</p>
            <p class="text-xs text-slate-400 mt-1">The submitted code passed all static security checks.</p>
        `;
        resultsContainer.appendChild(cleanState);
        return;
    }

    // Render Individual Issue Cards
    data.issues.forEach(issue => {
        const card = document.createElement("div");
        card.className = "bg-slate-900 border border-slate-700 rounded-lg p-4 flex flex-col gap-2";

        const severityColor = getSeverityColor(issue.severity);

        card.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="font-semibold text-slate-200 text-sm">${escapeHtml(issue.issue_type)}</span>
                <span class="px-2 py-0.5 text-xs rounded-full border font-mono ${severityColor}">
                    ${escapeHtml(issue.severity || 'Notice')}
                </span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(issue.description)}</p>
            ${issue.suggestion ? `
                <div class="mt-2 bg-slate-950 rounded p-2.5 border border-slate-800">
                    <span class="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">Recommended Fix:</span>
                    <pre class="text-emerald-300 font-mono text-xs overflow-x-auto whitespace-pre-wrap">${escapeHtml(issue.suggestion)}</pre>
                </div>
            ` : ''}
        `;
        resultsContainer.appendChild(card);
    });
}

// Render Error State
function renderError(message) {
    resultsContainer.className = "flex-grow bg-slate-800 rounded-lg border border-rose-900/50 p-6 overflow-y-auto max-h-[460px] flex flex-col justify-center items-center text-center";
    resultsContainer.innerHTML = `
        <div class="h-12 w-12 rounded-full bg-rose-950/50 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-3 font-bold">!</div>
        <p class="text-rose-400 font-semibold">Review Request Failed</p>
        <p class="text-xs text-slate-400 max-w-sm mt-1 mb-4">${escapeHtml(message)}</p>
        <button onclick="toggleDemoMode()" class="text-xs bg-slate-900 hover:bg-slate-700 border border-slate-600 px-3 py-1.5 rounded text-amber-300 transition-colors">
            Switch to Demo Mode
        </button>
    `;
}

// Fetch and Render Database Review History
async function loadReviewHistory() {
    try {
        const response = await fetch("/reviews");
        if (!response.ok) return;

        const records = await response.json();
        if (records.length === 0) {
            historyContainer.innerHTML = `<p class="text-sm text-slate-500 text-center italic">No saved reviews in database.</p>`;
            return;
        }

        historyContainer.innerHTML = "";
        const grid = document.createElement("div");
        grid.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3";

        records.forEach(record => {
            const item = document.createElement("div");
            item.className = "bg-slate-900 border border-slate-700 hover:border-slate-500 p-3 rounded-lg flex flex-col justify-between transition-colors";

            const issueCount = record.issues ? record.issues.length : 0;
            const dateStr = record.created_at ? new Date(record.created_at).toLocaleString() : "Unknown date";

            item.innerHTML = `
                <div>
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-xs font-bold text-emerald-400">Review #${record.id}</span>
                        <span class="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">${record.language}</span>
                    </div>
                    <p class="text-xs text-slate-400">${issueCount} issue(s) recorded</p>
                    <p class="text-[10px] text-slate-400 mt-1">${dateStr}</p>
                </div>
                <button onclick="fetchReviewById(${record.id})" class="mt-3 w-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs py-1.5 rounded border border-slate-700 transition-colors">
                    View Findings
                </button>
            `;
            grid.appendChild(item);
        });

        historyContainer.appendChild(grid);
    } catch (e) {
        historyContainer.innerHTML = `<p class="text-xs text-rose-400 text-center">Unable to load review history.</p>`;
    }
}

// Fetch a Specific Review from DB by ID
async function fetchReviewById(reviewId) {
    try {
        const response = await fetch(`/reviews/${reviewId}`);
        if (!response.ok) throw new Error("Review not found");

        const data = await response.json();
        renderFindings(data, false);
        window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
        alert(`Failed to load review #${reviewId}: ${err.message}`);
    }
}

// Helpers
function setLoadingState(isLoading) {
    submitBtn.disabled = isLoading;
    if (isLoading) {
        btnSpinner.classList.remove("hidden");
        btnText.textContent = "Analyzing Code...";
        submitBtn.classList.replace("bg-emerald-600", "bg-slate-700");
    } else {
        btnSpinner.classList.add("hidden");
        btnText.textContent = "Run Security Review";
        submitBtn.classList.replace("bg-slate-700", "bg-emerald-600");
    }
}

function getSeverityColor(severity) {
    const s = (severity || "").toLowerCase();
    if (s === "high") return "bg-rose-950/60 text-rose-300 border-rose-700";
    if (s === "medium") return "bg-amber-950/60 text-amber-300 border-amber-700";
    return "bg-sky-950/60 text-sky-300 border-sky-700";
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}