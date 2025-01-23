#include <experimental/filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>
#include <fcgio.h>
#include <stdio.h>
#include <cstdlib>
#include "utils/simple-cmd-line-helper.h"
#include "bmi_para.h"
#include "bmi_para_scal.h"
#include "bmi_doc_scal.h"
#include "corpus_processor.h"
#include "features.h"
#include "utils/feature_parser.h"
#include "utils/utils.h"
#include <nlohmann/json.hpp>
#include <list>
#include <filesystem>

using json = nlohmann::json;

namespace fs = std::experimental::filesystem;
using namespace std;

unordered_map<string, unique_ptr<BMI>> SESSIONS;
unique_ptr<Dataset> documents = nullptr;
unique_ptr<ParagraphDataset> paragraphs = nullptr;
unordered_map<uint32_t, string> id_tokens;

// Get the uri without following and preceding slashes
string parse_action_from_uri(string uri){
    int st = 0, end = int(uri.length())-1;

    while(st < uri.length() && uri[st] == '/') st++;
    while(end >= 0 && uri[end] == '/') end--;

    return uri.substr(st, end - st + 1);
}

vector<pair<string, string>> parse_json_body(string body){
    json j = json::parse(body);

    vector<pair<string, string>> key_vals;
    string key, val;


    for (auto& el : j.items()) {
        key = el.key();
        if (el.value().is_string()) {
            val = el.value().get<string>();  // Get the value as a string
        } else {
            val = el.value().dump();  // If it's not a string, serialize it to string
        }
        key_vals.push_back({key, val});
    }

    return key_vals;
}

list<string> parse_json_list(string body){
    json j = json::parse(body);

   	list<string> result;
    string val;


    for (auto& el : j) {
        val = el.get<string>();
   	    result.push_back(val);
    }

    return result;
}

vector<pair<string, int>> parse_json_body_str_int(string body){
    json j = json::parse(body);

    vector<pair<string, int>> key_vals;
    string key;
    int val;


    for (auto& el : j.items()) {
        key = el.key();
        val = stoi(el.value().dump());
        key_vals.push_back({key, val});
    }

    return key_vals;
}



// Use a proper library someday
// returns a vector of <key, value> in given url query string
vector<pair<string, string>> parse_query_string(string query_string){
    vector<pair<string, string>> key_vals;
    string key, val;
    bool valmode = false;
    for(char ch: query_string){
        if(ch == '&'){
            if(key.length() > 0)
                key_vals.push_back({key, val});
            key = val = "";
            valmode = false;
        }else if(ch == '=' && !valmode){
            valmode = true;
        }else{
            if(valmode)
                val.push_back(ch);
            else
                key.push_back(ch);
        }
    }
    if(key.length() > 0)
        key_vals.push_back({key, val});
    return key_vals;
}

// returns the content field of request
// Built upon http://chriswu.me/blog/writing-hello-world-in-fcgi-with-c-plus-plus/
string read_content(const FCGX_Request & request){
    fcgi_streambuf cin_fcgi_streambuf(request.in);
    istream request_stream(&cin_fcgi_streambuf);

    char * content_length_str = FCGX_GetParam("CONTENT_LENGTH", request.envp);
    unsigned long content_length = 0;

    if (content_length_str) {
        content_length = atoi(content_length_str);
    }

    char * content_buffer = new char[content_length];
    request_stream.read(content_buffer, content_length);
    content_length = request_stream.gcount();

    do request_stream.ignore(1024); while (request_stream.gcount() == 1024);
    string content(content_buffer, content_length);
    delete [] content_buffer;
    return content;
}

// Given info write to the request's response
void write_response(const FCGX_Request & request, int status, string content_type, string content){
    fcgi_streambuf cout_fcgi_streambuf(request.out);
    ostream response_stream(&cout_fcgi_streambuf);
    response_stream << "Status: " << to_string(status) << "\r\n"
                    << "Content-type: " << content_type << "\r\n"
                    << "\r\n"
                    << content << "\n";
    /* if(content.length() > 50) */
    /*     content = content.substr(0, 50) + "..."; */
    cerr<<"Wrote response: "<<content<<endl;
}


