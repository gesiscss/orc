function copy_link_into_clipboard(b) {
    var $temp = $("<input>");
    $("#login_widget").append($temp);
    $temp.val(window.location.origin.concat($(b).data('url'))).select();
    document.execCommand("copy");
    $temp.remove();
}

var login_widget = $("#login_widget");
if (login_widget.length) {
    var button_tag = '<button id="copy-{name}-link" ' +
            '                 title="Copy {name} link to clipboard" ' +
            '                 class="btn btn-sm navbar-btn" ' +
            '                 style="color: #333; background-color: #fff; border-color: #ccc;" ' +
            '                 data-url="{url}" ' +
            '                 onclick="copy_link_into_clipboard(this);">' +
            '         Copy {name} link</button>';

    if ($("#ipython_notebook").length && $("#ipython_notebook>a").length) {
        login_widget.prepend(button_tag.replace(/{name}/g, 'session').replace('{url}', $("#ipython_notebook>a").attr('href')));
    }
    login_widget.prepend(button_tag.replace(/{name}/g, 'build').replace('{url}', '{binder_url}'));
    login_widget.prepend(button_tag.replace(/{name}/g, 'repo').replace('{url}', '{repo_url}'));
}