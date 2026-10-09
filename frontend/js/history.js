async function loadHistory() {

    const history = document.getElementById("historyList");

    if (!history) return;

    history.innerHTML = `
    <div style="padding:20px;text-align:center;">
        Loading...
    </div>
    `;

    try {

        const data = await apiRequest("/reviews");

        updateStats(data);

        if (!data.length) {

            history.innerHTML = `
            <div class="empty-history">
                <h3>No Reviews Yet</h3>
                <p>Analyze a repository to see it here.</p>
            </div>
            `;

            return;

        }

        let html = "";

        data.forEach(review => {

            html += `

            <div class="history-card">

                <h3>${review.repository}</h3>

                <p>Overall Score :
                <b>${review.overall_score}/100</b></p>

                <p>Files :
                ${review.files_analyzed}</p>

                <div class="history-buttons">

                    <button
                        class="primary-btn"
                        onclick="viewReview(${review.id})">

                        View

                    </button>

                    <button
                        class="danger-btn"
                        onclick="deleteReview(${review.id})">

                        Delete

                    </button>

                </div>

            </div>

            `;

        });

        history.innerHTML = html;

    }

    catch (err) {

        history.innerHTML = `

        <div class="empty-history">

            <h3>Error</h3>

            <p>${err.message}</p>

        </div>

        `;

    }

}


// Fills in the counters on the Dashboard home cards (#repoCount,
// #reviewCount) and the Profile page (#profileRepos, #profileReviews).
// "Reviews" = total analyses run. "Repositories" = distinct repos,
// since the same repo can be analyzed more than once (as in your
// history: company-research-agent appears 3 times but is 1 repo).
function updateStats(data) {

    const total = data.length;
    const uniqueRepos = new Set(data.map(r => r.repository)).size;

    const repoCountEl = document.getElementById("repoCount");
    const reviewCountEl = document.getElementById("reviewCount");
    const profileReposEl = document.getElementById("profileRepos");
    const profileReviewsEl = document.getElementById("profileReviews");

    if (repoCountEl) repoCountEl.innerText = uniqueRepos;
    if (reviewCountEl) reviewCountEl.innerText = total;
    if (profileReposEl) profileReposEl.innerText = uniqueRepos;
    if (profileReviewsEl) profileReviewsEl.innerText = total;

}


async function viewReview(id) {

    showLoading("Loading Review...");

    try {

        const review = await apiRequest("/reviews/" + id);

        document.getElementById("output").innerHTML = `

        <div class="repo-result">

            <h2>${review.repository}</h2>

            <p>

                <b>Files Analyzed :</b>

                ${review.files_analyzed}

            </p>

            <div class="score-grid">

                <div class="score-card">

                    <h3>Security</h3>

                    <h1>${review.security_score}</h1>

                </div>

                <div class="score-card">

                    <h3>Performance</h3>

                    <h1>${review.performance_score}</h1>

                </div>

                <div class="score-card">

                    <h3>Quality</h3>

                    <h1>${review.code_quality_score}</h1>

                </div>

                <div class="score-card">

                    <h3>Overall</h3>

                    <h1>${review.overall_score}</h1>

                </div>

            </div>

            <hr>

            <h3>Issues</h3>

            <ul>

            ${review.issues.map(issue => `

                <li>${issue}</li>

            `).join("")}

            </ul>

            <hr>

            <h3>Suggestions</h3>

            <ul>

            ${review.suggestions.map(item => `

                <li>${item}</li>

            `).join("")}

            </ul>

        </div>

        `;

        showSection('repoScan', document.querySelector('.sidebar nav li:nth-child(4)'));

    }

    catch (err) {

        showToast("Unable to load review", "#DC2626");

    }

}


async function deleteReview(id) {

    if (!confirm("Delete this review?")) {

        return;

    }

    try {

        await apiRequest("/reviews/" + id, "DELETE");

        showToast("Review Deleted");

        loadHistory();

        document.getElementById("output").innerHTML =
            "Waiting for analysis...";

    }

    catch (err) {

        showToast("Delete Failed", "#DC2626");

    }

}