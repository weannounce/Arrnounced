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

function animate_actions() {
  $('[data-bs-hover-animate]')
    .mouseenter( function(){ var elem = $(this); elem.addClass('animated ' + elem.attr('data-bs-hover-animate')) })
    .mouseleave( function(){ var elem = $(this); elem.removeClass('animated ' + elem.attr('data-bs-hover-animate')) });
}

$('#announced-pagination').twbsPagination({
    totalPages: announcement_pages,
    visiblePages: 7,
    hideOnlyOnePage: true,
    onPageClick: function (event, page) {
      alite({
            url: '/announced',
            method: 'POST',
            data: {
              page_nr: page
            },
        }).then(function (result) {
          function add_row(tbody, item, index, backends) {
            var newRow = tbody.insertRow();
            var keys = ['date', 'indexer', 'title', 'backend']
            for(var key in keys) {
              var newCell = newRow.insertCell();
              var newText = document.createTextNode(item[keys[key]])
              newCell.appendChild(newText)
            }
            action = document.getElementById('action_div').cloneNode(true);
            action.removeAttribute('id');
            action.querySelector('#torrent_url').href = item['torrent']
            ul = action.querySelector('ul')

            for(var backend of backends) {
              var li_item = $("<li />").appendTo(ul);

              var a_b = $("<a />", {
                href: "javascript:notify_backend(" + item['id'] + ", '" + backend + "');",
                text: backend
              }).appendTo(li_item);
            }

            action.style.display = "block";
            var newCell = newRow.insertCell();
            newCell.setAttribute("class", "action_td");
            newCell.appendChild(action)
          }

          var new_tbody = document.createElement('tbody');
          var old_tbody = document.getElementById('announced_torrents').getElementsByTagName('tbody')[0];
          result.announces.forEach(function(item, index) {
            add_row(new_tbody, item, index, result.backends)
          });
          old_tbody.parentNode.replaceChild(new_tbody, old_tbody)

          animate_actions();

        }).catch(function (err) {
            toastr.error("Error getting announments ");
        });
    }
});

$('#snatched-pagination').twbsPagination({
    totalPages: snatch_pages,
    visiblePages: 7,
    hideOnlyOnePage: true,
    onPageClick: function (event, page) {
      alite({
            url: '/snatched',
            method: 'POST',
            data: {
              page_nr: page
            },
        }).then(function (result) {
          function add_row(tbody, item, index) {
            var newRow = tbody.insertRow();
            var keys = ['date', 'indexer', 'title', 'backend']
            for(var key in keys) {
              var newCell = newRow.insertCell();
              var newText = document.createTextNode(item[keys[key]])
              newCell.appendChild(newText)
            }
          }

          var new_tbody = document.createElement('tbody');
          var old_tbody = document.getElementById('snatched_torrents').getElementsByTagName('tbody')[0];
          result.snatches.forEach(function(item, index) {
            add_row(new_tbody, item, index)
          });
          old_tbody.parentNode.replaceChild(new_tbody, old_tbody)


        }).catch(function (err) {
            toastr.error("Error getting announments ");
        });
    }
});
