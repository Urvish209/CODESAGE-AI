async function register() {

    const name = document.getElementById("regName").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;

    if (!name || !email || !password) {
        showToast("Please fill all fields", "#DC2626");
        return;
    }

    try {

        const data = await apiRequest("/register", "POST", {
            name,
            email,
            password
        });

        showToast(data.message || "Registration Successful");

        document.getElementById("regName").value = "";
        document.getElementById("regEmail").value = "";
        document.getElementById("regPassword").value = "";

        setTimeout(() => {
            window.location.href = "login.html";
        }, 800);

    }

    catch (err) {

        showToast(err.message, "#DC2626");

    }

}


async function login() {

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    if (!email || !password) {

        showToast("Enter email and password", "#DC2626");

        return;

    }

    try {

        const data = await apiRequest("/login", "POST", {
            email,
            password
        });

        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );

        showToast("Welcome " + data.user.name);

        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 700);

    }

    catch (err) {

        showToast(err.message, "#DC2626");

    }

}


function logout() {

    localStorage.removeItem("user");

    showToast("Logged Out", "#2563EB");

    setTimeout(() => {
        window.location.href = "login.html";
    }, 500);

}


// Only meaningful on dashboard.html — dashboard.html's own inline
// script calls this pattern already (checks localStorage, fills in
// userName / profileName / profileEmail, redirects to login.html
// if there's no session). Kept here as a reusable helper in case
// other pages need to read the logged-in user without redirecting.
function getCurrentUser() {
    return JSON.parse(localStorage.getItem("user") || "null");
}