bool parse_seed_judgments(const string &str, vector<pair<string, int>> &seed_judgments){
    size_t cur_idx = 0;
    while(cur_idx < str.size()){
        string doc_judgment_pair;
        while(cur_idx < str.size() && str[cur_idx] != ','){
            doc_judgment_pair.push_back(str[cur_idx]);
            cur_idx++;
        }
        cur_idx++;
        if(doc_judgment_pair.find(':') == string::npos){
            return false;
        }
        try{
            auto sep = doc_judgment_pair.find(':');
            seed_judgments.push_back(
                    {doc_judgment_pair.substr(0, sep), stoi(doc_judgment_pair.substr(sep+1))}
            );
        } catch (const invalid_argument& ia){
            return false;
        }
    }
    return true;
}

void update_document_loader(vector<pair<string, string>> seed_documents, const FCGX_Request & request,
    const string& doc_features, const string& para_features, const string& id_term_map_path){

    // call corpus processor
    try {
        parse_documents(seed_documents, doc_features, para_features, id_term_map_path);
    } catch (const invalid_argument& ia) {
        write_response(request, 400, "application/json", "{\"error\": \"Invalid document parsing\"}");
        return;
    }    
    cerr<<"Loading document features on memory: "<<doc_features<<endl;
    {
        unique_ptr<FeatureParser> feature_parser = make_unique<BinFeatureParser>(doc_features);
        documents = Dataset::build(feature_parser.get());
        cerr<<"Read "<<documents->size()<<" docs"<<endl;
    }
    if(para_features.length() > 0){
        cerr<<"Loading paragraph features on memory: "<<para_features<<endl;
        {
            unique_ptr<FeatureParser> feature_parser = make_unique<BinFeatureParser>(para_features);
            paragraphs = ParagraphDataset::build(feature_parser.get(), *documents);
            cerr<<"Read "<<paragraphs->size()<<" paragraphs"<<endl;
        }
    }

     // Load tokens map
    if(id_term_map_path.length() > 0){
        cerr<<"Loading id-tokens map on memory"<<endl;
        {
            ifstream id_map_file;
            id_map_file.open(id_term_map_path);
            string line;
            while (getline(id_map_file, line)){
                istringstream iss(line);
                uint32_t token_id;
                string token;
                if (!(iss >> token_id >> token)) { break; } // error
                id_tokens[token_id] = token;
            }
            id_map_file.close();
            cerr<<"Read "<< id_tokens.size() << " id-tokens entries"<<endl;
        }
    }
    write_response(request, 200, "application/json", "{\"BMI Setup\": \"success\"}");
}

void index_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string docs_directory = "";
  	for(auto kv: params){
        cerr<< kv.first<<endl;
        if (kv.first == "docs_directory"){
            docs_directory = kv.second;
        }
    }

    if (docs_directory.length() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_directory\"}");
        return;
    }

    string doc_features = docs_directory + ".bin";
    string para_features = docs_directory + "_para.bin";
	string data_internal = "data_internal/" + docs_directory;
    fs::path doc_store_path = data_internal + "/docs";

    if (!fs::exists(data_internal) or !fs::exists(doc_store_path) or fs::is_empty(doc_store_path)){
        write_response(request, 400, "application/json", "{\"error\": \"Insufficient docs to index\"}");
        return;
    }

    vector<pair<string, string>> seed_documents;
    for(const auto & entry : fs::directory_iterator(doc_store_path)){
        std::ifstream t(entry.path().string());
        std::stringstream buffer;
        buffer << t.rdbuf();
        std::size_t found = entry.path().string().find_last_of("/\\");
        string doc_id =  entry.path().string().substr(found+1);
        seed_documents.emplace_back(make_pair(doc_id, buffer.str()));
    }
    fs::path path = data_internal;
    doc_features = path / doc_features;
    para_features = path / para_features;
    const string id_term_map_path = path / "id_token_map.txt";
    update_document_loader(seed_documents, request, doc_features, para_features, id_term_map_path);
}

