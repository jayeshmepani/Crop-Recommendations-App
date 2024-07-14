$(document).ready(function () {
    $('#cropForm').submit(function (event) {
        event.preventDefault();

        // Gather form data
        var formData = {
            'place': $('#place').val()
        };

        // Send AJAX POST request
        $.ajax({
            type: 'POST',
            url: '/get_crop_recommendation', 
            contentType: 'application/json',
            data: JSON.stringify(formData),
            beforeSend: function() {
                $('#recommendations').html('<p>Loading recommendations...</p>');
            },
            success: function (response) {
                $('#recommendations').html(response.recommendations);
            },
            error: function (error) {
                console.log(error);
            }
        });
    });
});