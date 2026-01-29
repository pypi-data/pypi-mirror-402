var _global_plots = [];

function updateClock() {
	var currentTime = new Date();
	var currentHours = currentTime.getHours();
	var currentMinutes = currentTime.getMinutes();
	var currentSeconds = currentTime.getSeconds();

	// Pad the minutes and seconds with leading zeros, if required
	currentMinutes = ( currentMinutes < 10 ? "0" : "" ) + currentMinutes;
	currentSeconds = ( currentSeconds < 10 ? "0" : "" ) + currentSeconds;

	// Choose either "AM" or "PM" as appropriate
	var timeOfDay = ( currentHours < 12 ) ? "AM" : "PM";

	// Convert the hours component to 12-hour format if needed
	currentHours = ( currentHours > 12 ) ? currentHours - 12 : currentHours;

	// Convert an hours component of "0" to "12"
	currentHours = ( currentHours == 0 ) ? 12 : currentHours;

	// Compose the string for display
	var currentTimeString = currentHours + ":" + currentMinutes + ":" + currentSeconds + " " + timeOfDay;

	var timeInMs = "" + Math.floor((Date.now() - 315964800000 + 17000)/1000.) + "&nbsp;" + currentTimeString;
	$("#clock").html(timeInMs);
	//$("#clock").html(currentTimeString);

}


$(document).ready(function()
{
    updateClock();
	setInterval('updateClock()', 1000);
});

function floor_div(x, n) {
	return ~~(x / n) * n;
}

function default_layout() {
	return {
		displayModeBar: false,
		margin: {t:15, b:20, l:30, r:0},
		font: {
			family: 'Noto Serif TC',
			size: 11,
		},
		xaxis: {tickformat: "d"},
	}
}


function default_options() {
	return {
		displayModeBar: false,
	}
}


function default_series_data_options() {
	return {
		line: {
			width: 0.5,
		},
	}
}


function duration_to_dt(duration) {
	if (duration <= 1000) {
		return 1;
	} else if (duration <= 10000) {
		return 10;
	} else if (duration <= 100000) {
		return 100;
	} else if (duration <= 1000000) {
		return 1000;
	} else if (duration <= 10000000) {
		return 10000;
	} else {
		return 100000;
	}
}


function duration_to_str(duration) {
	if (duration % 31540000 == 0) {
		return (duration / 31540000) + ' yr';
	} else if (duration % 2628000 == 0) {
		return (duration / 2628000) + ' mo';
	} else if (duration % 604800 == 0) {
		return (duration / 604800) + ' wk';
	} else if (duration % 86400 == 0) {
		return (duration / 86400) + ' day';
	} else if (duration % 3600 == 0) {
		return (duration / 3600) + ' hr';
	} else if (duration % 60 == 0) {
		return (duration / 60) + ' min';
	} else {
		return duration + ' s';
	}
}

function gpsnow() {
	//FIXME doesn't account correctly for leapseconds (assumes 18)
	return Math.round(Date.now() / 1000.) - 315964800 + 18;
}


function update_config_object(old_object, new_object) {
	for (var key in new_object) {
		old_object[key] = new_object[key];
	}
	return old_object;
}


function add_data_options(data, data_options) {
	for(i = 0; i<data.length; i++) {
		for (var key in data_options) {
			data[i][key] = data_options[key];
		}
		if ('name' in data) {
			for (var key in data_options[data.name]) {
				data[i][key] = data_options[data.name][key];
			}
		}
	}
	return data;
}

/**
 * generate log ticks for heatmaps
 */
function log_tick_maker(zvals, zmin = null, zmax = null, numticks = 6) {
	var d3 = Plotly.d3;
	if (zmin == null || zmax == null) {
		var zLogMin = zvals[0][0];
		var zLogMax = zvals[0][0];
		for (i = 0; i < zvals.length; i++) {
			var lowest = Math.min(...zvals[i]);
			var highest = Math.max(...zvals[i]);
			if(lowest < zLogMin)
				zLogMin = lowest;
			if(highest > zLogMax)
				zLogMax = highest;
		}
		zmin = Math.exp(zLogMin);
		zmax = Math.exp(zLogMax);
	}
	var tickValues = [];
	var tickName = [];
	var dtick = Math.floor((zmax - zmin) / numticks);
	var tempTick = floor_div(zmin + dtick, dtick);
	while (tempTick <= zmax) {
		tickName.push(d3.format("~s")(tempTick));
		tickValues.push(Math.log(tempTick));
		tempTick += dtick;
	}

	return [tickValues, tickName];
}


