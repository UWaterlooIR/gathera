/* docView.js, (c) 2016 - 2020 Mustafa Abualsaud - http://www.mustafa-s.com */

var docView = function() {

  var self = this;
  this.version = '0.1.0';

  this.options = {
    csrfmiddlewaretoken: null, // required
    judgingSourceName: "CAL",

    username: null,

    // urls
    getPrevDocumentsJudgedURL: null, // required if showing prev reviewed docs
    getDocumentsToJudgeURL: null, // required if caching enabled
    getDocumentIDsToJudgeURL: null, // required
    sendDocumentJudgmentURL: null, // required
    getDocumentURL: null, // required
    getSCALInfoURL: null, // required for discovery page

    // options
    hideFullDocument: false,
    hideSnippet: false,
    allowShowFullDocumentButton: false,
    allowJudgingKeyboardShortcuts: false, // if true, requires importing Mousetrap lib
    allowDocumentCaching: true, // if true, requires LRU cache library (https://github.com/tusharf5/runtime-memcache)
    cacheStoreMax: 50,
    showTopTerms: true,
    fetchPreviouslyJudgedDocsOnInit: false,
    singleDocumentMode: false,
    searchMode: false,
    reviewMode: false,
    embedTweet: false, // only for tweet data. Needs twitter's widget.js to be loaded (https://platform.twitter.com/widgets.js).
    mainJudgingCriteriaName: "Relevant", // adjective of criteria

    // Specific to search
    queryID: null,
    query: null,

    // Selectors
    docViewSelector: "#docView",
    documentTabSelector: "#docViewTab",
    documentIDSelector: "#docViewDocID",
    documentIndicatorSelector: "#docViewDocIndicator",
    documentTitleSelector: "#docViewDocTitle",
    documentMetaSelector: "#docViewDocMeta",
    documentMessageSelector: "#docViewDocMessage",
    documentWrapperSelector: "#docViewDocWrapper",
    documentSnippetSelector: "#docViewDocSnippet",
    documentShowFullDocumentButtonSelector: "#docViewDocShowFullDocumentButton",
    documentBodySelector: "#docViewDocBody",
    documentCloseButtonSelector: "#docViewDocCloseButton",
    documentJudgingCriteriaButtonGroupSelector: ".judging-criteria-btn-group",
    documentHRelButtonSelector: ".docViewDocHRelButton",
    documentRelButtonSelector: ".docViewDocRelButton",
    docViewNextDocButtonSelector: ".docViewNextDocButton",
    docViewPreviousDocButtonSelector: ".docViewPreviousDocButton",
    documentNonRelButtonSelector: ".docViewDocNonRelButton",
    documentAdditionalJudgingCriterionSelector: ".additionalJudgingCriterion",
    previouslyReviewedListSelector: ".previouslyReviewedList",
    previouslyReviewedListSpinnerSelector: ".previouslyReviewedListSpinner",
    searchItemSelector: ".searchItemSelector",
    documentModalSelector: "#documentModal",
    sortReviewedDocumentsSelector: ".docViewSortReviewListByRelButton",

    // Colors
    highlyRelevantColor: "#84c273",
    relevantColor: "#c6fab8",
    nonrelevantColor: "#a5a5a5",
    otherColor: "#DEE2E6",
    primaryColor: "#000",
    secondaryColor: "#5C7080",
    projectPrimaryColor: "#F7533D",
    dangerColor: "#DB3737",

    // CSS
    primaryTitleFont: "document-title-font-family",
    secondaryTitleFont: "docView-default-font-family",

    // others
    prevReviewedDocumentItemClass: "prev-reviewed-doc-item",

    // event callbacks
    beforeDocumentLoad: null,
    afterDocumentLoad: null,
    afterDocumentClose: null,
    afterDocumentJudge: null,
    afterErrorShown: null,
    afterCALFailedToReceiveJudgment: null
  };

  /*************
   * VARIABLES *
   *************/
  this.currentDocID = null;
  this.currentDocIndex = -1;
  this.viewStack = [];
  this.previouslyJudgedDocs = {};
  this.previouslyJudgedDocsStack = [];
  this.documentCacheStore = null;
  this.additionalJudgingCriteriaList = [];


  this._init = function() {
    console.log("Initiating document view.");
    // create cache store
    if (this.options.allowDocumentCaching){
      // uses RMStore from https://github.com/tusharf5/runtime-memcache.
      this.documentCacheStore = RMStore({"cacheStoreMax": this.options.cacheStoreMax});
    }

    return true;
  };
};