// Handler for API setup endpoint (1 or more documents per request)
void add_docs_to_collection_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string document_id, document_content, docs_directory = "";
    vector<pair<string, string>> documents;
    for(auto kv: params){
        cerr<< kv.first<<endl;
        if (kv.first == "seed_documents") {
          try{
            documents = parse_json_body(kv.second);
            }
            catch (const invalid_argument& ia) {
                write_response(request, 400, "application/json", "{\"error\": \"Invalid seed_documents\"}");
                return;
            }
        } else if (kv.first == "docs_directory"){
            docs_directory = kv.second;
        }
    }
    if (documents.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid seed_documents\"}");
        return;
    }
    if (docs_directory.length() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_directory\"}");
        return;
    }

    try {
        string data_internal = "data_internal";
    	fs::create_directory(data_internal);

		data_internal = "data_internal/" + docs_directory;
		fs::create_directory(data_internal);


    	fs::path doc_store_path = data_internal + "/docs";
    	fs::create_directory(doc_store_path);

    	for(auto kv: documents){
			std::ofstream out(doc_store_path / kv.first);
    		out << kv.second;
    		out.close();
        }
        write_response(request, 200, "application/json", "{\"BMI Setup\": \"successfully saved documents\"}");
    	return;
	}
    catch (const invalid_argument& ia) {
        write_response(request, 400, "application/json", "{\"error\": \"unable to save documents\"}");
        return;
    }

}


// Handler for API endpoint /begin
void begin_session_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id, query, mode = "doc";
    vector<pair<string, int>> seed_judgments;
    int judgments_per_iteration = -1;
    bool async_mode = false;

    for(auto kv: params){
        cerr << kv.first << kv.second << endl;
        if(kv.first == "session_id"){
            session_id = kv.second;
        }else if(kv.first == "seed_query"){
            query = kv.second;
        }else if(kv.first == "mode"){
            mode = kv.second;
        }else if(kv.first == "seed_judgments"){
            try{
            	seed_judgments = parse_json_body_str_int(kv.second);
            } catch (const invalid_argument& ia) {
                write_response(request, 400, "application/json", "{\"error\": \"Invalid seed_judgments\"}");
                return;
            }
        }else if(kv.first == "judgments_per_iteration"){
            try {
                judgments_per_iteration = stoi(kv.second);
            } catch (const invalid_argument& ia) {
                write_response(request, 400, "application/json", "{\"error\": \"Invalid judgments_per_iteration\"}");
                return;
            }
        }else if(kv.first == "async_mode"){
            if(kv.second == "true" || kv.second == "True"){
                async_mode = true;
            }else if(kv.second == "false" || kv.second == "False"){
                async_mode = false;
            }
        }
    }

    if(SESSIONS.find(session_id) != SESSIONS.end()){
        write_response(request, 400, "application/json", "{\"error\": \"session already exists\"}");
        return;
    }

    if(session_id.size() == 0 || query.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Non empty session_id and query required\"}");
        return;
    }

    Seed seed_query = {{features::get_features(query, *documents.get()), 1}};
    if(mode == "doc"){
        cerr << "here" << endl;
        SESSIONS[session_id] = make_unique<BMI>(
                seed_query,
                documents.get(),
                CMD_LINE_INTS["--threads"],
                judgments_per_iteration,
                async_mode,
                200000);
    }else if(mode == "para"){
        SESSIONS[session_id] = make_unique<BMI_para>(
                seed_query,
                documents.get(),
                paragraphs.get(),
                CMD_LINE_INTS["--threads"],
                judgments_per_iteration,
                async_mode,
                200000);
    }else if(mode == "para_scal"){
        SESSIONS[session_id] = make_unique<BMI_para_scal>(
                seed_query,
                documents.get(),
                paragraphs.get(),
                CMD_LINE_INTS["--threads"],
                200000, 25, seed_judgments);
    }else if(mode == "doc_scal"){
        SESSIONS[session_id] = make_unique<BMI_doc_scal>(
                seed_query,
                documents.get(),
                CMD_LINE_INTS["--threads"],
                200000, 25, seed_judgments);
    }else {
        write_response(request, 400, "application/json", "{\"error\": \"Invalid mode\"}");
        return;
    }

    if(mode != "para_scal"){
        SESSIONS[session_id]->record_judgment_batch(seed_judgments);
        SESSIONS[session_id]->perform_training_iteration();
    }

    // need proper json parsing!!
    write_response(request, 200, "application/json", "{\"session-id\": \""+session_id+"\"}");
}