/**
 * base class for time-aware data structure
 * use derived Stream classes instead (e.g. Stream2D)
 */
class _Stream {
    constructor(measurement, schema, segment, data_options = {}, refresh_interval = -1, update = false, delay = 0) {
        this.measurement = measurement;
        this.schema = schema;
        this.segment = segment;
		this.delay = delay;
        this.update = update;
		this.latest = 0;
		this.data = [];
		this.data_options = update_config_object(default_series_data_options(), data_options);
    }

	_cat_data(d1, d2, segment) {
		return this._range(this._concat(d1,d2), segment.start, segment.stop);
	}

	_add_data_options(data) {
		// Custom trace data options have precedence over default
		// Both lists of trace options are added as well, but plotly ignores them
		$.extend(true, data, this.data_options);
		if ('name' in data) {
			for (var key in this.data_options[data.name]) {
				data[key] = this.data_options[data.name][key];
			}
		}
		if ('name' in this.schema) {
			data.name = this.schema.name;
		}
		return data;
	}
}


/**
 * time-aware data structure for timeseries data
 *
 * @param {String} measurement : the measurement name
 * @param {Object} schema : the schema to use, defines the table to query from
 * @param {Object} segment : a start. stop pair of the gps range to query
 * @param {Object} data_options : custom options to apply to incoming data
 * @param {Number} refresh_interval : how often to query for new data,
        negative values turn off refresh
 * @param {Number} delay : offset from real-time to query for new data
 */
class Stream2D extends _Stream {
    constructor(measurement, schema, segment, data_options = {}, refresh_interval = -1, update = false, delay = 0) {
        super(measurement, schema, segment, data_options, refresh_interval, update, delay);
	}

	_new_data(respdata) {
		return {x:[], y:[], name:''};
	}

	_concat(d1, d2) {
		var xdata = d1.x.slice(0);
		var ydata = d1.y.slice(0);

		// find time to remove duplicate data
		if (xdata.length == 0) {
			var maxt = 0;
		} else {
			var maxt = xdata[xdata.length - 1];
		}

		// search for time and slice out duplicates
		var start_idx = d3.bisectLeft(d2.x, maxt);
		xdata = xdata.concat(d2.x.slice(start_idx));
		ydata = ydata.concat(d2.y.slice(start_idx));

		return {x: xdata, y: ydata, name: d2.name, yaxis: d2.yaxis}
	}

	_range(data, start, stop) {
		var newdata = this._new_data(data);

		// NOTE assumes x is time
		var start_idx = d3.bisectLeft(data.x, start);
		var stop_idx = d3.bisectLeft(data.x, stop);

		newdata.x = data.x.slice(start_idx, stop_idx);
		newdata.y = data.y.slice(start_idx, stop_idx);

		if (data.name) {
			newdata.name = data.name;
		}
		if (data.yaxis) {
			newdata.yaxis = data.yaxis;
		}
		return newdata
	}

	update_data(respdata) {
		// FIXME: make sure that this is doing all of the right sanity checking, etc
		var newdata = [];

		for (var i = 0; i < respdata.length; i++) {
			var thisdata = this.data[i];

			// add new data to current
			if (typeof thisdata === "undefined") {
				thisdata = this._new_data(respdata[i]);
			}
			var thisnewdata = this._cat_data(thisdata, respdata[i], this.segment);
			newdata[i] = this._add_data_options(thisnewdata);

			this.latest = newdata[i].x[newdata[i].x.length - 1];
		}
		this.data = newdata;
	}
}


/*
 * time-aware data structure for heatmap data
 *
 * @param {String} measurement : the measurement name
 * @param {Object} schema : the schema to use, defines the table to query from
 * @param {Object} segment : a start. stop pair of the gps range to query
 * @param {Object} data_options : custom options to apply to incoming data
 * @param {Number} refresh_interval : how often to query for new data,
        negative values turn off refresh
 * @param {Number} delay : offset from real-time to query for new data
 */
