## Log Events Formats

* **SEARCH_ATTEMPT**

  Every attempt for search will trigger this log event. It contains:
  * User ID
  * Query text
  * Timestamp 
    
  Sample:
  ```
  [2020-12-15 15:54:30.000723] INFO [web.post:32] {"user": "111", "timestamp": "2020-12-15T20:54:30.420Z", "event": "SEARCH_ATTEMPT", "data": {"query": "covid"}, "message": "log"}
  ```

* **SERP_SELECT**

  Each SERP item selection will trigger this log event. It contains:
  * User ID
  * Selected DocId
  * Timestamp
    
  Sample:
  ```
  [2020-12-15 15:54:30.000723] INFO [web.post:32] {"user": "111", "timestamp": "2020-12-15T20:54:30.420Z", "event": "SERP_SELECT", "data": {"docId": "044631"}, "message": "log"}
  ```
  
* **JUDGMENT_START**

  After watching a document to be judged this log event is triggered. It contains:
  * User ID
  * DocId
  * Previous Judgement (`null` if not present)  
  * Timestamp 
    
  Sample:
  ```
  [2020-12-15 15:54:30.000723] INFO [web.post:32] {"user": "111", "timestamp": "2020-12-15T20:54:30.420Z", "event": "JUDGMENT_START", "data": {"docId": "044631", "rel": null}, "message": "log"}
  ```
  
* **JUDGMENT_END**

  After finishing the process of judging a document this log event is triggered. It contains:
  * User ID
  * DocId
  * New Judgement (unchanged if just opened the doc and closed)  
  * Timestamp 
    
  Sample:
  ```
  [2020-12-15 15:54:30.000723] INFO [web.post:32] {"user": "111", "timestamp": "2020-12-15T20:54:30.420Z", "event": "JUDGMENT_END", "data": {"docId": "044631", "rel": 1},, "message": "log"}
  ```
