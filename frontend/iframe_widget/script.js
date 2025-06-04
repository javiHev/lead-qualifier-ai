// frontend/iframe_widget/script.js

const WS_URL = "ws://localhost:8000/ws";

const messagesDiv = document.getElementById("messages");
const form = document.getElementById("input-area");
const input = document.getElementById("msg-input");

function appendMessage(who, text) {
  const el = document.createElement("div");
  el.className = `message ${who}`;
  el.innerText = text;
  messagesDiv.appendChild(el);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

const ws = new WebSocket(WS_URL);

ws.addEventListener("open", () => {
  appendMessage("system", "Conectado al servidor WebSocket");
});

ws.addEventListener("message", (event) => {
  appendMessage("bot", event.data);
});

ws.addEventListener("close", () => {
  appendMessage("system", "Conexi\u00f3n cerrada");
});

ws.addEventListener("error", () => {
  appendMessage("system", "Error de conexi\u00f3n");
});

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  appendMessage("user", text);
  ws.send(text);
  input.value = "";
  input.focus();
});