class Stream3D extends _Stream{
    constructor(measurement, schema, segment, data_options = {}, refresh_interval = -1, update = false, delay = 0) {
        super(measurement, schema, segment, data_options, refresh_interval, update, delay);
		this.earliest_idx = null;
		if ('fill' in this.schema) {
			this.fill = this.schema.fill;
		} else {
			this.fill = 'NaN';
		}
	}

	_new_data(respdata) {
		var zd = [];
		var i;
		if ('text' in respdata) {
			var td = [];
		}
		for (i=0; i<respdata.y.length; i++) {
			zd.push([]);
			if ('text' in respdata) {
				td.push([]);
			}
		}
		if ('text' in respdata) {
			return {x:[], y:[], z:zd, text:td};
		} else {
			return {x:[], y:[], z:zd};
		}
	}

	_concat(d1, d2) {
		var xdata = d1.x.slice(0);
		var ydata = d1.y.slice(0);
		var zdata = d1.z.slice(0);
		if (ydata.length == 0) {
			ydata = d2.y.slice(0); // y data should never change though the first time this is called there might not be anything set in d1
		}
		if ('text' in d1) {
			var labels = d1.text.slice(0);
		}

		// find time to remove duplicate data
		if (xdata.length == 0) {
			var maxt = 0;
		}
		else {
			var maxt = xdata[xdata.length -1];
		}

		// search for time and slice out duplicates
		var start_idx = d3.bisectLeft(d2.x, maxt);
		xdata = xdata.concat(d2.x.slice(start_idx));

		// find missing tags
		var yold = new Set(ydata);
		var ynew = new Set(d2.y);
		var ydiff = new Set([...yold].filter(x => !ynew.has(x)));

		var j = 0;
		var fillValue = this.fill;
		ydata.forEach( function(y, i) {
			if ( !(ydiff.has(y)) ) {
				var thisZdata = d2.z[j].slice(start_idx);
				if ('text' in d1) {
					var thisTextdata = d2.text[j].slice(start_idx);
				}
				j++;
			} else {
				var thisZdata = new Array(xdata.length).fill(fillValue);
				if ('text' in d1) {
					var thisTextdata = new Array(xdata.length).fill(fillValue);
				}
			}
			zdata[i] = zdata[i].concat(thisZdata);
			if ('text' in d1) {
				labels[i] = labels[i].concat(thisTextdata);
			}
		});

		if ('text' in d1) {
			return {x: xdata, y: ydata, z: zdata, text: labels};
		} else {
			return {x: xdata, y: ydata, z: zdata};
		}
	}

	_range(data, start, stop) {
		var newdata = this._new_data(data);

		// NOTE assumes x is time
		var start_idx = d3.bisectLeft(data.x, start);
		var stop_idx = d3.bisectLeft(data.x, stop);

		newdata.x = data.x.slice(start_idx, stop_idx);
		for (var i = 0; i < data.z.length; i++) {
			newdata.z[i] = data.z[i].slice(start_idx, stop_idx);
			if ('text' in data) {
				newdata.text[i] = data.text[i].slice(start_idx, stop_idx);
			}
		}
		newdata.y = data.y // The y's should never change or else stuff will go really wrong.

		return newdata
	}

