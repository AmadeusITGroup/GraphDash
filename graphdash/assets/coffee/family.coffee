
isScrolledIntoView = (elem) ->
    docViewTop = $(window).scrollTop()
    docViewBottom = docViewTop + $(window).height()
    elemTop = $(elem).offset().top
    elemBottom = elemTop + $(elem).height()
    (elemBottom <= docViewBottom) and (elemTop >= docViewTop)


throttle = (fn, threshhold, scope) ->
    threshhold = threshhold or 250
    last = undefined
    deferTimer = undefined
    ->
        context = scope or this
        now = +new Date()
        args = arguments
        if last and now < last + threshhold
            # hold on to it
            clearTimeout deferTimer
            deferTimer = setTimeout(->
                last = now
                fn.apply context, args
                return
            , threshhold)
        else
            last = now
            fn.apply context, args
        return


$(document).ready ->
    # Lazy loading all images
    $("img").lazyload(
        threshold : 200
        effect : "fadeIn"
    )

    # Is sidebar shown?
    sidebarShown = true
    marginWithMenu = $('#main_family').css('margin-left')
    marginWithoutMenu = $('#main_family').css('margin-right')

    $("#togglebutton").click ->
        toggleSidebar()
        return

    toggleSidebar = ->
        sidebarShown = not sidebarShown
        if sidebarShown is false
            $("#togglebutton").text('⇥')
            $('#sidemenu').css('display', 'none')
            $('#main_family, #title_family').css('margin-left', marginWithoutMenu)
        else
            $("#togglebutton").text('⇤')
            $('#main_family, #title_family').css('margin-left', marginWithMenu)
            $('#sidemenu').css('display', 'block')

    # Some caching
    $root = $("html, body")
    $anchors = $("a[id]")
    $sidebarLinks = $("#menulinks a[href*=#]")

    # This is the integer of the current graph being displayed
    # It can also be found in the window.location.hash like #7
    selected = undefined

    updateSelected = (newSelected) ->
        # We only change css if the selection has changed,
        # to avoid blinking effect on small scrolls
        if newSelected is selected
            return
        # Update global variable here
        selected = newSelected
        $sidebarLinks.queue ->
            $(this).removeClass('selected')
            $(this).dequeue()
        $("#menulinks a[href='##{selected}']").addClass('selected', 200)

    updateSidebar = ->
        $anchors.each ->
            if isScrolledIntoView $(this)
                updateSelected(parseInt($(this).attr('id'), 10))
                return false # breaks the $.each

    scrollToAnchor = ($anchor) ->
        updateSelected(parseInt($anchor.attr('id'), 10))
        $root.stop().animate
            scrollTop: $anchor.offset().top
        , 750, "swing", ->
            window.location.hash = $anchor.attr("id")
            return
        return

    detectShortcut = (e) ->
        # Do not use shortcut if user is typing something in an input
        return if $("input").is(":focus")

        if e.keyCode is 74 # j, up in the page
            if selected isnt 1
                anchor = document.getElementById(selected - 1)
                scrollToAnchor $(anchor)

        if e.keyCode is 75 # k, down in the page
            if selected isnt $anchors.length
                anchor = document.getElementById(selected + 1)
                scrollToAnchor $(anchor)

        if e.keyCode is 38 # up arrow
            updateSidebar()

        if e.keyCode is 40 # down arrow
            updateSidebar()

        if e.keyCode is 72 # h, toggle sidebar
            toggleSidebar()

        return

    document.addEventListener "keyup", detectShortcut, false

    $("a[href*=#]").click ->
        hash = $(this).attr('href')
        # anchor = $(hash) fails with ids containing '/', this does not
        anchor = document.getElementById(hash.substring(1))
        scrollToAnchor $(anchor)
        false

    # Current selection if based on the hash
    hashnb = window.location.hash.substring(1)
    hashnb = "1" if hashnb is ""
    updateSelected(parseInt(hashnb, 10))

    $(window).bind 'mousewheel', throttle(updateSidebar, 150)

    return

