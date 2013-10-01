(function() {
    function init() {
        $('#login-submit').on('click', function() {
            var jqxhr;

            jqxhr = $.ajax({
                contentType: 'application/json',
                data: JSON.stringify({
                    'login': $('#login-field').val(),
                    'password': $('#password-field').val()
                }),
                dataType: 'json',
                success: function(data, textStatus, jqxhr) {
                    window.location.href = '/';
                },
                error: function(jqxhr, textStatus, errorThrown) {
                    console.log(textStatus);
                },
                type: 'POST',
                url: '/api/login'
            });
        });

        $('#logout-link').on('click', function() {
            var jqxhr;

            jqxhr = $.ajax({
                contentType: 'application/json',
                success: function(data, textStatus, jqxhr) {
                    window.location.href = '/';
                },
                error: function(jqxhr, textStatus, errorThrown) {
                    console.log(textStatus);
                },
                type: 'POST',
                url: '/api/logout'
            });
        });
    }

    $(init);
}());