	update_data(respdata) {
		// FIXME: make sure that this is doing all of the right sanity checking, etc
		var newdata = [];

		for (var i = 0; i < respdata.length; i++) {
			var thisdata = this.data[i];

			// remove part of heatmap with missing data if needed
			if (this.earliest_idx != null) {
				var latest_idx = thisdata.x.indexOf(this.latest);
				if (latest_idx != -1) {
					var maxslice = Math.min(latest_idx, thisdata.x.length);
					thisdata.x = thisdata.x.slice(0, maxslice);
					for (var l = 0; l < thisdata.y.length; l++) {
						thisdata.z[l] = thisdata.z[l].slice(0, maxslice);
						if ('text' in thisdata) {
							thisdata.text[l] = thisdata.text[l].slice(0, maxslice);
						}
					}
				}
			}

			// add new data to current
			if (typeof thisdata === "undefined") {
				thisdata = this._new_data(respdata[i]);
			}
			var thisnewdata = this._cat_data(thisdata, respdata[i], this.segment);
			thisnewdata = this._add_data_options(thisnewdata)
			if ('text' in thisnewdata) {
				if ('zmin' in thisnewdata && 'zmax' in thisnewdata) {
					var tick_vals = log_tick_maker(thisnewdata.z, thisnewdata.zmin, thisnewdata.zmax);
					thisnewdata.zmin = Math.log(thisnewdata.zmin);
					thisnewdata.zmax = Math.log(thisnewdata.zmax);
				} else {
					var tick_vals = log_tick_maker(thisnewdata.z);
				}
				var colorbar_opts = {showticklabels: true, tickmode: 'array', ticks: 'outside', tickvals: tick_vals[0], ticktext: tick_vals[1]};
				thisnewdata.colorbar = colorbar_opts;
			}

			newdata[i] = thisnewdata;

			// find first time where there is missing data
			this.earliest_idx = respdata[i].x.length - 1;
			for (var k = 0; k < respdata[i].y.length; k++) {
				var idx = respdata[i].z[k].indexOf(null);
				if (idx != -1) {
					this.earliest_idx = Math.min(this.earliest_idx, idx);
				}
			}

			this.latest = respdata[i].x[this.earliest_idx];
		}

		this.data = newdata;
	}
}


/*
 * time-aware data structure for grabbing latest N points from a set of
 * timeseries, grouped by tag
 *
 * @param {String} measurement : the measurement name
 * @param {Object} schema : the schema to use, defines the table to query from
 * @param {Object} segment : a start. stop pair of the gps range to query
 * @param {Object} data_options : custom options to apply to incoming data
 * @param {Number} refresh_interval : how often to query for new data,
        negative values turn off refresh
 * @param {Number} delay : offset from real-time to query for new data
 */
class StreamLatest extends Stream2D {
    constructor(measurement, schema, segment, data_options = {}, refresh_interval = -1, update = false, delay = 0) {
        super(measurement, schema, segment, data_options, refresh_interval, update, delay);
	}

	update_data(respdata) {
		var newdata = [];
		for (var i = 0; i < respdata.length; i++) {
			var thisdata = this.data[i];
			if (typeof thisdata === "undefined") {
				thisdata = this._new_data(respdata[i]);
			}
			newdata[i] = this._add_data_options(respdata[i]);
		}
		this.data = newdata;
	}
}


/*
 * time-aware data structure for displaying dynamic tables
 *
 * @param {String} measurement : the measurement name
 * @param {Object} schema : the schema to use, defines the table to query from
 * @param {Object} segment : a start. stop pair of the gps range to query
 * @param {Object} data_options : custom options to apply to incoming data
 * @param {Number} refresh_interval : how often to query for new data,
        negative values turn off refresh
 * @param {Number} delay : offset from real-time to query for new data
 */
class StreamTable extends Stream2D {
    constructor(measurement, schema, segment, data_options = {}, refresh_interval = -1, update = false, delay = 0) {
        super(measurement, schema, segment, data_options, refresh_interval, update, delay);
	}

	update_data(respdata) {
		var newdata = [{'x':[], 'y':[]}];
		var thisdata = this.data[0];
		if (typeof thisdata === "undefined") {
			thisdata = this._new_data();
		}
		newdata[0] = this._add_data_options(thisdata)
		for (var i = 0; i < respdata.items.length; i++) {

			// check if far_key in schema and adds appropriate x values (inverse far)
			if (this.schema.far_key) {
				newdata[0].x.push(1 / respdata.items[i][this.schema.far_key]);
			} else {
				newdata[0].x.push(1 / respdata.items[i].far);
			}

			// push y values (1,2,3,4...), checks for prev y values and adds onto those
			// ex: prev-(98,99,100), next vals-(101,102,103)
			if (this.data[0] == null && i === 0) { // first ever run and first loop run
				newdata[0].y.push(1);
			} else if (i === 0) { // first loop run but already ran before
				newdata[0].y.push(this.data[0].y.length + 1);
			} else if (this.data[0] == null) { // first ever run but not first loop run
				newdata[0].y.push(i+1)
			} else { // already ran everything at least once
				newdata[0].y.push(newdata[0].y.length + 1);
			}
		}

		// Sort plot data from a higher x value having a lower index than a lower x value
		newdata[0].x.sort(function(a, b){return b-a});

		// Adds available fields to FAR_Table
		for (var i = 0; i < respdata.fields.length; i++) {
			FAR_Table.fields[respdata.fields[i].key] = respdata.fields[i];
		}
		// Adds available items to FAR_Table
		for (var key in respdata.items) {
			FAR_Table.items.push(respdata.items[key]);
		}
		FAR_Table.totalRows = FAR_Table.items.length;
		if (FAR_Table.dataTrack) {
			FAR_Table.currentPage += 1;
		}
		this.data = newdata;
		this.latest = this.segment.stop;
	}
}


