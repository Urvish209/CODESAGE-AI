const API = "https://codesage-ai-h5jm.onrender.com";

/* =========================================================
   API REQUEST
   ========================================================= */

async function apiRequest(endpoint, method = "GET", body = null) {

    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    let response;

    try {
        response = await fetch(API + endpoint, options);
    } catch (error) {

        console.error("API connection error:", error);

        throw new Error(
            "Unable to connect to the backend. Make sure FastAPI is running."
        );
    }

    let data;

    try {
        data = await response.json();
    } catch (error) {

        console.error("Invalid API response:", error);

        throw new Error(
            `Server returned an invalid response (${response.status}).`
        );
    }

    if (!response.ok) {

        let message = "Request failed.";

        if (data) {

            if (typeof data.detail === "string") {
                message = data.detail;
            }

            else if (Array.isArray(data.detail)) {
                message = data.detail
                    .map(item => item.msg || JSON.stringify(item))
                    .join(", ");
            }

            else if (data.message) {
                message = data.message;
            }
        }

        throw new Error(message);
    }

    return data;
}


/* =========================================================
   TOAST
   ========================================================= */

function showToast(message, color = "#16A34A") {

    const toast = document.getElementById("toast");

    if (!toast) {
        console.warn("Toast element not found.");
        return;
    }

    toast.innerText = message;

    toast.style.background = color;

    toast.classList.add("show");

    clearTimeout(window.toastTimer);

    window.toastTimer = setTimeout(() => {

        toast.classList.remove("show");

    }, 3000);
}


/* =========================================================
   LOADING
   ========================================================= */

function showLoading(text = "Loading...", targetId = "output") {

    const output = document.getElementById(targetId);

    if (!output) return;

    output.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>${escapeHTML(text)}</p>
        </div>
    `;
}


/* =========================================================
   ERROR
   ========================================================= */

function showError(message, targetId = null) {

    showToast(message, "#DC2626");

    if (targetId) {

        const output = document.getElementById(targetId);

        if (output) {

            output.innerHTML = `
                <div class="error-message">
                    <h3>Something went wrong</h3>
                    <p>${escapeHTML(message)}</p>
                </div>
            `;
        }
    }
}


/* =========================================================
   HTML ESCAPE
   Prevents API/user content from injecting HTML.
   ========================================================= */

function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/* =========================================================
   MARKDOWN FORMATTER
   ========================================================= */

function formatMarkdown(text) {

    if (!text) {
        return "";
    }

    /*
     * Use Marked when available.
     * Your dashboard already loads marked.min.js.
     */

    if (typeof marked !== "undefined") {

        try {

            return marked.parse(text);

        } catch (error) {

            console.error("Markdown parsing failed:", error);
        }
    }

    /*
     * Fallback formatter if Marked is unavailable.
     */

    return escapeHTML(text)
        .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\n/g, "<br>");
}


/* =========================================================
   HIGHLIGHT CODE
   ========================================================= */

function highlightCodeBlocks(container = document) {

    if (
        typeof hljs === "undefined" ||
        !container
    ) {
        return;
    }

    container
        .querySelectorAll("pre code")
        .forEach(block => {

            try {

                hljs.highlightElement(block);

            } catch (error) {

                console.warn(
                    "Code highlighting failed:",
                    error
                );
            }
        });
}


/* =========================================================
   API HEALTH CHECK
   ========================================================= */

async function checkBackend() {

    try {

        const response = await fetch(API + "/", {
            method: "GET"
        });

        return response.ok;

    } catch (error) {

        console.warn(
            "Backend is not reachable:",
            error
        );

        return false;
    }
}


/* =========================================================
   DISABLE / ENABLE BUTTON
   ========================================================= */

function setButtonLoading(button, loading, text = "Loading...") {

    if (!button) return;

    if (loading) {

        button.dataset.originalText = button.innerHTML;

        button.disabled = true;

        button.innerHTML = `
            <span class="button-spinner"></span>
            ${escapeHTML(text)}
        `;

    } else {

        button.disabled = false;

        if (button.dataset.originalText) {

            button.innerHTML =
                button.dataset.originalText;
        }
    }
}


/* =========================================================
   GLOBAL API CONFIG
   ========================================================= */

console.log("api.js loaded");
console.log("Backend:", API);