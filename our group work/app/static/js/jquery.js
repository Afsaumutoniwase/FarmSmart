(function() {
    var selectors = {
        nav: '[data-features-nav]',
        tabs: '[data-features-tabs]',
        active: '.__active'
    }
    var classes = {
        active: '__active'
    }
    $('a', selectors.nav).on('click', function() {
        let $this = $(this)[0];
        $(selectors.active, selectors.nav).removeClass(classes.active);
        $($this).addClass(classes.active);
        $('div', selectors.tabs).removeClass(classes.active);
        $($this.hash, selectors.tabs).addClass(classes.active);
        return false
    });
}());

$(".btn-with-icon").on("click", function() {
    $(".wave-anim").addClass('visible').one("webkitAnimationEnd mozAnimationEnd MSAnimationEnd", function() {
        $(".wave-anim").removeClass('visible');
    });
});


// scripts.js

document.addEventListener("DOMContentLoaded", () => {
    const notificationCards = document.querySelectorAll(".notification-card");

    notificationCards.forEach(card => {
        if (card.getAttribute("data-unread") === "true") {
            card.classList.add("unread");
        }

        card.addEventListener("click", () => {
            card.setAttribute("data-unread", "false");
            card.classList.remove("unread");
            const unreadBadge = card.querySelector(".unread-badge");
            if (unreadBadge) {
                unreadBadge.remove();
            }
        });
    });
});

