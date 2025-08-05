import ultralytics
import cv2
import os

model_path = os.path.join(os.path.dirname(__file__), 'yolov12s-face.pt')
yoloface = ultralytics.YOLO(model_path)

def draw_box(frame):
    predict = yoloface(frame, device = 'cuda')
    for box in predict[0].boxes:
        cv2.rectangle(frame, (int(box.xyxy[0][0]), int(box.xyxy[0][1])), (int(box.xyxy[0][2]), int(box.xyxy[0][3])), (0, 255, 0), 2)
    return frame