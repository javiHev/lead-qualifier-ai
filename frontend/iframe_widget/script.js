// frontend/iframe_widget/script.js

const API_URL = "http://localhost:8001/chat";

const btn = document.getElementById("start-btn");
const leadNameInput = document.getElementById("lead-name");
const companyInput = document.getElementById("company");
const messagesDiv = document.getElementById("messages");

function appendMessage(who, text) {
  const el = document.createElement("div");
  el.className = `message ${who}`;
  el.innerText = text;
  messagesDiv.appendChild(el);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

btn.addEventListener("click", async () => {
  const leadName = leadNameInput.value.trim() || "SinNombre";
  const company = companyInput.value.trim() || "SinEmpresa";
  appendMessage("user", `Nombre: ${leadName}, Empresa: ${company}`);
  btn.disabled = true;
  leadNameInput.disabled = true;
  companyInput.disabled = true;

  appendMessage("bot", "Procesando tu información, por favor espera...");
  try {
    const resp = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lead_name: leadName, company: company })
    });
    const data = await resp.json();
    const result = data.result || {};

    // Mostrar información de cualificación
    if (result.get("qualification_task")) {
      const qual = result.qualification_task;
      appendMessage("bot", `🔍 Lead Score: ${qual.get("lead_score", "N/A")}`);
      appendMessage("bot", `✅ Estado: ${qual.get("qualification_status", "N/A")}`);
      appendMessage("bot", `💡 Recomendaciones: ${qual.get("next_actions", "Ninguna")}`);
      if (result.get("airtable_registration_task")) {
        const rec = result.airtable_registration_task;
        appendMessage("bot", `📋 Guardado en Airtable con ID: ${rec.get("record_id", "—")}`);
      }
    } else {
      appendMessage("bot", "Lo siento, no se pudo cualificar el lead.");
    }
  } catch (err) {
    appendMessage("bot", "⚠️ Error de conexión con el servidor.");
    console.error(err);
  }
});
