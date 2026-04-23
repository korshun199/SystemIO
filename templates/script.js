$(document).ready(function() {
    // Функция загрузки списка пользователей
    function loadUsers() {
        $.get('/api/users', function(users) {
            let rows = '';
            users.forEach(user => {
                rows += `<tr>
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.full_name}</td>
                    <td><span class="uk-label">${user.role}</span></td>
                    <td><span class="uk-text-success" uk-icon="icon: check"></span></td>
                </tr>`;
            });
            $('#user-list-table').html(rows);
        });
    }

    // Логин (пока простая проверка)
    $('#login-form').on('submit', function(e) {
    e.preventDefault();
    const user = $('#admin-login').val();
    const pass = $('#admin-pass').val();
    
    console.log("Попытка входа:", user); // Это появится в консоли Eruda

    // ВНИМАНИЕ: Проверь, чтобы ID полей в HTML совпадали с этими!
    if (user === 'Oleg_Boss' && pass === 'pass123') {
        console.log("Доступ разрешен!");
        $('#login-section').fadeOut(300, function() {
            $('#admin-dashboard').fadeIn();
            loadUsers(); 
        });
    } else {
        console.error("Ошибка входа: Неверные данные");
        UIkit.notification({message: 'Ошибка доступа!', status: 'danger'});
    }
});

    // Реальное добавление пользователя в БД
    $('#add-user-form').on('submit', function(e) {
        e.preventDefault();
        const userData = {
            username: $('#new-username').val(),
            fullname: $('#new-fullname').val(),
            password: $('#new-password').val(),
            role: $('#new-role').val()
        };

        $.ajax({
            url: '/api/users',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(userData),
            success: function() {
                UIkit.notification({message: 'Пользователь сохранен в БД!', status: 'success'});
                loadUsers(); // Обновляем таблицу
                $('#add-user-form')[0].reset();
            },
            error: function() {
                UIkit.notification({message: 'Ошибка! Возможно, логин занят.', status: 'danger'});
            }
        });
    });
});