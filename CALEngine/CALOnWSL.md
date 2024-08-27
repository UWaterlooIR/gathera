Install WSL and run Ubuntu on Windows

```commandline
wsl --install
ubuntu
```

Install required CAL packages

```commandline
sudo apt-get update
sudo apt-get install -y libfcgi-dev spawn-fcgi g++ libarchive-dev make git
mkdir -p /src/
```


Make corpus_parser and create CAL index
```commandline
cd <path_to_cal_directory>
sudo make corpus_parser
./corpus_parser --in <path_to_archive.gz> --out <output_path.bin>
```

Make bmi_fcgi and run the server
```commandline
sudo make bmi_fcgi

sudo /usr/bin/spawn-fcgi -p 8002 -n -- ./bmi_fcgi --doc-features <path_to_bin_file> --token-map <path_to_id_token_map>  --threads 8
```

Open new terminal and run the following command to install nginx
```commandline
ubuntu

sudo apt-get install nginx

sudo nginx -c <path_to_nginx_config=/mnt/c/Users/username/gathera/CALEngine/nginx/nginx.conf>
```


CAL server: localhost:9000/CAL/
api information in api.py


