#!/usr/bin/env python3
"""
Human Detection and Emotion Recognition for Pepper Robot
Author: Siddharth Patni
Date: November 2025
"""

import cv2
import numpy as np
import argparse
import sys
import json
import time
from datetime import datetime
from deepface import DeepFace

class HumanDetector:
    def __init__(self, method='mobilenet', confidence=0.5, camera='0', display=True, detect_emotion=False, emotion_interval=1):
        self.method = method
        self.confidence = confidence
        self.display = display
        self.enable_emotion_detection = detect_emotion  # Renamed to avoid method name conflict
        self.emotion_interval = emotion_interval  # Detect emotion every N detections
        self.emotion_frame_counter = 0  # Counter for emotion detection interval
        self.detector = None
        self.emotion_detector = None
        
        # Initialize camera
        try:
            camera_id = int(camera) if camera.isdigit() else camera
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                self.output_error(f"Failed to open camera: {camera}")
                sys.exit(1)
        except Exception as e:
            self.output_error(f"Camera initialization error: {str(e)}")
            sys.exit(1)
        
        # Initialize detector based on method
        self.init_detector()
        
        # Initialize emotion detector if enabled
        if self.enable_emotion_detection:
            self.init_emotion_detector()
        
    def output_json(self, data):
        """Output JSON to stdout for Node-RED"""
        print(json.dumps(data), flush=True)
    
    def output_error(self, message):
        """Output error in JSON format"""
        self.output_json({'error': message})
    
    def init_detector(self):
        """Initialize the selected detection method"""
        try:
            if self.method == 'hog':
                self.detector = cv2.HOGDescriptor()
                self.detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                
            elif self.method == 'mobilenet':
                # MobileNet SSD paths
                prototxt = 'models/MobileNetSSD_deploy.prototxt'
                model = 'models/MobileNetSSD_deploy.caffemodel'
                
                try:
                    self.detector = cv2.dnn.readNetFromCaffe(prototxt, model)
                except:
                    self.output_error(f"MobileNet model not found. Please run: cd models && bash download_models.sh")
                    sys.exit(1)
                    
            elif self.method == 'yolo':
                # YOLO paths
                config = 'models/yolov3.cfg'
                weights = 'models/yolov3.weights'
                
                try:
                    self.detector = cv2.dnn.readNetFromDarknet(config, weights)
                    # Load COCO class names
                    with open('models/coco.names', 'r') as f:
                        self.classes = f.read().strip().split('\n')
                except:
                    self.output_error(f"YOLO model not found. Please run: cd models && bash download_models.sh")
                    sys.exit(1)
            
            self.output_json({'status': 'ready', 'method': self.method})
            
        except Exception as e:
            self.output_error(f"Detector initialization failed: {str(e)}")
            sys.exit(1)
    
    def init_emotion_detector(self):
        """Initialize emotion recognition"""
        try:
            # Verify DeepFace is installed and working
            from deepface import DeepFace
            
            # Create a small test image to verify DeepFace can analyze
            test_img = np.zeros((48, 48, 3), dtype=np.uint8)
            DeepFace.analyze(
                test_img, 
                actions=['emotion'], 
                enforce_detection=False, 
                silent=True
            )
            
            self.output_json({'status': 'emotion_detector_ready'})
        except ImportError:
            self.output_error("DeepFace library not installed. Install with: pip install deepface")
            self.enable_emotion_detection = False
        except Exception as e:
            self.output_error(f"Emotion detector failed: {str(e)}")
            # Don't exit, just disable emotion detection
            self.enable_emotion_detection = False
    
    def should_detect_emotion(self):
        """Check if emotion detection should run on this frame based on interval"""
        if not self.enable_emotion_detection:
            return False
        
        self.emotion_frame_counter += 1
        return self.emotion_frame_counter % self.emotion_interval == 0
    
    def detect_emotion(self, frame, bbox):
        """Analyze facial emotion in detected human"""
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        
        # Ensure bbox is within frame bounds
        frame_h, frame_w = frame.shape[:2]
        x = max(0, x)
        y = max(0, y)
        w = min(w, frame_w - x)
        h = min(h, frame_h - y)
        
        # Extract person region (not just face)
        person_region = frame[y:y+h, x:x+w]
        
        if person_region.size == 0:
            return None
        
        try:
            # Try with strict face detection first
            result = DeepFace.analyze(
                person_region, 
                actions=['emotion'],
                enforce_detection=True,  # Ensure face is detected
                detector_backend='opencv',  # Use OpenCV for face detection
                silent=True
            )
            
            if result and len(result) > 0:
                # Get emotions from first detected face
                emotion_data = result[0]['emotion']
                
                # Find dominant emotion
                dominant_emotion = result[0]['dominant_emotion']
                
                return {
                    'label': str(dominant_emotion),
                    'confidence': round(float(emotion_data[dominant_emotion]) / 100, 2),
                    'scores': {k: round(float(v) / 100, 2) for k, v in emotion_data.items()}
                }
        except ValueError as e:
            # Face not detected with strict mode, try without enforcement
            try:
                result = DeepFace.analyze(
                    person_region, 
                    actions=['emotion'],
                    enforce_detection=False,  # Don't require face detection
                    detector_backend='opencv',
                    silent=True
                )
                
                if result and len(result) > 0:
                    emotion_data = result[0]['emotion']
                    dominant_emotion = result[0]['dominant_emotion']
                    
                    return {
                        'label': str(dominant_emotion),
                        'confidence': round(float(emotion_data[dominant_emotion]) / 100, 2),
                        'scores': {k: round(float(v) / 100, 2) for k, v in emotion_data.items()},
                        'note': 'low_confidence_face'  # Indicate face detection was weak
                    }
            except Exception:
                # Still failed, face too small or unclear
                pass
        except Exception:
            # Other error, silently fail
            pass
        
        return None
    
    def detect_hog(self, frame):
        """Detect humans using HOG"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes, weights = self.detector.detectMultiScale(gray, winStride=(8, 8), padding=(4, 4), scale=1.05)
        
        humans = []
        for i, (x, y, w, h) in enumerate(boxes):
            # weights can be 1D array, extract confidence properly
            if len(weights) > i:
                conf = float(weights[i]) if weights[i].size == 1 else float(weights[i][0])
            else:
                conf = 1.0
                
            if conf >= self.confidence:
                human_data = {
                    'id': i,
                    'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'confidence': round(conf, 2)
                }
                
                # Add emotion if enabled
                if self.should_detect_emotion():
                    emotion = self.detect_emotion(frame, human_data['bbox'])
                    if emotion:
                        human_data['emotion'] = emotion
                
                humans.append(human_data)
                
                if self.display:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    label = f'Person {conf:.2f}'
                    if 'emotion' in human_data:
                        label += f" ({human_data['emotion']['label']})"
                    cv2.putText(frame, label, (x, y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return humans, frame
    
    def detect_mobilenet(self, frame):
        """Detect humans using MobileNet SSD"""
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        
        self.detector.setInput(blob)
        detections = self.detector.forward()
        
        humans = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            class_id = int(detections[0, 0, i, 1])
            
            # Class 15 is 'person' in MobileNet SSD
            if class_id == 15 and confidence >= self.confidence:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                human_data = {
                    'id': len(humans),
                    'bbox': {
                        'x': int(startX),
                        'y': int(startY),
                        'width': int(endX - startX),
                        'height': int(endY - startY)
                    },
                    'confidence': round(float(confidence), 2)
                }
                
                # Add emotion if enabled
                if self.should_detect_emotion():
                    emotion = self.detect_emotion(frame, human_data['bbox'])
                    if emotion:
                        human_data['emotion'] = emotion
                
                humans.append(human_data)
                
                if self.display:
                    cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                    label = f'Person {confidence:.2f}'
                    if 'emotion' in human_data:
                        label += f" ({human_data['emotion']['label']})"
                    cv2.putText(frame, label, (startX, startY - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return humans, frame
    
    def detect_yolo(self, frame):
        """Detect humans using YOLO"""
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        
        self.detector.setInput(blob)
        layer_names = self.detector.getLayerNames()
        output_layers = [layer_names[i - 1] for i in self.detector.getUnconnectedOutLayers()]
        detections = self.detector.forward(output_layers)
        
        boxes = []
        confidences = []
        
        for output in detections:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # Class 0 is 'person' in COCO
                if class_id == 0 and confidence >= self.confidence:
                    box = detection[0:4] * np.array([w, h, w, h])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
        
        # Apply non-maxima suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence, 0.4)
        
        humans = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                human_data = {
                    'id': len(humans),
                    'bbox': {'x': x, 'y': y, 'width': w, 'height': h},
                    'confidence': round(confidences[i], 2)
                }
                
                # Add emotion if enabled
                if self.should_detect_emotion():
                    emotion = self.detect_emotion(frame, human_data['bbox'])
                    if emotion:
                        human_data['emotion'] = emotion
                
                humans.append(human_data)
                
                if self.display:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    label = f'Person {confidences[i]:.2f}'
                    if 'emotion' in human_data:
                        label += f" ({human_data['emotion']['label']})"
                    cv2.putText(frame, label, (x, y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return humans, frame
    
    def run(self):
        """Main detection loop"""
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    self.output_error("Failed to read from camera")
                    break
                
                # Perform detection based on method
                if self.method == 'hog':
                    humans, frame = self.detect_hog(frame)
                elif self.method == 'mobilenet':
                    humans, frame = self.detect_mobilenet(frame)
                elif self.method == 'yolo':
                    humans, frame = self.detect_yolo(frame)
                
                # Output detection results
                if len(humans) > 0:
                    result = {
                        'status': 'detected',
                        'count': len(humans),
                        'humans': humans,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.output_json(result)
                    
                    # For Node-RED integration, we detect once and exit
                    break
                
                # Display frame if enabled
                if self.display:
                    cv2.imshow('Human Detection', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Small delay to reduce CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Release resources"""
        if self.cap:
            self.cap.release()
        if self.display:
            cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='Human Detection for Pepper Bot')
    parser.add_argument('--method', type=str, default='mobilenet',
                       choices=['hog', 'mobilenet', 'yolo'],
                       help='Detection method to use')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Confidence threshold (0.0-1.0)')
    parser.add_argument('--camera', type=str, default='0',
                       help='Camera source (0 for default webcam)')
    parser.add_argument('--no-display', action='store_true',
                       help='Disable visual feedback window')
    parser.add_argument('--emotion', action='store_true',
                       help='Enable emotion detection')
    parser.add_argument('--emotion-interval', type=int, default=1,
                       help='Detect emotion every N detections (default: 1, every detection)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (continuous detection)')
    
    args = parser.parse_args()
    
    detector = HumanDetector(
        method=args.method,
        confidence=args.confidence,
        camera=args.camera,
        display=not args.no_display,
        detect_emotion=args.emotion,
        emotion_interval=args.emotion_interval
    )
    
    detector.run()


if __name__ == '__main__':
    main()
