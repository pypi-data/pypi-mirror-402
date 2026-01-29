import cv2
import time
import numpy as np
from pyaidrone.aiDrone import AIDrone
from pyaidrone.vision_ai import TFLiteDetector, yolo_decode, draw_box_xywh, largest_contour, contour_centroid
from pyaidrone.deflib import *

class EduAIDrone:
    """
    AI 교육을 위해 복잡한 기능을 단순화한 통합 API 클래스
    """
    def __init__(self, port="COM3", model_path=None, labels_path=None):
        # 드론 객체 및 기본 설정
        self.aidrone = AIDrone()
        self.port = port
        self.detector = TFLiteDetector(model_path) if model_path else None
        self.labels = []
        if labels_path:
            with open(labels_path, 'r', encoding='utf-8') as f:
                self.labels = [line.strip() for line in f.readlines()]
        
        self.cap = None
        self.last_frame = None
        self.height = 100 # 기본 유지 고도

    # --- 연결 및 영상 관리 ---
    def connect(self):
        """드론 연결 및 초기 세팅"""
        if self.aidrone.Open(self.port):
            self.aidrone.setOption(0)
            print(f"✅ 연결 성공: {self.port}")
            return True
        return False

    def start_stream(self, url="http://192.168.4.1/?action=stream"):
        """영상 스트리밍 시작"""
        self.cap = cv2.VideoCapture(url)
        return self.cap.isOpened()

    def update_screen(self, window_name="AI Drone Edu"):
        """화면을 갱신하고 현재 프레임을 반환 (AI 처리의 핵심)"""
        ret, frame = self.cap.read()
        if not ret: return None
        self.last_frame = cv2.resize(frame, (640, 480))
        return self.last_frame

    # --- 단순 제어 명령어 ---
    def takeoff(self):
        print("🚀 이륙합니다..."); self.aidrone.takeoff(); time.sleep(2)

    def land(self):
        print("🛬 착륙합니다..."); self.aidrone.landing()

    def move(self, direction, speed=100):
        """방향: 'front', 'back', 'left', 'right'"""
        dir_map = {'front': FRONT, 'back': BACK, 'right': RIGHT, 'left': LEFT}
        if direction in dir_map:
            self.aidrone.velocity(dir_map[direction], speed)

    def set_height(self, cm):
        """고도 설정 (50~150cm 추천)"""
        self.height = max(50, min(150, cm))
        self.aidrone.altitude(self.height)

    def turn(self, angle):
        """회전: 양수(우회전), 음수(좌회전)"""
        self.aidrone.rotation(angle)

    def stop(self):
        """모든 이동 정지 (호버링)"""
        self.aidrone.velocity(FRONT, 0)
        self.aidrone.velocity(RIGHT, 0)

    # --- AI 인지 기능 ---
    def find_color(self, color="red"):
        """색상을 찾아 화면에 표시하고 좌표 반환"""
        if self.last_frame is None: return None
        hsv = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2HSV)
        
        # 교육용 프리셋
        ranges = {
            "red": [(0, 150, 50), (10, 255, 255)],
            "blue": [(100, 150, 50), (140, 255, 255)],
            "green": [(40, 100, 50), (80, 255, 255)]
        }
        low, high = ranges.get(color, ranges["red"])
        mask = cv2.inRange(hsv, np.array(low), np.array(high))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        big_c = largest_contour(contours)
        
        if big_c is not None:
            cv2.drawContours(self.last_frame, [big_c], -1, (0, 255, 0), 2)
            return contour_centroid(big_c)
        return None

    def find_object(self, target_name, threshold=0.5):
        """YOLO 모델로 사물 찾기 (통합된 vision_ai 로직 활용)"""
        if not self.detector or self.last_frame is None: return None
        
        # 1. vision_ai에 내장된 정식 yolo_decode를 사용하여 추론
        results = self.detector.infer(self.last_frame, yolo_decode) 
        
        # 2. 결과 분석
        for res in results:
            # 라벨 리스트가 있다면 이름으로 비교, 없으면 ID로 비교
            name = self.labels[res.class_id] if self.labels else f"ID:{res.class_id}"
            
            if name == target_name and res.score > threshold:
                # 3. 화면에 인식 결과 그리기 (xyxy -> xywh 변환 후 그리기)
                x1, y1, x2, y2 = res.box
                w, h = x2 - x1, y2 - y1
                draw_box_xywh(self.last_frame, (x1, y1, w, h), label=f"{name} {int(res.score*100)}%")
                
                # 4. 물체의 중심 좌표 반환 (학생들이 제어에 사용하기 위함)
                return ((x1 + x2) / 2, (y1 + y2) / 2)
        
        return None

    def read_qr(self):
        """QR 코드 텍스트 읽기"""
        if self.last_frame is None: return None
        data, _, _ = cv2.QRCodeDetector().detectAndDecode(self.last_frame)
        return data if data else None
    
    # 오차값을 바탕으로 드론이 알아서 회전하고 고도를 조절    
    def follow_target(self, error_x, error_y):  
        """오차값을 보고 드론을 자동으로 회전 및 고도 조절"""
        # 1. 좌우 회전 (Yaw) 제어
        yaw = int(error_x * 0.15)
        self.aidrone.rotation(yaw)

        # 2. 상하 고도 (Throttle) 제어
        throttle_change = int(error_y * 0.2)
        self.height = max(50, min(150, self.height + throttle_change))
        self.aidrone.altitude(self.height)
    
    # 조건이 맞으면 사진을 저장.
    def save_image(self, frame, folder="captured_images"):
        """사진을 저장하고 기존 폴더가 없으면 생성"""
        import os
        if not os.path.exists(folder): os.makedirs(folder)
        
        timestamp = time.strftime("%H%M%S")
        filename = f"{folder}/target_{timestamp}.jpg"
        cv2.imwrite(filename, frame)