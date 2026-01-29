% import json
% if current_page != 'index':
%   script_name = '../' + script_name
% end

<script>
  document.body.onkeydown = function(e) {
    if (e.keyCode == 32) {
      e.preventDefault();
    }
  };

  document.body.onkeyup = function(e) {
    if(e.keyCode == 32) {
      var i;
      for (i = 0; i < _global_plots.length; i++) {
        _global_plots[i].toggle_interval();
      }

      var isPlaying = function(audio) {return !audio.paused;};
      var a = document.getElementById('main_audio');
      if (isPlaying(a)) {
          a.pause();
      } else {
          a.play();
      }
    }
  };

  function disableSelect(event) {
    event.preventDefault();
  }

  var app = new Vue({
    el: '#plots',
    data() {
      return {
        plotConfig: {{! json.dumps(plots) }},
        plotDefaults: {{! json.dumps(plot_defaults) }},
        plots: [],
        layout: [],
        analysis: true,
        liveData: true,
        responsive: true,
        modalShow: false,
        timeOptions: [
          { value: 'historical', html: '<i class="fas fa-hourglass-half"></i>' },
          { value: 'online', html: '<i class="fas fa-step-forward"></i>' },
        ],
        form: {
          lookback: {{ lookback }},
          delay: {{ delay }},
          start: {{ start }},
          end: {{ stop }},
          type: '{{ type }}'
        },
        selected: {{ lookback }},
        options: [
          { value: 30, text: '30 s' },
          { value: 60, text: '1 min' },
          { value: 300, text: '5 min' },
          { value: 600, text: '10 min' },
          { value: 900, text: '15 min' },
          { value: 1800, text: '30 min' },
          { value: 3600, text: '1 hr' },
          { value: 14400, text: '4 hr' },
          { value: 43200, text: '12 hr' },
          { value: 86400, text: '1 day' },
          { value: 604800, text: '1 wk' },
          { value: 2628000, text: '1 mo' },
          { value: 7884000, text: '3 mo' },
          { value: 15770000, text: '6 mo' },
          { value: 31540000, text: '1 yr' },
        ]
      }
    },
    created: function() {
      this.attachPlots();
      var ranges = this.options.map(function(e) { return e.value; });
      var idx = ranges.indexOf(this.form.lookback);
      if (idx == -1) {
        var insertIdx = d3.bisectLeft(ranges, this.form.lookback);
        var text = duration_to_str(this.form.lookback);
        this.options.splice(insertIdx, 0, {value: this.form.lookback, text: text});
      }
    },
    watch: {
      "form.lookback": function() {
        if (this.form.type == 'historical') {
          this.form.end = this.form.start + this.form.lookback;
          this.selected = this.form.lookback;
        }
      },
    },
    methods: {
      increaseTime: function() {
        idx = this.options.map(function(e) { return e.value; }).indexOf(this.selected);
        idx = Math.min(idx + 1, this.options.length - 1);
        this.selected = this.options[idx].value;
        this.form.lookback = this.selected;
        if (this.form.type == 'historical') {
          this.form.end = this.form.start + this.selected;
        }
      },
      decreaseTime: function() {
        idx = this.options.map(function(e) { return e.value; }).indexOf(this.selected);
        idx = Math.max(idx - 1, 0);
        this.selected = this.options[idx].value;
        this.form.lookback = this.selected;
        if (this.form.type == 'historical') {
          this.form.end = this.form.start + this.selected;
        }
      },
      resizeEvent: function() {
        window.addEventListener('selectstart', disableSelect);
      },
      resizedEvent: function() {
        window.removeEventListener('selectstart', disableSelect);
      },
      moveEvent: function() {
        window.addEventListener('selectstart', disableSelect);
      },
      movedEvent: function() {
        window.removeEventListener('selectstart', disableSelect);
      },
      deleteItem: function(item) {
        // TODO: Account for if an item spans multiple rows and is the only item
        // If so the take the max yspan of items in rows spanned by the item
        // Change height by ySpace - max ySpan that is less than ySpace

        this.plots[item].okay_to_draw = false;
        var yItem = this.layout[item]['y'];
        var xItem = this.layout[item]['x'];
        var height = this.layout[item]['h'];
        var ySpace = this.layout[item]['y'] + height;
        var xSpace = this.layout[item]['w'] + xItem;
        var singleRow = true;
        this.layout[item]['h'] = 0;
        this.layout[item]['w'] = 0;
        this.layout[item]['x'] = 0;
        this.layout[item]['y'] = 0;
        this.layout[item]['show'] = false;

        for (var i = 0; i < this.layout.length; i++) {
          var y = this.layout[i]['y'];
          var ySpan = this.layout[i]['h'] + y;
          // First case if y is in same row
          // Second case if ySpace of another item is in the same row
          // Third case if the item spans through the row
          if (
            ((y >= yItem && y < ySpace) || (ySpan <= ySpace && ySpan > yItem) || (y <= yItem && ySpan >= ySpace)) &&
            this.layout[i]['h'] != 0 &&
            this.layout[i]['w'] != 0 &&
            this.layout[i]['i'] != item
          ) {
            singleRow = false;
          }
        }
        if (singleRow){
          for (var i in this.layout) {
            if (this.layout[i]['y'] >= ySpace) {
              this.layout[i]['y'] -= height;
            }
          }
        } else {
          for (var i = 0; i < this.layout.length; i++) {
            y = this.layout[i]['y'];
            ySpan = this.layout[i]['h'] + y;
            var x = this.layout[i]['x'];
            var xSpan = this.layout[i]['w'] + x;
            if (maxYSpan) {
              if (y >= ySpace && x >= xItem && xSpan <= xSpace && y == maxYSpan) {
                this.layout[i]['y'] -= height;
                maxYSpan = ySpan;
                i = 0;
              }
            } else {
              if (y >= ySpace && y == ySpace && x >= xItem && xSpan <= xSpace) {
                this.layout[i]['y'] -= height;
                var maxYSpan = ySpan;
                i = 0;
              }
            }
          }
        }
      },

      addItem: function(plot) {
        var totalHeight = 0;
        var ySpace = 0;
        for (var i in this.layout) {
          if (this.layout[i]['divname'] == plot.divname) {
            if(this.layout[i]['show'] == true) {
              this.modalShow = true;
              return
            }
            var gridID = this.layout[i]['i'];
          }
          if (this.layout[i]['y'] + this.layout[i]['h'] > ySpace) {
            ySpace = this.layout[i]['y'] + this.layout[i]['h']
          }
        }
        this.layout[gridID]['x'] = 0;
        this.layout[gridID]['y'] = ySpace;
        this.layout[gridID]['h'] = plot.grid['h'];
        this.layout[gridID]['w'] = plot.grid['w'];
        this.layout[gridID]['show'] = true;
        this.layout[gridID]['dragIgnoreFrom'] = '.js-plotly-plot';
        plot.okay_to_draw = true;
        plot.populate();
      },

      attachPlots: function() {
        this.ySpace = 0;
        this.plotConfig.forEach( function(plot, idx) {
          // set up grid options
          if ('grid' in plot) {
            var grid = Object.assign({}, plot.grid);
          } else {
            var grid = {'w': 12, 'h': 4, 'x': 0};
            plot.grid = Object.assign({}, grid);
          };
          grid.title = plot.title;
          grid.type = plot.type;
          grid.i = idx;
          grid.divname = 'plot'+idx;
          grid.dragIgnoreFrom = '.js-plotly-plot';
          if (plot.visible) {
            if (!('y' in grid)) {
              grid.y = this.ySpace;
            };
            grid.show = 1;
          } else {
            grid.y = 0;
            grid.w = 0;
            grid.h = 0;
            grid.show = 0;
          };
          if (grid.y + grid.h > this.ySpace) {
            this.ySpace = grid.y + grid.h;
          };

          // add grid to layout
          this.layout.push(grid);

          // set default plot options
          var plotLayout = ('layout' in plot) ? plot.layout : {};
          var dataOptions = ('data_options' in plot) ? plot.data_options : {};
          var options = ('options' in plot) ? plot.options : {};
          var segment = {"start":  {{ start }}, "stop": {{ stop }} };

          if ('default' in this.plotDefaults) {
            if ('layout' in this.plotDefaults.default) {
              plotLayout = update_config_object(plotLayout, this.plotDefaults['default']['layout']);
            } if ('data_options' in this.plotDefaults.default) {
              dataOptions = update_config_object(dataOptions, this.plotDefaults['default']['data_options']);
            } if ('options' in this.plotDefaults.default) {
              options = update_config_object(options, this.plotDefaults['default']['options']);
            }
          }
          if (plot.type in this.plotDefaults) {
            if ('layout' in this.plotDefaults[plot.type]) {
              plotLayout = update_config_object(plotLayout, this.plotDefaults[plot.type]['layout']);
            } if ('data_options' in this.plotDefaults[plot.type]) {
              dataOptions = update_config_object(dataOptions, this.plotDefaults[plot.type]['data_options']);
            } if ('options' in this.plotDefaults[plot.type]) {
              options = update_config_object(options, this.plotDefaults[plot.type]['options']);
            }
          }
          if ('schema' in plot) {
            plot.schema = update_config_object(plot.schema, plot.settings);
          }

          // create the plot
          var thisplot = new (plotFactory.get(plot.type))(
            grid.divname,         // div name for the plot
            plot.title,           // plot title stored for regeneration
            plot.schema.measurement, // name of measurement to query
            plot.schema,          // schema for retrieving data
            '{{ script_name }}',  // script name (hack to deal with cgi/apache)
            segment,              // initial data segment
            {{ refresh }},        // refresh interval in ms, -1 to disable refresh
            dataOptions,          // custom plot data options
            plot.grid,            // custom grid item for vue grid layout
            plotLayout,           // custom plot layout, provided as a dict
            options,              // custom plot options, provided as a dict
            {{ delay }},          // sets delay for realtime data
          );

          // populate plot and push
          if (plot.visible) {
            thisplot.populate();
          }
          this.plots.push(thisplot);
        }, this);
      },
    },
    delimiters: ['[[',']]'],
  });

  var FAR_Table = new Vue({
    el: '#table',
    data: function () {
      return {
        isShown: true,
        search: '',
        filter: null,
        dataTrack: false,
        sortBy: 'ifar',
        sortDesc: true,
        totalRows: {},
        perPage:5,
        currentPage: {},
        items: [],
        fields: {},
      }
    },
    watch: {
      dataTrack: function() {
        if (!this.dataTrack) {
          this.currentPage = 1;
        }
      },
      filter: function() {
        this.dataTrack = false;
        this.currentPage = 1;
      },
    },
    methods: {
      getTableJson: function (url) {
        axios
          .get(url)
          .then(response => {
            Vue.set(this.items, url, response.data.items);
            Vue.set(this.fields, url, response.data.fields);
            Vue.set(this.totalRows, url, response.data.items.length);
            Vue.set(this.currentPage, url, 1);
          })
      },
    },
    delimiters: ['[[',']]'],
  });

</script>
