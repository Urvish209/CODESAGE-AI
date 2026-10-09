// ==========================================
// Code Sage AI - Repository Analyzer
// ==========================================

async function analyzeRepo() {

    const repoInput =
        document.getElementById("repo");

    const output =
        document.getElementById("output");


    if (!repoInput || !output) {
        return;
    }


    const repoUrl =
        repoInput.value.trim();


    if (!repoUrl) {

        showToast(
            "Enter a GitHub Repository URL",
            "#DC2626"
        );

        repoInput.focus();

        return;
    }


    if (
        !repoUrl.startsWith("https://github.com/")
    ) {

        showToast(
            "Please enter a valid GitHub URL.",
            "#DC2626"
        );

        return;
    }


    output.innerHTML = `
        <div style="
            text-align:center;
            padding:20px;
            color:var(--muted);
        ">
            <div style="font-size:24px;">⏳</div>
            <strong>Analyzing repository...</strong>
            <p>
                Reading repository files and generating review.
            </p>
        </div>
    `;


    try {

        const result =
            await apiRequest(
                "/analyze-repo",
                "POST",
                {
                    repo_url: repoUrl
                }
            );


        const security =
            result.security_score ?? 0;

        const performance =
            result.performance_score ?? 0;

        const quality =
            result.code_quality_score ?? 0;

        const overall =
            result.overall_score ?? 0;

        const files =
            result.files_analyzed ?? 0;


        const issues =
            Array.isArray(result.issues)
                ? result.issues
                : [];


        const suggestions =
            Array.isArray(result.suggestions)
                ? result.suggestions
                : [];


        output.innerHTML = `

            <div class="repo-result">

                <h2>
                    ${escapeHTML(
            result.repository || "Repository"
        )}
                </h2>

                <p>
                    Repository analysis completed successfully.
                </p>


                <div class="score-grid">

                    <div class="score-card">

                        <h3>Security</h3>

                        <h1>
                            ${security}
                        </h1>

                    </div>


                    <div class="score-card">

                        <h3>Performance</h3>

                        <h1>
                            ${performance}
                        </h1>

                    </div>


                    <div class="score-card">

                        <h3>Quality</h3>

                        <h1>
                            ${quality}
                        </h1>

                    </div>


                    <div class="score-card">

                        <h3>Overall</h3>

                        <h1>
                            ${overall}
                        </h1>

                    </div>

                </div>


                <div class="progress-title">
                    Overall Repository Score
                </div>


                <div class="progress">

                    <div
                        class="progress-fill"
                        style="width:${Math.min(
            Math.max(overall, 0),
            100
        )}%">
                    </div>

                </div>


                <p>
                    <b>Files Analyzed:</b>
                    ${files}
                </p>


                <hr>


                <h3>Issues Found</h3>

                ${issues.length
                ? `
                            <ul>
                                ${issues
                    .map(issue => `
                                        <li>
                                            ${escapeHTML(issue)}
                                        </li>
                                    `)
                    .join("")}
                            </ul>
                        `
                : `
                            <p>
                                No major issues were detected.
                            </p>
                        `
            }


                <hr>


                <h3>Suggestions</h3>

                ${suggestions.length
                ? `
                            <ul>
                                ${suggestions
                    .map(item => `
                                        <li>
                                            ${escapeHTML(item)}
                                        </li>
                                    `)
                    .join("")}
                            </ul>
                        `
                : `
                            <p>
                                No additional suggestions.
                            </p>
                        `
            }

            </div>
        `;


        // ==========================================
        // Store repo context for AI Chat / AI Auto Fix
        // / Documentation widgets embedded on other pages.
        // ==========================================

        localStorage.setItem(
            "lastRepoUrl",
            repoUrl
        );

        localStorage.setItem(
            "lastRepoFileList",
            JSON.stringify(
                Array.isArray(result.file_list)
                    ? result.file_list
                    : []
            )
        );


        // Refresh any file-list dropdowns already in the DOM
        if (typeof refreshAllFileDropdowns === "function") {
            refreshAllFileDropdowns();
        }


        // Reveal the 'Report PDF' dropdown button
        // (set directly — don't depend on a separately
        // defined helper or on script load order)
        const reportBtn =
            document.getElementById("reportPdfBtn");

        if (reportBtn) {
            reportBtn.style.display = "inline-block";
        }


        repoInput.value = "";


        if (
            typeof loadHistory === "function"
        ) {

            loadHistory();

        }


        showToast(
            "Repository Analysis Completed"
        );


    } catch (error) {

        console.error(
            "Repository analysis error:",
            error
        );


        output.innerHTML = `

            <div style="
                padding:12px;
                color:#DC2626;
            ">

                <h3>
                    Repository Analysis Failed
                </h3>

                <p>
                    ${escapeHTML(
            error.message ||
            "Unable to analyze repository."
        )}
                </p>

            </div>
        `;


        showToast(
            "Repository Analysis Failed",
            "#DC2626"
        );
    }
}


// ==========================================
// Escape HTML
// ==========================================

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