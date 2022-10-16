// download.js

// ############################################
// GLOBAL VARIABLES
var gridLayer = new L.geoJson(null);
STARTZOOM = 7;
var topurl = 'http://localhost:5511';

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
    maxZoom: 15
});
$('.leaflet-container').css('cursor','crosshair'); // from https://stackoverflow.com/a/28724847/4355695 Changing mouse cursor to crosshairs
L.control.scale({metric:true, imperial:false, position: "bottomright"}).addTo(map);

// layers
var overlays = {
    "IMD data grid points": gridLayer
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



// ############################################
// RUN ON PAGE LOAD

$(document).ready(function () {
	authenticate(fillToken);
    initialData(which='all', defaultYr=2010); // def moved to common.js
});


// ############################################
// FUNCTIONS

function makeLink() {
	let year = $('#y1').val();
	let ll = $('#selectedLocation').html();
    if (!ll.length) return;
    let llholder = ll.split(',');
    let lat = llholder[0].trim();
    let lon = llholder[1].trim();
    let which = $('#whichSelect').val();
    let url = `${APIpath}/fetchData?year=${year}&lat=${lat}&lon=${lon}&which=${which}`;
    let token = $('#tokenField').val();
    if(token) {
    	url += `&token=${token}`;
    }
    $('#linksDump').prepend(`<a href="${url}" target="_blank">${url}</a><br>`);
}

function fillToken(token) {
	// console.log(token);
	$('#tokenField').val(token);
}

function clearLinks() {
    $('#linksDump').html(``);
}

// ############################################
// API CALLS

