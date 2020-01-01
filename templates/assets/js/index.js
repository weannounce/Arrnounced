// Index Pgae
function notify_pvr(announcement_id, pvr_name) {
    console.log("Notifying " + pvr_name +  " again for announcement: " + announcement_id);

    alite({
            url: '/notify',
            method: 'POST',
            data: {
                id: announcement_id,
                pvr_name: pvr_name
            },
        }).then(function (result) {
            console.log(pvr_name + '_notify result: ', result);
            if (result === 'ERR') {
                // PVR rejected the announcement
                toastr.error(pvr_name + " still declined this torrent...");
            } else {
                // PVR accepted the announcement
                toastr.success(pvr_name + " approved the torrent this time!");
            }
        }).catch(function (err) {
            console.error(pvr_name + '_notify error: ', err);
            toastr.error("Error notfying " +pvr_name + " of this announcement??");
        });
}
