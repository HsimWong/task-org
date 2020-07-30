echo "Provisioning..."
systemctl disable systemd-resolved
systemctl stop systemd-resolved 
apt install -y dnsmasq firewalld tmux net-tools\
    gcc python3-dev python3-pip psmisc
pip3 install psutil getmac
cp conf/dnsmasq.conf /etc/
cp conf/resolv.dnsmasq.conf /etc/
apt-get update
echo "Docker Installing"
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update

sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

apt-get install docker-ce docker-ce-cli containerd.io




echo "Enabling remote docker-engine api"
echo "# /etc/systemd/system/docker.service.d/override.conf
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2376
" > /etc/systemd/system/docker.service.d/override.conf
systemctl daemon-reload
systemctl stop firewalld



systemctl restart docker.service


