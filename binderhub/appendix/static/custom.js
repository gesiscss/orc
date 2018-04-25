function copy_share_link() {
    var $temp = $("<input>");
    $("#login_widget").append($temp);
    $temp.val(window.location.origin.concat($("#ipython_notebook>a").attr('href'))).select();
    document.execCommand("copy");
    $temp.remove();
}

if ($("#login_widget")) {
    $("#login_widget").prepend('<button id="copy-share-link" ' +
        '                               title="Copy sharable server link to clipboard" ' +
        '                               class="btn btn-sm navbar-btn" ' +
        '                               style="color: #333; background-color: #fff; border-color: #ccc;" ' +
        '                               onclick="copy_share_link()">' +
        '                       Copy link</button>');
}