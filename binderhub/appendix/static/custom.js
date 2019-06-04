function copy_link_into_clipboard(b) {
    var $temp = $("<input>");
    $(b).parent().append($temp);
    $temp.val($(b).data('url')).select();
    document.execCommand("copy");
    $temp.remove();
}

function add_binder_buttons() {
    var copy_button = '<button id="copy-{name}-link" ' +
            '                 title="Copy {name} link to clipboard" ' +
            '                 class="btn btn-default btn-sm navbar-btn" ' +
            '                 style="margin-left: 5px;" ' +
            '                 data-url="{url}" ' +
            '                 onclick="copy_link_into_clipboard(this);">' +
            '         Copy {name} link</button>';

    var link_button = '<a id="copy-{name}-link" ' +
        '                 href="{url}" ' +
        '                 class="btn btn-default btn-sm navbar-btn" ' +
        '                 style="margin-left: 5px;" ' +
        '                 target="_blank">' +
        '              Go to {name}</a>';

    // add buttons before quit button or at the end of header-container
    var shutdown_widget = $("#shutdown_widget");
    var s = shutdown_widget;
    if (!shutdown_widget.length) {
        s = $("<span id='binder-buttons'></span>");
    }

    // session url
    if ($("#ipython_notebook").length && $("#ipython_notebook>a").length) {
        s.prepend(copy_button.replace(/{name}/g, 'session').replace('{url}', window.location.origin.concat($("#ipython_notebook>a").attr('href'))));
    }
    // binder url
    var copy_binder_link  = copy_button.replace(/{name}/g, 'binder').replace('{url}', '{binder_url}');
    // if (window.location.hostname.indexOf("notebooks-test") === -1) {
    //     // TODO update federation url when we join into a federation
    //     var federation_url = "https://notebooks.gesis.org/binder";
    //     copy_binder_link.replace("https://notebooks.gesis.org/binder", federation_url);
    // }
    s.prepend(copy_binder_link);
    // repo url
    s.prepend(link_button.replace(/{name}/g, 'repo').replace('{url}', '{repo_url}'));

    if (!shutdown_widget.length) {
        // add buttons at the end of header-container
        $("#header-container").append(s);
    }
}

add_binder_buttons();
