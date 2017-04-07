// call when page is ready
$(function(){
    configure()
})

function configure()
{
    // configure typeahead
    $("#search .typeahead").typeahead({
        hint: true,
        highlight: false,
        minLength: 1
    },
    {
        display: function(suggestion) { return null; },
        limit: 10,
        source: search,
        templates: {
            suggestion: Handlebars.compile(
                "<div> {{abbreviation}}, {{string}} </div>"
            )
        }
    });

    $("#search .typeahead").on("typeahead:selected", function(eventObject, suggestion, name) {
        // get results
        var parameters = {
            q: suggestion.abbreviation
        }
        $.getJSON(Flask.url_for("search"), parameters)
        .done(function(data, textStatus, jqXHR) {
            $("#search").css("visibility", "hidden")
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.log(errorThrown.toString());
        });
    });
}

function search(query, syncResults, asyncResults)
{
    // get results
    var parameters = {
        q: query
    }
    $.getJSON(Flask.url_for("search"), parameters)
    .done(function(data, textStatus, jqXHR) {

        // callback
        asyncResults(data);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
        console.log(errorThrown.toString());
    });
}
