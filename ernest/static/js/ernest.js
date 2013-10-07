(function() {
    function init() {
        $('.login-form').hide();

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

        $('#login-link').on('click', function() {
            $('#login-link').hide();
            $('.login-form').show();
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
