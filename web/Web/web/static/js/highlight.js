/* SEARCH BAR and highlighter */
$('#searchContentForm').submit(function (e) {
    e.preventDefault();
    $("#searchNext").click();
    return false;
});

var marked_matches_in_document_title = [];
var marked_matches_in_document_snippet = [];
var marked_matches_in_document_content = [];
var marked_matches_counter = {};

function update_highlighted_terms_view(){
    var elm = $("#highlighted_terms_list");
    elm.empty();

    // SORTED (TODO: fix problem: sorting matches slows down rendering)
    // sort marked matches by count
    // let matches_sorted = []
    // for (let key in marked_matches_counter) {
    //   matches_sorted.push([ key, marked_matches_counter[key] ])
    // }
    // matches_sorted.sort(function compare(kv1, kv2) {
    //   return kv2[1] - kv1[1];
    // })
    //
    // for (let i = 0; i < matches_sorted.length; i++) {
    //    let match = matches_sorted[i][0];
    //    let count = matches_sorted[i][1];
    //    var template = `<li class="list-group-item d-flex justify-content-between align-items-center p-0 border-0"><mark class="badge text-truncate">${match}</mark> <small class="px-2">${count}</small></li>`;
    //    elm.append(template);
    // }

    // UNSORTED
    for (var keyMatch in marked_matches_counter) {
       var count = marked_matches_counter[keyMatch];
       var template = `<li class="list-group-item d-flex justify-content-between align-items-center p-0 border-0"><mark class="badge text-truncate">${keyMatch}</mark> <small class="px-2">${count}</small></li>`;
       elm.append(template);
    }
}


function searchForKeyword() {
  let highlighted_keyword = Cookies.get('highlighted_keyword');
  if (highlighted_keyword) {
    $("#search_content").val(highlighted_keyword).trigger('input');
  }
}