/**
 * base class for displaying dynamically updating plots
 * use derived Plot classes instead (e.g. TimeSeries)
 */
class _TimePlot {
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		this.divname = divname;
		this.title = title;
		this.okay_to_draw = true;
		this.measurement = measurement;
		this.schema = schema;
		this.delay = delay;
		this.segment = segment;
		this.update = false;

		// save a reference to the initial duration, we will use that even if you are using live updates
		this.duration = segment.stop - segment.start;

		// determine dt from the duration set (used in aggregated data)
		if ('aggregate' in this.schema) {
			this.schema['dt'] = duration_to_dt(this.duration);
		}

		// set up url for querying data
		this.url = '';
		this.url_params = $.param(this.schema, true);
		this.base_url = new URL(`${script_name}api/timeseries/${this.measurement}/`, window.location.href);

		// set plot options and intervals
		this.grid = grid;
		this.layout = update_config_object(default_layout(), layout);
		this.options = update_config_object(default_options(), options);
		this.data_options = update_config_object(default_series_data_options(), data_options);
		this.refresh_interval = refresh_interval;
		this.prev_refresh_interval = refresh_interval;

		// set data source
		this.stream = new Stream2D(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
	}

	populate() {
		// call this after plot is initialized to grab initial data
		this.get_data(this.stream.segment);
		if (this.refresh_interval > 0) {
			this.set_interval(this.refresh_interval);
		}
		_global_plots.push(this);
	}

	toggle_interval() {
		if (this.refresh_interval < 0) {
			this.set_interval(this.prev_refresh_interval);
		}
		else {
			this.clear_interval();
		}
		// Reset the query counters
		// NOTE because this is all asynchronous, things can get messed up if someone is pausing and unpausing rapidly
	}

	set_interval(interval) {
		this.refresh_interval = interval;
		var that = this;
		this.timer = setInterval(function() {that.increment_live_data();}, that.refresh_interval);
	}

	clear_interval() {
		this.refresh_interval = -1;
		clearInterval(this.timer);
	}

	increment_live_data() {
		var stop = gpsnow() - this.delay;
		// Keep the same duration as initially requested
		var start = stop - this.duration - this.delay;
		this.stream.segment.stop = stop;
		this.stream.segment.start = start;
		if (this.stream.latest > this.stream.segment.start) {
			start = this.stream.latest;
		}
		this.get_data({"start":Math.floor(start), "stop":stop});
	}

	get_data(segment = null) {
		if (this.okay_to_draw) {
			var that = this;
			if (!segment) {
				segment = this.stream.segment;
			}
			this.url = new URL(`${segment.start}/${segment.stop}`, this.base_url)
			$.getJSON(this.url.href + '?' + this.url_params.replace(/&amp;/g, "&"), function(respdata) {
				that.stream.update_data(respdata);
				that._draw(that.stream.data);
			});
			this.okay_to_draw = false;
		}
	}

	_draw(data) {
		this.okay_to_draw = true;
		this._update_dimensions(this.divname);
		Plotly.react(this.divname, data, this.layout, this.options);
	}

	_update_dimensions(divname) {
		// 50 as arbitrary test value to prevent plots from overflowing or taking too much space
		this.layout.width = eval('grid'+divname).offsetWidth - 25;
		this.layout.height = eval('grid'+divname).offsetHeight - 50;
	}

}


class TimeSeries extends _TimePlot {
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		this.stream = new Stream2D(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
	}
}


