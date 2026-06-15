/****************************************************
 * Doctor Dashboard – Live Queue (WebSocket)
 * STEP 7 – MedQueue AI
 ****************************************************/

// --------------------------------------------------
// 1. Read doctor_id from template
// --------------------------------------------------
const doctorIdInput = document.getElementById("doctor-id");

if (!doctorIdInput) {
  console.error("Doctor ID not found in template.");
}

const doctorId = doctorIdInput ? doctorIdInput.value : null;


// --------------------------------------------------
// 2. WebSocket connection
// --------------------------------------------------
let socket = null;

if (doctorId) {
  socket = new WebSocket(
    `ws://${window.location.host}/ws/queue/doctor/${doctorId}/`
  );

  socket.onopen = () => {
    console.log("✅ WebSocket connected for doctor:", doctorId);
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("📡 Queue update:", data);

    // Any event → refresh queue
    fetchQueue();
  };

  socket.onerror = (error) => {
    console.error("❌ WebSocket error:", error);
  };

  socket.onclose = () => {
    console.warn("⚠️ WebSocket closed");
  };
}


// --------------------------------------------------
// 3. Fetch doctor queue (REST API)
// --------------------------------------------------
function fetchQueue() {
  fetch(`/api/tokens/doctor/${doctorId}/`)
    .then(response => response.json())
    .then(tokens => renderQueue(tokens))
    .catch(error => console.error("Queue fetch failed:", error));
}

// Initial load
if (doctorId) {
  fetchQueue();
}


// --------------------------------------------------
// 4. Render queue in UI
// --------------------------------------------------
function renderQueue(tokens) {
  const list = document.getElementById("queue-list");
  list.innerHTML = "";

  if (!tokens.length) {
    list.innerHTML = "<li>No patients in queue</li>";
    return;
  }

  tokens.forEach(token => {
    const li = document.createElement("li");

    let statusLabel = "";
    if (token.status === "in_service") {
      statusLabel = " 🟢 In Service";
    }

    li.innerHTML = `
      <strong>Token ${token.token_number}</strong>
      ${token.priority === 1 ? " 🚨 Emergency" : ""}
      ${statusLabel}
      <br/>
      <button onclick="callToken(${token.id})">Call</button>
      <button onclick="skipToken(${token.id})">Skip</button>
      <button onclick="markEmergency(${token.id})">Emergency</button>
    `;

    list.appendChild(li);
  });
}


// --------------------------------------------------
// 5. Token Actions (API calls)
// --------------------------------------------------
function callToken(tokenId) {
  fetch(`/api/tokens/${tokenId}/call/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken()
    }
  });
}

function skipToken(tokenId) {
  fetch(`/api/tokens/${tokenId}/skip/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken()
    }
  });
}

function markEmergency(tokenId) {
  fetch(`/api/tokens/${tokenId}/priority/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ priority: 1 })
  });
}


// --------------------------------------------------
// 6. CSRF helper
// --------------------------------------------------
function getCSRFToken() {
  const token = document.querySelector('[name=csrfmiddlewaretoken]');
  return token ? token.value : "";
}
