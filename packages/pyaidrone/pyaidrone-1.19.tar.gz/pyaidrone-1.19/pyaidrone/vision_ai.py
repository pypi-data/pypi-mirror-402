import os
import cv2
import numpy as np
import time
from typing import Optional, Union, List, Tuple
from collections import namedtuple

# --- [파트 1: 기존 유틸리티 및 edu.py 필수 참조 함수] ---

class FPSMeter:
    def __init__(self):
        self.p_time = 0
    def get_fps(self):
        c_time = time.time()
        fps = 1 / (c_time - self.p_time) if (c_time - self.p_time) > 0 else 0
        self.p_time = c_time
        return int(fps)

def draw_box(img, box, label="", color=(0, 255, 0), thickness=2):
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    if label:
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

def draw_box_xywh(img, box_xywh, label="", color=(0, 255, 0)):
    x, y, w, h = box_xywh
    draw_box(img, (x, y, x + w, y + h), label, color)

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2]
    if isinstance(new_shape, int): new_shape = (new_shape, new_shape)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2; dh /= 2
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img, r, (left, top)

# edu.py에서 색상 인식을 위해 사용하는 필수 함수들 추가
def largest_contour(contours):
    if not contours: return None
    return max(contours, key=cv2.contourArea)

def contour_centroid(contour):
    M = cv2.moments(contour)
    if M["m00"] == 0: return None
    return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

# --- [파트 2: YOLOv8 대응 yolo_decode (edu.py 데이터 형식 지원)] ---

def yolo_decode(outputs, img_shape, input_shape, r, pad, threshold=0.4):
    """YOLOv8용 디코드 함수. 결과값을 edu.py가 기대하는 객체 형태로 반환"""
    output = np.squeeze(outputs[0]).transpose() # (8400, 84)
    
    # edu.py에서 res.box, res.score 등으로 접근하기 위한 구조
    Detection = namedtuple('Detection', ['class_id', 'score', 'box'])
    results = []
    
    for i in range(len(output)):
        scores = output[i][4:]
        max_score = np.max(scores)
        if max_score > threshold:
            cx, cy, w, h = output[i][:4]
            # 원본 좌표 복원 로직
            x1 = (cx - w / 2 - pad[0]) / r
            y1 = (cy - h / 2 - pad[1]) / r
            x2 = (cx + w / 2 - pad[0]) / r
            y2 = (cy + h / 2 - pad[1]) / r
            results.append(Detection(int(np.argmax(scores)), float(max_score), [x1, y1, x2, y2]))
            
    return results

# --- [파트 3: TFLiteDetector 클래스 (Windows & Linux 호환)] ---

class TFLiteDetector:
    def __init__(self, model_path: str):
        # 윈도우 환경(TensorFlow)과 라즈베리파이(tflite-runtime) 자동 선택
        try:
            import tensorflow.lite as tflite
        except ImportError:
            try:
                import tflite_runtime.interpreter as tflite
            except ImportError:
                print("❌ TFLite를 실행할 라이브러리가 없습니다.")
                return
            
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
    def infer(self, frame, decode_func, threshold=0.4):
        """edu.py에서 사용하는 명칭인 'infer'로 유지"""
        ih, iw = self.input_details[0]['shape'][1:3]
        img, r, pad = letterbox(frame, (ih, iw))
        
        input_data = np.expand_dims(img, axis=0).astype(np.float32)
        if self.input_details[0]['dtype'] == np.float32:
            input_data /= 255.0
            
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        outputs = [self.interpreter.get_tensor(out['index']) for out in self.output_details]
        return decode_func(outputs, (frame.shape[1], frame.shape[0]), (iw, ih), r, pad, threshold)

# --- [파트 4: VisionTracker - JPEG 에러 해결 버전] ---

class VisionTracker:
    def __init__(self):
        self.tracker = None
        self.is_tracking = False

    def set_target(self, frame, x, y):
        """클릭한 지점 주변(80x80)을 추적 대상으로 설정 - 예외 처리 강화"""
        try:
            # 🔧 1. 프레임 유효성 체크
            if frame is None or frame.size == 0:
                print("❌ 유효하지 않은 프레임")
                return False
            
            h, w = frame.shape[:2]
            
            # 🔧 2. ROI 계산
            x_roi = int(x - 40)
            y_roi = int(y - 40)
            w_roi = 80
            h_roi = 80
            
            # 🔧 3. 경계 체크 및 보정
            x_roi = max(0, min(x_roi, w - w_roi))
            y_roi = max(0, min(y_roi, h - h_roi))
            
            # 🔧 4. ROI가 프레임 안에 완전히 들어가는지 확인
            if x_roi + w_roi > w or y_roi + h_roi > h:
                print("⚠️ ROI가 프레임 밖으로 벗어남")
                return False
            
            roi = (x_roi, y_roi, w_roi, h_roi)
            
            # 🔧 5. 추적기 생성 및 초기화
            self.tracker = cv2.TrackerCSRT_create()
            success = self.tracker.init(frame, roi)
            
            if success:
                self.is_tracking = True
                print(f"✅ 추적 시작: ROI={roi}")
                return True
            else:
                print("❌ 추적기 초기화 실패")
                return False
                
        except Exception as e:
            print(f"❌ set_target 에러: {e}")
            self.is_tracking = False
            return False

    def get_error(self, frame):
        """현재 추적 중인 물체의 오차와 좌표 반환 - 예외 처리 강화"""
        if not self.is_tracking or self.tracker is None:
            return None
        
        try:
            # 🔧 1. 프레임 유효성 체크
            if frame is None or frame.size == 0:
                return None
            
            # 🔧 2. 추적 업데이트
            success, box = self.tracker.update(frame)
            
            if success:
                x, y, w, h = [int(v) for v in box]
                
                # 🔧 3. 박스가 유효한지 확인
                if w <= 0 or h <= 0:
                    print("⚠️ 유효하지 않은 박스 크기")
                    self.is_tracking = False
                    return None
                
                # 🔧 4. 오차 계산
                error_x = (x + w // 2) - 320  # 화면 중심(320)과의 오차
                error_y = 240 - (y + h // 2)  # 화면 중심(240)과의 오차
                return error_x, error_y, (x, y, w, h)
            else:
                print("⚠️ 추적 업데이트 실패")
                self.is_tracking = False
                return None
                
        except Exception as e:
            print(f"❌ get_error 에러: {e}")
            self.is_tracking = False
            return None
