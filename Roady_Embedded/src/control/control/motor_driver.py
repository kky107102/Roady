import board
import busio
from adafruit_servokit import ServoKit
from adafruit_pca9685 import PCA9685


class MotorDriver:
    """
    NVIDIA Jetson Orin Nano + Waveshare Motor HAT 제어 클래스
    - 0x60: 조향 서보모터 (Channel 0)
    - 0x40: DC 모터 (Channel 3: IN1, 4: IN2, 5: PWM, 6: STBY)
    """
    def __init__(self, servo_address=0x60, motor_address=0x40):
        # 단일 I2C 버스 생성 (Jetson Orin Nano I2C Bus)
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # 1. 서보모터 전용 PCA9685 (0x60)
        self.kit = ServoKit(channels=16, i2c=self.i2c, address=servo_address)

        # 핀 및 각도 관련 변수 선언
        self.STEERING_CHANNEL = 0
        self.IN1_PIN = 3
        self.IN2_PIN = 4
        self.PWM_PIN = 5
        self.STBY_PIN = 6

        # ★ 서보모터 펄스폭을 500~2500us로 확장 (회전각 제한 해제)
        self.kit.servo[self.STEERING_CHANNEL].set_pulse_width_range(500, 2500)

        # ★ 서보 각도 범위 재설정
        self.SERVO_CENTER_ANGLE = 90  # 수학적 정중앙 90도
        self.SERVO_MAX_DELTA = 35     # 조향 범위를 ±35도로 확대 (55도 ~ 125도)

        # 2. DC 모터 전용 PCA9685 (0x40)
        self.pca_motor = PCA9685(self.i2c, address=motor_address)
        self.pca_motor.frequency = 50

        # 초기화 시 안전 정지
        self.stop()

    def set_steering_angle(self, angle_ratio):
        angle_ratio = max(-1.0, min(1.0, angle_ratio))

        target_angle = self.SERVO_CENTER_ANGLE - int(
            angle_ratio * self.SERVO_MAX_DELTA
        )
        
        # 기존: max(80, min(120, target_angle))
        # 수정: 좌회전 각도(80도 이하)까지 허용하도록 범위 확대 (55도~125도)
        target_angle = max(55, min(125, target_angle))

        try:
            self.kit.servo[self.STEERING_CHANNEL].angle = target_angle
        except Exception:
            pass

    def move(self, speed):
        """
        전/후진 DC 모터 제어
        :param speed: -1.0 (최대 후진) ~ +1.0 (최대 전진)
        """
        speed = max(-1.0, min(1.0, speed))
        duty_cycle = int(abs(speed) * 65535)

        try:
            # Standby 핀 활성화 (0x40 모터 드라이버 ON)
            self.pca_motor.channels[self.STBY_PIN].duty_cycle = 65535

            if speed > 0:
                # 전진
                self.pca_motor.channels[self.IN1_PIN].duty_cycle = 0
                self.pca_motor.channels[self.IN2_PIN].duty_cycle = 65535
                self.pca_motor.channels[self.PWM_PIN].duty_cycle = duty_cycle
            elif speed < 0:
                # 후진
                self.pca_motor.channels[self.IN1_PIN].duty_cycle = 65535
                self.pca_motor.channels[self.IN2_PIN].duty_cycle = 0
                self.pca_motor.channels[self.PWM_PIN].duty_cycle = duty_cycle
            else:
                # 정지
                self.pca_motor.channels[self.IN1_PIN].duty_cycle = 0
                self.pca_motor.channels[self.IN2_PIN].duty_cycle = 0
                self.pca_motor.channels[self.PWM_PIN].duty_cycle = 0

        except Exception:
            pass

    def stop(self):
        """모든 모터 및 조향 안전 정지"""
        try:
            self.set_steering_angle(0.0)
            self.pca_motor.channels[self.PWM_PIN].duty_cycle = 0
            self.pca_motor.channels[self.IN1_PIN].duty_cycle = 0
            self.pca_motor.channels[self.IN2_PIN].duty_cycle = 0
            self.pca_motor.channels[self.STBY_PIN].duty_cycle = 0
        except Exception:
            pass
