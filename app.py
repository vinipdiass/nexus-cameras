from flask import Flask, render_template, Response, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from ultralytics import YOLO
from collections import Counter
import threading
import time

app = Flask(__name__)
CORS(app)

# Load the model
model = YOLO("yolov8n.pt")

# Class mapping (same as your original code)
class_mapping = {
    0: 'pessoa',
    1: 'bicicleta',
    # ... (include all class mappings here)
    79: 'escova de dentes'
}

# Colors for drawing rectangles
colors = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (128, 0, 0), (0, 128, 0), (0, 0, 128),
    (128, 128, 0), (128, 0, 128), (0, 128, 128)
]

# Global variables
latest_frame = None
processed_frame = None
latest_detections = ""
lock = threading.Lock()

def process_frames():
    global latest_frame, processed_frame, latest_detections
    while True:
        if latest_frame is not None:
            with lock:
                frame = latest_frame.copy()
            # Perform object detection
            results = model(frame)
            mapped_names = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls.item())
                        class_name = class_mapping.get(class_id, f'classe_{class_id}')
                        mapped_names.append(class_name)

                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confidence = box.conf.item()
                        label = f"{class_name} ({confidence:.2f})"

                        color = colors[class_id % len(colors)]
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            # Count occurrences
            counts = Counter(mapped_names)
            counts_str = ', '.join([f"{count} {name}" for name, count in counts.items()])

            # Update latest detections
            latest_detections = counts_str

            # Encode the frame
            ret, buffer = cv2.imencode('.jpg', frame)
            processed_frame = buffer.tobytes()
        else:
            time.sleep(0.01)  # Avoid busy waiting

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    global latest_frame
    # Get the frame data from the request
    frame_data = request.data
    # Convert string of image data to uint8
    nparr = np.frombuffer(frame_data, np.uint8)
    # Decode image
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    with lock:
        latest_frame = frame
    return '', 204

def gen_frames():
    global processed_frame
    while True:
        if processed_frame is not None:
            frame = processed_frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.01)  # Avoid busy waiting

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detections')
def detections():
    return jsonify({"detections": latest_detections})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Start the frame processing in a separate thread
    threading.Thread(target=process_frames, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
