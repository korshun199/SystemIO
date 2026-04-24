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

  // Единый цикл обновлений
  setInterval(() => {
    heartbeat();
    updateUsers();
    loadChat();
  }, 3000);

  heartbeat();
  updateUsers();
  loadChat();
}

function logout() {
  localStorage.removeItem("userData");
  location.reload();
}

function heartbeat() {
  if (!myData) return;
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
          // ВОЗВРАЩАЕМ СТАТУСЫ
          const statusIcon = u.is_online ? "● " : "○ ";
          opt.textContent = statusIcon + u.username.toUpperCase();
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
        box.scrollHeight - box.scrollTop <= box.clientHeight + 100;

      msgs.sort((a, b) => {
        let dateA = new Date(a.timestamp.replace(" ", "T"));
        let dateB = new Date(b.timestamp.replace(" ", "T"));
        return dateA - dateB || a.id - b.id;
      });

      box.innerHTML = msgs
        .map((m) => {
          let timeStr = "--:--";
          let dateStr = "";
          try {
            const parts = m.timestamp.split(" ");
            const dateParts = parts[0].split("-");
            dateStr = `${dateParts[2]}.${dateParts[1]}`;
            timeStr = parts[1].substring(0, 5);
          } catch (e) {}

          // ГЛАВНАЯ ЛОГИКА ВЫДЕЛЕНИЯ
          const isGeneral = m.receiver_id == 0; // Сообщение в общак
          const isToMe = m.receiver_id == myData.id; // Лично мне
          const isFromMe = m.sender_id == myData.id && m.receiver_id != 0; // Мой личный ответ

          let bgStyle = "background: #161616;"; // Стандартный фон
          let borderStyle = "border-left: 3px solid #00ff41;"; // Зеленый для общего
          let label = "";

          if (isToMe) {
            bgStyle = "background: #2a1010;"; // Темно-красный фон для входящей лички
            borderStyle = "border-left: 3px solid #ff3e3e;";
            label =
              "<small style='color: #ff3e3e; margin-left: 10px;'>[ЛИЧНО ВАМ]</small>";
          } else if (isFromMe) {
            bgStyle = "background: #101a10;"; // Темно-зеленый фон для исходящей лички
            borderStyle = "border-left: 3px solid #00ff41;";
            label =
              "<small style='color: #00ff41; margin-left: 10px;'>[ВАШ ШЕПОТ]</small>";
          }

          return `
              <div class="msg" style="${borderStyle} ${bgStyle} margin-bottom: 12px; padding: 8px; border-radius: 0 4px 4px 0;">
                  <div style="display: flex; justify-content: space-between; font-size: 0.75em; opacity: 0.8; margin-bottom: 5px;">
                      <span>
                          <b style="color: ${
                            m.sender_id == myData.id ? "#00ff41" : "#ff3e3e"
                          }">${m.sender_name.toUpperCase()}</b>
                          ${label}
                      </span>
                      <span style="color: #666;">${dateStr} | <strong style="color: #00ff41;">${timeStr}</strong></span>
                  </div>
                  <div style="color: #fff; font-family: sans-serif; font-size: 0.95em;">${
                    m.content
                  }</div>
              </div>
          `;
        })
        .join("");

      if (isAtBottom) box.scrollTop = box.scrollHeight;
    });
}

function send() {
  const input = document.getElementById("msg-input");
  const tid = document.getElementById("chat-target").value || 0;
  const val = input.value.trim();
  if (!val) return;

  fetch("/api/chat/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sender_id: myData.id,
      receiver_id: parseInt(tid),
      content: val,
    }),
  }).then(() => {
    input.value = "";
    loadChat();
  });
}