// get top terms
string stringify_top_terms(vector<pair<uint32_t, float>> top_terms) {
    string top_terms_json = "{";
    for(auto top_term: top_terms){
        if(top_terms_json.length() > 1)
            top_terms_json.push_back(',');
        top_terms_json += "\"" + id_tokens[top_term.first] + "\"" + ":" + to_string(top_term.second);
    }
    top_terms_json.push_back('}');
    return top_terms_json;
}


// Fetch doc-ids in JSON
// Also fetch top terms
string get_docs(string session_id, int max_count, int num_top_terms = 10){
    const unique_ptr<BMI> &bmi = SESSIONS[session_id];
    vector<pair<string, float>> doc_ids = bmi->get_doc_to_judge(max_count);
    string doc_json = "[";
    string top_terms_json = "{";
    for(auto doc_id: doc_ids){
        if(doc_json.length() > 1)
            doc_json.push_back(',');
        if(top_terms_json.length() > 1)
            top_terms_json.push_back(',');
        doc_json += "\"" + doc_id.first + ":" + to_string(doc_id.second) + "\"";
        vector<pair<uint32_t, float>> top_terms = bmi->get_top_terms(doc_id.first, num_top_terms);
        //cerr << stringify_top_terms(top_terms) << endl;
        top_terms_json += "\"" + doc_id.first + "\": " + stringify_top_terms(top_terms);
    }
    doc_json.push_back(']');
    top_terms_json.push_back('}');

    return "{\"session-id\": \"" + session_id + "\", \"docs\": " + doc_json + ",\"top-terms\": " + top_terms_json + "}";
}

string get_stratum_docs(string session_id, int stratum_number, int include_sampled){
    auto &bmi = SESSIONS[session_id];
    vector<pair<string, float>> doc_ids = bmi->get_stratum_docs(stratum_number);
    if (doc_ids.empty()) {
        return "{}";
    }
    string doc_json = "[";
    for (auto doc_id: doc_ids) {
        if (doc_json.length() > 1)
            doc_json.push_back(',');
        doc_json += "\"" + doc_id.first + ":" + to_string(doc_id.second) + "\"";
    }
    doc_json.push_back(']');

    string sampled_doc_json = "[]";
    if (include_sampled == 1) {
        auto stratum_info = bmi->get_stratum_info();
        if (stratum_info == nullptr){
            return "{}";
        }
        vector<pair<string, float>> sampled_doc_ids = bmi->get_doc_to_judge(stratum_info->sample_size);
        if (sampled_doc_ids.empty()) {
            return "{}";
        }
        sampled_doc_json = "[";
        for (auto doc_id: sampled_doc_ids) {
            if (sampled_doc_json.length() > 1)
                sampled_doc_json.push_back(',');
            sampled_doc_json += "\"" + doc_id.first + ":" + to_string(doc_id.second) + "\"";
        }
        sampled_doc_json.push_back(']');
    }

    return "{\"session-id\": \"" + session_id + "\", \"docs\": " + doc_json + ", \"sampled_docs\": " + sampled_doc_json + "}";
}

