from gpiozero import LED
from time import sleep

led = LED(17)

def led_illuminate():
    ctr = 0
    while ctr <= 120:
        print(str(ctr))
        led.on()
        sleep(2)
        ctr += 1

led_illuminate()
