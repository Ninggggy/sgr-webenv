(function($, window, wb){
'use strict';

var
authorizedError = false,
RealTime = {
  graph: {
    create: function($graphTag, parameters, double){
      var
      dataAvailable = RealTime.data.available(),
      $graphDiv = $graphTag.find('div'),
      axes,
      minY1,
      minY2,
      $html = $('html'),
      createErrorMessages = function($tag){
        $tag.find('a').remove();
        $tag.find('[data-parameterid] small, [data-parameterid2] small').each(function(){
          var
          $this = $(this),
          parameterName = $this.text().replace(/ \([A-Za-z0-9\/%'"°μ²³]+\)$/, '');
          $tag.append('<div class="text-danger">' + parameterName + ': ' + t('No data available') + '</span>');
          $this.parent().remove();
        });
      };

      RealTime.graph.tag = $graphTag;

      if(dataAvailable === true && $graphDiv.length !== 0){
        //Setting X-axis ticks
        if($html.is('.xxsmallview' )){
          RealTime.graph.options.xaxis.ticks = 2;
        }else{
          RealTime.graph.options.xaxis.ticks = 4;
        }

        RealTime.graph.options.xaxis.min = moment.utc(parameters.start_date + ' 00:00:00');
        RealTime.graph.options.xaxis.max = moment.utc(parameters.end_date + ' 23:59:59');

        if(!double){ // Creates graph for single parameter
          minY1 = RealTime.data.minValue(parameters.parameter_id);
          RealTime.graph.options.yaxes[1].show = false;

          if(minY1 !== null && minY1.toString().match(/^0(\.0[0-9]+)?$/) !== null){
            RealTime.graph.options.yaxes[0].min = (0 - (RealTime.data.maxValue(parameters.parameter_id) * 0.2));
          }

          RealTime.graph.plot = $.plot($graphDiv, RealTime.graph.dataSet(RealTime.data.values), RealTime.graph.options);
        }else{ // Creates graph for [46(Water Primary) or 16(Secondary) or 52(Tertiary)] and 47(Discharge) as combined.
          RealTime.graph.options.yaxes[1].show = true;
          minY1 = RealTime.data.minValue(parameters.parameter_id[0]);
          minY2 = RealTime.data.minValue(parameters.parameter_id[1]);

          // Makes sure that min is not touching the bottom of the graph. Updates Yaxis
          if(minY1 !== null && minY1.toString().match(/^0(\.0[0-9]+)?$/) !== null){
            RealTime.graph.options.yaxes[0].min = (0 - (RealTime.data.maxValue(parameters.parameter_id[0]) * 0.2));
          }
          // Makes sure that min is not touching the bottom of the graph. Updates Yaxis
          if(minY2 !== null && minY2.toString().match(/^0(\.0[0-9]+)?$/) !== null){
            RealTime.graph.options.yaxes[1].min = (0 - (RealTime.data.maxValue(parameters.parameter_id[1]) * 0.2));
          }

          RealTime.graph.plot = $.plot($graphDiv, RealTime.graph.dataSet(RealTime.data.values), RealTime.graph.options);
          $graphDiv.css('margin-top', '4%');


          var
          $graphHeader = $("span:contains(" + parameters.station_id + ")").parent(),
          count = 0,
          dataCheck;
          //Adds color legend icon.
          //If data for a single parameter in combined is empty then append (!) icon.
          for(var i = 1, j = parameters.parameter_id.length + 1; i < j; i++){
            $graphHeader.children('.y' + (i)).append('<span class="glyphicon glyphicon-stop"></span>');
            dataCheck = RealTime.data.values[parameters.parameter_id[i-1]];

            if(typeof dataCheck !== "undefined"){
              if(dataCheck['final'].length === 0 && dataCheck['provisional'].length === 0){
                count++;
                $graphHeader.children('.y' + i).children('.glyphicon-stop').remove(); //Removes color legend icon
                $graphHeader.children('.y' + i).append('<span class="glyphicon glyphicon-exclamation-sign text-danger mrgn-lft-sm" title="' + t('No data available for the selected time period.') + '"></span>');
              }
            }else{// Error for authorizedError parameter if not logged in.
              count++;
              $graphHeader.children('.y' + i).children('.glyphicon-stop').remove(); //Removes color legend icon
              $graphHeader.children('.y' + i).append('<span class="glyphicon glyphicon-exclamation-sign text-danger mrgn-lft-sm" title="' + t('Parameter is not authorized') + '"></span>');
            }
          }

          if(authorizedError){ //Remove non authorized message under the graph.
            $graphHeader.parent().children('.second-param-error').prev().remove();
            $graphHeader.parent().children('.second-param-error').remove();
          }

          if(count === parameters.parameter_id.length){// Error message displayed, if the data for combined graph empty.
            createErrorMessages($graphTag);
          }
        }
      }else {
        createErrorMessages($graphTag);
      }
    },
    dataSet: function(values){
      var
      dataSet = [],
      param,
      keysIndex = Object.keys(values);
      //For the combined graph, if parameter code for water is not on 0th index of keysIndex Array, then reverse the array.
      if(keysIndex.length === 2 && (keysIndex[0] !== "46" && keysIndex[0] !== "16" && keysIndex[0] !== "52")){
        keysIndex.reverse();
      }
      $.each(values, function(key, value){
        param = keysIndex.indexOf(key) + 1; //Works for both combined and single graph.
        $.each(value, function(k, v){
          dataSet.push({
            data: v,
            yaxis: param,
            lines: {
              show: true,
              lineWidth: 1
            },
            points: {
              show: false,
              symbol: 'circle',
              radius: 0.5,
              fillColor: RealTime.graph.line.colors[param][k]
            },
            shadowSize:0,
            color: RealTime.graph.line.colors[param][k]
          });
        });
      });

      return dataSet;
    },
    options: {
      xaxis: {
        show: true,
        position: 'bottom',
        mode: 'time',
        timeformat: '%Y-%m-%d',
        ticks: 4
      },
      yaxis: {
        tickFormatter: function(value, axis){
          var
          param,
          formatted;

          if(axis.n === 1){
            param = RealTime.graph.tag.find('[data-parameterid]').attr('data-parameterid');
          }
          else{
            param = RealTime.graph.tag.find('[data-parameterid2]').attr('data-parameterid2');
          }

          formatted = (param === '47') ? value.toPrecision(3) : value.toFixed(3);

          if(formatted.toString().match(/e[+-]/) !== null){
            formatted = Number(formatted);
          }

          return formatted;
        }
      },
      yaxes: [
        {
          show: true,
          position: 'left',
          min: null,
          max: null,
        },
        {
          show: false,
          position: 'right',
          min: null,
          max: null,
        }
      ],
      lines: {
        show: true
      },
      axisLabel: {
        show: true
      }
    },
    line: {
      colors: {
        1: {
          provisional: '#66CC66',
          final:'#6E6EEE'
        },
        2: {
          provisional: '#FF9900'
        }
      },
    },
    plot: null
  },
  request: {
    send: function(async, parameters){
      var
      params = {
        station: parameters.station_id,
        start_date: parameters.start_date,
        end_date: parameters.end_date,
      },
      token = document.cookie.replace(/(?:(?:^|.*;\s*)token\s*\=\s*([^;]*).*$)|^.*$/, "$1");

      if(token !== ''){
        params.token = token;
      }

      params.param1 = parameters.parameter_id[0];
      if(!authorizedError){ //If second parameter not authorizedError then set param2 for request.
        params.param2 = parameters.parameter_id[1];
      }

      RealTime.data.values = {};
      $.ajax({
        url: '/services/real_time_graph/json/inline',
        method: 'get',
        data: params,
        async: async,
        dataType: 'json'
      }).success(function(data){
        const replacer = (match, p1, p2, p3, offset, string) => {
          return Date.parse(`${p1}Z`);
        };
        data = JSON.stringify(data);
        data = data.replace(/"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"/g, replacer);
        data = JSON.parse(data);

        RealTime.data.values = data;
      }).error(function(){// Clear data so failed requests cannot show a previous station.
          RealTime.data.values = {};
          authorizedError = true;
      });
    },
    afterComplete: function(parameters, $graphTag, double){
      if(double === true){ //Request for combined graph
        RealTime.request.send(false, parameters);
        RealTime.graph.create($graphTag, parameters, true);
      }else{ // Request for single graph
        RealTime.request.send(false, parameters);
        RealTime.graph.create($graphTag, parameters, false);
      }
      authorizedError = false;
    }
  },
  data: {
    values: {},
    available: function(){
      var
      available = 0;

      $.each(RealTime.data.values, function(key, value){
        $.each(value, function(k, v){
          available += v.length;
        });
      });
      return (available > 0);
    },
    minValue: function(paramId){
      var
      min = null;

      if(typeof RealTime.data.values[paramId] !== 'undefined'){
        $.each(RealTime.data.values[paramId]['provisional'], function(k, v){
          if(min === null || v[1] < min){
            min = v[1];
          }
        });
      }

      return min;
    },
    maxValue: function(paramId){
      var
      max = 0;

      if(typeof RealTime.data.values[paramId] !== 'undefined'){
        $.each(RealTime.data.values[paramId]['provisional'], function(k, v){
          if(max === null || v[1] > max){
            max = v[1];
          }
        });
      }

      return max;
    }
  },
  axes: {}
},
loadingOverlay = {
  add: function(){
    $('main').after('<div id="loading-overlay"><img src="/images/loading.gif" alt=""/></div>')
  },
  remove: function(){
    $('#loading-overlay').remove();
  }
};

$(document).on('ready', function(e){
  var timeRange = $('#days').find(":selected").text();
  var start_date, end_date;
  var stationObject = {};

  loadingOverlay.add();

  var
  $this,
  stationID,
  paramID,
  paramID2;

  $('section.graph').each(function(k, v){ // Gets parameters for each station
    $this = $(this);
    stationID = $this.find('[data-stationid]').attr('data-stationid');
    paramID = $this.find('[data-parameterid]').attr('data-parameterid');
    paramID2 = $this.find('[data-parameterid2]').attr('data-parameterid2');

    if(typeof stationObject[stationID] === 'undefined'){
      stationObject[stationID] = [];
    }
    stationObject[stationID].push(paramID);
    if(paramID2 !== 'undefined'){
      stationObject[stationID].push(paramID2);
    }
  });

  $('section.graph').each(function(k, v){
    var $this = $(this);
    start_date = $this.attr('data-start-date');
    end_date = $this.attr('data-end-date');

    if($this.find('span.text-danger').length === 0){
      stationID = $this.find('[data-stationid]').attr('data-stationid');
      //Request for single graph.
      if(stationObject[stationID].length < 2){
        paramID = stationObject[stationID][0];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:[paramID]};
        RealTime.request.afterComplete(parameters, $this, false);
      }
      else {//Request for combined graph.
        combineGraph(stationObject, stationID, $this, start_date, end_date);
      }
    }else if($this.find('span.second-param-error').length !== 0){//Request when second parameter error.
      stationID = $this.find('[data-stationid]').attr('data-stationid');
      authorizedError = true;
      //Request for single graph.
      if(stationObject[stationID].length < 2){
        paramID = stationObject[stationID][0];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:[paramID]};
        RealTime.request.afterComplete(parameters, $this, false);
      }else{//Request for combined graph
        combineGraph(stationObject, stationID, $this, start_date, end_date);
      }
    }
  });

  function combineGraph(stationObject, stationID, $this, start_date, end_date){
    var paramID,
        parameters;
    if(stationObject[stationID].indexOf('47') >= 0){
      if(stationObject[stationID].indexOf('46') >= 0){
        paramID = stationObject[stationID];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:['46', '47']};
        RealTime.request.afterComplete(parameters, $this, true);
        stationObject[stationID] = stationObject[stationID].filter(function(value, index, arr){
          return (value !== '46' && value !== '47');
        });
      }else if(stationObject[stationID].indexOf('16') >= 0){ //For secondary and discharge
        paramID = stationObject[stationID];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:['16','47']};
        RealTime.request.afterComplete(parameters, $this, true);
        stationObject[stationID] = stationObject[stationID].filter(function(value, index, arr){
          return (value !=='16' && value !== '47');
        });
      }else if(stationObject[stationID].indexOf('52') >= 0){ //For tertiary and discharge
        paramID = stationObject[stationID];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:['52','47']};
        RealTime.request.afterComplete(parameters, $this, true);
        stationObject[stationID] = stationObject[stationID].filter(function(value, index, arr){
          return (value !=='52' && value !== '47');
        });
      }else{ // Single graph for paramater which was not chosen to be combined.
        paramID = $this.find('[data-parameterid]').attr('data-parameterid');
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:[paramID]};
        RealTime.request.afterComplete(parameters, $this, false);
      }
    }else if(stationObject[stationID].indexOf('8') >= 0){//SENSOR
      if(stationObject[stationID].indexOf('46') >= 0){
        paramID = stationObject[stationID];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:['46','8']};
        RealTime.request.afterComplete(parameters, $this, true);
        stationObject[stationID] = stationObject[stationID].filter(function(value, index, arr){
          return (value !=='46' && value !== '8');
        });
      }else if(stationObject[stationID].indexOf('16') >= 0){ //For secondary and discharge
        paramID = stationObject[stationID];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:['16','8']};
        RealTime.request.afterComplete(parameters, $this, true);
        stationObject[stationID] = stationObject[stationID].filter(function(value, index, arr){
          return (value !=='16' && value !== '8');
        });
      }else if(stationObject[stationID].indexOf('52') >= 0){ //For tertiary and discharge
        paramID = stationObject[stationID];
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:['52','8']};
        RealTime.request.afterComplete(parameters, $this, true);
        stationObject[stationID] = stationObject[stationID].filter(function(value, index, arr){
          return (value !=='52' && value !== '8');
        });
      }else{ // Single graph for paramater which was not chosen to be combined.
        paramID = $this.find('[data-parameterid]').attr('data-parameterid');
        parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:[paramID]};
        RealTime.request.afterComplete(parameters, $this, false);
      }
    }else{
      paramID = $this.find('[data-parameterid]').attr('data-parameterid');
      parameters = {start_date:start_date, end_date:end_date, station_id:stationID, parameter_id:[paramID]};
      RealTime.request.afterComplete(parameters, $this, false);
    }
  }

  loadingOverlay.remove();
});

})(jQuery, window, wb);
