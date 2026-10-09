// ==========================================
// Code Sage AI - Embedded AI Chat / Auto Fix /
// Documentation widgets
//
// These widgets are embedded on THREE pages:
//   - Repository        (prefix "repo")
//   - Code Review        (prefix "review")
//   - Rule Scanner       (prefix "rule")
//
// All three share the same last-analyzed repo URL,
// stored in localStorage by repo.js ("lastRepoUrl"
// and "lastRepoFileList").
// ==========================================

console.log("ai.js loaded");


// ==========================================
// Get the shared repo URL
// Falls back to whatever is currently typed into
// the Repository page's #repo input, then to the
// last successfully analyzed repo in localStorage.
// ==========================================

function getSharedRepoUrl() {

    const repoInput =
        document.getElementById("repo");

    if (repoInput && repoInput.value.trim()) {
        return repoInput.value.trim();
    }

    return (
        localStorage.getItem("lastRepoUrl") || ""
    );
}


function getSharedFileList() {

    try {

        const raw =
            localStorage.getItem("lastRepoFileList");

        const list = JSON.parse(raw || "[]");

        return Array.isArray(list) ? list : [];

    } catch {

        return [];
    }
}


function requireSharedRepoUrl() {

    const repoUrl = getSharedRepoUrl();

    if (!repoUrl) {

        showToast(
            "Analyze a repository first (Repository tab)",
            "#DC2626"
        );

        return null;
    }

    return repoUrl;
}


// ==========================================
// FILE DROPDOWNS
//
// Every page's Auto Fix widget has a <select
// id="{prefix}FixFile">. Call this after analysis
// completes to (re)populate all three at once.
// ==========================================

const AI_WIDGET_PREFIXES = ["repo", "review", "rule"];


function refreshAllFileDropdowns() {

    const files = getSharedFileList();

    AI_WIDGET_PREFIXES.forEach(prefix => {

        const select =
            document.getElementById(
                `${prefix}FixFile`
            );

        if (!select) return;

        if (!files.length) {

            select.innerHTML =
                `<option value="">
                    No files yet — analyze a repository first
                </option>`;

            return;
        }

        select.innerHTML = files
            .map(path => `
                <option value="${escapeHTML(path)}">
                    ${escapeHTML(path)}
                </option>
            `)
            .join("");
    });
}


// ==========================================
// ASK AI (embedded chat widget)
//
// Expects, per page prefix, these elements:
//   #{prefix}AiChatMessages
//   #{prefix}AiChatInput
// ==========================================

async function sendAIChat(prefix) {

    const input =
        document.getElementById(
            `${prefix}AiChatInput`
        );

    const messages =
        document.getElementById(
            `${prefix}AiChatMessages`
        );

    if (!input || !messages) return;


    const question =
        input.value.trim();

    if (!question) {

        showToast(
            "Type a question first",
            "#DC2626"
        );

        return;
    }


    // Repo check happens here, at send-time, so the
    // panel itself always opens instantly. If nothing
    // has been analyzed yet, show that inline in the
    // chat instead of blocking the panel from opening.

    const repoUrl = getSharedRepoUrl();

    if (!repoUrl) {

        appendAIChatBubble(
            messages,
            question,
            "user"
        );

        input.value = "";

        appendAIChatBubble(
            messages,
            "Analyze a repository first (Repository tab) — I need one to answer questions about.",
            "ai"
        );

        return;
    }


    appendAIChatBubble(
        messages,
        question,
        "user"
    );

    input.value = "";


    appendAIChatBubble(
        messages,
        "Thinking...",
        "ai",
        true
    );


    try {

        const result =
            await apiRequest(
                "/ai-chat",
                "POST",
                {
                    repo_url: repoUrl,
                    question
                }
            );


        removeLastAIChatBubble(messages);

        appendAIChatBubble(
            messages,
            formatMarkdown(result.answer),
            "ai"
        );

        highlightCodeBlocks(messages);


    } catch (error) {

        removeLastAIChatBubble(messages);

        appendAIChatBubble(
            messages,
            escapeHTML(
                error.message ||
                "AI Chat failed."
            ),
            "ai"
        );

        showToast(
            "AI Chat Failed",
            "#DC2626"
        );
    }
}


function appendAIChatBubble(
    container,
    html,
    type,
    isPending = false
) {

    const wrapper =
        document.createElement("div");

    wrapper.className =
        `chat-message ${type}-message`;

    if (isPending) {
        wrapper.dataset.pending = "true";
    }

    if (type === "user") {

        wrapper.innerHTML = `
            <div class="chat-bubble">
                <strong>You</strong>
                <p>${escapeHTML(html)}</p>
            </div>
        `;

    } else {

        wrapper.innerHTML = `
            <div class="chat-avatar">CS</div>
            <div class="chat-bubble">
                <strong>Code Sage AI</strong>
                <div>${html}</div>
            </div>
        `;
    }

    container.appendChild(wrapper);

    container.scrollTop =
        container.scrollHeight;
}


