// highlighting nav elements on hover
$("div#navbar>ul>li").hover(
    function() {
        // in
        $("div#navbar>ul>li>a").removeClass("gs_active_sub");
        $(this).addClass( "gs_active_sub" );
        },
    function() {
        // out
        $(this).removeClass( "gs_active_sub" );
        $("#navbar-active-a").addClass( "gs_active_sub" );
        }
    );