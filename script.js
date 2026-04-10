let currentUser = null;
const socket = io();

// 1. Функция загрузки истории
function loadHistory() {
  const target = $("#chat-target").val();
  $.get(`/api/history?to_id=${target}`, function (msgs) {
    $("#chat-messages").empty();
    msgs.forEach((m) => renderMessage(m));
  });
}

// 2. Функция отрисовки одного сообщения
function renderMessage(m) {
  const isPrivate = m.to_id !== null && m.to_id !== undefined;
  const privateClass = isPrivate ? 'style="border-left-color: #ff00ff;"' : ""; // Розовый бок для лички
  const privateLabel = isPrivate
    ? '<span style="color: #ff00ff; font-size: 0.7rem;">[ЛИЧНОЕ]</span> '
    : "";

  const html = `
        <div class="msg-item" ${privateClass}>
            <span class="msg-author">${privateLabel}${m.username}:</span>
            <span class="msg-text">${m.content}</span>
        </div>`;
  $("#chat-messages").append(html);
  $("#chat-messages").scrollTop($("#chat-messages")[0].scrollHeight);
}

$(document).ready(function () {
  console.log("SystemIO: Запуск...");

  // Логика входа
  $("#login-form").on("submit", function (e) {
    e.preventDefault();
    const username = $("#login-name").val().trim();

    $.get("/api/users", function (users) {
      const user = users.find(
        (u) => u.username.toLowerCase() === username.toLowerCase()
      );
      if (user) {
        currentUser = user;
        $("#login-section").fadeOut(300, function () {
          $("#chat-section").css("display", "flex");
          $("#my-name").text(user.full_name);

          socket.emit("go_online", { user_id: user.id });

          // Заполняем список
          $("#chat-target").html('<option value="all">📢 ВЕСЬ КОРПУС</option>');
          users.forEach((u) => {
            if (u.id !== currentUser.id) {
              $("#chat-target").append(
                `<option value="${u.id}">${u.full_name} (оффлайн)</option>`
              );
            }
          });
          loadHistory();
        });
      } else {
        alert("Незнакомец!");
      }
    });
  });

  // Смена цели чата (Общий / Личка)
  $("#chat-target").on("change", function () {
    loadHistory();
  });

  // Отправка
  $("#send-form").on("submit", function (e) {
    e.preventDefault();
    const content = $("#msg-input").val().trim();
    if (!content || !currentUser) return;

    const target = $("#chat-target").val();
    socket.emit("send_msg", {
      from_id: currentUser.id,
      username: currentUser.username,
      content: content,
      to_id: target === "all" ? null : target,
    });
    $("#msg-input").val("");
  });

  // Слушаем новые сообщения
  socket.on("new_msg", function (data) {
    const currentTarget = $("#chat-target").val();

    // Логика отображения:
    // 1. Сообщение в общий чат и мы в общем чате
    // 2. Личное сообщение нам или от нас, и мы в чате с этим человеком
    if (!data.to_id && currentTarget === "all") {
      renderMessage(data);
    } else if (data.to_id) {
      const otherSide =
        data.from_id == currentUser.id ? data.to_id : data.from_id;
      if (currentTarget == otherSide) {
        renderMessage(data);
      } else {
        UIkit.notification({
          message: `Новое личное от ${data.username}`,
          status: "primary",
        });
      }
    }
  });

  // Обновление статусов ОНЛАЙН
  socket.on("status_update", function (onlineIds) {
    $("#chat-target option").each(function () {
      const val = $(this).val();
      if (val !== "all") {
        const isOnline = onlineIds.includes(parseInt(val));
        const baseText = $(this).text().split(" ●")[0].split(" (")[0];
        $(this).text(
          isOnline ? `${baseText} ● В СЕТИ` : `${baseText} (оффлайн)`
        );
        $(this).css("color", isOnline ? "#00ff41" : "#fff");
      }
    });
  });
});
