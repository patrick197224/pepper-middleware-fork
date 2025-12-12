#!/bin/bash
# Download pre-trained models for human detection

echo "Downloading MobileNet SSD models..."

# MobileNet SSD
if [ ! -f "MobileNetSSD_deploy.prototxt" ]; then
    curl -L "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt" -o MobileNetSSD_deploy.prototxt
    echo "✓ Downloaded MobileNet prototxt"
fi

if [ ! -f "MobileNetSSD_deploy.caffemodel" ]; then
    curl -L "https://github.com/chuanqi305/MobileNet-SSD/raw/master/mobilenet_iter_73000.caffemodel" -o MobileNetSSD_deploy.caffemodel
    echo "✓ Downloaded MobileNet model"
fi

echo ""
echo "Downloading YOLO models (optional, may take a while)..."

# YOLO v3
if [ ! -f "yolov3.cfg" ]; then
    curl -L "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg" -o yolov3.cfg
    echo "✓ Downloaded YOLO config"
fi

if [ ! -f "yolov3.weights" ]; then
    curl -L "https://pjreddie.com/media/files/yolov3.weights" -o yolov3.weights
    echo "✓ Downloaded YOLO weights"
fi

if [ ! -f "coco.names" ]; then
    curl -L "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names" -o coco.names
    echo "✓ Downloaded COCO class names"
fi

echo ""
echo "✓ All models downloaded successfully!"
echo "You can now use the Human Detection node with MobileNet or YOLO methods."
