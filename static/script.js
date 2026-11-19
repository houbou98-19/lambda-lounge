const match = window.location.pathname.match(/\/(Prod|Stage)/);
const envPath = match ? match[0] : ""; 

let socket = null;
let lastTimestamp = 0n; // timestamp of the newest message on the screen

function showMessage(msg) {
    const messageContainer = document.getElementById("messages");
    if (!messageContainer.querySelector(".message")) {
        messageContainer.innerHTML = ""; // removes the "No messages" text
    }
    const atBottom = messageContainer.scrollHeight - messageContainer.scrollTop - messageContainer.clientHeight < 80;

    const sentAt = new Date(Number(BigInt(msg.timestamp) / 1000000n)); // the timestamp is in nanoseconds
    const msgElement = document.createElement("div");
    msgElement.className = "message";
    const timeElement = document.createElement("span");
    timeElement.className = "time";
    timeElement.textContent = `[${sentAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}]`;
    const userElement = document.createElement("span");
    userElement.className = "user";
    userElement.textContent = `${msg.username}:`;
    const textElement = document.createElement("span");
    textElement.className = "text";
    textElement.textContent = msg.messagecontent;
    msgElement.append(timeElement, userElement, textElement);
    messageContainer.appendChild(msgElement);
    lastTimestamp = BigInt(msg.timestamp);

    if (atBottom) {
        messageContainer.scrollTop = messageContainer.scrollHeight; // stay on the newest message
    }
}

function setStatus(status) {
    const statusElement = document.getElementById("status");
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `status ${status}`;
    }
}

async function fetchMessages() {
    try {
        const response = await fetch(`${envPath}/messages`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const messages = await response.json();
        const messageContainer = document.getElementById("messages");
        const wasAtBottom = messageContainer.scrollHeight - messageContainer.scrollTop - messageContainer.clientHeight < 80;
        const oldScroll = messageContainer.scrollTop;
        messageContainer.innerHTML = "";

        if (messages.length === 0) {
            messageContainer.textContent = "no messages yet";
        } else {
            messages.forEach(msg => showMessage(msg));
            // keeps the place when someone is reading older messages
            messageContainer.scrollTop = wasAtBottom ? messageContainer.scrollHeight : oldScroll;
        }
    } catch (error) {
        console.error("Error fetching messages:", error);
        document.getElementById("messages").textContent = "Failed to load messages.";
    }
}

async function connectWebSocket() {
    try {
        const response = await fetch(`${envPath}/ws-token`);
        if (response.status === 404) {
            setStatus("polling");
            return; // no websocket here (running locally), the polling keeps working
        }
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const { ticket, url } = await response.json();
        socket = new WebSocket(`${url}?ticket=${ticket}`);
        socket.onopen = () => {
            setStatus("online");
            fetchMessages(); // catches up on what was missed
        };
        socket.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (BigInt(msg.timestamp) > lastTimestamp) {
                showMessage(msg);
            }
        };
        socket.onclose = () => {
            socket = null;
            setStatus("polling");
            setTimeout(connectWebSocket, 5000);
        };
    } catch (error) {
        console.error("Error connecting websocket:", error);
        setStatus("polling");
        setTimeout(connectWebSocket, 5000);
    }
}

async function postMessage(event) {
    event.preventDefault();

    const messageContent = document.getElementById("message").value;
    document.getElementById("message").value = "";

    try {
        const response = await fetch(`${envPath}/messages`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json", 
            },
            body: JSON.stringify({ content: messageContent }), 
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to post the message");
        }

        if (!socket || socket.readyState !== WebSocket.OPEN) {
            fetchMessages(); // no websocket to tell us about it, so look right away
        }
    } catch (error) {
        console.error("Error posting message:", error);
        alert("Failed to post the message. Please try again.");
    }
}

async function loginUser(event) {
    event.preventDefault();

    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    const response = await fetch(envPath + "/token", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ username, password }),
    });

    if (response.ok) {
        const redirectUrl = window.location.origin + envPath + "/chat";
        window.location.href = redirectUrl;
    } else {
        showAuthMessage("wrong username or password", "error");
    }
}

function showAuthMessage(text, type) {
    const messageElement = document.getElementById("auth-message");
    messageElement.textContent = text;
    messageElement.className = `auth-message ${type}`;
    messageElement.hidden = false;
}

function showForm(name) {
    document.getElementById("login-section").hidden = name !== "login";
    document.getElementById("register-section").hidden = name !== "register";
    document.getElementById("auth-message").hidden = true;
    document.getElementById(`${name}-username`).focus();
}

async function logoutUser() {
    const response = await fetch(envPath + "/logout", {
        method: "POST"
    });
    if (response.ok) {
        window.location.href = envPath + "/login";
    } else {
        alert("Failed to log out.. thats crazy....");
    }
}

async function registerUser(event) {
    event.preventDefault();

    const username = document.getElementById("register-username").value;
    const password = document.getElementById("register-password").value;

    const response = await fetch(envPath + "/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ username, password }),
    });

    if (response.ok) {
        document.getElementById("register-form").reset(); // Clear form
        showForm("login");
        document.getElementById("login-username").value = username;
        document.getElementById("login-password").value = "";
        document.getElementById("login-password").focus();
        showAuthMessage("account created, you can log in now", "success");
    } else {
        const error = await response.json();
        const reason = typeof error.detail === "string" ? error.detail : "check your username and password";
        showAuthMessage(`registration failed: ${reason}`, "error");
    }
}



document.addEventListener("DOMContentLoaded", () => {
    const messageForm = document.getElementById("message-form");
    if (messageForm) {
        messageForm.addEventListener("submit", postMessage);
        fetchMessages();
        connectWebSocket();
        setInterval(() => {
            if (!socket || socket.readyState !== WebSocket.OPEN) {
                fetchMessages(); // only needed when the websocket is not working
            }
        }, 5000);
    }

    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", loginUser);
    }

    const registerForm = document.getElementById("register-form");
    if (registerForm) {
        registerForm.addEventListener("submit", registerUser);
        document.getElementById("show-register").addEventListener("click", () => showForm("register"));
        document.getElementById("show-login").addEventListener("click", () => showForm("login"));
        if (window.location.hash === "#register") {
            showForm("register"); // so a link can open the register form directly
        }
    }

    const logoutButton = document.getElementById("logout-btn");
    if (logoutButton) {
        logoutButton.addEventListener("click", logoutUser);
    }
});
