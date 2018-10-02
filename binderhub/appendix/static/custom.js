function copy_link_into_clipboard(b) {
    var $temp = $("<input>");
    $(b).parent().append($temp);
    $temp.val($(b).data('url')).select();
    document.execCommand("copy");
    $temp.remove();
}

function add_buttons(element) {
    var copy_button = '<button id="copy-{name}-link" ' +
            '                 title="Copy {name} link to clipboard" ' +
            '                 class="btn btn-default btn-sm navbar-btn" ' +
            '                 style="margin-right: 4px; margin-left: 2px;" ' +
            '                 data-url="{url}" ' +
            '                 onclick="copy_link_into_clipboard(this);">' +
            '         Copy {name} link</button>';

    var link_button = '<a id="copy-{name}-link" ' +
        '                 href="{url}" ' +
        '                 class="btn btn-default btn-sm navbar-btn" ' +
        '                 style="margin-right: 4px; margin-left: 2px;" ' +
        '                 target="_blank">' +
        '              Go to {name}</a>';

    if ($("#ipython_notebook").length && $("#ipython_notebook>a").length) {
        element.prepend(copy_button.replace(/{name}/g, 'session').replace('{url}', window.location.origin.concat($("#ipython_notebook>a").attr('href'))));
    }
    element.prepend(copy_button.replace(/{name}/g, 'build').replace('{url}', '{binder_url}'));
    element.prepend(link_button.replace(/{name}/g, 'repo').replace('{url}', '{repo_url}'));
}

var shutdown_widget = $("#shutdown_widget");
var login_widget = $("#login_widget");
if (shutdown_widget.length) {
    add_buttons(shutdown_widget);
} else if (login_widget.length) {
    add_buttons(login_widget);
}