function removeLastAIChatBubble(container) {

    const pending =
        container.querySelector(
            '[data-pending="true"]'
        );

    if (pending) {
        pending.remove();
    }
}


// ==========================================
// AI AUTO FIX (embedded widget)
//
// Expects, per page prefix, these elements:
//   #{prefix}FixFile     (select, populated by
//                          refreshAllFileDropdowns)
//   #{prefix}FixIssue    (text input)
//   #{prefix}FixOutput   (output container)
// ==========================================

async function runAIFix(prefix) {

    const fileSelect =
        document.getElementById(
            `${prefix}FixFile`
        );

    const issueInput =
        document.getElementById(
            `${prefix}FixIssue`
        );

    const output =
        document.getElementById(
            `${prefix}FixOutput`
        );

    if (!fileSelect || !issueInput || !output) return;


    const repoUrl = getSharedRepoUrl();

    if (!repoUrl) {

        output.innerHTML = `
            <p>
                Analyze a repository first (Repository tab) —
                I need one to know which files exist.
            </p>
        `;

        return;
    }


    const file =
        fileSelect.value;

    const issue =
        issueInput.value.trim();


    if (!file) {

        showToast(
            "Select a file first",
            "#DC2626"
        );

        return;
    }


    if (!issue) {

        showToast(
            "Describe the issue to fix",
            "#DC2626"
        );

        return;
    }


    showLoading(
        "AI is generating a fix...",
        `${prefix}FixOutput`
    );


    try {

        const result =
            await apiRequest(
                "/ai-fix",
                "POST",
                {
                    repo_url: repoUrl,
                    file,
                    issue
                }
            );


        output.innerHTML = `

            <h3>Fix Result — ${escapeHTML(file)}</h3>

            <p>${escapeHTML(result.explanation || "")}</p>

            ${Array.isArray(result.changes) && result.changes.length
                ? `<ul>${result.changes
                    .map(c => `<li>${escapeHTML(c)}</li>`)
                    .join("")}</ul>`
                : ""
            }

            <h4>Fixed Code</h4>

            <div class="markdown-output">
                ${formatMarkdown(
                "```\n" + (result.fixed_code || "") + "\n```"
            )}
            </div>
        `;

        highlightCodeBlocks(output);


        showToast("AI Auto Fix Completed");


    } catch (error) {

        output.innerHTML = `
            <h3 style="color:#DC2626;">
                ${escapeHTML(
            error.message || "AI Auto Fix Failed"
        )}
            </h3>
        `;

        showToast(
            "AI Auto Fix Failed",
            "#DC2626"
        );
    }
}


// ==========================================
// REPORT PDF DOWNLOAD
//
// Used by the "Report PDF" dropdown on the Repository
// page. Clicking SRS / Snapshot / Evolution Plan asks
// the backend (/generate-report-pdf) for a PDF and
// saves it straight to the user's computer.
// ==========================================

async function downloadReport(reportType, label) {

    const repoUrl = requireSharedRepoUrl();

    if (!repoUrl) return;


    const menuButton =
        document.getElementById("reportPdfBtn");

    setButtonLoading(
        menuButton,
        true,
        `Generating ${label}...`
    );


    try {

        const response =
            await fetch(
                API + "/generate-report-pdf",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        repo_url: repoUrl,
                        report_type: reportType
                    })
                }
            );


        if (!response.ok) {

            let message =
                "Failed to generate PDF.";

            try {

                const errorData =
                    await response.json();

                if (errorData && errorData.detail) {
                    message = errorData.detail;
                }

            } catch {
                // response wasn't JSON, keep default message
            }

            throw new Error(message);
        }


        const blob =
            await response.blob();

        const downloadUrl =
            window.URL.createObjectURL(blob);

        const link =
            document.createElement("a");

        link.href = downloadUrl;

        link.download =
            `${label.replace(/\s+/g, "-")}.pdf`;

        document.body.appendChild(link);

        link.click();

        link.remove();

        window.URL.revokeObjectURL(downloadUrl);


        showToast(`${label} downloaded`);


    } catch (error) {

        showToast(
            error.message || "PDF download failed",
            "#DC2626"
        );

    } finally {

        setButtonLoading(
            menuButton,
            false
        );
    }
}


// ==========================================
// Populate dropdowns on load in case a repo was
// already analyzed in a previous session.
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    refreshAllFileDropdowns
);