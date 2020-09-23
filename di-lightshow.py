import time
from numpy.random import randint
from infinity import InfinityBase


if __name__ == '__main__':
    base = InfinityBase()
    base.connect()
    print("connected")
    print("colors")
    base.set_color(1,   0,   0, 0)
    base.set_color(2,   0,   0, 0)
    base.set_color(3,   0,   0, 0)
    time.sleep(1)

    # fade_to ?
    base.fade_color(1,255,0,0)
    time.sleep(0.65)
    base.set_color(1,225,0,0)
    
    time.sleep(5)
    base.flash_color(1,0,0,255)
    time.sleep(5)
    
    s=0.1
    base.set_color(1, 255,   0,   0)
    time.sleep(s)
    base.set_color(1, 255, 127,   0)
    time.sleep(s)
    base.set_color(1, 255, 255,   0)
    time.sleep(s)
    base.set_color(1, 127, 255,   0)
    time.sleep(s)
    base.set_color(1,   0, 255,   0)
    time.sleep(s)
    base.set_color(1,   0, 255, 127)
    time.sleep(s)
    base.set_color(1,   0, 255, 255)
    time.sleep(s)
    base.set_color(1,   0, 127, 255)
    time.sleep(s)
    base.set_color(1,   0,   0, 255)
    time.sleep(s)
    base.set_color(1,  127,   0, 255)
    time.sleep(s)
    base.set_color(1,  255,   0, 255)
    time.sleep(s)
    base.set_color(1,  255,   0, 127)
    time.sleep(s)

    print("Jukebox is ready to jam. CTRL-C to quit")   
    for x in range(0,10):
    #         NUMBER RED GREEN BLUE
        for a in range(0,3):
            colors = randint(0,256,3)
            base.set_color(a, colors[0], colors[1], colors[2])
        for b in range(0,3):
            colors = randint(0,256,3)
            base.flash_color(b, colors[0], colors[1], colors[2])

        time.sleep(1)

      #  base.fade_color(1, 200, 0, 0)
      #  base.fade_color(2, 0, 200, 0)
      #  base.fade_color(3, 0, 0, 200)

      #  time.sleep(1)

      #  base.flash_color(1, 0, 0, 0)
      #  base.flash_color(2, 0, 0, 0)
      #  base.flash_color(3, 0, 0, 0)
