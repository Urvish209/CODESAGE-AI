// ==========================================
// Code Sage AI - Dashboard
// ==========================================

console.log("dashboard.js loaded");

function showSection(section, element) {

    document
        .querySelectorAll(".page-section")
        .forEach(page => {
            page.classList.remove("active");
        });

    const target = document.getElementById(section);

    if (target) {
        target.classList.add("active");
    }

    document
        .querySelectorAll(".sidebar nav li")
        .forEach(item => {
            item.classList.remove("active");
        });

    if (element) {
        element.classList.add("active");
    }

    if (section === "history") {
        if (typeof loadHistory === "function") {
            loadHistory();
        }
    }

    if (section === "home") {
        if (typeof loadDashboardStats === "function") {
            loadDashboardStats();
        }
    }
}

async function loadDashboardStats() {

    try {

        if (typeof loadHistory === "function") {
            await loadHistory();
        }

    } catch (error) {

        console.error(
            "Dashboard stats error:",
            error
        );

    }
}

function initializeDashboard() {

    const userData =
        localStorage.getItem("user");

    if (!userData) {
        window.location.href = "login.html";
        return;
    }

    let user;

    try {

        user = JSON.parse(userData);

    } catch {

        localStorage.removeItem("user");
        localStorage.removeItem("token");

        window.location.href = "login.html";
        return;
    }

    const userName =
        document.getElementById("userName");

    const profileName =
        document.getElementById("profileName");

    const profileEmail =
        document.getElementById("profileEmail");

    if (userName) {
        userName.innerText =
            user.name || "Developer";
    }

    if (profileName) {
        profileName.innerText =
            user.name || "Developer";
    }

    if (profileEmail) {
        profileEmail.innerText =
            user.email || "developer@email.com";
    }

    loadDashboardStats();
}

document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);