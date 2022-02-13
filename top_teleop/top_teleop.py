#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from pynput.keyboard import Key, Listener
import sys, select, os
if os.name == 'nt':
  import msvcrt
else:
  import tty, termios
import time

from geometry_msgs.msg import Twist

 
MAX_LIN_VEL = 2.0
MAX_ANG_VEL = 1.82

LIN_VEL_STEP_SIZE = 0.02
ANG_VEL_STEP_SIZE = 0.1

msg = """
Control Your TurtleBot3!
---------------------------
Moving around:
        w
   a    s    d

w/s : linear movement (Burger : ~ 0.22, Waffle and Waffle Pi : ~ 0.26)
a/d : angular movement (Burger : ~ 2.84, Waffle and Waffle Pi : ~ 1.82)

stop when key released
ESC to quit
"""

e = """
Communications Failed
"""


class TopTeleop(Node):
    def __init__(self):
        super().__init__('top_teleop')
        if os.name != 'nt':
            self.settings = termios.tcgetattr(sys.stdin)
        print(msg)
        self.keys = set()
        self.status = 0
        self.target_linear_vel   = 0.0
        self.target_angular_vel  = 0.0
        self.key = ""


        self.status = 0
        self.target_linear_vel   = 0.0
        self.target_angular_vel  = 0.0
        self.control_linear_vel  = 0.0
        self.control_angular_vel = 0.0
    
        listener = Listener(
        on_press=self.on_press,
        on_release=self.on_release)
        listener.start()

        self.cmd_vel_publisher = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_timer(0.1, self.cmd_vel_loop)

    def cmd_vel_loop(self):
        key = self.get_key()
        if key == 'w' :
            self.target_linear_vel = self.checkLinearLimitVelocity(self.target_linear_vel + LIN_VEL_STEP_SIZE)
            self.status = self.status + 1
            print(self.vels(self.target_linear_vel,self.target_angular_vel))
        elif key == 'x' :
            self.target_linear_vel = self.checkLinearLimitVelocity(self.target_linear_vel - LIN_VEL_STEP_SIZE)
            self.status = self.status + 1
            print(self.vels(self.target_linear_vel,self.target_angular_vel))
        elif key == 'a' :
            self.target_angular_vel = self.checkAngularLimitVelocity(self.target_angular_vel + ANG_VEL_STEP_SIZE)
            self.status = self.status + 1
            print(self.vels(self.target_linear_vel,self.target_angular_vel))
        elif key == 'd' :
            self.target_angular_vel = self.checkAngularLimitVelocity(self.target_angular_vel - ANG_VEL_STEP_SIZE)
            self.status = self.status + 1
            print(self.vels(self.target_linear_vel,self.target_angular_vel))
        elif key == ' ' or key == 's' :
            self.target_linear_vel   = 0.0
            self.control_linear_vel  = 0.0
            self.target_angular_vel  = 0.0
            self.control_angular_vel = 0.0
            print(self.vels(self.target_linear_vel, self.target_angular_vel))
  

        if self.status == 20 :
            print(msg)
            self.status = 0

        twist = Twist()

        self.control_linear_vel = self.makeSimpleProfile(self.control_linear_vel, self.target_linear_vel, (LIN_VEL_STEP_SIZE/2.0))
        twist.linear.x = self.control_linear_vel 
        twist.linear.y = 0.0
        twist.linear.z = 0.0

        self.control_angular_vel = self.makeSimpleProfile(self.control_angular_vel, self.target_angular_vel, (ANG_VEL_STEP_SIZE/2.0))
        twist.angular.x = 0.0 
        twist.angular.y = 0.0 
        twist.angular.z = self.control_angular_vel
        self.cmd_vel_publisher.publish(twist)
        # pub.publish(twist)

    def vels(self, target_linear_vel, target_angular_vel):
        return "currently:\tlinear vel %s\t angular vel %s " % (target_linear_vel,target_angular_vel)

    def constrain(self, input, low, high):
        if input < low:
            input = low
        elif input > high:
            input = high
        else:
            input = input

        return input

    def on_press(self, key):
        # to remove input buffer
        if os.name == 'nt':
            msvcrt.getch() 
        else:
            tty.setraw(sys.stdin.fileno())
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

        if not hasattr(key, 'char'):
            if(key.name == "space" or key.name == "enter"):
                self.key = " "
            # if(key.name == "up"):
            #     self.key = "w"
            # if(key.name == "down"):
            #     self.key = "x"
            # if(key.name == "left"):
            #     self.key = "a"
            # if(key.name == "right"):
            #     self.key = "d"
        else: 
            self.key = key.char
        return self.key

    def get_key(self):
        return self.key

    def on_release(self, key):
        self.key = ""
        return ""



    def checkLinearLimitVelocity(self,vel):
        vel = self.constrain(vel, -MAX_LIN_VEL, MAX_LIN_VEL)
        return vel

    def checkAngularLimitVelocity(self,vel):
        vel = self.constrain(vel, -MAX_ANG_VEL, MAX_ANG_VEL)
        return vel




    def makeSimpleProfile(self, output, input, slop):
        if input > output:
            output = min( input, output + slop )
        elif input < output:
            output = max( input, output - slop )
        else:
            output = input

        return output
def main(args=None):


    rclpy.init(args=args)
    node = TopTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('server stopped cleanly')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