$(function() {

  // the input field
  var $input = $("#search_content"),
    // clear button
    $clearBtn = $("button[data-search='clear']"),
    // prev button
    $prevBtn = $("button[data-search='prev']"),
    // next button
    $nextBtn = $("button[data-search='next']"),
    // the context where to search
    $content = $(".highlight-include"),
    // list of selectors to ignore during the search
    $exclude = [".highlight-exclude"],

    $className = "manual-highlight"

    // jQuery object to save <mark> elements
    $results = "",
    // the class that will be appended to the current
    // focused element
    currentClass = "current",
    // top offset for the jump (the search bar)
    offsetTop = 73,
    // the current index of the focused element
    currentIndex = 0;

  /**
   * Jumps to the element matching the currentIndex
   */
  function jumpTo() {
    if ($results.length) {
      $input.addClass("greenBorder").css("border-color","#449D44");
      var position,
        $current = $results.eq(currentIndex);
      $results.removeClass(currentClass);
      if ($current.length) {
        $current.addClass(currentClass);
        position = $current.offset().top - offsetTop;
        window.scrollTo(0, position);
      }else{
        if(!$input.val()){
          $input.removeAttr('style');
        }else if ($input.is(':focus')){
          $input.addClass("redBorder").css("border-color","#C9302C");
        }
      }
    }
  }

  /**
   * Update dicts of matches and matches counter in document title, snippet, and content
   */
  function updateMatchesDictionaries(){
    resetMatchesDict();
    let document_title_mark_instances = $("#docViewDocTitle").find("mark");
    let document_snippet_mark_instances = $("#docViewDocSnippet").find("mark");
    let document_content_mark_instances = $("#docViewDocBody").find("mark");

    function update_in_location(instances, marked_matches_list){
      /**
       * Updates dict of matches and matches counter in a specific location
       */
      for(let i = 0; i < instances.length; i++){
          let match_elm = instances[i];
          let match_text = match_elm.innerHTML;
          let data = {
              "match": match_text,
              "wholeWord": get_surroundings_of_match(match_elm)
          };
          // Append new match to matches list
          marked_matches_list.push(data);

          // Update counter
          if (!(match_text.toLowerCase() in marked_matches_counter)){marked_matches_counter[match_text.toLowerCase()]=0;}
          marked_matches_counter[match_text.toLowerCase()] += 1;
      }

    }

    update_in_location(document_title_mark_instances, marked_matches_in_document_title);
    update_in_location(document_snippet_mark_instances, marked_matches_in_document_snippet);
    update_in_location(document_content_mark_instances, marked_matches_in_document_content);
    console.log(marked_matches_counter);
    update_highlighted_terms_view();
  }

    /**
     * Gets the surrounding letters of a highlighted match.
     * E.g. "The company is ba<mark>se</mark>d in California"
     * retrun "based".
     */
    function get_surroundings_of_match(match){
        if(match.previousSibling != undefined && match.nextSibling != undefined){
            var prev = match.previousSibling.nodeValue;
            var next = match.nextSibling.nodeValue;
            if(prev == ""){
                prev = " ";
            }
            if(next == ""){
                next = " ";
            }
            var wholeMatch = [];
            var i;
            for(i = 0; i < prev.length; i++){
                var index = prev.length - i - 1;
                if(prev[index] != "" && prev[index] != " ") {
                    wholeMatch.push(prev[index]);
                } else {
                    break;
                }
            }
            wholeMatch.reverse();
            wholeMatch.push.apply(wholeMatch, match.innerHTML.split());
            for(i = 0; i < next.length; i++){
                if(next[i] != "" && next[i] != " "){
                    wholeMatch.push(next[i]);
                }else{
                    break;
                }
            }
            return wholeMatch.join("");
        }else {
            return null;
        }
    }

  function resetMatchesDict() {
    marked_matches_in_document_title = [];
    marked_matches_in_document_snippet = [];
    marked_matches_in_document_content = [];
    marked_matches_counter = {};
  }

  /** This function processes the entered keyword to support both
   * phrase search (using double quotes) and seperate word search (seperated by space)
   * It takes advantage of the synonyms functionality in mark.js package
   * Sample input:
   *        phrase search + seperate word search: '"vitamin d" coronavirus cure'
   * Output:
   *        {"processed_keywords": ['vitamin d', 'coronavirus', 'cure'],
   *         "separateWordSearch": false,
   *         "synonyms": {
   *                       "vitamin d coronavirus cure": "vitamin d | coronavirus | cure"
   *                      }
   *        }
   * By setting synonyms like this, when the original input is: "vitamin d" coronavirus cure,
   * vitamin d, coronavirus, and cure would also be highlighted seperatly since they are considered synonyms.
  */
  function processKeyword(keywords) {
    // default return values
    let separateWordSearch = true;
    let synonyms = {};

    if (keywords == null || keywords == undefined) {
      return {
        "processed_keywords": keywords,
        "separateWordSearch": separateWordSearch,
        "synonyms": synonyms
      }
    }

    // Split keywords by space but not those in quotes
    let keywordsList = keywords.match(/[^\s"]+|"[^"]+"/gi);

    if (keywordsList != null) {
      // Remove double quotes in the list
      keywordsList = keywordsList.map(e => e.replace(/"(.+)"/, "$1"));
      console.log(keywordsList)

      if (keywords.includes("\"")) {
        // The original keywords have at least one phrase 
        separateWordSearch = false;
        synonyms[keywordsList.join(' ')] = keywordsList.join('|');
      }
    } else {
      // RegExp match returns NULL.
      keywordsList = keywords
    }

    return {
      "processed_keywords": keywordsList,
      "separateWordSearch": separateWordSearch,
      "synonyms": synonyms
    }
  }

  /**
   * Searches for the entered keyword in the
   * specified context on input
   */
  $input.on("input", function() {
    var searchVal = this.value;
    // Store the keyword in Cookie
    Cookies.set('highlighted_keyword', searchVal);

    let processed_keywords = processKeyword(searchVal);

    $content.unmark({
      className: $className,
      done: function() {
        $content.mark(processed_keywords["processed_keywords"], {
          className: $className,
          separateWordSearch: processed_keywords["separateWordSearch"],
          synonyms: processed_keywords["synonyms"],
          exclude: $exclude,
          done: function() {
            updateMatchesDictionaries();
            $results = $content.find("mark");
            currentIndex = 0;
            jumpTo();
          }
        });
      }
    });
  });

   $content.on("updated", function() {
       var searchVal = $input.val();
       console.log(searchVal);
       if(searchVal !== undefined){
           $content.unmark({
              className: $className,
              done: function() {
                console.log("Marking", searchVal);
                $content.mark(searchVal, {
                  className: $className,
                  separateWordSearch: true,
                  exclude: $exclude,
                  done: function() {
                    updateMatchesDictionaries();
                    $results = $content.find("mark");
                    currentIndex = 0;
                    //jumpTo();
                  }
                });
              }
           });
       }

    });


  /**
   * Clears the search
   */
  $clearBtn.on("click", function() {
    updateMatchesDictionaries();
    $content.unmark({className: $className});
    $input.val("").focus();
  });

  /**
   * Next and previous search jump to
   */
  $nextBtn.add($prevBtn).on("click", function() {
    if ($results.length) {
      currentIndex += $(this).is($prevBtn) ? -1 : 1;
      if (currentIndex < 0) {
        currentIndex = $results.length - 1;
      }
      if (currentIndex > $results.length - 1) {
        currentIndex = 0;
      }
      jumpTo();
    }
  });
});
