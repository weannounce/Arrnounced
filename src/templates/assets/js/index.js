// Index Pgae
function notify_backend(announcement_id, backend_name) {
    console.log("Notifying " + backend_name +  " again for announcement: " + announcement_id);

    alite({
            url: '/notify',
            method: 'POST',
            data: {
                id: announcement_id,
                backend_name: backend_name
            },
        }).then(function (result) {
            console.log(backend_name + '_notify result: ', result);
            if (result === 'ERR') {
                // Backend rejected the announcement
                toastr.error(backend_name + " still declined this torrent...");
            } else {
                // Backend accepted the announcement
                toastr.success(backend_name + " approved the torrent this time!");
            }
        }).catch(function (err) {
            console.error(backend_name + '_notify error: ', err);
            toastr.error("Error notfying " +backend_name + " of this announcement??");
        });
}
