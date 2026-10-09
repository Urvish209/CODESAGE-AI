async function ruleReview() {

    const code = document.getElementById("code").value.trim();

    if (!code) {

        showToast("Paste some code first", "#DC2626");

        return;

    }

    showLoading("Running Rule Based Review...");

    try {

        const result = await apiRequest("/review", "POST", {
            code
        });

        let html = `
        <h2>Rule Based Review</h2>
        <hr>
        `;

        if (result.issues && result.issues.length) {

            html += `<ul>`;

            result.issues.forEach(issue => {

                html += `<li>${issue}</li>`;

            });

            html += `</ul>`;

        } else {

            html += `<p>No issues found.</p>`;

        }

        document.getElementById("ruleOutput").innerHTML = html;

        showToast("Rule Scan Completed");

    }

    catch (err) {

        document.getElementById("ruleOutput").innerHTML = `
        <h3 style="color:#ef4444;">
        ${err.message}
        </h3>
        `;

        showToast("Rule Review Failed", "#DC2626");

    }

}


async function aiReview() {

    const code = document.getElementById("aiCode").value.trim();

    if (!code) {

        showToast("Paste some code first", "#DC2626");

        return;

    }

    showLoading("AI is reviewing your code...");

    try {

        const result = await apiRequest("/ai-review", "POST", {
            code
        });

        document.getElementById("aiOutput").innerHTML = `
        <h2>AI Review</h2>
        <hr>
        <div class="markdown-output">
        ${formatMarkdown(result.review)}
        </div>
        `;

        attachRunButtons(document.getElementById("aiOutput"));

        showToast("AI Review Completed");

    }

    catch (err) {

        document.getElementById("aiOutput").innerHTML = `
        <h3 style="color:#ef4444;">
        ${err.message}
        </h3>
        `;

        showToast("AI Review Failed", "#DC2626");

    }

}


function clearReview() {

    document.getElementById("code").value = "";
    document.getElementById("aiCode").value = "";

    document.getElementById("ruleOutput").innerHTML = "Waiting...";
    document.getElementById("aiOutput").innerHTML = "AI response appears here...";

}


// ===================================================
// Markdown rendering (marked.js + highlight.js)
// ===================================================

function formatMarkdown(markdown) {

    if (!markdown) return "";

    if (window.marked) {

        marked.setOptions({
            breaks: false,
            gfm: true,
            highlight: function (code, lang) {
                if (window.hljs) {
                    try {
                        return lang && hljs.getLanguage(lang)
                            ? hljs.highlight(code, { language: lang }).value
                            : hljs.highlightAuto(code).value;
                    } catch (e) {
                        return code;
                    }
                }
                return code;
            }
        });

        return marked.parse(markdown);
    }

    // Fallback if marked.js failed to load: at least escape it
    // so it's readable, instead of throwing raw markdown at the DOM.
    const div = document.createElement("div");
    div.innerText = markdown;
    return `<pre>${div.innerHTML}</pre>`;
}


// ===================================================
// Runnable code blocks (Piston API — free, no key needed)
// ===================================================

const RUNNABLE_LANGS = [
    "python", "py", "javascript", "js", "typescript", "ts",
    "java", "c", "cpp", "c++", "bash", "sh", "shell",
    "go", "golang", "ruby", "rb", "php", "rust", "rs"
];

function normalizeLang(lang) {

    const map = {
        py: "python", python3: "python", python: "python",
        js: "javascript", javascript: "javascript", node: "javascript",
        ts: "typescript", typescript: "typescript",
        java: "java",
        c: "c",
        "c++": "cpp", cpp: "cpp",
        bash: "bash", sh: "bash", shell: "bash",
        go: "go", golang: "go",
        rb: "ruby", ruby: "ruby",
        php: "php",
        rust: "rust", rs: "rust"
    };

    const key = (lang || "").toLowerCase().trim();
    return map[key] || key;
}

async function getPistonRuntimes() {

    if (!window.__pistonRuntimes) {
        const res = await fetch("https://emkc.org/api/v2/piston/runtimes");
        window.__pistonRuntimes = await res.json();
    }

    return window.__pistonRuntimes;
}

function attachRunButtons(container) {

    const blocks = container.querySelectorAll("pre code");

    blocks.forEach(codeEl => {

        const pre = codeEl.parentElement;

        if (pre.dataset.wrapped) return;
        pre.dataset.wrapped = "true";

        const langClass = [...codeEl.classList].find(c => c.startsWith("language-"));
        const rawLang = langClass ? langClass.replace("language-", "") : "";
        const lang = normalizeLang(rawLang);

        codeEl.dataset.lang = lang;

        const wrapper = document.createElement("div");
        wrapper.className = "code-block-wrapper";

        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);

        if (RUNNABLE_LANGS.includes(rawLang.toLowerCase()) || RUNNABLE_LANGS.includes(lang)) {

            const bar = document.createElement("div");
            bar.className = "code-block-bar";

            const tag = document.createElement("span");
            tag.className = "code-lang-tag";
            tag.innerText = lang || "code";
            bar.appendChild(tag);

            const runBtn = document.createElement("button");
            runBtn.className = "run-btn";
            runBtn.type = "button";
            runBtn.innerText = "▶ Run";
            runBtn.onclick = () => runCodeBlock(runBtn);
            bar.appendChild(runBtn);

            wrapper.insertBefore(bar, pre);

            const outputEl = document.createElement("pre");
            outputEl.className = "code-run-output";
            outputEl.style.display = "none";
            wrapper.appendChild(outputEl);
        }
    });
}

async function runCodeBlock(btn) {

    const wrapper = btn.closest(".code-block-wrapper");
    const codeEl = wrapper.querySelector("code");
    const outputEl = wrapper.querySelector(".code-run-output");
    const lang = codeEl.dataset.lang;
    const code = codeEl.innerText;

    btn.disabled = true;
    const originalLabel = btn.innerText;
    btn.innerText = "Running...";

    outputEl.style.display = "block";
    outputEl.innerText = "Running...";

    try {

        const runtimes = await getPistonRuntimes();

        const runtime = runtimes.find(r =>
            r.language === lang || (r.aliases && r.aliases.includes(lang))
        );

        if (!runtime) {
            outputEl.innerText = `No available runtime for "${lang}".`;
            return;
        }

        const res = await fetch("https://emkc.org/api/v2/piston/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                language: runtime.language,
                version: runtime.version,
                files: [{ content: code }]
            })
        });

        const data = await res.json();

        const stdout = data.run && data.run.stdout ? data.run.stdout : "";
        const stderr = data.run && data.run.stderr ? data.run.stderr : "";
        const compileErr = data.compile && data.compile.stderr ? data.compile.stderr : "";

        outputEl.innerText = [compileErr, stdout, stderr].filter(Boolean).join("\n") || "No output.";

    }

    catch (err) {

        outputEl.innerText = "Execution failed: " + err.message;

    }

    finally {

        btn.disabled = false;
        btn.innerText = originalLabel;

    }

}