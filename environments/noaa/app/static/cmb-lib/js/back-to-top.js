$(document).ready(function(e){
    $(window).scroll(function() {
        if ($(window).scrollTop() > $("#page-content").offset().top) {
            $("#backToTop").fadeIn(2000);
        } else {
            $("#backToTop").fadeOut();
        }
    });

    $("#backToTop").click(function(e){
        e.preventDefault();
        $("html, body").animate({ scrollTop: 0 });
        history.replaceState("", document.title, window.location.pathname+window.location.search);
        return false;
    });
});
