const currentConditionsText = {
  ALL_TIME_HIGH: t('All-time high for this day (100th percentile - maximum)'),
  MUCH_ABOVE_NORMAL: t('Much above normal (> 90th percentile)'),
  ABOVE_NORMAL: t('Above normal (76th – 90th percentile)'),
  NORMAL: t('Normal (25th – 75th percentile)'),
  BELOW_NORMAL: t('Below normal (10th – 24th percentile)'),
  MUCH_BELOW_NORMAL: t('Much below normal (< 10th percentile)'),
  ALL_TIME_LOW: t('All-time low for this day (0th percentile - minimum)'),
  NOT_FLOWING: t('Not flowing'),
  LACK_OF_STATS: t('Not ranked due to lack of statistics'),
  NO_DISCHARGE_DATA: t('No discharge data available today')
};

let download = {
  columns: {
    headers: (dataType, loggedIn) => {
      let headers = "\uFEFF";
      headers += `"${t('Station ID')}",`;
      headers += `"${t('Station Name')}",`;
      headers += `"${t('Province/Territory')}",`;
      headers += `"${t('Basin')}",`;
      headers += `"${t('Latitude')}",`;
      headers += `"${t('Longitude')}",`;
      headers += `"${t('Operating Agency')}",`;

      if(dataType === 'real_time'){
        headers += `"${t('Parameters')}",`;
      }

      headers += `"${t('Operation Schedule')}",`;
      headers += `"${t('Start Month')}",`;
      headers += `"${t('End Month')}",`;

      if(dataType === 'real_time'){
        headers += `"${t('Data Available (Past 2 hours)')}",`;
        headers += `"${t('Most Recent Water Level')} (m)",`;
        headers += `"${t('Most Recent Water Level Datestamp')}",`;
        headers += `"${t('Most Recent Discharge')} (m3/s)",`;
        headers += `"${t('Most Recent Discharge Datestamp')}",`;
        headers += `"${t('Timezone')}",`;
        headers += `"${t('Current Conditions')}"`;
        headers += `${(loggedIn === true) ? `,"${t('Deliver Image')}"` : ''}`;
      }

      if(dataType === 'historical'){
        headers += `"${t('Status')}"`;
      }

      return headers;
    },
    def: {
      "station_id": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `"${value}"`;
      },
      "station_name": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `,"${value}"`;
      },
      "province": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `,"${value}"`;
      },
      "basin_id": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `,"${value}"`;
      },
      "latitude": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `,"${parseFloat(value).toFixed(5)}"`;
      },
      "longitude": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `,"${parseFloat(value).toFixed(5)}"`;
      },
      "operating_agency_en": (value, dataType, loggedIn) => {
        if(lang === 'en'){
          if(value === null){
            return ',';
          }

          return `,"${value}"`;
        }

        return '';
      },
      "operating_agency_fr": (value, dataType, loggedIn) => {
        if(lang === 'fr'){
          if(value === null){
            return ',';
          }

          return `,"${value}"`;
        }

        return '';
      },
      "parameters": (value, dataType, loggedIn) => {
        if(dataType === 'real_time'){
          if(value === null){
            return ',';
          }

          return `,"${value.substring(1, (value.length -1))}"`;
        }

        return '';
      },
      "operation_schedule": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        const text = {
          C: t('Continuous'),
          S: t('Seasonal'),
          M: t('Miscellaneous')
        };

        return `,"${text[value]}"`;
      },
      "operation_start_month": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `,"${value}"`;
      },
      "operation_end_month": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        return `,"${value}"`;
      },
      "data_available": (value, dataType, loggedIn) => {
        if(value === null){
          return ',';
        }

        if(dataType === 'real_time'){
          return `,"${(value === 'Y') ? t('Yes') : t('No')}"`;
        }else if(dataType === 'historical'){
          return `,"${(value === 'A') ? t('Active') : t('Discontinued')}"`;
        }
      },
      "recent_water_level": (value, dataType, loggedIn) => {
        if(dataType === 'real_time'){
          if(value === null){
            return ',';
          }

          return `,"${formatData(value, '46')}"`;
        }

        return '';
      },
      "recent_water_level_datestamp": (value, dataType, loggedIn) => {
        if(dataType === 'real_time'){
          if(value === null){
            return ',';
          }

          return `,"${value}"`;
        }

        return '';
      },
      "recent_flow": (value, dataType, loggedIn) => {
        if(dataType === 'real_time'){
          if(value === null){
            return ',';
          }

          return `,"${formatData(value, '47')}"`;
        }

        return '';
      },
      "recent_flow_datestamp": (value, dataType, loggedIn) => {
        if(dataType === 'real_time'){
          if(value === null){
            return ',';
          }

          return `,"${value}"`;
        }

        return '';
      },
      "timezone_abbr_en": (value, dataType, loggedIn) => {
        if(dataType === 'real_time' && lang === 'en'){
          if(value === null){
            return ',';
          }

          return `,"${value}"`;
        }

        return '';
      },
      "timezone_abbr_fr": (value, dataType, loggedIn) => {
        if(dataType === 'real_time' && lang === 'fr'){
          if(value === null){
            return ',';
          }

          return `,"${value}"`;
        }

        return '';
      },
      "current_conditions": (value, dataType, loggedIn) => {
        if(dataType === 'real_time'){
          if(value === null){
            return ',';
          }

          return `,"${currentConditionsText[value]}"`;
        }

        return '';
      },
      "deliverimage": (value, dataType, loggedIn) => {
        if(dataType === 'real_time' && loggedIn === true){
          if(value === null){
            return ',';
          }

          return `,"${(value === 't') ? t('Yes') : t('No')}"`;
        }

        return '';
      }
    }
  },
  create: (data, dataType, loggedIn) => {
    let file = download.columns.headers(dataType, loggedIn);

    $.each(data, function(key, value){
      file += "\n";

      $.each(download.columns.def, function(k, v){
        if(typeof value[k] !== 'undefined'){
          file += v(value[k], dataType, loggedIn);
        }
      });
    });

    return file;
  }
};
