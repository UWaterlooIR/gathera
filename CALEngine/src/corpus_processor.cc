#include "corpus_processor.h"
#include <iostream>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <bits/stdc++.h>
 
#include <archive.h>
#include <archive_entry.h>
#include "utils/feature_writer.h"
#include "utils/text_utils.h"
#include "utils/utils.h"
#include "dataset.h"
#include "features.h"
#include "utils/feature_parser.h"
#include "utils/simple-cmd-line-helper.h"

 
string get_tempfile(){
    char file_template [] = "/tmp/CAL_XXXXXX";
    mkstemp(file_template);
    return file_template;
}

inline void ltrim_(string &str) {
    str.erase(str.begin(), find_if(str.begin(), str.end(), [](unsigned char ch) {
        return !std::isspace(ch);
    }));
}

inline void rtrim_(string &str) {
    str.erase(find_if(str.rbegin(), str.rend(), [](unsigned char ch) {
        return !std::isspace(ch);
    }).base(), str.end());
}

inline void trim(string &str){
    str.erase( std::remove(str.begin(), str.end(), '\r'), str.end() );
    ltrim_(str);
    rtrim_(str);
}
/**
 *  Extract paragraphs from documents.
 */
inline vector<string> get_paragraphs(const string& document) {
    vector<string> paragraphs;
    // Split paragraphs by \n\n
    const char* delimiter = "\r\n\r\n";

    size_t start = 0;
    size_t end = 0;

    while ((end = document.find(delimiter, start)) != std::string::npos) {
        paragraphs.push_back(document.substr(start, end - start));
        start = end + 2; // Skip the double newline
    }

    vector<string> final_paragraphs;
    vector<string> cur_para;
    for (const auto& para : paragraphs) {
        string trimmed_para = para;
        trim(trimmed_para);
        if (trimmed_para.empty()) {
            continue;
        }

        if (accumulate(cur_para.begin(), cur_para.end(), string()).length() <= 100) {
            cur_para.push_back(trimmed_para);
        } else {
            final_paragraphs.push_back(accumulate(cur_para.begin(), cur_para.end(), string(delimiter)));
            cur_para = {trimmed_para};
        }
    }
    if (!cur_para.empty() && accumulate(cur_para.begin(), cur_para.end(), string()).length() < 100 && !final_paragraphs.empty()) {
        final_paragraphs.back() += delimiter + accumulate(cur_para.begin(), cur_para.end(), string(delimiter));
    } else if (!cur_para.empty()) {
        final_paragraphs.push_back(accumulate(cur_para.begin(), cur_para.end(), string(delimiter)));
    }
    return final_paragraphs;
}
 
inline unordered_map <string, string> process_documents(const vector<pair<string, string>> &documents){
    unordered_map<string, string> paragraphs;
    for (auto i=0; i<documents.size(); i++){
        vector<string> paragraphs_per_doc = get_paragraphs(documents[i].second);
        // Save each paragraph title with the format (doc_id).(para_id)
        for(auto j=0; j< paragraphs_per_doc.size(); j++){
            paragraphs[documents[i].first+"."+to_string(j)] = paragraphs_per_doc[j];
        }
    }
    return paragraphs;
}
 
