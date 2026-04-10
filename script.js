let currentUser = null;
let currentTarget = "all";
const socket = io();

// 1. ЗАГРУЗКА ИСТОРИИ
function loadHistory() {
  if (!currentUser) return;

  let url = `/api/history?to_id=${currentTarget}`;
  if (currentTarget === "all") {
    url += `&for_user=${currentUser.id}`;
  }

  $.get(url, function (msgs) {
    $("#chat-messages").empty();
    msgs.forEach((m) => renderMessage(m));
  });
}

// 2. ОТРИСОВКА СООБЩЕНИЯ
function renderMessage(m) {
  const isPrivate = m.to_id !== null && m.to_id !== undefined;
  const borderStyle = isPrivate
    ? 'style="border-left: 3px solid #ff00ff; background: #1a1a1a;"'
    : "";
  const label = isPrivate
    ? '<span style="color: #ff00ff; font-size: 0.7rem; font-weight: bold;">[ЛИЧНО]</span> '
    : "";

  const html = `
        <div class="msg-item" ${borderStyle}>
            <span class="msg-author">${label}${m.username}:</span>
            <span class="msg-text">${m.content}</span>
        </div>`;

  $("#chat-messages").append(html);
  const container = $("#chat-messages");
  container.scrollTop(container[0].scrollHeight);
}

// 3. ПЕРЕКЛЮЧЕНИЕ МЕЖДУ ЧАТАМИ
function switchChat(id) {
  currentTarget = id;
  $(".user-item").removeClass("active");
  $(`#target-${id}`).addClass("active");

  const name = $(`#target-${id}`).text().replace("●", "").trim();
  $("#chat-title").text(name);

  loadHistory();
}

$(document).ready(function () {
  console.log("SystemIO Live: Системы запущены...");

  // ЛОГИКА ВХОДА
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

          // РИСУЕМ СПИСОК СЛЕВА
          const list = $("#user-list");
          list.empty(); // Полная очистка перед отрисовкой

          // Сначала всегда Общий Чат
          list.append(`
                        <div class="user-item active" id="target-all" onclick="switchChat('all')">
                            <span class="status-dot">●</span> 📢 ВЕСЬ КОРПУС
                        </div>
                    `);

          // Добавляем остальных (кроме себя)
          users.forEach((u) => {
            if (u.id !== currentUser.id) {
              list.append(`
                                <div class="user-item" id="target-${u.id}" onclick="switchChat(${u.id})">
                                    <span class="status-dot">●</span> ${u.full_name}
                                </div>
                            `);
            }
          });

          loadHistory();
        });
      } else {
        alert("Ошибка доступа: Пользователь не найден в базе Корпуса.");
      }
    });
  });

  // ОТПРАВКА СООБЩЕНИЯ
  $("#send-form").on("submit", function (e) {
    e.preventDefault();
    const txt = $("#msg-input").val().trim();
    if (!txt || !currentUser) return;

    socket.emit("send_msg", {
      from_id: currentUser.id,
      username: currentUser.username,
      content: txt,
      to_id: currentTarget === "all" ? null : currentTarget,
    });

    $("#msg-input").val("");
  });

  // ПРИЕМ НОВЫХ СООБЩЕНИЙ
  socket.on("new_msg", function (data) {
    if (currentTarget === "all") {
      const isMyPrivate =
        data.to_id == currentUser.id || data.from_id == currentUser.id;
      if (!data.to_id || isMyPrivate) {
        renderMessage(data);
      }
    } else {
      const otherSide =
        data.from_id == currentUser.id ? data.to_id : data.from_id;
      if (currentTarget == otherSide) {
        renderMessage(data);
      } else {
        UIkit.notification({
          message: `Сообщение от ${data.username}`,
          status: "primary",
        });
      }
    }
  });

  // ОБНОВЛЕНИЕ СТАТУСОВ (Зеленый неон)
  socket.on("status_update", function (onlineIds) {
    $(".user-item").each(function () {
      const elementId = $(this).attr("id");
      if (elementId && elementId !== "target-all") {
        const userId = parseInt(elementId.replace("target-", ""));
        const isOnline = onlineIds.includes(userId);
        $(this).toggleClass("online", isOnline);
      }
    });
  });
});
