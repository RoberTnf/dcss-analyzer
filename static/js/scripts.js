  // call when page is ready Time and space
$(function() {
    configure()
})

function load_stats(clicked = false) {
    // parse filters into parameters for /stats
    if ($("#filter_elements").valid()) {
        // add interactivity filtering to the graphs
        if (clicked) {
            console.log(clicked)

            // Filter for victory
            if (hasOwnProperty(clicked, "winrate"))
            {
                if (clicked["winrate"] == "loses")
                {
                    $("#selectVictory").val("Defeats")
                }
                if (clicked["winrate"] == "wins")
                {
                    $("#selectVictory").val("Victories")
                }
            }

            // Filter for gods
            if (hasOwnProperty(clicked, "god"))
            {
                $("#selectGod").val(clicked["god"])
            }
        }
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
        if ($("#selectPlayer").val() != null && $("#selectPlayer").val() != "") {
            parameters.name = $("#selectPlayer").val();
            statStr += ", for player {0}".format($("#selectPlayer").val());
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
}

function configure() {
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
    $(document).keypress(function(e) {
        if(e.which == 13) {
            load_stats()
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


function display_not_found() {
    $("#main-wrapper").append('<h2>ERROR: no results with those constraints</h2>')
}


function display_stats(data, statStr) {
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
            hoverable: true,
            clickable: true
        }
    }

    $.fn.clickable = function (label) {
        $(this).bind("plotclick", function (event, pos, item) {
            if (item) {
                param = {}
                param[label] = item["series"]["label"]
                load_stats(param);
            }
        });
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
        winrateStr = "In {0} games {1} were victories <br> (<b>{2}%</b> winrate).".f(
            data.games, data.wins, data.winrate.slice(0,5)
        )
        $("#winrate .sectionText").append(winrateStr)
        $("#winrate").append('<div class="graph-container"></div>');
        $("#winrate .graph-container").append('<div class="graph"></div>')
        $("#winrate .graph-container").append('<div class="graph-memo">')
        var Points = [];
        Points.push({data: data.wins, label: "wins"});
        Points.push({data: data.games - data.wins, label: "loses"});
        $.plot("#winrate .graph", Points, options);
        $("#winrate .graph").showMemo("#winrate .graph-memo");
        $("#winrate .graph").clickable("winrate")
    }

    if (hasOwnProperty(data, "gods"))
    {
        $("#main-wrapper").append("<div class=statSection id=gods></div>")
        $("#gods").append("<h3 class=sectionTitle> Gods: </h3>")
        // add div for graph
        $("#gods").append("<div class=sectionText></div>")
        var Points = [];
        var max = {"god":"none", "count":0};
        var total = 0;
        $.each(data.gods, function(i, item){
            Points.push({data: item[1], label: item[0]});
            total += item[1];
            if (max.count < item[1] && item[0] != "none") {
                max.count=item[1]
                max.god=item[0]
            };
        });
        godsStr = "The most played god is <b>{0}</b> <br>with {1} games (<b>{2}%</b>)".f(
            max.god, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#gods .sectionText").append(godsStr)
        $("#gods").append('<div class="graph-container"></div>');
        $("#gods .graph-container").append('<div class="graph"></div>')
        $("#gods .graph-container").append('<div class="graph-memo"></div>')
        $.plot("#gods .graph", Points, options);
        $("#gods .graph").showMemo("#gods .graph-memo");
        $("#gods .graph").clickable("god")
    }

    if (hasOwnProperty(data, "killers"))
    {
        $("#main-wrapper").append("<div class=statSection id=killers></div>")
        $("#killers").append("<h3 class=sectionTitle> Killers: </h3>")
        // add div for graph
        $("#killers").append("<div class=sectionText></div>")
        var Points = [];
        var max = {"god":"none", "count":0};
        var total = 0;
        $.each(data.killers, function(i, item){
            Points.push({data: item[1], label: item[0]});
            total += item[1];
            if (max.count < item[1] && item[0] != "none" && item[0] != "quit") {
                max.count=item[1]
                max.god=item[0]
            };
        });
        killersStr = "The monster with most kills is <b>{0}</b> <br>with {1} kills (<b>{2}%</b>)".f(
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
        var max = {"killer":"none", "count":0};
        var total = 0;
        var total_uniques = 0;
        $.each(data.killers, function(i, item){
            // if first char is uppercase
            if (item[0] != null) {
                if (item[0].slice(0,1).isUpperCase()){
                    Points.push({data: item[1], label: item[0]});
                    if (max.count < item[1] && item[0] != "other" && item[0] != "quit") {
                        max.count=item[1]
                        max.killer=item[0]
                    };
                }
            }
            total += item[1];
        });
        uniqueKillersStr = "The unique with most kills is <b>{0}</b> <br>with {1} kills (<b>{2}%</b> of totals)".f(
            max.killer, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#uniqueKillers .sectionText").append(uniqueKillersStr)
        $("#uniqueKillers").append('<div class="graph-container"></div>');
        $("#uniqueKillers .graph-container").append('<div class="graph"></div>')
        $("#uniqueKillers .graph-container").append('<div class="graph-memo"></div>')
        $.plot("#uniqueKillers .graph", Points, options);
        $("#uniqueKillers .graph").showMemo("#uniqueKillers .graph-memo");
    }

    if (hasOwnProperty(data, "races"))
    {
        $("#main-wrapper").append("<div class=statSection id=Races></div>")
        $("#Races").append("<h3 class=sectionTitle> Races: </h3>")
        // add div for graph
        $("#Races").append("<div class=sectionText></div>")
        var Points = [];
        var max = {"race":"none", "count":0};
        var total = 0;
        $.each(data.races, function(i, item){
            Points.push({data: item[1], label: item[0]});
            total += item[1];
            if (max.count < item[1]) {
                max.count=item[1]
                max.race=item[0]
            };
        });
        RacesStr = "The most played race is <b>{0}</b> <br>with {1} games (<b>{2}%</b> of totals).".f(
            max.race, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#Races .sectionText").append(RacesStr)
        $("#Races").append('<div class="graph-container"></div>');
        $("#Races .graph-container").append('<div class="graph"></div>')
        $("#Races .graph-container").append('<div class="graph-memo"></div>')
        $.plot("#Races .graph", Points, options);
        $("#Races .graph").showMemo("#Races .graph-memo");
    }

    if (hasOwnProperty(data, "bgs"))
    {
        $("#main-wrapper").append("<div class=statSection id=bgs></div>")
        $("#bgs").append("<h3 class=sectionTitle> Backgrounds: </h3>")
        // add div for graph
        $("#bgs").append("<div class=sectionText></div>")
        var Points = [];
        var max = {"bg":"none", "count":0};
        var total = 0;
        $.each(data.bgs, function(i, item){
            Points.push({data: item[1], label: item[0]});
            total += item[1];
            if (max.count < item[1]) {
                max.count=item[1]
                max.bg=item[0]
            };
        });
        bgsStr = "The most played background is <b>{0}</b> <br>with {1} games (<b>{2}%</b> of totals).".f(
            max.bg, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#bgs .sectionText").append(bgsStr)
        $("#bgs").append('<div class="graph-container"></div>');
        $("#bgs .graph-container").append('<div class="graph"></div>')
        $("#bgs .graph-container").append('<div class="graph-memo"></div>')
        $.plot("#bgs .graph", Points, options);
        $("#bgs .graph").showMemo("#bgs .graph-memo");
    }

    if (hasOwnProperty(data, "players"))
    {
        $("#main-wrapper").append("<div class=statSection id=players></div>")
        $("#players").append("<h3 class=sectionTitle> Top 5 players: </h3>")
        // add div for graph
        $("#players").append("<div class=sectionText></div>")
        var Points = [];
        var j = 0;
        var max = {"player":"none", "count":0};
        var total = 0;
        $.each(data.players, function(i, item){
            if (j < 5) {
                Points.push([item[0], item[1]]);
                if (j == 0) {
                    max.count=item[1]
                    max.player=item[0]
                };
            }
            total += item[1];
            j++;
        });
        playersStr = "The player with most games is <b>{0}</b> <br>with {1} games (<b>{2}%</b> of totals).".f(
            max.player, max.count, (max.count*100/total).toString().slice(0,5)
        )
        $("#players .sectionText").append(playersStr)
        $("#players").append('<div class="graph-container"></div>');
        $("#players .graph-container").append('<div class="graph"></div>')
        $("#players .graph-container").append('<div class="graph-memo"></div>')
        bar_options = {
			series: {
				bars: {
					show: true,
					barWidth: 0.6,
					align: "center"
				}
			},
			xaxis: {
				mode: "categories",
				tickLength: 0
			}
		}
        $.plot("#players .graph", [Points], bar_options);
        $("#players .graph").showMemo("#players .graph-memo");
    }

    $("#main-wrapper").append("<div class=statSection id=stats></div>")
    $("#stats").append("<h3 class=sectionTitle> Mean Stats: </h3>")
    statsHTML = '<div class="statTable"><table>'
    statsHTML += '<tr><td>XL</td><td>{0}</td>'.f(data.mean_XL)
    statsHTML += '<tr><td>Str</td><td>{0}</td>'.f(data.mean_Str)
    statsHTML += '<tr><td>Int</td><td>{0}</td>'.f(data.mean_Int)
    statsHTML += '<tr><td>Dex</td><td>{0}</td>'.f(data.mean_Dex)
    statsHTML += '<tr><td>AC</td><td>{0}</td>'.f(data.mean_AC)
    statsHTML += '<tr><td>EV</td><td>{0}</td>'.f(data.mean_EV)
    statsHTML += '<tr><td>SH</td><td>{0}</td>'.f(data.mean_SH)
    statsHTML += '<tr><td>Time</td><td>{0} hours</td>'.f(data.mean_time)
    statsHTML += '<tr><td>Turns</td><td>{0}</td>'.f(data.mean_turns)
    statsHTML += '</table></div>'
    $("#stats").append(statsHTML)
}

8
function search(query, syncResults, asyncResults) {
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


function searchGods(query, syncResults, asyncResults) {
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


function searchPlayers(query, syncResults, asyncResults) {
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


$.ajaxSetup( {
    beforeSend:function(){
        // show gif here, eg:
        $("#loader-gif").show();
    },
    complete:function(){
        // hide gif here, eg:
        $("#loader-gif").hide();
    }
});
