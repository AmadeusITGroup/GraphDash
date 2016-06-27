(function() {
  var isScrolledIntoView, throttle;

  isScrolledIntoView = function(elem) {
    var docViewBottom, docViewTop, elemBottom, elemTop;
    docViewTop = $(window).scrollTop();
    docViewBottom = docViewTop + $(window).height();
    elemTop = $(elem).offset().top;
    elemBottom = elemTop + $(elem).height();
    return (elemBottom <= docViewBottom) && (elemTop >= docViewTop);
  };

  throttle = function(fn, threshhold, scope) {
    var deferTimer, last;
    threshhold = threshhold || 250;
    last = void 0;
    deferTimer = void 0;
    return function() {
      var args, context, now;
      context = scope || this;
      now = +new Date();
      args = arguments;
      if (last && now < last + threshhold) {
        clearTimeout(deferTimer);
        deferTimer = setTimeout(function() {
          last = now;
          fn.apply(context, args);
        }, threshhold);
      } else {
        last = now;
        fn.apply(context, args);
      }
    };
  };

  $(document).ready(function() {
    var $anchors, $root, $sidebarLinks, detectShortcut, hashnb, marginWithMenu, marginWithoutMenu, scrollToAnchor, selected, sidebarShown, toggleSidebar, updateSelected, updateSidebar;
    $("img").lazyload({
      threshold: 200,
      effect: "fadeIn"
    });
    sidebarShown = true;
    marginWithMenu = $('#main_family').css('margin-left');
    marginWithoutMenu = $('#main_family').css('margin-right');
    $("#togglebutton").click(function() {
      toggleSidebar();
    });
    toggleSidebar = function() {
      sidebarShown = !sidebarShown;
      if (sidebarShown === false) {
        $("#togglebutton").text('⇥');
        $('#sidemenu').css('display', 'none');
        return $('#main_family, #title_family').css('margin-left', marginWithoutMenu);
      } else {
        $("#togglebutton").text('⇤');
        $('#main_family, #title_family').css('margin-left', marginWithMenu);
        return $('#sidemenu').css('display', 'block');
      }
    };
    $root = $("html, body");
    $anchors = $("a[id]");
    $sidebarLinks = $("#menulinks a[href*=#]");
    selected = void 0;
    updateSelected = function(newSelected) {
      if (newSelected === selected) {
        return;
      }
      selected = newSelected;
      $sidebarLinks.queue(function() {
        $(this).removeClass('selected');
        return $(this).dequeue();
      });
      return $("#menulinks a[href='#" + selected + "']").addClass('selected', 200);
    };
    updateSidebar = function() {
      return $anchors.each(function() {
        if (isScrolledIntoView($(this))) {
          updateSelected(parseInt($(this).attr('id'), 10));
          return false;
        }
      });
    };
    scrollToAnchor = function($anchor) {
      updateSelected(parseInt($anchor.attr('id'), 10));
      $root.stop().animate({
        scrollTop: $anchor.offset().top
      }, 750, "swing", function() {
        window.location.hash = $anchor.attr("id");
      });
    };
    detectShortcut = function(e) {
      var anchor;
      if ($("input").is(":focus")) {
        return;
      }
      if (e.keyCode === 74) {
        if (selected !== 1) {
          anchor = document.getElementById(selected - 1);
          scrollToAnchor($(anchor));
        }
      }
      if (e.keyCode === 75) {
        if (selected !== $anchors.length) {
          anchor = document.getElementById(selected + 1);
          scrollToAnchor($(anchor));
        }
      }
      if (e.keyCode === 38) {
        updateSidebar();
      }
      if (e.keyCode === 40) {
        updateSidebar();
      }
      if (e.keyCode === 72) {
        toggleSidebar();
      }
    };
    document.addEventListener("keyup", detectShortcut, false);
    $("a[href*=#]").click(function() {
      var anchor, hash;
      hash = $(this).attr('href');
      anchor = document.getElementById(hash.substring(1));
      scrollToAnchor($(anchor));
      return false;
    });
    hashnb = window.location.hash.substring(1);
    if (hashnb === "") {
      hashnb = "1";
    }
    updateSelected(parseInt(hashnb, 10));
    $(window).bind('mousewheel', throttle(updateSidebar, 150));
  });

}).call(this);

//# sourceMappingURL=family.js.map
