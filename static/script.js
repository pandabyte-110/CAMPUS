const messages = document.getElementById("messages");

function addMessage(text, type) {
  let msg = document.createElement("div");
  msg.className = "message " + type;

  let avatar = document.createElement("img");
  avatar.className = "avatar";
  avatar.src = type === "bot"
    ? "https://cdn-icons-png.flaticon.com/512/4712/4712027.png"
    : "https://cdn-icons-png.flaticon.com/512/847/847969.png";

  let bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerText = text;

  if (type === "bot") {
    msg.appendChild(avatar);
    msg.appendChild(bubble);
  } else {
    msg.appendChild(bubble);
    msg.appendChild(avatar);
  }

  messages.appendChild(msg);
  msg.scrollIntoView({ behavior: "smooth" });
}

function showTyping() {
  let div = document.createElement("div");
  div.className = "message bot";
  div.id = "typing";

  let bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerText = "Typing...";

  div.appendChild(bubble);
  messages.appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}
function removeTyping() {
  let typing = document.getElementById("typing");
  if (typing) typing.remove();
}

let sending = false;

function send() {
  if (sending) return;

  let msgInput = document.getElementById("msg");
  let msg = msgInput.value.trim();
  if (!msg) return;

  sending = true;

  addMessage(msg, "user");
  msgInput.value = "";

  showTyping();

  fetch("/get", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: "msg=" + encodeURIComponent(msg)
  })
  .then(response => response.json())
  .then(data => {
    removeTyping();
    addMessage(data.response, "bot");
    sending = false;
  })
  .catch(() => {
    removeTyping();
    addMessage("Error connecting to server.", "bot");
    sending = false;
  });
}

document.getElementById("msg").addEventListener("keypress", function(e) {
  if (e.key === "Enter") send();
});

function clearChat() {
  messages.innerHTML = "";
}

function openModal(src) {
  document.getElementById("imageModal").style.display = "block";
  document.getElementById("modalImg").src = src;
}

function closeModal() {
  document.getElementById("imageModal").style.display = "none";
}
// DARK MODE TOGGLE
function toggleDark() {
  document.body.classList.toggle("dark");
  localStorage.setItem("theme", document.body.classList.contains("dark"));
}

// LOAD THEME
window.onload = () => {
  if (localStorage.getItem("theme") === "true") {
    document.body.classList.add("dark");
  }
};

// SIMPLE FORM VALIDATION (LOGIN)
function validateLogin() {
  let email = document.getElementById("email").value;
  let password = document.getElementById("password").value;

  if (!email || !password) {
    alert("Please fill all fields");
    return false;
  }

  if (!email.includes("@")) {
    alert("Invalid email");
    return false;
  }

  return true;
}

// SUCCESS MESSAGE (ADMIN)
function showSuccess(msg) {
  let div = document.createElement("div");
  div.innerText = msg;
  div.style.background = "#22c55e";
  div.style.color = "white";
  div.style.padding = "10px";
  div.style.marginTop = "10px";
  div.style.borderRadius = "8px";

  document.body.prepend(div);

  setTimeout(() => div.remove(), 3000);
}