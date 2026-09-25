(function($, window, wb){
'use strict';

var
reportType = (window.location.href.indexOf('statistics') !== -1) ? 'statistics' : 'historical',
Historical = {
  graph: {
    coordinates: {
      start: {
        minX: null,
        maxX: null,
        minY1: null,
        maxY1: null
      },
      assign: function(minX, maxX, minY1, maxY1, name){
        Historical.graph.coordinates[name].minX = minX;
        Historical.graph.coordinates[name].maxX = maxX;
        Historical.graph.coordinates[name].minY1 = minY1;
        Historical.graph.coordinates[name].maxY1 = maxY1;
      },
      reset: function(ranges){
        if(ranges.xaxis.from < Historical.graph.coordinates.start.minX){
          ranges.xaxis.from = Historical.graph.coordinates.start.minX;
        }

        if(ranges.xaxis.to > Historical.graph.coordinates.start.maxX){
          ranges.xaxis.to = Historical.graph.coordinates.start.maxX;
        }

        if(ranges.yaxis.from < Historical.graph.coordinates.start.minY){
          ranges.yaxis.from = Historical.graph.coordinates.start.minY;
        }

        if(ranges.yaxis.to > Historical.graph.coordinates.start.maxY){
          ranges.yaxis.to = Historical.graph.coordinates.start.maxY;
        }

        return ranges;
      }
    },
    events: {
      plothover: function(event, pos, item){
        $('#tooltip').remove();

        if(item){
          Historical.graph.tooltip.add(
            Historical.graph.tooltip.label(item.series.label, item.datapoint, item.dataIndex, item.series.yaxis),
            item.pageX,
            item.pageY,
            item.series.color
          );
        }
      }
    },
    tooltip: {
      label: function(label, datapoint, index, axis){
        var
        text,
        parameter = {
          name: $('#parameter-type').val(),
          code: {
            Level: 'H',
            Flow: 'Q'
          }
        },
        dateFormat = function(date, label){
          var
          formatted = new Date(date).toISOString().replace(/T/, ' ').replace(/ (00:){2}\d{2}\.\d{3}Z$/, ''),
          dataType = $('#data-type').val(),
          statsLabels = ['maximum', 'minimum', 'mean', 'median', 'upper_quartile', 'lower_quartile'];

          if(reportType === 'historical' && dataType === 'Monthly'){
            formatted = formatted.replace(/-\d{2}$/, '');
          }else if(dataType === 'Annual Extremes' || dataType === 'Peak'){
            formatted = formatted.replace(/(-\d{2}){2}$/, '');
          }

          if(reportType === 'statistics' || statsLabels.includes(label)){
            formatted = formatted.replace(/^\d{4}-/, '');
          }

          return formatted;
        };

        text = '<b>' + Historical.graph.legend.title(label) + '</b><br>';
        text += dateFormat(datapoint[0], label) + '<br>';
        text += parameter.code[parameter.name] + ' = ' + Historical.graph.options.yaxis.tickFormatter(datapoint[1], axis) + ' ' + ((parameter.name === 'Flow') ? 'm<sup>3</sup>/s' : 'm') + '<br>';

        return text;
      },
      add: function(content, x, y, z){
        $('<div id="tooltip">' + content + '</div>').css({
          top: y - 30,
          left: x + 30,
          border: '2px solid ' + z,
        }).appendTo('body').fadeIn(200);
      }
    },
    create: function(){
      var
      dataType = $('#data-type').val(),
      graphHeight = $('main > div.container').width() / 1.5,
      axes,
      dataAvailable = Historical.data.available(),
      data,
      ticks = 0;

      if(dataAvailable === true){
        data = Historical.graph.dataSet(Historical.data.values);
        Historical.graph.show();

        $.each(data, function(k, v){
          if(v.data.length > ticks){
            ticks = v.data.length;
          }
        });

        Historical.graph.options.xaxis.timeformat = Historical.graph.axes.dateFormat();
        Historical.graph.options.xaxis.ticks = ($('html').is('.xxsmallview, .xsmallview')) ? 3 : null;

        if(Historical.graph.options.xaxis.ticks === null && ticks < 8){
          Historical.graph.options.xaxis.ticks = ticks;
        }

        if(reportType === 'historical' && dataType !== 'Peak' && dataType !== 'Annual Extremes'){
          Historical.graph.options.xaxis.min = moment.utc($('#first-year').val() + '-01-01 00:00:00');
          Historical.graph.options.xaxis.max = moment.utc($('#last-year').val() + '-12-31 23:59:59');
        } else if(reportType === 'statistics') {
          Historical.graph.options.xaxis.min = moment.utc('2016-' + $('input[name="start_month"]').val() + '-01 00:00:00');
          Historical.graph.options.xaxis.max = moment.utc('2016-' + $('input[name="end_month"]').val() + '-31 23:59:59');
        }

        if($('#log').is(':checked') === true){
          Historical.graph.options.yaxis.mode = 'log';
          Historical.graph.options.yaxis.transform = function(v){
            return (v > 0) ? Math.log(v) / Math.LN10 : null;
          };
          Historical.graph.options.yaxis.inverseTransform = function(v){
            return Math.pow(10, v);
          };
        }

        Historical.graph.$element.css({ height: `${graphHeight}px` });
        Historical.graph.plot = $.plot(Historical.graph.$element, data, Historical.graph.options);
        axes = Historical.graph.plot.getAxes();
        Historical.graph.coordinates.assign(axes.xaxis.min, axes.xaxis.max, axes.yaxis.min, axes.yaxis.max, 'start');

        Historical.graph.plot.setupGrid();
        Historical.graph.plot.draw();
        Historical.graph.legend.add();
        Historical.graph.axes.label.add();
      }else{
        Historical.graph.hide();
        Historical.graph.showNoData();
      }
    },
    show: function(){
      $('#legend, .graph-container, .controls.panel').removeClass('wb-inv');
      $('p.no-data-historical').remove();
    },
    hide: function(){
      $('#legend, .graph-container, .controls.panel').addClass('wb-inv');

      if($('p.no-data-historical').length === 0){
        $('.graph-container').after('<p class="no-data-historical text-center">' + t('No data available for the selected time period.') + '</p>');
      }
    },
    showNoData: function(){
      if($('#no-data-historical').length === 0){
        $('.graph-container').after('<p id="no-data-historical" class="text-center">' + t('You did not choose any statistic to be displayed, please choose at least one now and use the <strong>refresh</strong> button.') + '</p>');
      }
    },
    dataSet: function(values){
      var
      dataSet = [],
      param,
      legendText;

      Historical.graph.legend.values = {};

      $.each(values, function(key, value){
        if(value.length > 0){
          dataSet.push({
            label: key,
            data: value,
            yaxis: 1,
            lines: {
              show: true
            },
            points: {
              show: true,
              symbol: 'circle',
              radius: 0.5
            },
            shadowSize: 0,
            color: Historical.graph.line.colors[key]
          });

          Historical.graph.legend.values[Historical.graph.legend.title(key)] = Historical.graph.line.colors[key];
        }
      });

     return dataSet;
    },
    options: {
      xaxis: {
        show: true,
        position: 'bottom',
        mode: 'time',
        timeformat: '',
        autoScale: 'exact',
        min: null,
        max: null
      },
      yaxis: {
        tickFormatter: function(value, axis){
          var
          param = $('#parameter-type').val(),
          formatted;

          if(param === 'Flow'){
            formatted = value.toPrecision(3);
          }else{
            formatted = value.toFixed(3);
          }

          if(formatted.toString().match(/e[+-]/) !== null){
            formatted = Number(formatted);
          }

          return formatted;
        }
      },
      yaxes: [{
        show: true,
        position: 'left',
        min: null,
        max: null
      }],
      legend: {
        show: false,
        position: 'se',
        margin: 15,
        backgroundColor: '#EEE',
      },
      lines: {
        show: true,
        lineWidth: 1
      },
      grid: {
        hoverable: true,
        clickable: true,
        mouseActiveRadius: 20,
        autoHighlight: false
      },
      axisLabel: {
        show: true
      },
      zoom: {
        interactive: true
      },
      pan: {
        interactive: true
      }
    },
    legend: {
      values: {},
      add: function(){
        var
        $flotLegend = $('#flot-legend div.row');

        $flotLegend.empty();

        $.each(Historical.graph.legend.values, function(key, value){
          $flotLegend.append('<div class="col-sm-4 mrgn-tp-md"><div class="row"><div class="col-xs-3 text-center"><div class="legend-block  line" style="background-color: ' + value + ' !important;"></div></div><div class="col-xs-9">' + key + '</div></div></div>');
        });
      },
      title: function(label){
        var
        text = '',
        dataType = $('#data-type').val(),
        firstYear = $('#first-year').val(),
        lastYear = $('#last-year').val();

        if(label === 'provisional'){
          text = t('%year% Data').replace(/%year%/, `${(firstYear === lastYear) ? lastYear : `${firstYear}-${lastYear}`}`);
        }else{
          text = capitalize(t(label.replace('_', ' ').toLowerCase()));

          if(dataType === 'Annual Extremes'){
            text += ' ' + t('Daily');
          }else if(dataType === 'Peak'){
            text += ' ' + t('Instantaneous');
          }
        }

        return text;
      },
    },
    axes: {
      label: {
        add: function(){
          var
          $param = $('#parameter-type'),
          dateLabel = function(){
            var
            dataType = $('#data-type').val(),
            text = {
              Daily: t('Date'),
              Monthly: t('Month'),
              'Annual Extremes': t('Year'),
              Peak: t('Year')
            };

            return text[dataType];
          },
          paramLabel = function(param){
            var
            text = '';
            if(param === 'Flow'){
	      text = t('Discharge') + ' (m<sup>3</sup>/s)';
	    }else if(param === 'Level'){
              text = t('Level') + ' (m)';
	    }
            
            if($('#data-type').val()==='Daily' && reportType==='historical'){
	      text += ` <a title="${t('Daily mean calculation')}" href="/contactus/faq_${lang.substring(0, 1)}.html#data-measured"><span class="fas fa-info-circle text-info"></span></a>`;
	    }
		return text;
          },
          notice = function(paramid){
            var
            data = Historical.data.values[paramid];

            if(data['provisional'].length === 0){
              return '<span class="glyphicon glyphicon-exclamation-sign text-danger mrgn-lft-sm" title="' + t('No data available for the selected time period.') + '"></span>';
            }

            return '';
          };

          $('.axis.x').empty().append(dateLabel());
          $('.axis.y1').empty().append(paramLabel($param.val()));
        }
      },
      dateFormat: function(){
        var
        dataType = $('#data-type').val(),
        format = {
          Daily: (reportType === 'historical') ? '%Y-%m-%d' : '%m-%d',
          Monthly: (reportType === 'historical') ? '%Y-%m' : '%m-%d',
          'Annual Extremes': '%Y',
          Peak: '%Y'
        };

        return format[dataType];
      }
    },
    line: {
      colors: {
        provisional: '#FF0000',
        maximum: '#66CC66',
        minimum: '#0000FF',
        mean: '#00B100',
        median: '#FF9900',
        upper_quartile: '#800080',
        lower_quartile: '#66CDAA'
      },
    },
    plot: null,
    $element: $('#graph')
  },
  request: {
    send: function(async){
      var
      params = {
        station: $('#station').val(),
        data_type: $('#data-type').val().toLowerCase().replace(' ', '_'),
        first_year: (reportType === 'historical') ? $('#first-year').val() : '2016',
        last_year: (reportType === 'historical') ? $('#last-year').val() : '2016',
        start_year: $('#start-year').val(),
        end_year: $('#end-year').val(),
        start_month: ($('#start-month').length === 1) ? $('#start-month').val() : '01',
        end_month: ($('#end-month').length === 1) ? $('#end-month').val() : '12',
        results_type: reportType,
        parameter_type: $('#parameter-type').val().toLowerCase(),
      },
      token = document.cookie.replace(/(?:(?:^|.*;\s*)token\s*\=\s*([^;]*).*$)|^.*$/, "$1");

      if(token !== ''){
        params.token = token;
      }

      $.each({
        'maximum': 'y1Max', 'minimum': 'y1Min',
        'mean': 'mean1', 'median': 'median1',
        'upper': 'upper1', 'lower': 'lower1',
      }, function(k, v){
        if($('[type="checkbox"][name="' + v + '"]').prop('checked') === true){
          params[k] = '1';
        }
      });

      $('#offline-query-error').remove();
      Historical.data.values = {};
      $.ajax({
        url: '/services/historical_graph/json/inline',
        method: 'get',
        data: params,
        async: async,
        dataType: 'json'
      }).success(function(data){
        Historical.data.values = data;
      }).error(function(a, b, c){
        Historical.data.values = {};
        $('<div id="offline-query-error" class="alert alert-danger" role="alert"></div>').text(a.responseText || 'Data request failed').insertAfter('#wb-cont');
      });
    },
    afterComplete: function(){
      Historical.request.send(false);
      Historical.graph.create();
    },
  },
  data: {
    values: {},
    filter: function(minX, maxX, minY, maxY){
      var
      filtered = {};

      $.each(Historical.data.values, function(key, value){
        $.each(value, function(k, v){
          if(v[0] >= minX && v[0] <= maxX && v[1] >= minY && v[1] <= maxY){
            if(filtered[key] === undefined){
              filtered[key] = [];
            }

            filtered[key].push(v);
          }
        });
      });

      return (filtered === {}) ? filtered : Historical.data.values;
    },
    available: function(){
      var
      available = 0;

      $.each(Historical.data.values, function(key, value){
        $.each(value, function(k, v){
          available += v.length;
        });
      });

      return (available > 0);
    }
  }
},
loadingOverlay = {
  add: function(){
    $('main').after('<div id="loading-overlay"><img src="/images/loading.gif" alt=""/></div>')
  },
  remove: function(){
    $('#loading-overlay').remove();
  }
},
$body = $('body'),
capitalize = function(text){
  return text.substr(0, 1).toUpperCase() + text.substr(1);
},
disableStats = function(){
  var
  firstYear = $('#first-year').val(),
  lastYear = $('#last-year').val();

  if(firstYear === lastYear){
    $('#graph-settings input, #graph-settings select').prop('disabled', false);
    return;
  }

  $('#graph-settings input, #graph-settings select').prop('disabled', true);
  $('#graph-settings input[type="checkbox"]').prop('checked', false);
};

$(document).on('ready', function(e){
  loadingOverlay.add();
  disableStats();
  Historical.request.afterComplete();
  loadingOverlay.remove();
});

$body.on('resize', Historical.graph.create);

$('#graph').on('plothover', function(e, pos, item){
  Historical.graph.events.plothover(e, pos, item);
});

$('#first-year, #last-year').on('change', disableStats);

/*
  $('#apply-settings').on('click', function(e){
  loadingOverlay.add();
  Historical.request.afterComplete();
  loadingOverlay.remove();
  history.pushState({}, document.title, '/report/real_time_' + lang + '.html?' + $('#modify-settings').serialize());
  e.preventDefault();
  e.stopPropagation();
});*/

})(jQuery, window, wb);
