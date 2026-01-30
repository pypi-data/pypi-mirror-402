# Trosnoth (UberTweak Platform Game)
# Copyright (C) Joshua D Bartlett
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

from dataclasses import dataclass
from math import sin, cos

from trosnoth.utils.serialise import Dumpable


def distance(pt1, pt2):
    if len(pt1) != len(pt2):
        raise TypeError('vectors must have same length')
    return sum((pt2[i] - pt1[i]) ** 2 for i in range(len(pt1))) ** 0.5


def fadeValues(val1, val2, interval):
    return val2 * interval + val1 * (1 - interval)


def isNear(v1, v2, epsilon=1e-3):
    '''
    Compares two floating point values for approximate equality.
    '''
    return abs(v1 - v2) < epsilon


def moveTowardsPointAndReturnEndPoint(origin, target, speed, deltaT):
    maxMoveDistance = speed * deltaT
    distanceFromTarget = distance(origin, target)
    if distanceFromTarget < maxMoveDistance:
        return target
    else:
        # calculate fraction of total distance to move this tick
        fractionToMove = maxMoveDistance / distanceFromTarget
        return (
            origin[0] + fractionToMove * (target[0] - origin[0]),
            origin[1] + fractionToMove * (target[1] - origin[1])
        )


@dataclass
class Vector(Dumpable):
    x: float = 0
    y: float = 0

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, index):
        return (self.x, self.y)[index]

    def abs(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5


class RotatedAxes(object):
    def __init__(self, angle=None, vector=None):
        if angle is not None:
            if vector is not None:
                raise TypeError('Too many arguments')
            self.sinTheta = sin(angle)
            self.cosTheta = cos(angle)
        else:
            x, y = vector
            magnitude = (x ** 2 + y ** 2) ** 0.5
            self.sinTheta = y / magnitude
            self.cosTheta = x / magnitude

    def rotatedFromGlobal(self, point, origin=(0, 0)):
        x, y = point
        x -= origin[0]
        y -= origin[1]

        s = x * self.cosTheta + y * self.sinTheta
        t = -x * self.sinTheta + y * self.cosTheta
        return (s, t)

    def rotated_from_global(self, vector, origin=(0, 0)):
        s, t = self.rotatedFromGlobal((vector[0], vector[1]), (origin[0], origin[1]))
        return Vector(s, t)

    def globalFromRotated(self, point, origin=(0, 0)):
        s, t = point
        x = s * self.cosTheta - t * self.sinTheta + origin[0]
        y = s * self.sinTheta + t * self.cosTheta + origin[1]
        return (x, y)

    def global_from_rotated(self, vector, origin=(0, 0)):
        s, t = self.globalFromRotated((vector[0], vector[1]), (origin[0], origin[1]))
        return Vector(s, t)