class TimeHeatMap extends _TimePlot {
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		data_options.type = "heatmap";
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		this.stream = new Stream3D(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
		this.base_url = new URL(`${script_name}api/heatmap/${this.measurement}/`, window.location.href);
	}
}


class Bar extends _TimePlot {
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		data_options.type = "bar";
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		this.base_url = new URL(`${script_name}api/latest/${this.measurement}/`, window.location.href);
		this.stream = new StreamLatest(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
	}
}


class Snapshot extends _TimePlot {
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		this.base_url = new URL(`${script_name}api/snapshot/${this.measurement}/`, window.location.href);
		this.stream = new StreamLatest(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
	}
}


class MultiSchema extends _TimePlot{
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		this.stream = new Stream2D(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
		delete this.url_params;
		delete this.schema.dt;
		delete this.schema.measurement;
		this.script_name = script_name;
		for (var key in this.schema) {
			// Set a custom base URL for each schema measurement
			if (this.schema[key].measurement) {
				var base_url = new URL(`${script_name}api/timeseries/${this.schema[key].measurement}/`, window.location.href);
				delete this.schema[key].measurement;
			} else {
				var base_url = new URL(`${script_name}api/timeseries/${this.measurement}/`, window.location.href);
			}
			// Allow for custom data options for each schema
			if (this.schema[key].data_options) {
				var schema_options = this.schema[key].data_options;
				delete this.schema[key].data_options;
			} else {
				var schema_options = JSON.parse(JSON.stringify(this.data_options));
			}
			// Allow for a custom type for each schema
			if (this.schema[key].type) {
				data_options.type = this.schema[key].type;
				delete this.schema[key].type;
			}

			this[key] = {schema:this.schema[key], baseURL:base_url, schemaOptions:schema_options};
			if ('aggregate' in this[key].schema) {
				this[key].schema['dt'] = duration_to_dt(this.duration);
			}
		}
	}

	_add_label(data, sub_schema) {
		// FIXME: only works when there's a single trace per schema
		for (var i = 0; i < Object.keys(this.schema).length; i++) {
			if (!(data[i].length == 0) && 'name' in sub_schema["schema"+(i+1)]) {
				data[i][0].name = sub_schema["schema"+(i+1)].name;
			}
		}
		return data;
	}

	get_data(segment = null) {
		if (this.okay_to_draw) {
			var j = 0;
			var that = this;

			// ensure that data returned is ordered correctly
			this.newData = [];
			for (var i = 0; i < Object.keys(this.schema).length; i++) {
				this.newData.push([]);
			}

			// make API calls to each route
			Object.keys(that.schema).forEach( function(key, i) {
				if (!segment) {
					segment = that.stream.segment;
				}
				var schema_params = $.param(that.schema[key], true);
				var schema_url = new URL(`${segment.start}/${segment.stop}`, that[key].baseURL);
				$.getJSON(schema_url.href + '?' + schema_params.replace(/&amp;/g, "&"), function(respdata) {
					that.newData[i] = respdata;
					j++;

					// when all responses have been received, update current data and replot
					if (j == Object.keys(that.schema).length) {
						that.newData = that._add_label(that.newData, that.schema);
						that.stream.update_data(that.newData.flat());
						that._draw(that.stream.data);
					}
				});
			}, that);
			this.okay_to_draw = false;
		}
	}
}