docView.prototype = {
  /**
	 * Validate and merge user settings with default settings
	 *
	 * @param  {object} settings User settings
	 * @return {bool} False if settings contains error
	 */
	/* jshint maxstatements:false */
	init: function(settings) {
    "use strict";

    var parent = this;

    var options = parent.options = mergeRecursive(parent.options, settings);

    // Fatal errors
    // Stop script execution on error
    validateSelector(options.docViewSelector, false, "docViewSelector");
    validateSelector(options.documentIDSelector, false, "documentIDSelector");
    validateSelector(options.documentIndicatorSelector, true, "documentIndicatorSelector");
    validateSelector(options.documentTitleSelector, false, "documentTitleSelector");
    validateSelector(options.documentMetaSelector, true, "documentMetaSelector");
    validateSelector(options.documentMessageSelector, false, "documentMessageSelector");
    validateSelector(options.documentWrapperSelector, false, "documentWrapperSelector");
    validateSelector(options.previouslyReviewedListSelector, true, "previouslyReviewedListSelector");
    validateSelector(options.previouslyReviewedListSpinnerSelector, true, "previouslyReviewedListSpinnerSelector");
    validateSelector(options.documentSnippetSelector, true, "documentSnippetSelector");
    validateSelector(options.documentShowFullDocumentButtonSelector, true, "documentShowFullDocumentButtonSelector");
    validateSelector(options.documentJudgingCriteriaButtonGroupSelector, true, "documentJudgingCriteriaButtonGroupSelector");
    validateSelector(options.documentBodySelector, false, "documentIDSelector");
    validateSelector(options.documentCloseButtonSelector, true, "documentCloseButtonSelector");
    validateSelector(options.searchItemSelector, true, "searchItemSelector");
    validateSelector(options.documentModalSelector, true, "documentModalSelector");
    validateSelector(options.documentAdditionalJudgingCriterionSelector, true, "additionalJudgingCriterion");
    validateSelector(options.documentTabSelector, true, "documentTabSelector");

    // Don't touch these settings
    var s = [
      "beforeDocumentLoad",
      "afterDocumentLoad",
      "afterDocumentClose",
      "afterDocumentJudge",
      "afterErrorShown",
      "afterCALFailedToReceiveJudgment"
    ];

    for (var k in s) {
      if (settings.hasOwnProperty(s[k])) {
        options[s[k]] = settings[s[k]];
      }
    }

    function _linkJudgingButtons(elm, rel_val){
      if ($(elm).data('is-serp-judging')){
        $(elm).on("click", function(){sendSERPJudgment($(elm).data("doc-id"), rel_val)});
      }else{
        $(elm).on("click", function(){sendJudgment(rel_val, (options.searchMode || options.reviewMode)? null : refreshDocumentView)});
      }
    }

    function _linkNextDocButton(elm) {
      $(elm).on("click", function () { gotoNextDocument() });
    }

    function _linkPreviousDocButton(elm) {
      $(elm).on("click", function () { gotoPreviousDocument() });
    }

    function _linkSortByRelevanceButton(elm) {
      $(elm).on("click", function () { getDocumentsToJudge(refreshDocumentView); populatePrevReviewedDocuments() });
    }

    // start linking selectors and collect info on configurable additional judging criteria
    $(document).ready(function(){
      const mainJudgingSelectors = [options.documentHRelButtonSelector, options.documentRelButtonSelector, options.documentNonRelButtonSelector];
      mainJudgingSelectors.forEach(function (selector) {
          let rel_val = -1;
          switch (selector) {
            case options.documentHRelButtonSelector:
              rel_val = 2
              $(options.documentHRelButtonSelector).each(function() {_linkJudgingButtons(this, rel_val)});
              break
            case options.documentRelButtonSelector:
              rel_val = 1;
              $(options.documentRelButtonSelector).each(function() {_linkJudgingButtons(this, rel_val)});
              break
            case options.documentNonRelButtonSelector:
              rel_val = 0;
              $(options.documentNonRelButtonSelector).each(function() {_linkJudgingButtons(this, rel_val)});
              break
          }
        }
      );

      $('body').on("click", options.searchItemSelector, function(){showDocument($(this).data("doc-id").toString())});

      $(".additionalJudgingCriterion").each(function(){
        const criterion_name = $(this).data("criterion-name");
        parent.additionalJudgingCriteriaList.push(criterion_name);
        $(`input[type=radio][name=${criterion_name}_radio]`).change(function() {
            sendAdditionalJudgingCriteriaJudgments();
        });
      });

      $(options.documentCloseButtonSelector).on("click", function () { closePreviouslyReviewedDocument() });
      _linkNextDocButton($(options.docViewNextDocButtonSelector));
      _linkPreviousDocButton($(options.docViewPreviousDocButtonSelector));
      _linkSortByRelevanceButton($(options.sortReviewedDocumentsSelector));

      $(options.documentModalSelector).on('hidden.bs.modal', function () {
        parent.afterDocumentClose(parent.currentDocID)
      });
    });

    if (!options.singleDocumentMode && !options.searchMode){
      // start process of updating document view
      showLoading();
      getDocumentsToJudge(refreshDocumentView);
    }else{
      showNoDocumentIsSelected();
    }

    if (options.fetchPreviouslyJudgedDocsOnInit) {
      populatePrevReviewedDocuments();
    }



    /**
     * Validate that a queryString is valid
     *
     * @param  {Element|string|bool} selector   The queryString to test
     * @param  {bool}  canBeFalse  Whether false is an accepted and valid value
     * @param  {string} name    Name of the tested selector
     * @throws {Error}        If the selector is not valid
     * @return {bool}        True if the selector is a valid queryString
     */
    function validateSelector(selector, canBeFalse, name) {
      if (((canBeFalse && selector === false) || selector instanceof Element || typeof selector === "string") && selector !== "") {
        return true;
      }
      throw new Error("The " + name + " is not valid");
    }

    /*************
     * FUNCTIONS *
     *************/

    /**
     * Calls server to request document information and shows it once received.
     */
    function showDocument(docid) {
      parent.beforeDocumentLoad(docid);
      if (options.allowDocumentCaching){
        // check if it exists in cache
        if (parent.documentCacheStore.get(docid) !== null){
          _showDocumentCallback(docid, parent.documentCacheStore.get(docid));
          return;
        }
      }
      showLoading();
      fetchDocument(docid,  _showDocumentCallback);
    }

    function gotoNextDocument() {
      let currentDocIndex = parent.currentDocIndex;
      if (currentDocIndex < parent.viewStack.length - 1) {
        viewPreviouslyJudgedDocument(parent.viewStack[currentDocIndex + 1]);
      }
    }

    function gotoPreviousDocument() {
      let currentDocIndex = parent.currentDocIndex;
      if (currentDocIndex > 0) {
        viewPreviouslyJudgedDocument(parent.viewStack[currentDocIndex - 1]);
      }
    }

    /**
     * Views top of the view stack document. Or,if in review mode, view the doc at NextDocIndex
     */
    function refreshDocumentView(nextDocIndex=0) {
      // Show loading
      showLoading();
      if (parent.viewStack.length === 0){
        if (options.singleDocumentMode || options.searchMode){
          showNoDocumentIsSelected();
        }else{
          showNoMoreDocuments();
        }
        $(options.docViewSelector).trigger("updated");
        return;
      }

      parent.currentDocIndex = nextDocIndex
      let docid = parent.viewStack[nextDocIndex];
      if (!options.reviewMode) {
        parent.viewStack.shift(); // remove it from viewStack
      }
      // Show document
      showDocument(docid);
      $(options.docViewSelector).trigger("updated");
      if (options.getSCALInfoURL !== null){
          getSCALInfo()
      }

    }

    /**
     * Views a previously judged document
     * @param docid
     */
    function viewPreviouslyJudgedDocument(docid) {
      const currentDocid = parent.currentDocID;
      // If its the same document currently shown, don't do anything
      if (currentDocid === docid){
        return;
      }
      // If the current doc not already reviewed, add non-reviewed document back to stack
      if ( !options.reviewMode && currentDocid !== null && (!(currentDocid in parent.previouslyJudgedDocs) || parent.previouslyJudgedDocs[currentDocid]["relevance"]  === null) ) {
        parent.viewStack.unshift(currentDocid);
      }

      // Add the prev reviewed document to the beginning of the stack
      if (!options.reviewMode) {
        parent.viewStack.unshift(docid);
        refreshDocumentView();
      } else {
        refreshDocumentView(parent.viewStack.indexOf(docid));
      }
    }

    function closePreviouslyReviewedDocument() {
      // If the current doc is already reviewed, remove it and dont show it unless requested
      if (parent.currentDocID in parent.previouslyJudgedDocs && parent.previouslyJudgedDocs[parent.currentDocID]["relevance"]  !== null) {
        if (parent.viewStack.length !== 0 && parent.viewStack[0] === parent.currentDocID){
          parent.viewStack.shift();
        }
      }

      refreshDocumentView();
    }

    function checkIfDocumentPreviouslyJudged(docid) {
      let color = null;
      if (docid in parent.previouslyJudgedDocs){
        color = relToColor(parent.previouslyJudgedDocs[docid]["relevance"]);
        if (!(options.singleDocumentMode || options.searchMode || options.reviewMode)){
          showCloseButton();
        }
        updateActiveJudgingButton(docid, parent.previouslyJudgedDocs[docid]["relevance"]);
      } else{
        hideCloseButton();
        color = options.otherColor;
      }

      const prevJudgedDocObj = parent.previouslyJudgedDocs[docid];
      let prevJudgedDocRel = null;
      if (prevJudgedDocObj !== undefined){
        prevJudgedDocRel = prevJudgedDocObj["relevance"];
        updateAdditionalJudgingCriteriaValues(prevJudgedDocObj["additional_judging_criteria"]);
      }
      updateDocumentIndicator(relToTitle(prevJudgedDocRel), color);
    }

    function updateAdditionalJudgingCriteriaValues(criteria_value_map) {
      // update radio buttons for the additional judging criteria
      $.each(criteria_value_map, function (criteria , value) {
        $(`input[name="${criteria}_radio"][value="${value}"]`).prop("checked", "on");
      });
    }

    function closeDocumentModal() {
      $(options.documentModalSelector).modal('hide');
    }

    /****************
     * VIEW CHANGES *
     ***************/

    function clearDocumentView() {
      updateDocumentIndicator("",options.otherColor);
      showDocTab();
      clearAdditionalJudgingCriteria();
      updateDocID(null);
      updateTitle("");
      updateMessage("");
      updateMeta("");
      unhighlight();
      updateSnippet("");
      updateBody("");
      showWrapperContent();
    }

    function showDocTab() {
      const elm = $(options.documentTabSelector);
      elm.removeClass("d-none");
    }

    function hideDocTab() {
      const elm = $(options.documentTabSelector);
      elm.addClass("d-none");
    }

    function showLoading(){
      updateDocumentIndicator("",options.otherColor);
      updateTitle("Loading...", {"font": options.secondaryTitleFont, "color": options.projectPrimaryColor});
      //updateMessage("");
      updateDocID(null);
      updateMeta("");
      updateSnippet("Loading...", {"font": options.secondaryTitleFont, "color": options.secondaryColor});
      updateBody("Loading...", {"font": options.secondaryTitleFont, "color": options.secondaryColor});
      hideCloseButton();
      hideDocTab();
    }

    function showNoDocumentIsSelected() {
      updateDocumentIndicator("",options.otherColor);
      updateTitle("Please select a document to show", {"font": options.secondaryTitleFont, "color": options.projectPrimaryColor});
      updateMessage("No document has been selected. Please click on a document to view its content.");
      updateMeta("");
      updateDocID(null);
      hideCloseButton();
      hideDocTab();
    }

    function showNoMoreDocuments() {
      updateDocumentIndicator("",options.otherColor);
      updateTitle("Please wait..", {"font": options.secondaryTitleFont, "color": options.projectPrimaryColor});
      updateMessage("There are no more documents to judge. Please wait or try refreshing the page.");
      updateMeta("");
      updateDocID(null);
      hideCloseButton();
      hideDocTab();
    }

    function showMaxJudgmentReached() {
      updateDocumentIndicator("",options.otherColor);
      updateTitle("Max number of judgments reached", {"font": options.secondaryTitleFont, "color": options.projectPrimaryColor});
      updateMessage("You have reached the max number of judgments for this session. You will be redirected to the home page shortly.");
      updateMeta("");
      updateDocID(null);
      hideCloseButton();
      hideDocTab();

      window.setTimeout(function(){
        window.location.replace(window.location.origin);
      }, 2000);

    }


    function showError(err_msg){
      updateDocumentIndicator("",options.dangerColor);
      updateTitle("Error...", {"font": options.secondaryTitleFont, "color": options.dangerColor});
      updateMessage(err_msg, {"font": options.secondaryTitleFont, "color": options.dangerColor});
      updateMeta("");
      updateDocID(null);
      hideCloseButton();
      hideDocTab();
    }

    function updateTitle(content, styles) {
      const elm = $(options.documentTitleSelector);
      elm.html(content).removeClass();
      updateStyles(elm, styles);
    }

      function updateSCALInfo(result) {
        if (result) {
          let temp = [result['stratum_number'], result['stratum_size'], result['sample_size'], (parent.viewStack.length + 1).toString()]
          Array.from(document.getElementById('scal-info').getElementsByTagName('small')).forEach((span, i) => {
            span.innerHTML = temp[i]
          })
        }
      }

    function updateMeta(content) {
      if (isURL(content) === true){
        content = `<a href="${content}" target="_blank">${content}</a>`;
      }
      const elm = $(options.documentMetaSelector);
      elm.html(content);
    }

    function updateBody(content, styles) {
      const elm = $(options.documentBodySelector);
      elm.html(content).removeClass();
      updateStyles(elm, styles);
    }

    function updateSnippet(content, styles) {
      const elm = $(options.documentSnippetSelector);
      elm.html(content).removeClass();
      updateStyles(elm, styles);
    }

    function embedTweet(tweetid) {
      const parent = $(options.documentBodySelector);
      const elm = generate_embedded_tweet_elm();
      parent.append(elm);
      // needs twitter's widgets.js to be loaded
      try {
        twttr.widgets.createTweet(
          tweetid,
          elm.find("#embedded_tweet")[0],
          {}).then(function (el) {
            elm.find(".embeddedTweetSpinner").remove();
          }
        );
      } catch (e) {
        elm.find(".embeddedTweetSpinner").remove();
        elm.find("#embedded_tweet").html(e).addClass('text-danger');
        console.error(e);
      }
    }

    function updateActiveJudgingButton(docid, rel) {
      const btn_group = $(options.documentJudgingCriteriaButtonGroupSelector + `[data-doc-id='${docid}']`);
      btn_group.children().removeClass("active");
      if (rel === 2){
        btn_group.find(options.documentHRelButtonSelector).addClass("active");
      }else if (rel === 1){
        btn_group.find(options.documentRelButtonSelector).addClass("active");
      }else if (rel === 0){
        btn_group.find(options.documentNonRelButtonSelector).addClass("active");
      }
    }

    function updateDocumentIndicator(title, color) {
      if (color !== null){
        $(options.documentIndicatorSelector).css("border-color", color);
        $(options.documentIndicatorSelector).attr('title', title);
      }
    }

    function updateMessage(content, styles) {
      const elm = $(options.documentMessageSelector);
      elm.html(content).removeClass();
      hideWrapperContent();
      updateStyles(elm, styles);
    }

    function updateDocID(docid) {
      parent.currentDocID = docid;
      if (options.reviewMode) {
        parent.currentDocIndex = parent.viewStack.indexOf(docid);
      }

      const elm = $(options.documentIDSelector);
      if (docid){
        elm.html(docid);
        $(options.docViewSelector).data('doc-id', docid).attr("data-doc-id", docid);
      }else{
        elm.html("");
        $(options.docViewSelector).data('doc-id', '').attr("data-doc-id", '');
      }
      updateButtonGroupDocidAssociation(docid);
    }

    function updateButtonGroupDocidAssociation(docid) {
      const btn_group = $(options.documentJudgingCriteriaButtonGroupSelector + ":not('.SERP')");
      btn_group.attr("data-doc-id", docid);
      btn_group.children().removeClass("active");
    }

    function clearAdditionalJudgingCriteria() {
      $.each(parent.additionalJudgingCriteriaList, function(index, value){
        $(`input[name="${value}_radio"]`).prop('checked', false);
      });
    }

    function collectAdditionalJudgingCriteria() {
      let additional_judging_criteria_values = {};
      $.each(parent.additionalJudgingCriteriaList, function(index, value){
        const criteria_val = $(`input[name="${value}_radio"]:checked`).val();
        if (criteria_val !== undefined) {
          additional_judging_criteria_values[value] = criteria_val;
        }
      });
      return additional_judging_criteria_values;
    }

    function setAdditionalJudgingCriterionValue(criterion_name, value){
      $(`input[name="${criterion_name}_radio"][value="${value}"]`).prop("checked", "on");
    }

    function hideWrapperContent() {
      $(options.documentWrapperSelector).addClass("d-none");
    }

    function showWrapperContent() {
      $(options.documentWrapperSelector).removeClass("d-none");
    }

    function hideCloseButton(){
      $(options.documentCloseButtonSelector).addClass("d-none");
    }

    function showCloseButton() {
      $(options.documentCloseButtonSelector).removeClass("d-none");
    }

    function updateOrCreatePreviouslyReviewedListItem(docid, title, rel) {
      const div_elm = generate_prev_reviewed_doc_div_elm(docid, title, rel);
      // Check if docid is already in prev reviewed docs stack, if so, pop it
      const stack_index = parent.previouslyJudgedDocsStack.indexOf(docid);
      if (stack_index !== -1 && !options.reviewMode){
        parent.previouslyJudgedDocsStack.splice(stack_index, 1);
        // remove the div associated with the docid
        $("."+options.prevReviewedDocumentItemClass).each(function() {
          if ($(this).data("doc-id").toString() === docid){
            $(this).remove();
          }
        });
      }
      // link on click
      div_elm.on("click", function () {viewPreviouslyJudgedDocument($(this).data("doc-id").toString())});

      if (!options.reviewMode || stack_index === -1) {
        // add to top of the list view/stack
        $(options.previouslyReviewedListSelector).prepend(div_elm);
        parent.previouslyJudgedDocsStack.push(docid);
      } else {
        // update indicator
        const current = $("." + options.prevReviewedDocumentItemClass + `[data-doc-id='${docid}']`);
        current.children().eq(0).css('border-color', relToColor(rel));
      }
    }

    function highlightTerm(term, score) {
      const highlight_options = {
        element: "top-term",
        accuracy: "complementary",
        className: "top-term",
        each: function (elm) {
          $(elm).css('background', convertHex(options.projectPrimaryColor, score)); // TODO: have fixed color
          $(elm).data("markjs", "").attr("data-markjs", "");
        }
      }

      $(options.documentTitleSelector).mark(term, highlight_options);
      $(options.documentBodySelector).mark(term, highlight_options);
      $(options.documentSnippetSelector).mark(term, highlight_options);
    }

    function unhighlight() {
      $(options.documentTitleSelector).unmark();
      $(options.documentBodySelector).unmark();
      $(options.documentSnippetSelector).unmark();
    }


    /****************
     * SERVER CALLS *
     ***************/

    /**
     * Calls server to request documents to judge.
     */
    function getDocumentsToJudge(callback) {
      const url = options.allowDocumentCaching ? options.getDocumentsToJudgeURL : options.getDocumentIDsToJudgeURL;
      $.ajax({
          url: url,
          method: 'GET',
          success: function (result) {
            updateViewStack(result);
            if (typeof callback === "function") {
              callback();
            }
          },
          error: function (err_msg){
            showError(JSON.stringify(err_msg));
          }
      });
    }

      function getSCALInfo(callback) {
        const url = options.getSCALInfoURL;
        $.ajax({
          url: url,
          method: 'GET',
          success: function (result) {
            updateSCALInfo(result)
            if (typeof callback === "function") {
              callback();
            }
          },
          error: function (_) {
            updateSCALInfo({
              "stratum_number": "NA",
              "sample_size": "NA",
              "stratum_size": "NA",
            });
          }
        });
      }

    function populatePrevReviewedDocuments(callback) {
      const url = options.getPrevDocumentsJudgedURL;
      $.ajax({
          url: url,
          method: 'GET',
          success: function (result) {
            $(options.previouslyReviewedListSelector).empty();
            parent.previouslyJudgedDocsStack = [];
            parent.previouslyJudgedDocs = {};
            $(options.previouslyReviewedListSpinnerSelector).addClass("d-none");
            for (let i = 0; i < result.length; i++){
              let item = result[result.length - 1 - i];
              parent.previouslyJudgedDocs[item["doc_id"]] = {
                "relevance": item["relevance"],
                "additional_judging_criteria": item["additional_judging_criteria"]
              };
              updateOrCreatePreviouslyReviewedListItem(item["doc_id"], item["doc_title"], item["relevance"]);
            }
            if (typeof callback === "function") {
              callback();
            }
          },
          error: function (err_msg){
            $(options.previouslyReviewedListSpinnerSelector).addClass("d-none");
            $(options.previouslyReviewedListSelector).prepend(JSON.stringify(err_msg));
          }
      });
    }

    /**
     * Calls server to request document information.
     */
    function fetchDocument(docid, callback) {
      $.ajax({
            url: getDocumentURL(docid),
            type: 'GET',
            dataType: 'json', // added data type
            success: function(res) {
              // AFTER SUCCESSFUL RETRIEVAL OF DOCUMENT INFO
              callback(docid, res[0]);
        }
      });
    }

    function sendAdditionalJudgingCriteriaJudgments() {
      const docid = parent.currentDocID;
      if (docid === null){
        return;
      }
      const additional_judging_criteria = collectAdditionalJudgingCriteria();
      if ($.isEmptyObject(additional_judging_criteria)){
        return;
      }
      const currentTitle = getCurrentDocTitle();
      const currentSnippet = getCurrentDocSnippet();
      const now = + new Date();

      if (docid in parent.previouslyJudgedDocs){
        parent.previouslyJudgedDocs[docid]["additional_judging_criteria"] = additional_judging_criteria
      }else{
        parent.previouslyJudgedDocs[docid] = {
          "relevance": null,
          "additional_judging_criteria": additional_judging_criteria
        };
      }

      var data = {
          'doc_id': docid,
          'doc_title': currentTitle,
          'doc_CAL_snippet': currentSnippet,
          'doc_search_snippet': "",
          'relevance': null,
          'additional_judging_criteria': additional_judging_criteria,
          'source': options.judgingSourceName,
          'client_time': now,
          'search_query': null,
          'ctrl_f_terms_input': $("#search_content").val(),
          'csrfmiddlewaretoken': options.csrfmiddlewaretoken,
          'page_title': document.title,

          // history item
          'historyItem': {
            "username": options.username,
            "timestamp": now,
            "source": options.judgingSourceName,
            "judged": false,
            "relevance": null,
            'additional_judging_criteria': additional_judging_criteria,
          },
      };

      $.ajax({
          url: options.sendDocumentJudgmentURL,
          method: 'POST',
          data: JSON.stringify(data),
          success: function (result) {
              console.log(result);
          },
          error: function (result){
            if (parent.currentDocID === null){
              showError(result);
            }
            console.error("Something went wrong. ");
          },
          statusCode: {
              502: function (xhr) {
                if (parent.currentDocID === null){
                  showError(xhr.responseText);
                }
                console.log("Something went wrong. Timeout error." +
                      "Judgment may have not been recorded.", xhr.responseText);
              }
          }
      });

    }

    function sendSERPJudgment(docid, rel){
      if (docid in parent.previouslyJudgedDocs){
        parent.previouslyJudgedDocs[docid]["relevance"] = rel;
      }else{
        parent.previouslyJudgedDocs[docid] = {
          "relevance": rel,
        };
      }

      const docTitle = $(`#doc_${docid}_card`).data("title");
      const docSnippet = $(`#doc_${docid}_card`).data("snippet");

      const now = + new Date();
      var data = {
          'doc_id': docid,
          'doc_title': docTitle,
          'doc_CAL_snippet': "",
          'doc_search_snippet': docSnippet,
          'relevance': rel,
          'source': "search_SERP",
          'client_time': now,
          'search_query': null,
          'ctrl_f_terms_input': $("#search_content").val(),
          'csrfmiddlewaretoken': options.csrfmiddlewaretoken,
          'page_title': document.title,

          // history item
          'historyItem': {
            "username": options.username,
            "timestamp": now,
            "source": "search_SERP",
            "queryID": options.queryID,
            "query": options.query,
            "judged": true,
            "relevance": rel,
          },
      };

      $.ajax({
          url: options.sendDocumentJudgmentURL,
          method: 'POST',
          data: JSON.stringify(data),
          success: function (result) {
              updateActiveJudgingButton(docid, rel);

              if(result['is_max_judged_reached']){
                  showMaxJudgmentReached();
                  return;
              }

              if(result["CALFailedToReceiveJudgment"]){
                parent.afterCALFailedToReceiveJudgment(docid, rel);
              }

              parent.afterDocumentJudge(docid, rel);
          },
          error: function (result){
            console.error("Something went wrong. ", result);
          },
          statusCode: {
              502: function (xhr) {
                console.log("Something went wrong. Timeout error." +
                      "Judgment may have not been recorded.", xhr.responseText);
              }
          }
      });

    }

    function sendJudgment(rel, callback) {
      var current_docview_stack_size = parent.viewStack.length;
      if (!(options.singleDocumentMode || options.searchMode)){
        window.scrollTo(0, 0);
      }
      const docid = parent.currentDocID;
      if (docid === null){
        return;
      }

      const additional_judging_criteria = collectAdditionalJudgingCriteria();
      parent.previouslyJudgedDocs[docid] = {
        "relevance": rel,
        "additional_judging_criteria": additional_judging_criteria
      };
      const currentTitle = getCurrentDocTitle();
      const currentSnippet = getCurrentDocSnippet();
      updateOrCreatePreviouslyReviewedListItem(docid, currentTitle, rel);

      if (!options.singleDocumentMode && !options.searchMode && !options.reviewMode){
        clearDocumentView();
      } else {
        updateDocumentIndicator(relToTitle(rel), relToColor(rel));
      }
      // add document to previously judged map
      // load next in line document
      if (typeof callback === "function") {
        callback();
      }

      const now = + new Date();
      var data = {
          'doc_id': docid,
          'doc_title': currentTitle,
          'doc_CAL_snippet': currentSnippet,
          'doc_search_snippet': "",
          'relevance': rel,
          'additional_judging_criteria': additional_judging_criteria,
          'source': options.judgingSourceName,
          'client_time': now,
          'search_query': null,
          'ctrl_f_terms_input': $("#search_content").val(),
          'csrfmiddlewaretoken': options.csrfmiddlewaretoken,
          'page_title': document.title,
          'current_docview_stack_size': current_docview_stack_size,

          // history item
          'historyItem': {
            "username": options.username,
            "timestamp": now,
            "source": options.judgingSourceName,
            "judged": true,
            "relevance": rel,
            "queryID": options.queryID,
            "query": options.query,
            'additional_judging_criteria': additional_judging_criteria,
          },
      };

      if ($(`#doc_${docid}_card`).length){
        data["doc_search_snippet"] = $(`#doc_${docid}_card`).data("snippet");
      }

      $.ajax({
          url: options.sendDocumentJudgmentURL,
          method: 'POST',
          data: JSON.stringify(data),
          success: function (result) {
              if (!options.singleDocumentMode && !options.searchMode && !options.reviewMode) {
                updateViewStack(result["next_docs"]);
              }else{
                updateActiveJudgingButton(docid, rel);
              }
              if(result['is_max_judged_reached']){
                  showMaxJudgmentReached();
                  return;
              }

              if(result["CALFailedToReceiveJudgment"]){
                parent.afterCALFailedToReceiveJudgment(docid, rel);
              }

              if (parent.currentDocID === null){
                if (typeof callback === "function") {
                  callback();
                }
              }
              parent.afterDocumentJudge(docid, rel);
          },
          error: function (result){
            if (parent.currentDocID === null){
              showError(result);
            }
            console.error("Something went wrong. ");
          },
          statusCode: {
              502: function (xhr) {
                if (parent.currentDocID === null){
                  showError(xhr.responseText);
                }
                console.log("Something went wrong. Timeout error." +
                      "Judgment may have not been recorded.", xhr.responseText);
              }
          }
      });

    }

    /*************
     * CALLBACKS *
     *************/

    function _showDocumentCallback(docid, data) {
      /**
       * Callback to show document in document view once server returns document information.
       */
      clearDocumentView();

      updateDocID(docid);

      if (typeof data.title === "string"){
        updateTitle(data.title, {"font": options.primaryTitleFont, "color": options.primaryColor});
      }
      if (typeof data.content === "string"){
        updateBody(data.content, {"color": options.primaryColor});
        if (options.embedTweet){
          embedTweet(docid); // docid is the tweet id.
        }
      }
      if (typeof data.date === "string"){
        updateMeta(data.date);
      }
      if (typeof data.snippet === "string"){
        updateSnippet(data.snippet, {"color": options.primaryColor});
      }
      if (options.showTopTerms && isDict(data.top_terms)){
        for (let term in data.top_terms){
          const score = data.top_terms[term]
          if (term.endsWith("i")){ // this is because we have stemmed top terms
            term = term.slice(0, -1) + 'y';
          }
          highlightTerm(term, score);
        }
      }

      // unbold the previous document
      const previous = $("." + options.prevReviewedDocumentItemClass + `[data-is-current='true']`);
      previous.removeClass("bold");
      previous.attr("data-is-current", "false");

      //bold the current document
      const current = $("." + options.prevReviewedDocumentItemClass + `[data-doc-id='${docid}']`);
      current.addClass("bold");
      current.attr("data-is-current", "true");

      if (data.rel !== undefined && typeof data.rel === "number"){
        const color = relToColor(data.rel);
        checkIfDocumentPreviouslyJudged(docid);
        updateDocumentIndicator(relToTitle(data.rel), color);
        updateActiveJudgingButton(docid, data.rel);
        updateAdditionalJudgingCriteriaValues(data.additional_judging_criteria);
      }else{
        checkIfDocumentPreviouslyJudged(docid);
      }

      parent.afterDocumentLoad(docid);
    }


    /**************
     * EXCEPTIONS *
     **************/

    /**
     * Unknown search engine.
     * @param message
     * @constructor
     */
    // function UnknownSearchEngine(message) {
    //   this.name = 'UnknownSearchEngine';
    //   this.message = message || 'Could not determine search engine.';
    //   this.stack = (new Error()).stack;
    // }
    // UnknownSearchEngine.prototype = Object.create(Error.prototype);
    // UnknownSearchEngine.prototype.constructor = UnknownSearchEngine;


    /////////////////////////////////////////////////////

    /***********
     * HELPERS *
     ***********/

    /**
     * Updates the view stack from results returned by server
     */
    function updateViewStack(result) {
      let docids = [];
      for (let i = 0; i < result.length; i++){
        const doc = result[i];
        if (options.allowDocumentCaching){
          parent.documentCacheStore.set(doc.doc_id, doc);
        }
        // make sure stack doesn't include previously judged documents or current doc
        if (((!(doc.doc_id in parent.previouslyJudgedDocs) || (parent.previouslyJudgedDocs[doc.doc_id]["relevance"]  === null)) &&  doc.doc_id !== parent.currentDocID) || options.reviewMode){
          docids.push(doc.doc_id);
        }
      }
      parent.viewStack = docids;
    }

    function generate_prev_reviewed_doc_div_elm(docid, title, rel) {
      const rel_color = relToColor(rel);
      return $(`
        <a href="#" class="d-flex mb-1 text-muted ${options.prevReviewedDocumentItemClass}" style="min-height: 1rem;" data-doc-id="${docid}" data-is-current="false">
            <div class="align-self-center align-self-stretch p-1" style="border-width: 0.15rem!important; border-style: none none none solid; border-color: ${rel_color};"></div>
            <div class="align-self-center text-truncate">
                <div class="docView-default-font-family text-truncate">${title}</div>
            </div>
        </a>
      `);
    }

    function generate_embedded_tweet_elm() {
      return $(`
      <div class="card border-0">
        <div class="card-body py-4 px-0">
          <div class="d-flex w-50 justify-content-between font-sans text-primary mb-3 border-bottom highlight-exclude unselectable" unselectable="on">
            <small class="highlight-exclude">Embedded tweet</small>
          </div>
          <div class="mx-auto embeddedTweetSpinner mt-2 pl-4">
            <div class="la-ball-circus text-secondary"><div></div><div></div><div></div><div></div><div></div></div>
          </div>
          <div id="embedded_tweet"></div>
        </div>
      </div>
      `);
    }

    function getCurrentDocTitle() {
      if (parent.currentDocID !== null){
        return $(options.documentTitleSelector).text()
      }
      return null;
    }

    function getCurrentDocSnippet() {
      if (parent.currentDocID !== null){
        return $(options.documentSnippetSelector).text()
      }
      return null;
    }

    function updateStyles(selector, styles) {
      if (styles !== undefined){
        if (styles.font !== undefined){
          selector.addClass(styles.font);
        }
        if (styles.color !== undefined){
          selector.css("color", styles.color);
        }
      }

    }

    function getDocumentURL(docid) {
      return options.getDocumentURL + docid;
    }

    function isDict(v) {
      return typeof v==='object' && v!==null && !(v instanceof Array) && !(v instanceof Date);
    }

    function convertHex(hex, opacity){
      hex = hex.replace('#','');
      const r = parseInt(hex.substring(0,2), 16);
      const g = parseInt(hex.substring(2,4), 16);
      const b = parseInt(hex.substring(4,6), 16);
      return 'rgba('+r+','+g+','+b+','+opacity+')';
    }

    /**
     * Given a numerical value of the relevance, return the appropriate color.
     * */
    function relToColor(rel) {
      if (rel === 2) {
        return options.highlyRelevantColor;
      }else if (rel === 1) {
        return options.relevantColor;
      } else if (rel === 0) {
        return options.nonrelevantColor;
      }
      return options.otherColor;
    }

    /**
     * Given a numerical value of the the main judging criteria, return the appropriate title.
     * */
    function relToTitle(rel) {
      if (rel === 2) {
        return `Highly ${options.mainJudgingCriteriaName}`;
      }else if (rel === 1) {
        return `${options.mainJudgingCriteriaName}`;
      } else if (rel === 0) {
        return `Non${options.mainJudgingCriteriaName}`;
      }
      return "";
    }

    function isURL(str) {
      var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
      return !!pattern.test(str);
    }

    return this._init();
  },


  // =========================================================================//
  // EVENTS CALLBACK                                                          //
  // =========================================================================//

  /**
   * Helper method for triggering event callback
   *
   * @param  string  eventName       Name of the event to trigger
   * @param  array  successArgs     List of argument to pass to the callback
   * @param  boolean  skip      Whether to skip the event triggering
   * @return mixed  True when the triggering was skipped, false on error, else the callback function
   */
  triggerEvent: function(eventName, successArgs, skip) {
    "use strict";

    if ((arguments.length === 3 && skip) || this.options[eventName] === null) {
      return true;
    }

    if (typeof this.options[eventName] === "function") {
      if (typeof successArgs === "function") {
        successArgs = successArgs();
      }
      return this.options[eventName].apply(this, successArgs);
    } else {
      console.log("Provided callback for " + eventName + " is not a function.");
      return false;
    }
  },

  beforeDocumentLoad: function(docid) {
    "use strict";
    return this.triggerEvent("beforeDocumentLoad", [docid]);
  },

  afterDocumentLoad: function(docid) {
    "use strict";
    return this.triggerEvent("afterDocumentLoad", [
      docid,
      this.previouslyJudgedDocs[docid] ? this.previouslyJudgedDocs[docid]["relevance"] : null
    ]);
  },

  afterDocumentClose: function (docid) {
    "use strict";
    return this.triggerEvent("afterDocumentClose", [docid]);
  },

  afterDocumentJudge: function(docid, rel) {
    "use strict";
    return this.triggerEvent("afterDocumentJudge", [docid, rel]);
  },

  afterCALFailedToReceiveJudgment: function(docid, rel) {
    "use strict";
    return this.triggerEvent("afterCALFailedToReceiveJudgment", [docid, rel]);
  },


  afterErrorShown: function () {
    "use strict";
    return this.triggerEvent("afterErrorShown");
  }
};

/**
 * #source http://stackoverflow.com/a/383245/805649
 */
function mergeRecursive(obj1, obj2) {
  "use strict";

  /*jshint forin:false */
  for (var p in obj2) {
    try {
      // Property in destination object set; update its value.
      if (obj2[p].constructor === Object) {
        obj1[p] = mergeRecursive(obj1[p], obj2[p]);
      } else {
        obj1[p] = obj2[p];
      }
    } catch(e) {
      // Property in destination object not set; create it and set its value.
      obj1[p] = obj2[p];
    }
  }

  return obj1;
}

/**
 * Loader
 */
if (typeof define === "function" && define.amd) {
  define([], function() {
    "use strict";

    return docView;
  });
} else if (typeof module === "object" && module.exports) {
  module.exports = docView;
} else {
  window.docView = docView;
}
