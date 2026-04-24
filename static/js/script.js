let myData = JSON.parse(localStorage.getItem("userData"));

const sync = (el) => {
  const val = $(el).val();
  $(".chat-sync").val(val);
  loadChat();
};

const auth = () => {
  const u = $("#login-user").val();
  const p = $("#login-pass").val();
  $.ajax({
    url: "/api/login",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ username: u, password: p }),
    success: (res) => {
      if (res.status === "ok") {
        localStorage.setItem("userData", JSON.stringify(res.user));
        myData = res.user;
        showMain();
      } else {
        $("#login-error").text(res.message);
      }
    },
  });
};

const showMain = () => {
  $("#login-screen").addClass("hidden");
  $("#main-screen").removeClass("hidden").css("display", "flex");
  $("#display-name").text(myData.username.toUpperCase());

  if (myData.id === 1 || myData.username.toLowerCase() === "admin") {
    $("#admin-btn").removeClass("hidden");
  }

  if (window.chatInterval) clearInterval(window.chatInterval);
  window.chatInterval = setInterval(() => {
    heartbeat();
    updateUsers();
    loadChat();
  }, 3000);
  heartbeat();
  updateUsers();
  loadChat();
};

const logout = () => {
  localStorage.removeItem("userData");
  location.reload();
};

const heartbeat = () => {
  if (!myData) return;
  $.ajax({
    url: "/api/heartbeat",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ user_id: myData.id }),
  });
};

const updateUsers = () => {
  $.get("/api/users", (data) => {
    const selects = $(".chat-sync");
    const currentVal = selects.val() || "0";
    selects.each(function () {
      const s = $(this);
      s.empty().append('<option value="0">🌍 ОБЩИЙ КАНАЛ</option>');
      data.forEach((u) => {
        if (u.id != myData.id) {
          const dot = u.is_online ? "●" : "○";
          const color = u.is_online ? "#32d296" : "#888";
          const opt = $("<option>")
            .val(u.id)
            .text(`${dot} ${u.username.toUpperCase()}`)
            .css("color", color);
          s.append(opt);
        }
      });
      s.val(currentVal);
    });
  });
};

const loadChat = () => {
  const tid = $(".chat-sync").val() || 0;
  const url =
    tid == "0"
      ? `/api/chat/main/${myData.id}`
      : `/api/chat/private/${myData.id}/${tid}`;
  $.get(url, (msgs) => {
    const box = $("#chat-box");
    const isAtBottom =
      box[0].scrollHeight - box.scrollTop() <= box.outerHeight() + 100;
    msgs.sort(
      (a, b) =>
        new Date(a.timestamp.replace(" ", "T")) -
          new Date(b.timestamp.replace(" ", "T")) || a.id - b.id
    );

    const html = msgs
      .map((m) => {
        // Формируем дату и время (24.04 | 10:49)
        let timeStr = "--:--";
        let dateStr = "";
        if (m.timestamp) {
          const parts = m.timestamp.split(" ");
          const dateParts = parts[0].split("-");
          dateStr = `${dateParts[2]}.${dateParts[1]}`; // 24.04
          timeStr = parts[1].substring(0, 5); // 10:49
        }

        let bubbleClass = m.sender_id == myData.id ? "msg-right" : "msg-left";
        if (m.receiver_id == myData.id) bubbleClass += " msg-private";

        return `
                <div class="msg-bubble ${bubbleClass}">
                    <div class="uk-flex uk-flex-between uk-margin-small-bottom">
                        <span class="uk-text-bold" style="font-size: 0.75em; color: #32d296;">${m.sender_name.toUpperCase()}</span>
                        <span class="uk-text-muted" style="font-size: 0.65em;">${dateStr} | ${timeStr}</span>
                    </div>
                    <div style="font-size: 0.9em; word-wrap: break-word;">${
                      m.content
                    }</div>
                </div>
            `;
      })
      .join("");
    box.html(html);
    if (isAtBottom) box.scrollTop(box[0].scrollHeight);
  });
};

const send = () => {
  const input = $("#msg-input");
  const tid = $(".chat-sync").val() || 0;
  const val = input.val().trim();
  if (!val) return;
  $.ajax({
    url: "/api/chat/send",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      sender_id: myData.id,
      receiver_id: parseInt(tid),
      content: val,
    }),
    success: () => {
      input.val("");
      loadChat();
    },
  });
};

$(document).ready(() => {
  if (myData) showMain();
  $("#msg-input").on("keypress", (e) => {
    if (e.which === 13) send();
  });
});
