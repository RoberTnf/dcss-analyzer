// call when page is ready
$(function(){
    configure()

})

function configure()
{
    // configure main typeahead
    var options = {
        hint: true,
        highlight: false,
        minLength: 1
    };
    var sug = {
        display: function(suggestion) { return null; },
        limit: 10,
        source: search,
        templates: {
            suggestion: Handlebars.compile(
                "<div> {{abbreviation}}, {{string}} </div>"
            )
        }
    }
    $("#search .typeahead").typeahead(options, sug);

    //configure filters typeahead
    sug.templates = {suggestion: Handlebars.compile("<div> {{suggestion}} </div>")};
    sug.source = searchGods;
    $("#selectGod").typeahead(options, sug);

    sug.source = searchPlayers;
    $("#selectPlayer").typeahead(options, sug);

    //selection typeahead -> replace content with suggestion
    $(".typeahead").on("typeahead:selected", function(eventObject, suggestion, name) {
        $(this).typeahead('val', suggestion.suggestion);
    });
    $("#search .typeahead").on("typeahead:selected", function(eventObject, suggestion, name) {
        $(this).typeahead('val', suggestion.abbreviation);
    });
    // selection of main search
    $(document).keypress(function(e) {if(e.which == 13) {
        // parse filters into parameters for /stats
        if ($("#filter_elements").valid()) {
            var parameters = {}
            var statStr = "Stats for "
            if($("#selectAbbreviation").val() != null && $("#selectAbbreviation").val() != "") {
                parameters.abbreviation = $("#selectAbbreviation").val();
                statStr += parameters.abbreviation;
            }
            else {
                statStr += "every combination"
            }
            if ($("#selectVictory").val() == "Victories") {
                parameters.success = 1;
                statStr += ", ended in victory";
            }
            else if ($("#selectVictory").val() == "Defeats") {
                parameters.success = 0;
                statStr += ", ended in defeat";
            }
            if ($("#selectRunes").val() != null && $("#selectRunes").val() != "") {
                parameters.runes = $("#selectRunes").val();
                statStr += ", with {0} runes".f($("#selectRunes").val());
            }
            if ($("#selectGod").val() != null && $("#selectGod").val() != "") {
                parameters.god = $("#selectGod").val();
                statStr += ", worshiping {0}".format($("#selectGod").val());
            }
            if ($("#selectName").val() != null && $("#selectName").val() != "") {
                parameters.name = $("#selectName").val();
                statStr += ", for player {0}".format($("#selectName").val());
            }
            if ($("#selectVersion").val() != null && $("#selectVersion").val() != "") {
                parameters.version = $("#selectVersion").val();
                statStr += ", under version {0}".f($("#selectVersion").val());
            }
            // get results via AJAX and call display_stats
            $.getJSON(Flask.url_for("stats"), parameters)
            .done(function(data, textStatus, jqXHR) {
                $('#main-wrapper').empty();
                if (hasOwnProperty(data, "ERROR")){
                    display_not_found();
                }
                else{
                    display_stats(data, statStr);
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.log(errorThrown.toString());
            })
        }
    }});

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
            },
            selectVersion: {
                required: "false",
                range: [0.00, 1]
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

function hasOwnProperty(obj, prop) {
    // to know if obj has prop
    var proto = obj.__proto__ || obj.constructor.prototype;
    return (prop in obj) &&
        (!(prop in proto) || proto[prop] !== obj[prop]);
}

function display_not_found(){
    $("#main-wrapper").append('<h2>ERROR: no results with those constraints</h2>')
}
function display_stats(data, statStr){
    // graph options
    // var colors = ["#f00000", "#f01000", "#00f000", "000f00", "#0000f0", "00000f"]
    var options = {
        series: {
            pie: {
                show: true,
                label: {
                    threshold: 0.1,
                    show:true,
                    radius: 0.8,
                    formatter: function (label, series) {
                        return '<div style="border:1px solid grey;font-size:8pt;text-align:center;padding:5px;color:white;">' +
                        label + ' : ' +
                        Math.round(series.percent) +
                        '%</div>';
                    },
                    background: {
                        opacity: 0.8,
                        color: '#000'
                    }
                },
                combine: {
                    threshold: 0.01,
                    label: "Other"
                }
            }
        },
        legend: {
            show: false
        },
        grid: {
            hoverable: true
        }
    }

    // shows info about pie chart
    $.fn.showMemo = function (flotdiv) {
        $(this).bind("plothover", function (event, pos, item) {
            if (!item) { return; }

            var html = [];
            var percent = parseFloat(item.series.percent).toFixed(2);

            html.push("<div style=\"border:1px solid grey;background-color:",
                 item.series.color,
                 "\">",
                 "<span style=\"color:#000;font-weight:700\">",
                 item.series.label,
                 " : ",
                 item.series.data[0][1],
                 " (", percent, "%)",
                 "</span>",
                 "</div>");
            $(flotdiv).html(html.join(''));
        });
    }

    // Print string with information about query
    $("#main-wrapper").append("<div id=statStr><h1>{0}</h1></div>".f(statStr))

    // WinRate section:
    if (hasOwnProperty(data, "winrate"))
    {
        $("#main-wrapper").append("<div class=statSection id=winrate></div>")
        $("#winrate").append("<h3 class=sectionTitle> Games: </h3>")
        // add div for graph
        $("#winrate").append("<div class=sectionText></div>")
        winrateStr = "In {0} games {1} were victories (<b>{2}</b> winrate).".f(
            data.games, data.wins, data.winrate
        )
        $("#winrate .sectionText").append(winrateStr)
        $("#winrate").append('<div class="graph-container"></div>');
        $("#winrate .graph-container").append('<div class="graph"></div>')
        $("#winrate .graph-container").append('<div class="graph-memo"></div>')
        var Points = [];
        Points.push({data: data.wins, label: "wins"});
        Points.push({data: data.games - data.wins, label: "loses"});
        $.plot("#winrate .graph", Points, options);
        $("#winrate .graph").showMemo("#winrate .graph-memo");
    }

    if (hasOwnProperty(data, "gods"))
    {
        $("#main-wrapper").append("<div class=statSection id=gods></div>")
        $("#gods").append("<h3 class=sectionTitle> Gods: </h3>")
        // add div for graph
        $("#gods").append("<div class=sectionText></div>")
        var Points = [];
        var j = 0;
        var max = {"god":"none", "count":0};
        var total = 0;
        $.each(data.gods, function(i, item){
            Points.push({data: item, label: i});
            total += item;
            if (max.count < item && i != "none") {
                max.count=item
                max.god=i
            };
        });
        godsStr = "The most played god is <b>{0}</b> with {1} games (<b>{2}%</b>)".f(
            max.god, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#gods .sectionText").append(godsStr)
        $("#gods").append('<div class="graph-container"></div>');
        $("#gods .graph-container").append('<div class="graph"></div>')
        $("#gods .graph-container").append('<div class="graph-memo"></div>')
        $.plot("#gods .graph", Points, options);
        $("#gods .graph").showMemo("#gods .graph-memo");
    }

    if (hasOwnProperty(data, "killers"))
    {
        $("#main-wrapper").append("<div class=statSection id=killers></div>")
        $("#killers").append("<h3 class=sectionTitle> Killers: </h3>")
        // add div for graph
        $("#killers").append("<div class=sectionText></div>")
        var Points = [];
        var j = 0;
        var max = {"god":"none", "count":0};
        var total = 0;
        $.each(data.killers, function(i, item){
            Points.push({data: item, label: i});
            total += item;
            if (max.count < item && i != "other" && i != "quit") {
                max.count=item
                max.god=i
            };
        });
        killersStr = "The monster with most kills is <b>{0}</b> with {1} kills (<b>{2}%</b>)".f(
            max.god, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#killers .sectionText").append(killersStr)
        $("#killers").append('<div class="graph-container"></div>');
        $("#killers .graph-container").append('<div class="graph"></div>')
        $("#killers .graph-container").append('<div class="graph-memo"></div>')
        $.plot("#killers .graph", Points, options);
        $("#killers .graph").showMemo("#killers .graph-memo");
    }

    if (hasOwnProperty(data, "killers"))
    {
        $("#main-wrapper").append("<div class=statSection id=uniqueKillers></div>")
        $("#uniqueKillers").append("<h3 class=sectionTitle> Unique killers: </h3>")
        // add div for graph
        $("#uniqueKillers").append("<div class=sectionText></div>")
        var Points = [];
        var j = 0;
        var max = {"killer":"none", "count":0};
        var total = 0;
        var total_uniques = 0;
        $.each(data.killers, function(i, item){
            // if first char is uppercase
            if (i.slice(0,1).isUpperCase()){
                Points.push({data: item, label: i});
                if (max.count < item && i != "other" && i != "quit") {
                    max.count=item
                    max.killer=i
                };
            }
            total += item;
        });
        uniqueKillersStr = "The monster with most kills is <b>{0}</b> with {1} kills (<b>{2}%</b> of totals)".f(
            max.killer, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#uniqueKillers .sectionText").append(uniqueKillersStr)
        $("#uniqueKillers").append('<div class="graph-container"></div>');
        $("#uniqueKillers .graph-container").append('<div class="graph"></div>')
        $("#uniqueKillers .graph-container").append('<div class="graph-memo"></div>')
        $.plot("#uniqueKillers .graph", Points, options);
        $("#uniqueKillers .graph").showMemo("#uniqueKillers .graph-memo");
    }


    /*
    // Gods section:
    if (hasOwnProperty(data, "gods"))
    {
        $("#main-wrapper").append("<div id=gods class=statSection></div>")
        $("#gods").append("<h3 class=sectionTitle> Gods: </h3>")
        // add div for graph
        $("#gods").append('<div id="gods-pie" style="width:100%;height:300px"></div>')
        $("#gods").append('<div id="gods-memo" style="text-align:center;height:30px;width:250px;height:20px;text-align:center;margin:0 auto"></div>')
        var Points = [];
        $.each(data.gods, function(i, item){
            Points.push({data: item, label: i})
        });
        $.plot("#gods-pie", Points, options)
        $("#gods").showMemo("#gods-memo");
    }*/
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

function searchGods(query, syncResults, asyncResults)
{
    // get results
    var parameters = {
        q: query
    }
    $.getJSON(Flask.url_for("searchGods"), parameters)
    .done(function(data, textStatus, jqXHR) {

        // callback
        asyncResults(data);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
        console.log(errorThrown.toString());
    });
}

function searchPlayers(query, syncResults, asyncResults)
{
    // get results
    var parameters = {
        q: query
    }
    $.getJSON(Flask.url_for("searchPlayers"), parameters)
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

String.prototype.isUpperCase = function() {
    return this.valueOf().toUpperCase() === this.valueOf();
};

$.ajaxSetup({
    beforeSend:function(){
        // show gif here, eg:
        $("#loader-gif").show();
    },
    complete:function(){
        // hide gif here, eg:
        $("#loader-gif").hide();
    }
});
