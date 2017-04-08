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
        // parse filters into parameters for /stats
        var searchString = "Stats for {0}".format(suggestion.abbreviation)
        console.log(searchString);
        if ($("#filter_elements").valid()) {
            var parameters = {
                abbreviation: suggestion.abbreviation
            }
            if ($("#selectVictory").val() == "Victories") {
                parameters.success = 1;
            }
            else if ($("#selectVictory").val() == "Defeats") {
                parameters.success = 0;
            }
            if ($("#selectRunes").val() != null && $("#selectRunes").val() != "") {
                parameters.runes = $("#selectRunes").val();
            }

            // get results via AJAX and call display_stats
            $.getJSON(Flask.url_for("stats"), parameters)
            .done(function(data, textStatus, jqXHR) {
                display_stats(data);
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.log(errorThrown.toString());
            });
        }
    });

    // initialize tooltipster on form input elements
    $('#filter_elements input[type="text"]').tooltipster({
        theme: 'tooltipster-punk',
        trigger: 'custom', // default is 'hover' which is no good here
        onlyOne: false,    // allow multiple tips to be open at a time
        position: 'right'  // display the tips to the right of the element
    });

    // initialize validator
    $('#filter_elements').validate({
        rules: {
            selectRunes: {
                range:[0,15],
                required:"false"
            }
        },
        errorPlacement: function (error, element) {
            $(element).tooltipster('content', $(error).text());
            $(element).tooltipster('show');
        },
        success: function (label, element) {
            $(element).tooltipster('hide');
        }
    });


}

function display_stats(data)
{
    // where the points for each graph will be saved
    console.log(data.games)
    var Points = [];
    var options = {
        series: {
            pie: {
                show: true,
                radius: 1,
                label: {
                    show: true,
                    radius: 3/4,
                    formatter: function(label, slice) {
						return "<div style='font-size:x-small;text-align:center;padding:2px;color:" + slice.color + ";'>" + label + "<br/>" + Math.round(slice.percent) + "%</div>";
					},	// formatter function
                    background: {
                        opacity: 0.5,
                        color: '#000'
                    }
                }
            }
        },
        legend: {
            show: false
        }
    }
    // god
    $.each(data.gods, function(i, item){
        Points.push({data: item, label: i})
    });
    // add div for graph
    $("#main-wrapper").append('<div id="gods" style="width:100%;height:300px"></div>')
    $.plot("#gods", Points, options)
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

String.prototype.format = String.prototype.f = function() {
    var s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};