class MultiAxis extends _TimePlot{
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		this.stream = new Stream2D(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
		delete this.url_params;
		delete this.schema.dt;
		delete this.schema.measurement;
		var axis = 1;
		for (var key in this.schema) {
			// Create the info for each yaxis supplied
			// Needs to be fixed to push any axis over 2 outside of the graph
			if (key != "axis1") {
				var layoutKey = 'y'+key;
				var axisLayout = {};

				if (axis != 2) {
					if (axis % 2 == 0) {
						axisLayout[layoutKey] = {side:'right', overlaying:'y', anchor:'free', position:axis*.15};
					} else {
						axisLayout[layoutKey] = {side:'left', overlaying:'y', anchor:'free', position:axis*-.15};
					}
				} else {
					axisLayout[layoutKey] = {side:'right', overlaying:'y', anchor:'x'};
				}
				axisLayout[layoutKey].title = this.layout[layoutKey].title;
				this.layout = update_config_object(this.layout, axisLayout);
			}
			// Allows for custom measurements to be used for each axis
			if (this.schema[key].measurement) {
				var base_url = new URL(`${script_name}api/timeseries/${this.schema[key].measurement}/`, window.location.href);
				delete this.schema[key].measurement;
			} else {
				var base_url = new URL(`${script_name}api/timeseries/${this.measurement}/`, window.location.href);
			}
			// Allows for custom data options to be passed to each yaxis
			if (this.schema[key].data_options) {
				var axis_options = this.schema[key].data_options;
				delete this.schema[key].data_options;
			} else {
				var axis_options = JSON.parse(JSON.stringify(this.data_options));
			}
			// Allows for a type to be specified for each yaxis
			if (this.schema[key].type) {
				axis_options.type = this.schema[key].type;
				delete this.schema[key].type;
			}
			this[key] = {schema:this.schema[key].schema, baseURL:base_url, axisOptions:axis_options};
			if ('aggregate' in this[key].schema) {
				this[key].schema['dt'] = duration_to_dt(this.duration);
			}
			axis++;
		}
	}

	_add_axis_options(data, axis) {
		for (var set in data) {
			data[set].yaxis = 'y'+axis;
		}
		return data
	}

	_update_dimensions(divname) {
		// 50 as arbitrary test value to prevent plots from overflowing or taking too much space
		if (Object.keys(this.schema).length > 2) {
			this.layout.width = eval('grid'+divname).offsetWidth - (25 * Object.keys(this.schema).length);
		}
		else {
			this.layout.width = eval('grid'+divname).offsetWidth - 25;
		}
		this.layout.height = eval('grid'+divname).offsetHeight - 50;
	}

	get_data(segment = null) {
		if (this.okay_to_draw) {
			var that = this;
			that.newData = []
			var i = 0
			for (var key in this.schema) {
				var axis_params = $.param(this[key].schema, true);
				var axis_url = new URL(`${segment.start}/${segment.stop}`, this[key].baseURL)
				if (!segment) {
					segment = this.stream.segment;
				}
				$.getJSON(axis_url.href + '?' + axis_params.replace(/&amp;/g, "&"), function(respdata) {
					i += 1
					respdata = that._add_axis_options(respdata, i);
					Array.prototype.push.apply(that.newData, respdata);
					if (i == Object.keys(that.schema).length) {
						that.stream.update_data(that.newData);
						that._draw(that.stream.data);
					}
				});
			}
			this.okay_to_draw = false;
		}
	}
}


class BinnedTimeHistogram extends _TimePlot {
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		data_options.type = "histogram2d";
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);

		// set histogram options
		if ('ybin' in schema) {
			this.data_options = update_config_object({autobiny: false, ybins: {start: schema['ybin_start'], end: schema['ybin_end'], size: schema['ybin']}}, this.data_options);
		}
		if ('tbin' in schema) {
			this.data_options = update_config_object({autobiny: false, xbins: {start: this.segment.start, end: this.segment.end, size: this.schema['tbin'] * this.schema['dt']}}, this.data_options);
		}
		this.stream = new Stream2D(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
	}

	increment_live_data() {
		var stop = gpsnow() - this.delay;
		// Keep the same duration as initially requested
		var start = stop - this.duration - this.delay;
		this.stream.segment.stop = stop;
		this.stream.segment.start = start;
		if (this.stream.latest > this.stream.segment.start) {
			start = this.stream.latest;
		}
		this.get_data({"start":Math.floor(start), "stop":stop});

		// time bins are now dynamic and will shift the entire graph over over time
		if ('tbin' in this.schema) {
			this.data_options.xbins.start =  Math.floor(this.stream.segment.start / this.data_options.xbins.size) * this.data_options.xbins.size;
			this.data_options.xbins.stop = Math.floor(this.stream.segment.stop / this.data_options.xbins.size) * this.data_options.xbins.size;
		}
	}
}


