const match = window.location.pathname.match(/\/(Prod|Stage)/);
const envPath = match ? match[0] : ""; 

let socket = null;
let lastTimestamp = 0n; // timestamp of the newest message on the screen

function showMessage(msg) {
    const messageContainer = document.getElementById("messages");
    if (!messageContainer.querySelector(".message")) {
        messageContainer.innerHTML = ""; // removes the "No messages" text
    }
    const msgElement = document.createElement("div");
    msgElement.className = "message";
    msgElement.textContent = `${msg.username}: ${msg.messagecontent}`;
    messageContainer.appendChild(msgElement);
    lastTimestamp = BigInt(msg.timestamp);
}

async function fetchMessages() {
    try {
        const response = await fetch(`${envPath}/messages`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const messages = await response.json();
        const messageContainer = document.getElementById("messages");
        messageContainer.innerHTML = "";

        if (messages.length === 0) {
            messageContainer.textContent = "No messages to display.";
        } else {
            messages.forEach(msg => showMessage(msg));
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
            return; // no websocket here (running locally), the polling keeps working
        }
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const { ticket, url } = await response.json();
        socket = new WebSocket(`${url}?ticket=${ticket}`);
        socket.onopen = () => fetchMessages(); // catches up on what was missed
        socket.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (BigInt(msg.timestamp) > lastTimestamp) {
                showMessage(msg);
            }
        };
        socket.onclose = () => {
            socket = null;
            setTimeout(connectWebSocket, 5000);
        };
    } catch (error) {
        console.error("Error connecting websocket:", error);
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
        alert("Invalid username or password");
    }
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
        alert("Registration successful! You can now log in.");
        document.getElementById("register-form").reset(); // Clear form
    } else {
        const error = await response.json();
        alert(`Registration failed: ${error.detail}`);
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
    }

    const logoutButton = document.getElementById("logout-btn");
    if (logoutButton) {
        logoutButton.addEventListener("click", logoutUser);
    }
});
