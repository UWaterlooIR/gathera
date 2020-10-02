# gathera


### Installation
#### Requirements
The system is dockerized into different docker images. Make sure your machine has these installed

* `docker`: Refer to this [installation guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04) if you would like to install it on Ubuntu 16.04
* `docker-compose`

#### Corpus and How to Install
Before you start installing, you need to make sure your corpus is ready and in the right format. This step is necessary to be able run the system. We will work with a toy corpus called `athome`.

```
# Clone the repo
git clone https://github.com/UWaterlooIR/gathera.git
cd gathera
# Checkout the sample dataset
git clone https://github.com/hical/sample-dataset.git
cd sample-dataset
python process.py athome4_sample.tgz
# Move files to the data directory which will be mounted to the docker containers
cp athome4_sample.tgz athome4_sample_para.tgz ../data/
cd ..
```

`process.py` is an example of how one might clean the corpus and generate excerpts.
 We will use the `athome4_sample.tgz` and the newly generated `athome4_sample_para.tgz` to generate document features.


```
# Build and access the shell from the cal container
docker-compose run cal bash
root@container-id:/# cd src && make corpus_parser
# Generate features
root@container-id:/# ./corpus_parser  --in /data/athome4_sample.tgz --out /data/athome4_sample.bin --para-in /data/athome4_sample_para.tgz --para-out /data/athome4_para_sample.bin
# Exit the shell with Ctrl+D
```

We will now copy the search index and generate the document and paragraph files which will be showed to the assessors

```
# Extract the tgz files
cd data
# Fetch the anserini index for this collection
wget https://git.uwaterloo.ca/m2abuals/indexes/-/raw/master/athome_sample_index.tar.gz
# Double check MD5 checksum is equal to 59830814de4f1a2363e4dc8242049756
md5 athome_sample_index.tar.gz
# untar index
tar xvzf athome_sample_index.tar.gz

tar xvzf athome4_sample.tgz
mv athome4_test docs
tar xvzf athome4_sample_para.tgz
mv athome4_test para
cd ..

# We are all set! Lets fire up the containers
DOC_BIN=/data/athome4_sample.bin PARA_BIN=/data/athome4_para_sample.bin docker-compose up -d
# Visit localhost:9000
```

If you get a `502 Bad Gateway` error, please wait few seconds while the containers finish processing.

Port `9001` and `9000` will be used by system. Make sure these ports are not being used by other applications in your machine. If you would like to change these ports, please read the configuration section below.

#### How to run
Once your docker images are up and running (you can verify by running docker-compose ps), 
open your browser to [http://localhost:9000/](http://localhost:9000/). 
You should be able to access system's web interface. 
If you are still unable to view the web interface, 
try replacing [http://localhost:9000/](http://localhost:9000/) with the ip address 
of your docker machine (you can get the ip by running docker-machine ip)
