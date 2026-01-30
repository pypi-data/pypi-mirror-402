#AIDrone sensor 라이브러리 (26.01.15)
import struct
from pyaidrone.deflib import DefLib

class AIDroneSensor:
    def __init__(self):
        # 센서 데이터 및 비행 상태 통합 저장소
        self.state = {
            'battery': 0,      # 배터리 잔량 (%) 
            'tof': 0,          # VL53L01X 고도 센서 값 (mm) 
            'flow_x': 0,       # PMW3901 광학 흐름 센서 X축 변화량 
            'flow_y': 0,       # PMW3901 광학 흐름 센서 Y축 변화량 
            'pos_x': 0,        # 이륙 지점 기준 X 좌표 (cm) 
            'pos_y': 0,        # 이륙 지점 기준 Y 좌표 (cm) 
            'height': 0,       # 드론이 계산한 현재 높이 (cm) 
            'roll': 0,         # 현재 좌우 기울기 
            'pitch': 0,        # 현재 앞뒤 기울기 
            'ready': False,    # 비행 준비 상태 
            'emergency': False # 응급 정지 상태 여부 
        }

    def parse(self, packet):
        """
        pyaidrone의 parse.py에서 수신된 패킷을 분석하여 상태를 업데이트합니다.
        """
        if packet is None or packet == "None":
            return None

        # 패킷 헤더 및 타입 확인 (0xA2: Output Packet) 
        if (packet[3] & 0xF0) == 0xA0:
            # 1. 기본 상태 정보 추출 (배터리 및 옵션 비트) 
            opt1 = packet[6]
            self.state['battery'] = packet[8]
            self.state['emergency'] = bool(opt1 & 0x01)
            self.state['ready'] = bool(opt1 & 0x02)
            
            # INFO 데이터 구간 (packet[9]부터 시작) 
            info = packet[9:]
            
            # 2. 센서 신호 파싱 (OPT1 BIT2 활성화 시 - POS_SIGNAL 0x06) 
            if opt1 & 0x04:
                data_type = info[0]
                if data_type == 0x06:
                    # D1~D4 슬롯에서 Flow 및 ToF 데이터 추출 (Little Endian short) 
                    self.state['flow_x'] = struct.unpack('<h', info[1:3])[0]
                    self.state['flow_y'] = struct.unpack('<h', info[3:5])[0]
                    self.state['tof'] = struct.unpack('<h', info[5:7])[0]

            # 3. 비행 정보 파싱 (OPT1 BIT5 활성화 시 - 비행 정보 응답) 
            if opt1 & 0x20:
                # 기울기, 높이, 그리고 요청하신 절대 위치(pos_x, pos_y) 추출 
                self.state['roll'] = struct.unpack('<h', info[1:3])[0]
                self.state['pitch'] = struct.unpack('<h', info[3:5])[0]
                self.state['height'] = struct.unpack('<h', info[5:7])[0]
                self.state['pos_x'] = struct.unpack('<h', info[7:9])[0]
                self.state['pos_y'] = struct.unpack('<h', info[9:11])[0]

        return self.state