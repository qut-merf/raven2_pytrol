"""
 * Copyright (C) 2018 Queensland University of Technology
 *
 * Creators: Professor Cameron Brown (Project Sponsor) and James Levander
 *
 * This file is part of Raven 2 Python Control.
 *
 * Raven 2 Python Control is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Raven 2 Python Control is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Raven 2 Python Control.  If not, see <http://www.gnu.org/licenses/>.
 *
"""

import socket
import struct
import time
from collections import namedtuple

UDP_IP_RAVEN = "192.168.6.137"
UDP_PORT_RAVEN = 36000

'''
Define the C based u_struct that is described in teleoperation.h

sequence: sequence (unsigned int)
pactyp: packet type (unsigned int)
version: version (unsigned int)

delx0, delx1: cartesian position increment X in micrometres - arm 0, 1 (int[2])
dely0, dely1: cartesian position increment Y in micrometres - arm 0, 1 (int[2])
delz0, delz1: cartesian position increment Z in micrometres - arm 0, 1 (int[2])

Qx0, Qx1: quaternion rotation increment Qx - arm 0, 1 (double[2])
Qy0, Qy1: quaternion rotation increment Qy - arm 0, 1 (double[2])
Qz0, Qz1: quaternion rotation increment Qz - arm 0, 1 (double[2])
Qw0, Qw1: quaternion rotation increment Qw - arm 0, 1 (double[2])

buttonstate0, buttonstate1: button state - arm 0, 1 (int[2])

grasp0, grasp1: grasp angle increment in milliradians - arm 0, 1 (int[2])

surgeon_mode: surgeon mode (int)
checksum: checksum (int)

Data format of u_struct. See https://docs.python.org/3/library/struct.html
'''
U_STRUCT_DEF = namedtuple('u_struct',
                          'sequence pactyp version delx0 delx1 dely0 dely1 delz0 delz1 Qx0 Qx1 Qy0 Qy1 Qz0 Qz1 Qw0 Qw1 buttonstate0 buttonstate1 grasp0 grasp1 surgeon_mode checksum');
U_STRUCT_FMT = '<IIIiiiiiiddddddddiiiiii'


