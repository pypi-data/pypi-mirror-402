
WIN_HOST=192.168.10.101
export http_proxy="http://$WIN_HOST:7890"
export https_proxy="http://$WIN_HOST:7890"

sudo tee /etc/apt/apt.conf.d/99proxy >/dev/null <<EOF
Acquire::http::Proxy "$http_proxy";
Acquire::https::Proxy "$https_proxy";
EOF

sudo apt clean
sudo apt update
