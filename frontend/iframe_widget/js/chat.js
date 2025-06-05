/**
 * chat.js
 *
 * - Inserta el mensaje de usuario al hacer clic o pulsar Enter.
 * - Muestra el indicador "robot tipeando" de inmediato.
 * - Lanza la petición POST /chat/stream y consume el ReadableStream.
 * - Añade cada delta de la respuesta en tiempo real en la burbuja de asistente.
 * - Al acabar, elimina el indicador y guarda el texto final.
 * - Maneja "Shift+Enter" para nueva línea.
 * - Botón "✕" finaliza la conversación con POST /chat/finish.
 */

(() => {
  // ================================
  // 1) CONFIGURACIÓN (ajusta si hace falta)
  // ================================
  const API_BASE_URL = "http://127.0.0.1:8000";
  const STREAM_ENDPOINT = API_BASE_URL + "/chat/stream";
  const FINISH_ENDPOINT = API_BASE_URL + "/chat/finish";

  // ================================
  // 2) SELECTORES DEL DOM
  // ================================
  const messagesContainer = document.getElementById("messages");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const endChatBtn = document.getElementById("end-chat-btn");

  // Conversación (para enviar al backend)
  const conversation = [];
  let isStreaming = false;

  // ================================
  // 3) FUNCIONES AUXILIARES DE UI
  // ================================

  /**
   * Crea y retorna un div.message con la clase correspondiente.
   * role: "user" | "assistant" | "system"
   */
  function appendMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", role);
    msgDiv.textContent = text;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
  }

  /**
   * Muestra un texto de sistema en pantalla (errores, avisos).
   */
  function appendSystemMessage(text) {
    appendMessage("system", text);
  }

  /**
   * Habilita/deshabilita el textarea y el botón de enviar.
   */
  function setInputDisabled(disabled) {
    userInput.disabled = disabled;
    sendBtn.disabled = disabled;
    sendBtn.style.opacity = disabled ? "0.6" : "1";
  }

  /**
   * Ajusta dinámicamente la altura del textarea (muy parecido a OpenAI).
   */
  function adjustTextareaHeight() {
    userInput.classList.add("truncate");
    userInput.style.height = "auto";
    userInput.style.height = `${userInput.scrollHeight}px`;
  }

  /**
   * Crea y devuelve el indicador “robot tipeando” (burbuja centrada).
   */
  function createTypingIndicator() {
    const container = document.createElement("div");
    container.classList.add("typing-indicator");

    // Robot icon
    const robot = document.createElement("div");
    robot.classList.add("robot-icon");
    // Ojos
    const eyeL = document.createElement("div");
    eyeL.classList.add("eye", "left");
    const eyeR = document.createElement("div");
    eyeR.classList.add("eye", "right");
    robot.appendChild(eyeL);
    robot.appendChild(eyeR);

    // Puntos que rebotan
    const dots = document.createElement("div");
    dots.classList.add("dots");
    for (let i = 0; i < 3; i++) {
      const span = document.createElement("span");
      dots.appendChild(span);
    }

    container.appendChild(robot);
    container.appendChild(dots);
    return container;
  }

  // ================================
  // 4) PARSING DEL STREAM (SSE SIMULADO)
  // ================================

  /**
   * Dado un ReadableStream (body de fetch), parsea datos SSE (“data: {...}”).
   * Por cada chunk JSON que encuentre, llama a onChunk(obj).
   */
  async function parseSseStream(stream, onChunk) {
    const reader = stream.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop(); // última parte (incompleta)

      for (const part of parts) {
        const trimmed = part.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith("data:")) {
          const jsonStr = trimmed.replace(/^data:\s*/, "");
          try {
            const obj = JSON.parse(jsonStr);
            onChunk(obj);
          } catch (e) {
            console.error("Error parseando SSE chunk:", e, jsonStr);
          }
        }
      }
    }
  }

  // ================================
  // 5) FUNCIÓN PRINCIPAL: ENVIAR MENSAJE Y PROCESAR STREAMING
  // ================================

  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isStreaming) return;

    // ─── 5.1) INSERTAR LA BURBUJA DEL USUARIO ───
    appendMessage("user", text);
    conversation.push({ role: "user", content: text });

    // ─── 5.2) PREPARAR LA UI PARA STREAMING ───
    userInput.value = "";
    adjustTextareaHeight();
    setInputDisabled(true);
    isStreaming = true;

    // ─── 5.3) CREAR EL CONTENEDOR DEL ASISTENTE (BURBUJA + INDICADOR) ───
    // Creamos la burbuja vacía de asistente pero NO le ponemos texto aún.
    const assistantMsgDiv = document.createElement("div");
    assistantMsgDiv.classList.add("message", "assistant");
    assistantMsgDiv.textContent = "";
    messagesContainer.appendChild(assistantMsgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Ahora creamos el typing indicator y lo situamos justo debajo de la burbuja vacía
    const typingIndicator = createTypingIndicator();
    messagesContainer.appendChild(typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // ─── 5.4) LANZAR LA PETICIÓN POST CON STREAMING ───
    try {
      const resp = await fetch(STREAM_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: conversation }),
      });

      if (!resp.ok || !resp.body) {
        const errorText = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${errorText}`);
      }

      // ─── 5.5) PARSEAR CADA CHUNK DEL STREAM SSE ───
      await parseSseStream(resp.body, (chunk) => {
        // chunk = { role: "assistant", delta: "texto parcial" }
        assistantMsgDiv.textContent += chunk.delta;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      });

      // ─── 5.6) AL TERMINAR, ELIMINAR INDICADOR Y GUARDAR MENSAJE FINAL ───
      typingIndicator.remove();
      const finalText = assistantMsgDiv.textContent.trim();
      conversation.push({ role: "assistant", content: finalText });
    } catch (error) {
      console.error("Error durante streaming:", error);
      appendSystemMessage(
        "❗ Ha ocurrido un error. Inténtalo de nuevo en unos segundos."
      );
      assistantMsgDiv.remove();
      typingIndicator.remove();
    } finally {
      isStreaming = false;
      setInputDisabled(false);
    }
  }

  // ================================
  // 6) FINALIZAR CHAT (/chat/finish)
  // ================================

  async function endChat() {
    if (isStreaming) return; // Esperar a que termine

    if (!confirm("¿Seguro que deseas finalizar y enviar el lead?")) {
      return;
    }

    appendSystemMessage("⏳ Enviando lead para calificación...");

    try {
      const payload = {
        messages: conversation,
        user_id: null,
        session_id: null,
      };
      const resp = await fetch(FINISH_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const errorText = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${errorText}`);
      }

      const data = await resp.json();
      if (data.success) {
        appendSystemMessage(
          `✅ Lead enviado correctamente. ID CRM: ${data.airtable_record_id}`
        );
        if (data.summary) {
          appendMessage("assistant", "📝 Resumen de conversación:");
          appendMessage("assistant", data.summary);
        }
        setInputDisabled(true);
        sendBtn.style.display = "none";
        endChatBtn.disabled = true;
      } else {
        throw new Error("Servidor respondió success=false");
      }
    } catch (error) {
      console.error("Error finalizando chat:", error);
      appendSystemMessage(
        "❗ Error al enviar la información. Inténtalo nuevamente más tarde."
      );
    }
  }

  // ================================
  // 7) EVENT LISTENERS
  // ================================
  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("input", adjustTextareaHeight);

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  endChatBtn.addEventListener("click", endChat);

  // Al cargar la página, ajustar altura inicial y enfocar
  window.addEventListener("load", () => {
    adjustTextareaHeight();
    userInput.focus();
  });
})();
