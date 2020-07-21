# #!/bin/bash
GATEWAY=192.168.122

function getPkgMgr {
    dist=$(hostnamectl | grep 'Operating System' | awk '{print $3}')
    declare -A pkgMgrs=( [Ubuntu]="apt" [Fedora]="yum" [Debian]="apt" )
    echo ${pkgMgrs[$dist]}
}


function getIP {
    echo $(ifconfig | grep $GATEWAY | awk '{print $2}')
}

$(getPkgMgr) install dnsmasq\
    tmux net-tools

echo "listen-address=$getIP,127.0.0.1
conf-dir=/etc/dnsmasq.d,.rpmnew,.rpmsave,.rpmorig
addn-hosts=/etc/dnsmasq.hosts"\
>> /etc/dnsmasq.conf