string get_stratum_info(string session_id){
    auto &bmi = SESSIONS[session_id];
    auto stratum_info = bmi->get_stratum_info();
    if (stratum_info == nullptr){
        return "{}";
    }
    string stratum_info_string = "{\"stratum_number\": " + to_string(stratum_info->stratum_number) + 
        ",\"sample_size\": " + to_string(stratum_info->sample_size) + 
        ",\"stratum_size\": " + to_string(stratum_info->stratum_size) +
        ",\"T\": " + to_string(stratum_info->T) +
        ",\"N\": " + to_string(stratum_info->N) +
        ",\"R\": " + to_string(stratum_info->R) +
        ",\"n\": " + to_string(stratum_info->n) + "}";
    return "{\"session-id\": \"" + session_id + "\", \"info\": " + stratum_info_string + "}";
}

// Handler for /delete_session
void delete_session_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    SESSIONS.erase(session_id);

    write_response(request, 200, "application/json", "{\"session-id\": \"" + session_id + "\"}");
}

// Handler for /get_docs
void get_docs_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id;
    int max_count = 2;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }else if(kv.first == "max_count"){
            max_count = stoi(kv.second);
        }
    }

    if(session_id.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Non empty session_id required\"}");
        return;
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    write_response(request, 200, "application/json", get_docs(session_id, max_count));
}

// Handler for /get_stratum_docs
void get_stratum_docs_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id;
    int stratum_number;
    int include_sampled;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }
        else if (kv.first == "stratum_number") {
            stratum_number = stoi(kv.second);
        }
        else if (kv.first == "include_sampled") {
            include_sampled = stoi(kv.second);
        }
    }

    if(session_id.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Non empty session_id required\"}");
        return;
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    write_response(request, 200, "application/json", get_stratum_docs(session_id, stratum_number, include_sampled));
}

// Handler for /get_stratum_info
void get_stratum_info_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }
    }

    if(session_id.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Non empty session_id required\"}");
        return;
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    write_response(request, 200, "application/json", get_stratum_info(session_id));
}

// Handler for /get_ranklist
void get_ranklist(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }
    }

    if(session_id.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Non empty session_id required\"}");
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    vector<pair<string, float>> ranklist = SESSIONS[session_id]->get_ranklist();
    string ranklist_str = "";
    for(int i=0; i < ranklist.size(); i++){
      ranklist_str += ranklist[i].first + " " + to_string(ranklist[i].second);
      if(i!=(ranklist.size()-1)){
        ranklist_str += ",";
      }
    }

    //text to json
    string json_ret = "{\"ranklist\": \"" + ranklist_str + "\"}";
    write_response(request, 200, "application/json", json_ret);
}

// Handler for /log
void log_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }
    }

    if(session_id.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Non empty session_id required\"}");
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    write_response(request, 200, "text/plain", SESSIONS[session_id]->get_log());
}

void status_working_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
  if (documents != nullptr){
    write_response(request, 200, "application/json", "{\"working\": true}");
    return;
  } else {
    write_response(request, 200, "application/json", "{\"working\": false}");
    return;
  }
}

// Handler for /docid_exists
void docid_exists_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id, doc_id;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }else if(kv.first == "doc_id"){
            doc_id = kv.second;
        }
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    const unique_ptr<BMI> &bmi = SESSIONS[session_id];

    if(bmi->get_dataset()->get_index(doc_id) == bmi->get_dataset()->NPOS){
        write_response(request, 200, "application/json", "{\"exists\": false}");
        return;
    }
    write_response(request, 200, "application/json", "{\"exists\": true}");
}

