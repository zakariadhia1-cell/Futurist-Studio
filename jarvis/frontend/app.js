const API_BASE = "";

const orb = document.getElementById("orb");
const statusEl = document.getElementById("status");
const transcriptEl = document.getElementById("transcript");
const micBtn = document.getElementById("micBtn");
const activateBtn = document.getElementById("activateBtn");
const player = document.getElementById("player");

let history = [];
let recognition = null;
let isListening = false;

function setStatus(text) {
  statusEl.textContent = text;
}

function setMode(mode) {
  orb.classList.remove("listening", "thinking");
  if (mode) orb.classList.add(mode);
}

function speakFallback(text) {
  if (!("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "de-DE";
  window.speechSynthesis.speak(utterance);
}

async function playReply(text, audioBase64) {
  setMode(null);
  setStatus("Jarvis antwortet");
  transcriptEl.textContent = text;

  if (audioBase64) {
    player.src = `data:audio/mpeg;base64,${audioBase64}`;
    try {
      await player.play();
      return;
    } catch (err) {
      // fall through to speechSynthesis fallback
    }
  }
  speakFallback(text);
}

async function sendMessage(message) {
  setMode("thinking");
  setStatus("Jarvis denkt nach ...");
  try {
    const resp = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
    if (!resp.ok) throw new Error(`Server-Fehler ${resp.status}`);
    const data = await resp.json();
    history = data.history;
    await playReply(data.text, data.audio_base64);
  } catch (err) {
    setMode(null);
    setStatus("Fehler bei der Verbindung zu Jarvis");
    console.error(err);
  }
}

async function activateJarvis() {
  setMode("thinking");
  setStatus('"Jarvis activate" ...');
  try {
    const resp = await fetch(`${API_BASE}/api/activate`, { method: "POST" });
    if (!resp.ok) throw new Error(`Server-Fehler ${resp.status}`);
    const data = await resp.json();
    history = data.history;
    await playReply(data.text, data.audio_base64);
  } catch (err) {
    setMode(null);
    setStatus("Fehler bei der Verbindung zu Jarvis");
    console.error(err);
  }
}

function setupRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    setStatus("Spracherkennung wird von diesem Browser nicht unterstuetzt (Chrome empfohlen).");
    micBtn.disabled = true;
    return;
  }
  recognition = new SpeechRecognition();
  recognition.lang = "de-DE";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isListening = true;
    setMode("listening");
    setStatus("Ich hoere zu ...");
  };

  recognition.onresult = (event) => {
    const said = event.results[0][0].transcript;
    transcriptEl.textContent = said;
    sendMessage(said);
  };

  recognition.onerror = (event) => {
    setMode(null);
    setStatus(`Spracherkennung-Fehler: ${event.error}`);
  };

  recognition.onend = () => {
    isListening = false;
    if (!orb.classList.contains("thinking")) setMode(null);
  };
}

micBtn.addEventListener("click", () => {
  if (!recognition) return;
  if (isListening) {
    recognition.stop();
  } else {
    recognition.start();
  }
});

activateBtn.addEventListener("click", activateJarvis);

window.addEventListener("keydown", (event) => {
  if (event.code === "Space" && !event.repeat && document.activeElement === document.body) {
    event.preventDefault();
    if (recognition && !isListening) recognition.start();
  }
});

setupRecognition();
setStatus("Bereit. Klicke auf Sprechen oder Aktivieren.");
