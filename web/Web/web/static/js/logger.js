/* Copyright (c) Dec 2020 Kamyar Ghajar */

const postLogURL = '/logger/';
const LOG_EVENT = {
  SERP_SELECT: 'SERP_SELECT',
  SEARCH_ATTEMPT: 'SEARCH_ATTEMPT',
  JUDGMENT_START: 'JUDGMENT_START',
  JUDGMENT_END: 'JUDGMENT_END',
  OPEN_FULL_DOC: 'OPEN_FULL_DOC'
};

/**
 * Sends a log to the logger
 * @param event
 * @param data
 */
function sendLog(event, data) {
  $.ajax({
    url: postLogURL,
    method: 'POST',
    data: JSON.stringify({
      timestamp: new Date(),
      event: event,
      data: data
    }),
    success: function (response) {
      console.log('log saved with response: ' + JSON.stringify(response))
    },
    error: function (err) {
      console.error(err)
    }
  });
}