// Handler for /judge
void judge_view(const FCGX_Request & request, const vector<pair<string, string>> &params){
    string session_id, doc_id;
    int rel = -2;

    for(auto kv: params){
        if(kv.first == "session_id"){
            session_id = kv.second;
        }else if(kv.first == "doc_id"){
            doc_id = kv.second;
        }else if(kv.first == "rel"){
            rel = stoi(kv.second);
        }
    }

    if(session_id.size() == 0 || doc_id.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Non empty session_id and doc_id required\"}");
    }

    if(SESSIONS.find(session_id) == SESSIONS.end()){
        write_response(request, 404, "application/json", "{\"error\": \"session not found\"}");
        return;
    }

    const unique_ptr<BMI> &bmi = SESSIONS[session_id];
    if(bmi->get_dataset()->get_index(doc_id) == bmi->get_dataset()->NPOS){
        write_response(request, 404, "application/json", "{\"error\": \"doc_id not found\"}");
        return;
    }

    if(rel < -1 || rel > 1){
        write_response(request, 400, "application/json", "{\"error\": \"rel can either be -1, 0 or 1\"}");
        return;
    }

    bmi->record_judgment(doc_id, rel);
    write_response(request, 200, "application/json", get_docs(session_id, 20));
}


void delete_docs_view(const FCGX_Request & request, const vector<pair<string, string>> &params) {
    list<string> docs_to_delete;
    string docs_directory = "";
    bool delete_all = false;
    for(auto kv: params){
        if(kv.first == "docs_directory"){
            docs_directory = kv.second;
        }else if(kv.first == "docs_to_delete"){
          try{
            docs_to_delete = parse_json_list(kv.second);
          } catch (const invalid_argument& ia) {
            write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_to_delete\"}");
            return;
          }
        }else if(kv.first == "delete_all"){
            if(kv.second == "true" || kv.second == "True"){
                delete_all = true;
            }else if(kv.second == "false" || kv.second == "False"){
                delete_all = false;
            }
        }
    }
    try {
	if (docs_to_delete.empty() && !delete_all){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_to_delete.\"}");
        return;
    }
    if (docs_directory == ""){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_directory\"}");
        return;
    }
    string data_internal = "data_internal";
	if (!fs::exists(data_internal + "/" + docs_directory)){
	    write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_directory\"}");
        return;
    }
	if (delete_all) {
        fs::remove_all( data_internal + "/" + docs_directory);
        documents = nullptr;
		write_response(request, 200, "application/json", "{\"BMI Setup\": \"successfully deleted documents\"}");
		return;
    }
    if (docs_to_delete.size() == 0){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_to_delete\"}");
        return;
    }
    for(auto doc_id: docs_to_delete){
		string doc_path = data_internal + "/" + docs_directory + "/docs/" + doc_id;
        if (!fs::remove(doc_path)){
            write_response(request, 400, "application/json", "{\"error\": \"failed to delete one or more documents\"}");
            return;
        }
    }
    fs::remove(data_internal + "/" + docs_directory + "/" + docs_directory + ".bin");
    fs::remove(data_internal + "/" + docs_directory + "/" + docs_directory + "_para.bin");
    fs::remove(data_internal + "/" + docs_directory + "/id_token_map.txt");
    documents = nullptr;
	write_response(request, 200, "application/json", "{\"BMI Setup\": \"successfully deleted documents\"}");
    return;
    } catch (const invalid_argument& ia) {
		cerr << "Error:" << ia.what() << endl;
        write_response(request, 400, "application/json", "{\"error\": \"failed to delete one or more documents\"}");
        return;
    }
}


void get_available_collections_view(const FCGX_Request & request, const vector<pair<string, string>> &params) {
    string data_internal = "data_internal";
    vector<string> collections;
    for(const auto & entry : fs::directory_iterator(data_internal)){
        if (fs::is_directory(entry)){
            collections.push_back(entry.path().filename());
        }
    }
    json j = collections;
    string collections_json = j.dump();
    write_response(request, 200, "application/json", collections_json);
}

