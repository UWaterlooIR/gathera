#ifndef CORPUS_PROCESSOR_H
#define CORPUS_PROCESSOR_H

#include<string>
#include <vector>

using namespace std;


void parse_documents(const vector<pair<string, string>>& documents, const string &out_filename, const string &para_out_filename);

#endif // CORPUS_PROCESSOR_H
