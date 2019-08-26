#!/bin/sh
# 26 aug 2019

set_init(){
git clone https://github.com/pjreddie/darknet
cd darknet
make
cd -
}

set_run(){
local ALINK="http://tdcctv.data.one.gov.hk/DF3641.JPG"
local ADATA="source.jpg"
local AWEIGHT="yolov2-tiny-voc.weights"
local APATH=".."
local ACONFIG="yolov2-tiny-voc.cfg"
local ATHRESHOLD="0.25"
local ATEMP="atemp"
ATHRESHOLD="0.05"
rm ./${ADATA}
wget -O ./${ADATA} "${ALINK}"
#cat ./darknet/cfg/${ACONFIG} | sed -e 's/random=1/random=0/g' > ./${ACONFIG}
cat ./darknet/cfg/${ACONFIG} | sed -e 's/random=1/random=1/g' > ./${ACONFIG}
cd ./darknet
./darknet detector test ${APATH}/darknet/cfg/voc.data ${APATH}/yolov2-tiny-voc.cfg ${APATH}/${AWEIGHT} ${APATH}/${ADATA} -thresh ${ATHRESHOLD} > ${APATH}/${ATEMP}
cat ${APATH}/${ATEMP} | grep -E "^([^:]+): ([1-9])([0-9]+)%\$"
cp -pr ${APATH}/darknet/predictions.jpg ${APATH}/
cd -
}

set_pretrained(){
wget https://pjreddie.com/media/files/yolov2-tiny-voc.weights
}

#set_init ""
#set_pretrained ""
set_run ""