void get_total_docs_in_collection_view(const FCGX_Request & request, const vector<pair<string, string>> &params) {
    string docs_directory = "";
    for(auto kv: params){
        if (kv.first == "docs_directory"){
            docs_directory = kv.second;
        }
    }
    if (docs_directory == ""){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_directory\"}");
        return;
    }
    string data_internal = "data_internal";
    if (!fs::exists(data_internal + "/" + docs_directory)){
        write_response(request, 400, "application/json", "{\"error\": \"Invalid docs_directory\"}");
        return;
    }
    fs::path doc_store_path = data_internal + "/" + docs_directory + "/docs";
    int total_docs = 0;
    for(const auto & entry : fs::directory_iterator(doc_store_path)){
        total_docs++;
    }
    write_response(request, 200, "application/json", "{\"total_docs\": " + to_string(total_docs) + "}");
}


void log_request(const FCGX_Request & request, const vector<pair<string, string>> &params){
    cerr<<string(FCGX_GetParam("RELATIVE_URI", request.envp))<<endl;
    cerr<<FCGX_GetParam("REQUEST_METHOD", request.envp)<<endl;
    for(auto kv: params){
        cerr<<kv.first<<" "<<kv.second<<endl;
    }
    cerr<<endl;
}

void process_request(const FCGX_Request & request) {
    string action = parse_action_from_uri(FCGX_GetParam("RELATIVE_URI", request.envp));
    string method = FCGX_GetParam("REQUEST_METHOD", request.envp);

    vector<pair<string, string>> params;
    if(method == "GET")
        params = parse_query_string(FCGX_GetParam("QUERY_STRING", request.envp));
    else if(method == "POST" || method == "DELETE") {
      try {
        params = parse_json_body(read_content(request)); }
      catch (...) {
        write_response(request, 400, "application/json", "{\"error\": \"Invalid json\"}");
        return;
        }
     }
	list<string> valid_endpoints = [
       "add_docs", "index", "status_working", "get_available_collections",
       "get_total_docs_in_collection", "delete_docs", "begin", "get_docs", "get_stratum_docs",
       "get_stratum_info", "docid_exists", "judge", "get_ranklist", "delete_session", "log"
    ];
    if (find(valid_endpoints.begin(), valid_endpoints.end(), action) == valid_endpoints.end()){
        write_response(request, 404, "application/json", "{\"error\": \"Invalid endpoint\"}");
        return;
    }
    log_request(request, params);
    if (action == "add_docs"){
        if(method == "POST"){
            add_docs_to_collection_view(request, params);
        }
    }else if (action == "index"){
        if(method == "GET"){
            index_view(request, params);
        }
    }else if(action == "status_working"){
        if(method == "GET"){
            status_working_view(request, params);
        }
    }else if (action == "get_available_collections"){
        if(method == "GET"){
            get_available_collections_view(request, params);
        }
    }else if (action == "get_total_docs_in_collection"){
        if(method == "GET"){
            get_total_docs_in_collection_view(request, params);
        }
    }else if (action == "delete_docs") {
      	if (method == "POST"){
        	delete_docs_view(request, params);
      	}
    }else if (documents == nullptr){
        write_response(request, 400, "application/json", "{\"error\": \"Indexing required\"}");
        return;
    }else if(action == "begin"){
        if(method == "POST"){
            begin_session_view(request, params);
        }
    }else if(action == "get_docs"){
        if(method == "GET"){
            get_docs_view(request, params);
        }
    }else if(action == "get_stratum_docs"){
        if(method == "GET"){
            get_stratum_docs_view(request, params);
        }
    }else if(action == "get_stratum_info"){
        if(method == "GET"){
            get_stratum_info_view(request, params);
    }
    }else if(action == "docid_exists"){
        if(method == "POST"){
            docid_exists_view(request, params);
        }
    }else if(action == "judge"){
        if(method == "POST"){
            judge_view(request, params);
        }
    }else if(action == "get_ranklist"){
        if(method == "GET"){
            get_ranklist(request, params);
        }
    }else if(action == "delete_session"){
        if(method == "DELETE"){
            delete_session_view(request, params);
        }
    }else if(action == "log"){
        if(method == "GET"){
            log_view(request, params);
        }
    }
}

