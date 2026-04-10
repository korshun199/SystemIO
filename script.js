let currentUser = null;
const socket = io(); // Подключаемся к серверу

$(document).ready(function () {
  console.log("SystemIO: Скрипт загружен и готов!");

  // Логика входа
  $("#login-form").on("submit", function (e) {
    e.preventDefault();
    const username = $("#login-name").val().trim();
    console.log("Пытаемся войти как:", username);

    $.get("/api/users", function (users) {
      console.log("Пользователи в базе:", users);
      const user = users.find(
        (u) => u.username.toLowerCase() === username.toLowerCase()
      );

      if (user) {
        currentUser = user;
        console.log("Успех! Входим как:", user.full_name);

        $("#login-section").fadeOut(300, function () {
          $("#chat-section").css("display", "flex");
          $("#my-name").text(user.full_name);

          // Заполняем список пользователей
          $("#chat-target").html('<option value="all">📢 ВЕСЬ КОРПУС</option>');
          users.forEach((u) => {
            if (u.id !== currentUser.id) {
              $("#chat-target").append(
                `<option value="${u.id}">${u.full_name}</option>`
              );
            }
          });
          loadHistory();
        });
      } else {
        console.error("Пользователь не найден!");
        UIkit.notification({
          message: "Ошибка: Пользователь не найден!",
          status: "danger",
        });
      }
    }).fail(function () {
      UIkit.notification({
        message: "Ошибка сервера! Проверь app.py",
        status: "danger",
      });
    });
  });

  // Загрузка истории
  function loadHistory() {
    const target = $("#chat-target").val();
    $.get(`/api/history?to_id=${target}`, function (msgs) {
      $("#chat-messages").empty();
      msgs.forEach((m) => renderMessage(m));
    });
  }

  function renderMessage(m) {
    const html = `
            <div class="msg-item">
                <span class="msg-author">${m.username}:</span>
                <span class="msg-text">${m.content}</span>
            </div>`;
    $("#chat-messages").append(html);
    $("#chat-messages").scrollTop($("#chat-messages")[0].scrollHeight);
  }

  // Смена чата
  $("#chat-target").on("change", function () {
    loadHistory();
  });

  // Отправка сообщения
  $("#send-form").on("submit", function (e) {
    e.preventDefault();
    const content = $("#msg-input").val().trim();
    if (!content) return;

    const target = $("#chat-target").val();
    socket.emit("send_msg", {
      from_id: currentUser.id,
      username: currentUser.username,
      content: content,
      to_id: target === "all" ? null : target,
    });
    $("#msg-input").val("");
  });

  // Прием сообщений в реальном времени
  socket.on("new_msg", function (data) {
    const currentTarget = $("#chat-target").val();
    // Показываем, если это общий чат или личка нам/от нас
    if (
      !data.to_id ||
      data.to_id == currentUser.id ||
      data.from_id == currentUser.id
    ) {
      renderMessage(data);
    }
  });
});
