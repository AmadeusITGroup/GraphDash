
getParameterByName = (name) ->
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]")
    regex = new RegExp("[\\?&]" + name + "=([^&#]*)")
    results = regex.exec(location.search)
    (if results is null then "" else decodeURIComponent(results[1].replace(/\+/g, " ")))

if typeof String::trim == 'undefined'
    String::trim = ->
        String(this).replace /^\s+|\s+$/g, ''

$(document).ready ->
    # Patch autocomplete to support a maxItems parameter
    $.widget "ui.autocomplete", $.ui.autocomplete,
        options:
            maxItems: 9999

        _renderMenu: (ul, items) ->
            that = this
            count = 0
            $.each items, (index, item) ->
                that._renderItemData ul, item if count < that.options.maxItems
                count++
                return
            return

    # Force reload of popState
    window.onpopstate = (event) ->
        if event
            # We reload if there is search parameters (meaning AJAX was used)
            # or if we land on the homepage
            href = window.location.href.slice(0, -1)
            origin = window.location.origin
            location.reload() if (href is origin) or window.location.search
        return

    Handlebars.registerHelper "withObj", (context, options) ->
        options.fn context[options.hash.key]

    Handlebars.registerHelper 'uri', (context) ->
        encodeURI(context)

    Handlebars.registerHelper "generate_parents", (context, options) ->
        if context
            families = context.split('/')
            ret = ''
            for i in [0...families.length]
                up_url = families[..i].join('/')
                ret += options.fn(
                    up_url  : up_url
                    up_name : options.hash.aliases[up_url]
                )
            ret

    template = Handlebars.compile($("#response-template").html())

    $('#box').on 'input', ->
        $(this).addClass 'notsubmitted'

    $("#form").submit (event) ->
        $('#box').removeClass 'notsubmitted'
        # Lose focus after submit, to close or abort autocomplete
        $('#box').blur().focus()
        # '#' is not supported in get parameters
        keywords = encodeURIComponent $("#box").val().trim()
        $.ajax(
            url: URL_SEARCH
            type: "get"
            data: "value=" + keywords
        ).done (response, textStatus, jqXHR) ->
            response.url = URL_FAMILY
            $("#response").html template(response)
            history.pushState {}, "Title", URL_FAMILY + "?search=" + keywords
            return
        # Important to stop redirection
        false

    $("#clearbutton").click ->
        $("#response").html ""
        $('#box').removeClass 'notsubmitted'
        $("#box").val ""
        history.pushState {}, "Title", "/"
        return

    $("#searchbutton").click ->
        $("#form").submit()
        return

    spaces = RegExp(' \\s*')

    $.ajax(
        url: URL_TAGS
        type: "get"
    ).done (response, textStatus, jqXHR) ->
        # We also autocomplete on the excluded parameters
        tags = [response.tags..., ('-' + t for t in response.tags)...]
        $("#box").autocomplete(
            minLength: 0
            maxItems: 20
            focus: (request, ui) ->
                terms = @value.split spaces
                terms.pop()
                terms.push ui.item.value
                @value = terms.join(" ")
                false
            source: (request, resp) ->
                # delegate back to autocomplete, but extract the last term
                resp $.ui.autocomplete.filter(tags, request.term.split(spaces).pop())
            select: (event, ui) ->
                @value = @value + ' '
                $("#form").submit()
                false
        )
        return

    # Make placeholder disappear on focus
    $("input:text, textarea").each ->
        $this = $(this)
        $this.data("placeholder", $this.attr("placeholder")).focus(->
            $this.removeAttr "placeholder"
            return
        ).blur ->
            $this.attr "placeholder", $this.data("placeholder")
            return
        return

    # Trigger search at load time if url contains search= parameters
    params = getParameterByName("search")
    if params isnt ""
        $("#box").val params
        $("#form").submit()
    return

