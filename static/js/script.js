let myData = JSON.parse(localStorage.getItem("userData"));

document.addEventListener("DOMContentLoaded", () => {
  if (myData) {
    showMain();
  } else {
    document.getElementById("login-screen").classList.remove("hidden");
  }

  document.getElementById("msg-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") send();
  });
});

function auth() {
  const u = document.getElementById("login-user").value;
  const p = document.getElementById("login-pass").value;

  fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: u, password: p }),
  })
    .then((res) => res.json())
    .then((res) => {
      if (res.status === "ok") {
        localStorage.setItem("userData", JSON.stringify(res.user));
        myData = res.user;
        showMain();
      } else {
        document.getElementById("login-error").textContent = res.message;
      }
    });
}

function showMain() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("main-screen").classList.remove("hidden");
  document.getElementById("display-name").textContent =
    myData.username.toUpperCase();

  // Запуск циклов
  setInterval(heartbeat, 15000);
  setInterval(updateUsers, 5000);
  setInterval(loadChat, 3000);

  heartbeat();
  updateUsers();
  loadChat();
}

function logout() {
  localStorage.removeItem("userData");
  location.reload();
}

function heartbeat() {
  fetch("/api/heartbeat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: myData.id }),
  });
}

function updateUsers() {
  fetch("/api/users")
    .then((res) => res.json())
    .then((data) => {
      const select = document.getElementById("chat-target");
      const current = select.value;
      select.innerHTML = '<option value="0">-- ОБЩИЙ КАНАЛ --</option>';
      data.forEach((u) => {
        if (u.id != myData.id) {
          const opt = document.createElement("option");
          opt.value = u.id;
          opt.textContent =
            (u.is_online ? "● " : "○ ") + u.username.toUpperCase();
          if (u.is_online) opt.style.color = "#00ff41";
          select.appendChild(opt);
        }
      });
      select.value = current;
    });
}

function loadChat() {
  const tid = document.getElementById("chat-target").value || 0;
  const url =
    tid == "0"
      ? `/api/chat/main/${myData.id}`
      : `/api/chat/private/${myData.id}/${tid}`;

  fetch(url)
    .then((res) => res.json())
    .then((msgs) => {
      const box = document.getElementById("chat-box");
      const isAtBottom =
        box.scrollHeight - box.scrollTop <= box.clientHeight + 50;

      box.innerHTML = msgs
        .map(
          (m) => `
            <div class="msg">
                <b style="color:${
                  m.sender_id == myData.id ? "#00ff41" : "#ff3e3e"
                }">${m.sender_name}:</b> ${m.content}
            </div>
        `
        )
        .join("");

      if (isAtBottom) box.scrollTop = box.scrollHeight;
    });
}

function send() {
  const input = document.getElementById("msg-input");
  const tid = document.getElementById("chat-target").value || 0;
  if (!input.value.trim()) return;

  fetch("/api/chat/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sender_id: myData.id,
      receiver_id: parseInt(tid),
      content: input.value.trim(),
    }),
  }).then(() => {
    input.value = "";
    loadChat();
  });
}
