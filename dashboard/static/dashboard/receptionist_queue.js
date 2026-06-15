/****************************************************
 * Receptionist Live Queue – STEP 8
 ****************************************************/

let socket = null;
let currentDoctorId = null;

// DOM
const doctorSelect = document.getElementById("doctor-select");
const queueList = document.getElementById("queue-list");

// ----------------------------------------
// Doctor selection
// ----------------------------------------
doctorSelect.addEventListener("change", () => {
  const doctorId = doctorSelect.value;

  if (!doctorId) {
    queueList.innerHTML = "";
    closeSocket();
    return;
  }

  currentDoctorId = doctorId;
  connectSocket(doctorId);
  fetchQueue(doctorId);
});

// ----------------------------------------
// WebSocket logic
// ----------------------------------------
function connectSocket(doctorId) {
  closeSocket();

  socket = new WebSocket(
    `ws://${window.location.host}/ws/queue/doctor/${doctorId}/`
  );

  socket.onopen = () => {
    console.log("✅ Receptionist connected to doctor", doctorId);
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("📡 Queue update:", data);
    fetchQueue(currentDoctorId);
  };

  socket.onclose = () => {
    console.warn("⚠️ WebSocket closed");
  };
}

function closeSocket() {
  if (socket) {
    socket.close();
    socket = null;
  }
}

// ----------------------------------------
// Fetch queue
// ----------------------------------------
function fetchQueue(doctorId) {
  fetch(`/api/tokens/doctor/${doctorId}/`)
    .then(res => res.json())
    .then(data => renderQueue(data));
}

// ----------------------------------------
// Render queue
// ----------------------------------------
function renderQueue(tokens) {
  queueList.innerHTML = "";

  if (!tokens.length) {
    queueList.innerHTML = "<li>No patients in queue</li>";
    return;
  }

  tokens.forEach(token => {
    const li = document.createElement("li");
    li.innerHTML = `
      <strong>Token ${token.token_number}</strong>
      ${token.priority === 1 ? " 🚨 Emergency" : ""}
      (${token.status})
    `;
    queueList.appendChild(li);
  });
}
