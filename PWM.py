import RPi.GPIO as gpio

class door_component():
    def __init__(self, pin_idx):
        self.pwm_pin = pin_idx
        self.pwm_fre = 50.0
        self.pwm_dutyCycle = 10.0
        gpio.setmode(gpio.BCM)
        gpio.setup(self.pwm_pin, gpio.OUT)
        self.pwm = gpio.PWM(self.pwm_pin, self.pwm_fre)
        
    def control(self, degree):
        if degree < -90:
            degree = -90
        elif degree > 90:
            degree = 90
            
        if degree < 0:
            self.pwm_dutyCycle = 8.0 + (degree * 3.5)/90
        else:
            self.pwm_dutyCycle = 8.0 + (degree * 5.0)/90
        
        self.pwm.ChangeDutyCycle(self.pwm_dutyCycle)
    
    def start(self):
        self.pwm.start(self.pwm_dutyCycle)
    
    def stop(self):
        self.pwm.stop()