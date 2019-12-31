// Settings Page
$(function(){
    $('#sonarr_check').on('click', function() {
        alite({
            url: '/sonarr/check',
            method: 'POST',
            data: {
                url: $("#sonarr_url").val().trim(),
                apikey: $("#sonarr_apikey").val().trim()
            },
        }).then(function (result) {
            console.log('sonarr_check result: ', result);
            // TODO: A toastr would be nice here instead
            if (result == 'ERR') {
                // apikey was invalid
                $("#sonarr_check").removeClass("btn-success").addClass("btn-danger");
            } else {
                // apikey was valid
                $("#sonarr_check").removeClass("btn-danger").addClass("btn-success");
            }
        }).catch(function (err) {
            console.error('sonarr_check error: ', err);
            $("#sonarr_check").removeClass("btn-success").addClass("btn-danger");
        });        
    });

    $('#radarr_check').on('click', function() {
        alite({
            url: '/radarr/check',
            method: 'POST',
            data: {
                url: $("#radarr_url").val().trim(),
                apikey: $("#radarr_apikey").val().trim()
            },
        }).then(function (result) {
            console.log('radarr_check result: ', result);
            if (result == 'ERR') {
                // apikey was invalid
                $("#radarr_check").removeClass("btn-success").addClass("btn-danger");
            } else {
                // apikey was valid
                $("#radarr_check").removeClass("btn-danger").addClass("btn-success");
            }
        }).catch(function (err) {
            console.error('radarr_check error: ', err);
            $("#radarr_check").removeClass("btn-success").addClass("btn-danger");
        });
    });
});
