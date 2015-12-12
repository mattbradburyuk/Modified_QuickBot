import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import time


LEFT = 0
RIGHT = 1


dir1Pin = ('P8_14', 'P8_12')
dir2Pin = ('P8_16', 'P8_10')
pwmPin = ('P9_16', 'P9_14')


pwm = [100,100]

GPIO.setup(dir1Pin[LEFT], GPIO.OUT)
GPIO.setup(dir2Pin[LEFT], GPIO.OUT)
GPIO.setup(dir1Pin[RIGHT], GPIO.OUT)
GPIO.setup(dir2Pin[RIGHT], GPIO.OUT)


# Initialize PWM pins: PWM.start(channel, duty, freq=2000, polarity=0)
PWM.start(pwmPin[LEFT], 0)
PWM.start(pwmPin[RIGHT], 0)


# Left wheel forward
GPIO.output(dir1Pin[LEFT], GPIO.LOW)
GPIO.output(dir2Pin[LEFT], GPIO.HIGH)
PWM.set_duty_cycle(pwmPin[LEFT], abs(pwm[LEFT]))

time.sleep(2)

#left wheel backwards
GPIO.output(dir1Pin[LEFT], GPIO.HIGH)
GPIO.output(dir2Pin[LEFT], GPIO.LOW)
PWM.set_duty_cycle(pwmPin[LEFT], abs(pwm[LEFT]))

time.sleep(2)

# left wheel stop
GPIO.output(dir1Pin[LEFT], GPIO.LOW)
GPIO.output(dir2Pin[LEFT], GPIO.LOW)
PWM.set_duty_cycle(pwmPin[LEFT], 0)

#right wheel forwards
GPIO.output(dir1Pin[RIGHT], GPIO.LOW)
GPIO.output(dir2Pin[RIGHT], GPIO.HIGH)
PWM.set_duty_cycle(pwmPin[RIGHT], abs(pwm[RIGHT]))

time.sleep(2)

#right wheel backwards
GPIO.output(dir1Pin[RIGHT], GPIO.HIGH)
GPIO.output(dir2Pin[RIGHT], GPIO.LOW)
PWM.set_duty_cycle(pwmPin[RIGHT], abs(pwm[RIGHT]))

time.sleep(2)

# right wheel stop
GPIO.output(dir1Pin[RIGHT], GPIO.LOW)
GPIO.output(dir2Pin[RIGHT], GPIO.LOW)
PWM.set_duty_cycle(pwmPin[RIGHT], 0)
