// call when page is ready
$(function(){
    configure()
})

function configure()
{
    // configure typeahead
    $("#q").typeahead({
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

    $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {
        var parameters = {
            q: suggestion.abbreviation
        };
        console.log("replace");
        window.location.replace(Flask.url_for("stats").concat("?q=").concat(suggestion.abbreviation))
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