class Pytroller:
    def __init__(self):
        # Create the UDP socket for sending surgeon u_struct commands to robot
        self.sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Keep track of the command sequence number
        self.seq = 0

        # Cartesian position increments (in micrometres)
        self.arm_0_x_inc = 0
        self.arm_0_y_inc = 0
        self.arm_0_z_inc = 0

        self.arm_1_x_inc = 0
        self.arm_1_y_inc = 0
        self.arm_1_z_inc = 0

        # Quaternion rotation increments
        self.arm_0_qx_inc = 0.0
        self.arm_0_qy_inc = 0.0
        self.arm_0_qz_inc = 0.0
        self.arm_0_qw_inc = 1.0

        self.arm_1_qx_inc = 0.0
        self.arm_1_qy_inc = 0.0
        self.arm_1_qz_inc = 0.0
        self.arm_1_qw_inc = 1.0

        # Grasp angle increments (in milliradians)
        # Fully open is +1570 milliradians (90 degrees)
        self.arm_0_grasp_inc = 0
        self.arm_1_grasp_inc = 0

    def set_position_increment(self, arm_0_x_inc, arm_0_y_inc, arm_0_z_inc, arm_1_x_inc, arm_1_y_inc, arm_1_z_inc):
        """
        Create a move command for arm 0 (GOLD) and arm 1 (GREEN)
        :param arm_0_x_inc: Cartesian position increment X in micrometres on arm 0 (GOLD) as int value
        :param arm_0_y_inc: Cartesian position increment Y in micrometres on arm 0 (GOLD) as int value
        :param arm_0_z_inc: Cartesian position increment Z in micrometres on arm 0 (GOLD) as int value
        :param arm_1_x_inc: Cartesian position increment X in micrometres on arm 1 (GREEN) as int value
        :param arm_1_y_inc: Cartesian position increment Y in micrometres on arm 1 (GREEN) as int value
        :param arm_1_z_inc: Cartesian position increment Z in micrometres on arm 1 (GREEN) as int value
        """
        self.arm_0_x_inc = arm_0_x_inc
        self.arm_0_y_inc = arm_0_y_inc
        self.arm_0_z_inc = arm_0_z_inc

        self.arm_1_x_inc = arm_1_x_inc
        self.arm_1_y_inc = arm_1_y_inc
        self.arm_1_z_inc = arm_1_z_inc

    def set_rotation_increment(self, arm_0_qx_inc, arm_0_qy_inc, arm_0_qz_inc, arm_0_qw_inc,
                               arm_1_qx_inc, arm_1_qy_inc, arm_1_qz_inc, arm_1_qw_inc):
        """
        Create a rotation command for arm 0 (GOLD) and arm 1 (GREEN)

        Calculate required increment in EULER and then convert to Quaternion (e.g. https://quaternions.online)
        EULER X - Moves the grasper joint
        EULER Y - Moves the wrist joint
        EULER Z - Rotates the tool shaft

        :param arm_0_qx_inc: Quaternion rotation increment Qx on arm 0 (GOLD) as float value
        :param arm_0_qy_inc: Quaternion rotation increment Qy on arm 0 (GOLD) as float value
        :param arm_0_qz_inc: Quaternion rotation increment Qz on arm 0 (GOLD) as float value
        :param arm_0_qw_inc: Quaternion rotation increment Qw on arm 0 (GOLD) as float value
        :param arm_1_qx_inc: Quaternion rotation increment Qx on arm 1 (GREEN) as float value
        :param arm_1_qy_inc: Quaternion rotation increment Qy on arm 1 (GREEN) as float value
        :param arm_1_qz_inc: Quaternion rotation increment Qz on arm 1 (GREEN) as float value
        :param arm_1_qw_inc: Quaternion rotation increment Qw on arm 1 (GREEN) as float value
        """
        self.arm_0_qx_inc = arm_0_qx_inc
        self.arm_0_qy_inc = arm_0_qy_inc
        self.arm_0_qz_inc = arm_0_qz_inc
        self.arm_0_qw_inc = arm_0_qw_inc

        self.arm_1_qx_inc = arm_1_qx_inc
        self.arm_1_qy_inc = arm_1_qy_inc
        self.arm_1_qz_inc = arm_1_qz_inc
        self.arm_1_qw_inc = arm_1_qw_inc

    def set_grasp_increment(self, arm_0_grasp_inc, arm_1_grasp_inc):
        """
        Create a grasp command for arm 0 (GOLD) and arm 1 (GREEN)

        Negative increments opens the grasper

        :param arm_0_grasp_inc: Grasp angle increment in milliradians on arm 0 (GOLD) as int value
        :param arm_1_grasp_inc: Grasp angle increment in milliradians on arm 1 (GREEN) as int value
        """
        self.arm_0_grasp_inc = arm_0_grasp_inc
        self.arm_1_grasp_inc = arm_1_grasp_inc

    def send_data(self):
        """
        Send a command (u_struct) containing current position via the socket to the robot
        :return: The number of bytes sent through the socket
        """
        self.seq += 1
        tuple_to_send = U_STRUCT_DEF(sequence=self.seq,
                                     pactyp=0,
                                     version=0,
                                     delx0=int(self.arm_0_x_inc),
                                     delx1=int(self.arm_1_x_inc),
                                     dely0=int(self.arm_0_y_inc),
                                     dely1=int(self.arm_1_y_inc),
                                     delz0=int(self.arm_0_z_inc),
                                     delz1=int(self.arm_1_z_inc),
                                     Qx0=float(self.arm_0_qx_inc),
                                     Qx1=float(self.arm_1_qx_inc),
                                     Qy0=float(self.arm_0_qy_inc),
                                     Qy1=float(self.arm_1_qy_inc),
                                     Qz0=float(self.arm_0_qz_inc),
                                     Qz1=float(self.arm_1_qz_inc),
                                     Qw0=float(self.arm_0_qw_inc),
                                     Qw1=float(self.arm_1_qw_inc),
                                     buttonstate0=int(0),
                                     buttonstate1=int(0),
                                     grasp0=int(self.arm_0_grasp_inc),
                                     grasp1=int(self.arm_1_grasp_inc),
                                     surgeon_mode=int(1),
                                     checksum=int(0)
                                     )

        command = struct.pack(U_STRUCT_FMT, *tuple_to_send._asdict().values())
        bytes_sent = self.sock1.sendto(command, (UDP_IP_RAVEN, UDP_PORT_RAVEN))
        self.print_data_sent(bytes_sent)

        return bytes_sent

    def print_data_sent(self, bytes_sent):
        print('[ SEQ:' + str(self.seq) + ' BYTES:' + str(bytes_sent)
              + ' | ARM0_POS_INC X:' + str(self.arm_0_x_inc)
              + ' Y:' + str(self.arm_0_y_inc)
              + ' Z:' + str(self.arm_0_z_inc)
              + ' | ARM1_POS_INC X:' + str(self.arm_1_x_inc)
              + ' Y:' + str(self.arm_1_y_inc)
              + ' Z:' + str(self.arm_1_z_inc)
              + ' | ARM0_ROT_INC Qx:' + str(self.arm_0_qx_inc)
              + ' Qy:' + str(self.arm_0_qy_inc)
              + ' Qz:' + str(self.arm_0_qz_inc)
              + ' Qw:' + str(self.arm_0_qw_inc)
              + ' | ARM1_ROT_INC Qx:' + str(self.arm_1_qx_inc)
              + ' Qy:' + str(self.arm_1_qy_inc)
              + ' Qz:' + str(self.arm_1_qz_inc)
              + ' Qw:' + str(self.arm_1_qw_inc)
              + ' | ARM0_GRASP_INC:' + str(self.arm_0_grasp_inc)
              + ' | ARM1_GRASP_INC:' + str(self.arm_1_grasp_inc)
              + ' ]')

    def reset_data(self):
        """
        Reset the u_struct values
        """
        self.set_position_increment(0, 0, 0, 0, 0, 0)
        self.set_rotation_increment(1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0)
        self.set_grasp_increment(0, 0)

    def reset_sequence(self):
        """
        Reset the sequence on the robot (described in network_layer.cpp:297)
        """
        print('Sequence reset requested!')

        if self.seq < 1002:
            push_forward_count = 1002 - self.seq
            print('Pushing robot sequence forward to prepare for reset: ' + str(push_forward_count))

            self.reset_data()  # we don't want to re-send the last increments push_forward_count times

            for s in range(push_forward_count):
                self.send_data()
                time.sleep(0.01)

        self.seq = 0  # next send_data will self.seq += 1 and then the raven seq will be reset to 1

    def __del__(self):
        self.sock1.close()


