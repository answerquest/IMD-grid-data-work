// game.js

// ############################################
// GLOBAL VARIABLES
var gridLayer = new L.geoJson(null);
var globalGameid = null;

// #################################
/* MAP */
var cartoPositron = L.tileLayer.provider('CartoDB.Positron', {maxNativeZoom:19, maxZoom: 20});
var OSM = L.tileLayer.provider('OpenStreetMap.Mapnik', {maxNativeZoom:19, maxZoom: 20});
var gStreets = L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{maxZoom: 20, subdomains:['mt0','mt1','mt2','mt3']});
var gHybrid = L.tileLayer('https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}',{maxZoom: 20, subdomains:['mt0','mt1','mt2','mt3']});
var esriWorld = L.tileLayer.provider('Esri.WorldImagery', {maxNativeZoom:18, maxZoom: 20});

var baseLayers = { 
    "OpenStreetMap.org" : OSM, 
    "Carto Positron": cartoPositron, 
    "ESRI Satellite": esriWorld,
    "gStreets": gStreets, 
    "gHybrid": gHybrid
};

var map = new L.Map('map', {
    center: STARTLOCATION,
    zoom: STARTZOOM,
    layers: [cartoPositron],
    scrollWheelZoom: true,
    maxZoom: 15,
    // contextmenu: true,
    // contextmenuWidth: 140,
    // contextmenuItems: [
    //     { text: 'Load THIS block', callback: blockFromMap },
    //     // { text: 'Map an unmapped Stop here', callback: route_unMappedStop_popup }
    // ]
});
$('.leaflet-container').css('cursor','crosshair'); // from https://stackoverflow.com/a/28724847/4355695 Changing mouse cursor to crosshairs
L.control.scale({metric:true, imperial:false, position: "bottomright"}).addTo(map);

// layers
var overlays = {
    "IMD temperature data grid points": gridLayer
};
var layerControl = L.control.layers(baseLayers, overlays, {collapsed: true, autoZIndex:true}).addTo(map); 

// SVG renderer
var myRenderer = L.canvas({ padding: 0.5 });

// Load India int'l boundary as per shapefile shared on https://surveyofindia.gov.in/pages/outline-maps-of-india
L.geoJSON(india_outline, {
    style: function (feature) {
        return {
            color: "black",
            fillOpacity: 0,
            weight: 1,
            opacity: 1
        };
    },
    interactive: false
}).addTo(map);

var circleMarkerOptions = {
    renderer: myRenderer,
    radius: 5,
    fillColor: "blue",
    color: "white",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.7
};

// ############################################
// RUN ON PAGE LOAD

$(document).ready(function () {
    authenticate();
    initialData(); // def moved to common.js
});


// ############################################
// API CALLS




function gameStart() {
    let ll = $('#selectedLocation').html();
    if (!ll.length) return;
    let llholder = ll.split(',');
    let lat = parseFloat( llholder[0].trim() );
    let lon = parseFloat( llholder[1].trim() );
    let payload = {
        "y1": parseInt($("#y1").val()),
        "y2": parseInt($("#y2").val()),
        "lat": lat,
        "lon": lon
    };
    if( payload.y1 == payload.y2 ) {
        alert(`Please choose different Y1 and Y2.`);
        return;
    }
    let token = localStorage.getItem("imdapi_token");
    if(!token) {
        alert(`Please login first`);
        return;
    }
    $('#gameStart_status').html(`Fetching data, Generating graph...`);

    $.ajax({
        url: `${APIpath}/gameStart`,
        type: "POST",
        data : JSON.stringify(payload),
        headers: { "x-access-token": token },
        cache: false,
        contentType: 'application/json',
        success: function (returndata) {
            globalGameid = returndata.gameid;
            $('#graph1').html(`<img class="graph1" src="viz/${returndata.graph}" width="100%" height="auto" />`);
            $('#gameStart_status').html(`Graph generated`);

        },
        error: function (jqXHR, exception) {
            console.log("error:", jqXHR.responseText);
            $('#gameStart_status').html(`Error, check logs`);
        }
    });  

}


function gameSubmit(){
    let payload = {
        "gameid": globalGameid,
        "y1_tmax": $('#y1_tmax').val(),
        "y1_tmin": $('#y1_tmin').val(),
        "y2_tmax": $('#y2_tmax').val(),
        "y2_tmin": $('#y2_tmin').val(),
        "reasoning": $('#reasoning').val()
    };
    let token = localStorage.getItem("imdapi_token");
    if(!token) {
        alert(`Please login first`);
        return;
    }
    
    $('#gameSubmit_status').html(`Submitting your answer..`);
    $.ajax({
        url: `${APIpath}/gameSubmit`,
        type: "POST",
        data : JSON.stringify(payload),
        headers: { "x-access-token": token },
        cache: false,
        contentType: 'application/json',
        success: function (returndata) {
            $('#result').html(`<p>${JSON.stringify(returndata)}</p>`);
            $('#gameSubmit_status').html(`Scoring done. How'd it go?`);
            
        },
        error: function (jqXHR, exception) {
            console.log("error:", jqXHR.responseText);
            $('#gameSubmit_status').html(`Error, check logs`);
        }
    });  

}