void parse_documents(const vector<pair<string, string>>& documents, const string &out_filename, const string &para_out_filename, const string& id_term_map_path){
    string pass1_filename = get_tempfile();
    unordered_map<string, uint32_t> token_ids;
    vector<double> idf(1);
    vector<pair<string, uint32_t>> dictionary;
    size_t num_docs = 0;
    string doc_id;
 
    BMITokenizer tokenizer = BMITokenizer();
    // Pass 1: get corpus stat and compute term frequencies
    {
        unique_ptr<FeatureWriter> fw_1;
        fw_1 = make_unique<BinFeatureWriter>(pass1_filename, vector<pair<string, uint32_t>>());
 
        for (const pair<string, string> & document:documents){
            num_docs++;
            doc_id = document.first;
            vector<string> tokens = tokenizer.tokenize(document.second);
 
            vector<FeatureValuePair> features;
            for (pair<string, int> token: features::get_tf(tokens)) {
                if (token_ids.count(token.first) == 0) {
                    dictionary.push_back({token.first, 0});
                    token_ids[token.first] = dictionary.size();
                }
                dictionary[token_ids[token.first]-1].second += 1.0;
                features.push_back({token_ids[token.first], (float) token.second});
            }
 
            sort(features.begin(), features.end(),
                 [](const FeatureValuePair &a, const FeatureValuePair &b) -> bool { return a.id_ < b.id_; });
 
            fw_1->write(SfSparseVector(doc_id, features));
            cerr<<num_docs<<" documents processed\r";
        }
        fw_1->finish();
    }
    cerr<<endl<<"Computing idf"<<endl;
 
    vector<int> new_ids(dictionary.size());
    for(int i = 0; i < dictionary.size(); i++){
        new_ids[i] = i;
    }
    // Compute idf
    {
        int end = dictionary.size() - 1;
        for(int i = 0; i <= end; i++){
            if(dictionary[i].second < 2){
                while(end > i){
                    if(dictionary[end].second > 1){
                        swap(dictionary[i], dictionary[end]);
                        new_ids[i] = end;
                        new_ids[end] = i;
                        break;
                    }
                    end--;
                }
            }
            idf.push_back(dictionary[i].second < 2?-1:log(num_docs / (float)dictionary[i].second));
        }
        while(dictionary[end].second < 2)
            end--;
        dictionary = vector<pair<string, uint32_t>>(dictionary.begin(), dictionary.begin() + end + 1);
    }
    cerr<<"Beginning Pass 2"<<endl;
    // Pass 2
    unique_ptr<FeatureParser> fp_1;
    unique_ptr<FeatureWriter> fw_2;

    fp_1 = make_unique<BinFeatureParser>(pass1_filename);
    fw_2 = make_unique<BinFeatureWriter>(out_filename, dictionary);
    unique_ptr<SfSparseVector> spv;
    unordered_map<uint32_t, string> id_tokens;
 
    num_docs = 0;
    while((spv = fp_1->next()) != nullptr){
        vector<FeatureValuePair> features;
        double sum = 0;
        for(auto &f: spv->features_){
            if(f.id_ != 0){
                f.id_ = new_ids[f.id_-1] + 1;
                if(f.id_ - 1 < dictionary.size() && dictionary[f.id_-1].second > 1){
                    features.push_back({f.id_, (float) ((1 + log(f.value_)) * idf[f.id_])});
                    id_tokens[f.id_] = dictionary[f.id_-1].first;
                    sum += features.back().value_ * features.back().value_;
                }
            }
        }
        sum = sqrt(sum);
        for(auto &f: features){
            f.value_ /= sum;
        }
 
        sort(features.begin(), features.end(),
             [](const FeatureValuePair &a, const FeatureValuePair &b) -> bool { return a.id_ < b.id_; });
        fw_2->write(SfSparseVector(spv->doc_id, features));
        num_docs++;
        cerr<<num_docs<<" documents processed\r"<<endl;
    }
    cerr<<endl;
    fw_2->finish();

    // Write the token ID to actual token map
    ofstream id_map_file;
    id_map_file.open(id_term_map_path);
    cerr << "Writing " << id_tokens.size() << " tokens" << endl;
    for (auto it : id_tokens) {
        id_map_file << it.first << " " << it.second << endl;
    }
    id_map_file.close();
 
    cerr<<"Generating Paragraph features"<<endl;
    unordered_map<string, string> paragraphs = process_documents(documents);
 
    unique_ptr<FeatureWriter> para_fw;
 
    para_fw = make_unique<BinFeatureWriter>(para_out_filename, dictionary);
 
    for (auto it=paragraphs.begin(); it != paragraphs.end(); it++) {
        string para_name = it->first, paragraph = it->second;
        num_docs++;
        vector<string> tokens = tokenizer.tokenize(paragraph);
 
        vector<FeatureValuePair> features;
        double sum = 0;
        for (pair<string, int> token: features::get_tf(tokens)) {
            if (token_ids.count(token.first) == 0) {
                continue;
            }
            uint32_t id = new_ids[token_ids[token.first]-1] + 1;
            if(id - 1 < dictionary.size() && dictionary[id-1].second > 1){
                float wt = (float) (token.second * idf[id]);
                features.push_back({id, wt});
                sum += wt * wt;
            }
        }
        sum = max(20.0, sqrt(sum));
        for(auto &f: features){
            f.value_ /= sum;
        }
 
        sort(features.begin(), features.end(),
             [](const FeatureValuePair &a, const FeatureValuePair &b) -> bool { return a.id_ < b.id_; });
 
        para_fw->write(SfSparseVector(para_name, features));
        cerr<<num_docs<<" paragraphs processed\r";

    }
    para_fw->finish();
}