class IFAR extends _TimePlot {
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		data_options = update_config_object({line: {shape: 'hv', width: 0.5}}, data_options);
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		if (schema.lookback) {
			this.segment.start = this.segment.stop - schema.lookback;
		}
		this.stream = new StreamTable(this.measurement, this.schema, this.segment, this.data_options, this.refresh_interval, this.update, this.delay);
		this.type = 'IFAR';
		this.base_url = new URL(`${script_name}api/table/${this.measurement}/`, window.location.href);
	}

	_draw(data) {
		// FIXME: This is very hacky and very heavy, creates a new plot each time cuz react does not work
		this.okay_to_draw = true;
		this._update_dimensions(this.divname);
		Plotly.newPlot(this.divname, data, this.layout, this.options);
	}

	_update_dimensions(divname){
		this.layout.width = eval('grid'+divname).offsetWidth - 25;
		this.layout.height = eval('grid'+divname).offsetHeight - table.offsetHeight - 55;
	}

}


class TimeSegment extends _TimePlot{
	constructor(divname, title, measurement, schema, script_name, segment, refresh_interval = -1, data_options = {}, grid = {}, layout = {}, options = {}, delay = 0) {
		layout = update_config_object(layout, {'yaxis': {'type': 'linear', 'domain': [0.05, 1], 'visible': true, 'title': {'text': layout.yaxis.title.text}}, 'yaxis2': {'type': 'linear', 'domain': [0.02, 0.07], 'visible': false}});
		super(divname, title, measurement, schema, script_name, segment, refresh_interval, data_options, grid, layout, options, delay);
		delete this.url_params;
		delete this.schema.dt;
		this.script_name = script_name;
		for (var key in this.schema) {
			// Set a custom base URL for each schema measurement
			var base_url = new URL(`${script_name}api/${key}/${this.schema[key].measurement}/`, window.location.href);
			delete this.schema[key].measurement;

			// Allow for custom data options for each schema
			if (this.schema[key].data_options) {
				var schema_options = this.schema[key].data_options;
				delete this.schema[key].data_options;
			} else {
				var schema_options = JSON.parse(JSON.stringify(this.data_options));
			}

			this[key] = {schema:this.schema[key], baseURL:base_url, data_options:schema_options};
			if ('aggregate' in this[key].schema) {
				this[key].schema['dt'] = duration_to_dt(this.duration);
			}

			// set data options
			if (key === "segment") {
				this[key].data_options = update_config_object(this.data_options[key], {'showscale': false, 'yaxis': 'y2', 'type': 'heatmap'})
			} else {
				this[key].data_options = this.data_options[key]
			}
		}
		this.stream_series = new Stream2D(measurement, this["timeseries"].schema, segment, this["timeseries"].data_options, refresh_interval, this.update, delay);
		this.stream_segment = new Stream3D(measurement, this["segment"].schema, segment, this["segment"].data_options, refresh_interval, this.update, delay);
	}

	get_data(segment = null) {
		if (this.okay_to_draw) {
			var that = this;
			that.newData = []
			var i = 0;
			for (var key in this.schema) {
				var schema_params = $.param(this[key].schema, true);
				var schema_url = new URL(`${segment.start}/${segment.stop}`, this[key].baseURL);
				if (!segment) {
					segment = this.stream_segment.segment;
				}
				$.getJSON(schema_url.href + '?' + schema_params.replace(/&amp;/g, "&"), function(respdata) {
					if ('z' in respdata[0]) { // segmentplot
						that.stream_segment.update_data(respdata);
						Array.prototype.push.apply(that.newData, that.stream_segment.data);
					} else {
						that.stream_series.update_data(respdata);
						Array.prototype.push.apply(that.newData, that.stream_series.data);
					}
					i++;
					if (i == Object.keys(that.schema).length) {
						that._draw(that.newData);
					}
				});
			}
			this.okay_to_draw = false;
		}
	}
}


const plotFactory = new Map([
    ['TimeSeries', TimeSeries],
    ['TimeHeatMap', TimeHeatMap],
    ['Bar', Bar],
    ['Snapshot', Snapshot],
    ['MultiAxis', MultiAxis],
    ['MultiSchema', MultiSchema],
    ['BinnedTimeHistogram', BinnedTimeHistogram],
    ['IFAR', IFAR],
    ['TimeSegment', TimeSegment],
]);