# MAIN

#  TODO(JL): Need to get a python side inverse kinematics solver so we can send sane moves increments to the raven.
#  TODO(JL): The r2_kinematics.cpp check_solutions() code drops updates when an acceptable solution is not found

pytroller = Pytroller()

'''
Lift instrument arms vertical
'''
for i in range(100):
    pytroller.set_position_increment(800, 0, -1000, 800, 0, -1000)
    pytroller.set_rotation_increment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    pytroller.set_grasp_increment(0, 0)

    pytroller.send_data()
    time.sleep(0.01)

'''
Move instrument arms towards each other
'''
for i in range(100):
    pytroller.set_position_increment(0, 1200, 0, 0, -1200, 0)
    pytroller.set_rotation_increment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    pytroller.set_grasp_increment(0, 0)

    pytroller.send_data()
    time.sleep(0.01)

#  TODO(JL): Graspers are not always fully opening due to dropped updates. An extra increment hack added
'''
Open graspers
'''
for i in range(11):
    pytroller.set_position_increment(0, 0, 0, 0, 0, 0)
    pytroller.set_rotation_increment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    pytroller.set_grasp_increment(-157, -157)

    pytroller.send_data()
    time.sleep(0.1)

time.sleep(1)

'''
Rotate tool shaft
'''
pytroller.set_position_increment(0, 0, 0, 0, 0, 0)
#  Rotate tool shaft 90 DEG - Arm0 [EULER X:0, Y:0, Z:90] Arm1 [EULER X:0, Y:0, Z:-90]
pytroller.set_rotation_increment(0.0, 0.0, 0.707, 0.707, 0.0, 0.0, 0.707, -0.707)
pytroller.set_grasp_increment(0, 0)
pytroller.send_data()

time.sleep(1)

'''
Move grasper in joint
'''
pytroller.set_position_increment(0, 0, 0, 0, 0, 0)
#  Move grasper in joint 40 DEG - Arm0 [EULER X:-40, Y:0, Z:0] Arm1 [EULER X:40, Y:0, Z:0]
pytroller.set_rotation_increment(-0.342, 0.0, 0.0, 0.940, 0.342, 0.0, 0.0, 0.940)
pytroller.set_grasp_increment(0, 0)
pytroller.send_data()

time.sleep(1)

#  TODO(JL): Graspers are not always fully closing due to dropped updates. An extra increment hack added
'''
Close graspers
'''
for i in range(11):
    pytroller.set_position_increment(0, 0, 0, 0, 0, 0)
    pytroller.set_rotation_increment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    pytroller.set_grasp_increment(157, 157)

    pytroller.send_data()
    time.sleep(0.1)