void fcgi_listener(){
    FCGX_Request request;
    FCGX_InitRequest(&request, 0, 0);

    while (FCGX_Accept_r(&request) == 0) {
        process_request(request);
    }
}

int main(int argc, char **argv){
    AddFlag("--doc-features", "Path of the file with list of document features", string(""));
    AddFlag("--para-features", "Path of the file with list of paragraph features", string(""));
    AddFlag("--df", "Path of the file with list of terms and their document frequencies", string(""));
    AddFlag("--threads", "Number of threads to use for scoring", int(8));
    AddFlag("--start-without-indexing", "Start without indexing a corpus", int(0));
    AddFlag("--help", "Show Help", bool(false));

    ParseFlags(argc, argv);

    if(CMD_LINE_BOOLS["--help"]){
        ShowHelp();
        return 0;
    }


    if(CMD_LINE_INTS["--start-without-indexing"] == 1){
        FCGX_Init();

    	std::cout<<"Starting FastCGI server\n";

        vector<thread> fastcgi_threads;
        for(int i = 0;i < 50; i++){
            fastcgi_threads.push_back(thread(fcgi_listener));
        }

        for(auto &t: fastcgi_threads){
            t.join();
        }

    	return 0;
    }

    if(CMD_LINE_STRINGS["--doc-features"].length() == 0){
        cerr<<"Required argument --doc-features missing"<<endl;
        return -1;
    }

    // Load docs
    TIMER_BEGIN(documents_loader);
    cerr<<"Loading document features on memory"<<endl;
    {
        unique_ptr<FeatureParser> feature_parser;
        if(CMD_LINE_STRINGS["--df"].size() > 0)
            feature_parser = make_unique<BinFeatureParser>(CMD_LINE_STRINGS["--doc-features"], CMD_LINE_STRINGS["--df"]);
        else
            feature_parser = make_unique<BinFeatureParser>(CMD_LINE_STRINGS["--doc-features"]);
        documents = Dataset::build(feature_parser.get());
        cerr<<"Read "<<documents->size()<<" docs"<<endl;
    }
    TIMER_END(documents_loader);

    // Load para
    string para_features_path = CMD_LINE_STRINGS["--para-features"];
    if(para_features_path.length() > 0){
        TIMER_BEGIN(paragraph_loader);
        cerr<<"Loading paragraph features on memory"<<endl;
        {
            unique_ptr<FeatureParser> feature_parser;
            if(CMD_LINE_STRINGS["--df"].size() > 0)
                feature_parser = make_unique<BinFeatureParser>(para_features_path, "");
            else
                feature_parser = make_unique<BinFeatureParser>(para_features_path);
            paragraphs = ParagraphDataset::build(feature_parser.get(), *documents);
            cerr<<"Read "<<paragraphs->size()<<" paragraphs"<<endl;
        }
        TIMER_END(paragraph_loader);
    }

    // Load tokens map
    string id_term_map_path = "/data/id_token_map.txt";
    if(id_term_map_path.length() > 0){
        cerr<<"Loading id-tokens map on memory"<<endl;
        {
            TIMER_BEGIN(tokens_loader);
            ifstream id_map_file;
            id_map_file.open(id_term_map_path);
            string line;
            while (getline(id_map_file, line)){
                istringstream iss(line);
                uint32_t token_id;
                string token;
                if (!(iss >> token_id >> token)) { break; } // error
                id_tokens[token_id] = token;
            }
            id_map_file.close();
            cerr<<"Read "<< id_tokens.size() << " id-tokens entries"<<endl;
            TIMER_END(tokens_loader);
        }
    }

    FCGX_Init();

    vector<thread> fastcgi_threads;
    for(int i = 0;i < 50; i++){
        fastcgi_threads.push_back(thread(fcgi_listener));
    }

    for(auto &t: fastcgi_threads){
        t.join();
    }

    return 0;
}
