'''
Linear Algebra
Author: Tawn Kramer
Date: Nov 11, 2014
'''
from __future__ import annotations

import math
from typing import Any


class Vec2(object):
    def __init__(self, x=0.0, y=0.0) -> None:
        self.x: float = x
        self.y: float = y

    def __add__(self, other) -> Vec2:
        return self.add(other)

    def __sub__(self, other) -> Vec2:
        return self.subtract(other)

    def __mul__(self, other) -> Vec2:
        return self.multiply(other)

    def __div__(self, other) -> Vec2:
        return self.multiply(other.reciprocal())

    def __neg__(self) -> Vec2:
        return self.scaled(-1.0)

    def __iadd__(self, other) -> "Vec2":  # += other
        result: Vec2 = self.add(other)
        self.x = result.x
        self.y = result.y
        return self

    def mag_squared(self):
        return self.x * self.x + self.y * self.y

    def mag(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def scale(self, s) -> "Vec2":
        self.x *= s
        self.y *= s
        return self

    def scaled(self, s) -> Vec2:
        r = Vec2()
        r.x = self.x * s
        r.y = self.y * s
        return r

    def normalize(self) -> "Vec2":
        m: float = self.mag()
        self.scale(1.0 / m)
        return self

    def subtract(self, v) -> Vec2:
        r = Vec2()
        r.x = self.x - v.x
        r.y = self.y - v.y
        return r

    def add(self, v) -> Vec2:
        r = Vec2()
        r.x = self.x + v.x
        r.y = self.y + v.y
        return r

    def multiply(self, v) -> Vec2:
        r = Vec2()
        r.x = self.x * v.x
        r.y = self.y * v.y
        return r

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def cross(self, v):
        # the sign tells you which side the other vector lies
        return self.x * v.y - self.y * v.x

    def dist(self, v) -> float:
        r: Vec2 = self.subtract(v)
        return r.mag()

    def reciprocal(self) -> Vec2:
        r = Vec2()
        if (self.x != 0.0):
            r.x = 1.0 / self.x
        if (self.y != 0.0):
            r.y = 1.0 / self.y
        return r

    def unit_angle(self, v) -> float:
        # note! requires normalized vectors as input
        # returns radian angle
        return math.acos(self.dot(v))


class Vec3(object):
    def __init__(self, x=0.0, y=0.0, z=0.0) -> None:
        self.x: float = x
        self.y: float = y
        self.z: float = z

    def __add__(self, other) -> Vec3:
        return self.add(other)

    def __sub__(self, other) -> Vec3:
        return self.subtract(other)

    def __mul__(self, other) -> Vec3:
        return self.multiply(other)

    def __div__(self, other) -> Vec3:
        return self.multiply(other.reciprocal())

    def __neg__(self) -> Vec3:
        return self.scaled(-1.0)

    def __iadd__(self, other) -> Self:  # += other
        result: Vec3 = self.add(other)
        self.x = result.x
        self.y = result.y
        self.z: math.Any | float = getattr(
            result, 'z', getattr(self, 'z', 0.0))
        if hasattr(self, 'w'):
            self.w: math.Any | float = getattr(
                result, 'w', getattr(self, 'w', 0.0))
        return self

    def mag(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def scale(self, s) -> Self:
        self.x *= s
        self.y *= s
        self.z *= s
        return self

    def scaled(self, s) -> Vec3:
        r = Vec3()
        r.x = self.x * s
        r.y = self.y * s
        r.z = self.z * s
        return r

    def normalize(self) -> Self:
        m: float = self.mag()
        self.scale(1.0 / m)
        return self

    def normalized(self) -> Vec3:
        m: float = self.mag()
        v = Vec3(self.x, self.y, self.z)
        if m > 0:
            v.scale(1.0 / m)
        return v

    def subtract(self, v) -> Vec3:
        r = Vec3()
        r.x = self.x - v.x
        r.y = self.y - v.y
        r.z = self.z - v.z
        return r

    def add(self, v) -> Vec3:
        r = Vec3()
        r.x = self.x + v.x
        r.y = self.y + v.y
        r.z = self.z + v.z
        return r

    def multiply(self, v) -> Vec3:
        r = Vec3()
        r.x = self.x * v.x
        r.y = self.y * v.y
        r.z = self.z * v.z
        return r

    def dot(self, v):
        return (self.x * v.x + self.y * v.y + self.z * v.z)

    def cross(self, v) -> Vec3:
        r = Vec3()
        r.x = (self.y * v.z) - (self.z * v.y)
        r.y = (self.z * v.x) - (self.x * v.z)
        r.z = (self.x * v.y) - (self.y * v.x)
        return r

    def dist(self, v) -> float:
        r: Vec3 = self.subtract(v)
        return r.mag()

    def reciprocal(self) -> Vec3:
        r = Vec3()
        if (self.x != 0.0):
            r.x = 1.0 / self.x
        if (self.y != 0.0):
            r.y = 1.0 / self.y
        if (self.z != 0.0):
            r.z = 1.0 / self.z
        return r

    def unit_angle(self, v) -> float:
        # note! requires normalized vectors as input
        return math.acos(self.dot(v))


def Quat_RotY(radians) -> Quat:
    halfAngle = radians * 0.5
    sinHalf: float = math.sin(halfAngle)
    cosHalf: float = math.cos(halfAngle)
    return Quat(0.0, sinHalf, 0.0, cosHalf)


class Quat(object):
    def __init__(self, x=0.0, y=0.0, z=0.0, w=1.0) -> None:
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.w: float = w

    def rot_x(self, angle) -> None:
        # make this quat a rotation about the X axis of radian angle
        halfa = angle * 0.5
        self.x: float = math.sin(halfa)
        self.y = 0.
        self.z = 0.
        self.w: float = math.cos(halfa)

    def rot_y(self, angle) -> None:
        # make this quat a rotation about the Y axis of radian angle
        halfa = angle * 0.5
        self.y: float = math.sin(halfa)
        self.x = 0.
        self.z = 0.
        self.w: float = math.cos(halfa)

    def rot_z(self, angle) -> None:
        # make this quat a rotation about the Z axis of radian angle
        halfa = angle * 0.5
        self.z: float = math.sin(halfa)
        self.y = 0.
        self.x = 0.
        self.w: float = math.cos(halfa)

    def __mul__(self, other) -> Quat:
        q = Quat()
        q.multiply(self, other)
        return q

    def mag(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)

    def normalize(self) -> Self:
        m: float = self.mag()
        invM: float = 1.0 / m
        self.scale(invM)
        return self

    def normalized(self) -> Vec4:
        return self.scaled(1.0 / self.mag())

    def scale(self, s) -> Self:
        """
        Scale the vector by a scalar value in-place.

        Args:
            s (float): The scalar value to multiply each component by.

        Returns:
            Vec4: The scaled vector (self).
        """
        self.x *= s
        self.y *= s
        self.z *= s
        self.w *= s
        return self

    def scaled(self, s) -> Vec4:
        """
        Returns a new Vec4 instance with each component scaled by the given scalar value.

        Args:
            s (float): The scalar value to multiply each component by.

        Returns:
            Vec4: A new Vec4 object with scaled components.
        """
        r = Vec4()
        r.x = self.x * s
        r.y = self.y * s
        r.z = self.z * s
        r.w = self.w * s
        return r

    def conjugate(self) -> Quat:
        """
        Returns the conjugate of the quaternion.

        The conjugate of a quaternion inverts the sign of the vector part (x, y, z) while keeping the scalar part (w) unchanged.
        This is useful for quaternion inversion and certain rotation operations.

        Returns:
            Quat: The conjugated quaternion.
        """
        return Quat(-self.x, -self.y, -self.y, self.w)

    def inverse(self) -> Vec4:
        """
        Returns the inverse of the current object by normalizing it and scaling by -1.

        The method first normalizes the object (assumed to be a quaternion or similar mathematical entity),
        then returns its scaled version with a factor of -1.0, effectively computing its inverse.

        Returns:
            Same type as self: The inverse of the normalized object.
        """
        q0: Vec4 = self.normalized()
        return q0.scale(-1.0)

    def multiply(self, q1, q2) -> None:
        self.x = q2.w * q1.x + q2.x * q1.w + q2.y * q1.z - q2.z * q1.y
        self.y = q2.w * q1.y + q2.y * q1.w + q2.z * q1.x - q2.x * q1.z
        self.z = q2.w * q1.z + q2.z * q1.w + q2.x * q1.y - q2.y * q1.x
        self.w = q2.w * q1.w - q2.x * q1.x - q2.y * q1.y - q2.z * q1.z

    def vector_transform(self, v):
        qxyz = Vec3(self.x, self.y, self.z)
        cross_v: Vec3 = qxyz.cross(v)
        vw = v.scale(self.w)
        halfV: Vec3 = qxyz.cross(cross_v.add(vw))
        return v.add(halfV.scale(2.0))

    def from_axis_angle(self, axis, angle) -> None:
        '''
        construct a quat from an normalized axis vector and radian rotation about that axis
        '''
        sinha: float = math.sin(angle * 0.5)
        cosha: float = math.cos(angle * 0.5)
        self.w: float = cosha
        self.x = sinha * axis.x
        self.y = sinha * axis.y
        self.z = sinha * axis.z

    def to_axis_angle(self) -> tuple[Vec3, float]:
        '''
        returns a normalized axis vector and radian rotation about that axis
        '''
        halfa: float = math.acos(self.w)
        sinha: float = math.sin(halfa)
        axis = Vec3()
        if sinha != 0.0:
            axis.x = self.x / sinha
            axis.y = self.y / sinha
            axis.z = self.z / sinha
        else:
            axis.z = 1.0
        angle: float = 2.0 * halfa
        return axis, angle

    def getYAxisRot(self) -> float:
        c = Vec3()
        x2 = self.x + self.x
        y2 = self.y + self.y
        z2 = self.z + self.z
        xx = self.x * x2
        xz = self.x * z2
        yy = self.y * y2
        wy = self.w * y2

        c.x = xz + wy
        c.y = 0.0
        c.z = 1.0 - (xx + yy)
        cx2cz2 = c.x * c.x + c.z * c.z

        if cx2cz2 > 0.0:
            factor: float = 1.0 / math.sqrt(cx2cz2)
            c.x = c.x * factor
            c.z = c.z * factor
        else:
            return 0.0

        if c.z <= -0.9999999:
            return math.pi

        if c.z >= 0.9999999:
            return 0.0

        return math.atan2(c.x, c.z)

    def slerp(self, tval, low, high) -> None:
        lHigh = Quat()
        cosom = low.x*high.x + low.y*high.y + low.z*high.z + low.w*high.w
        if cosom < 0.0:
            cosom = -cosom
            lHigh.x = -high.x
            lHigh.y = -high.y
            lHigh.z = -high.z
            lHigh.w = -high.w
        else:
            lHigh.x = high.x
            lHigh.y = high.y
            lHigh.z = high.z
            lHigh.w = high.w

        FLOAT_EPSILON = 0.0000001
        if ((1.0 - cosom) > FLOAT_EPSILON):
            # standard case (slerp)
            omega: float = math.acos(cosom)
            sinom: float = math.sin(omega)
            fOneOverSinom: float = 1.0/sinom
            scalar0: float = math.sin(((1.0 - tval) * omega)) * fOneOverSinom
            scalar1: float = math.sin((tval * omega)) * fOneOverSinom
        else:
            # "from" and "to" Quaternions are very close
            #  ... so we can do a linear interpolation
            scalar0 = 1.0 - tval
            scalar1 = tval

        # calculate final values
        self.x = scalar0 * low.x + scalar1 * lHigh.x
        self.y = scalar0 * low.y + scalar1 * lHigh.y
        self.z = scalar0 * low.z + scalar1 * lHigh.z
        self.w = scalar0 * low.w + scalar1 * lHigh.w


class Vec4(object):
    def __init__(self, x=0.0, y=0.0, z=0.0, w=0.0) -> None:
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.w: float = w

    def __add__(self, other) -> Vec4:
        return self.add(other)

    def __sub__(self, other) -> Vec4:
        return self.subtract(other)

    def __mul__(self, other) -> Vec4:
        return self.multiply(other)

    def __div__(self, other) -> Vec4:
        return self.multiply(other.reciprocal())

    def __neg__(self) -> Vec4:
        return self.scaled(-1.0)

    def __iadd__(self, other) -> Self:  # += other
        result: Vec4 = self.add(other)
        self.x = result.x
        self.y = result.y
        self.z = result.z
        self.w = result.w
        return self

    def mag(self) -> float:
        """
        Calculate the magnitude (Euclidean norm) of the vector.

        Returns:
            float: The magnitude of the vector, computed as the square root of the sum of the squares of its components (x, y, z, w).
        """
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)

    def scale(self, s) -> Self:
        self.x *= s
        self.y *= s
        self.z *= s
        self.w *= s
        return self

    def scaled(self, s) -> Vec4:
        r = Vec4()
        r.x = self.x * s
        r.y = self.y * s
        r.z = self.z * s
        r.w = self.w * s
        return r

    def normalize(self) -> Self:
        m: float = self.mag()
        self.scale(1.0 / m)
        return self

    def normalized(self) -> Vec4:
        m: float = self.mag()
        return self.scaled(1.0 / m)

    def subtract(self, v) -> Vec4:
        r = Vec4()
        r.x = self.x - v.x
        r.y = self.y - v.y
        r.z = self.z - v.z
        r.w = self.w - v.w
        return r

    def add(self, v) -> Vec4:
        r = Vec4()
        r.x = self.x + v.x
        r.y = self.y + v.y
        r.z = self.z + v.z
        r.w = self.w + v.w
        return r

    def multiply(self, v) -> Vec4:
        r = Vec4()
        r.x = self.x * v.x
        r.y = self.y * v.y
        r.z = self.z * v.z
        return r

    def dot(self, v):
        return (self.x * v.x + self.y * v.y + self.z * v.z + self.w * v.w)

    def dist(self, v) -> float:
        r: Vec4 = self.subtract(v)
        return r.mag()

    def reciprocal(self) -> Vec4:
        r = Vec4()
        if (self.x != 0.0):
            r.x = 1.0 / self.x
        if (self.y != 0.0):
            r.y = 1.0 / self.y
        if (self.z != 0.0):
            r.z = 1.0 / self.z
        if (self.w != 0.0):
            r.w = 1.0 / self.w
        return r


def Det2x2(a, b, c, d):
    return (a * d - b * c)


def Det3x3(a1, a2, a3, b1, b2, b3, c1, c2, c3):
    return (
        a1 * Det2x2(b2, b3, c2, c3) -
        b1 * Det2x2(a2, a3, c2, c3) +
        c1 * Det2x2(a2, a3, b2, b3))


class Mat44(object):
    def __init__(self, a=Vec4(), b=Vec4(), c=Vec4(), d=Vec4()) -> None:
        self.a: Vec4 = a
        self.b: Vec4 = b
        self.c: Vec4 = c
        self.d: Vec4 = d

    def indentity(self) -> None:
        self.a = Vec4(1.0, 0.0, 0.0, 0.0)
        self.b = Vec4(0.0, 1.0, 0.0, 0.0)
        self.c = Vec4(0.0, 0.0, 1.0, 0.0)
        self.d = Vec4(0.0, 0.0, 0.0, 1.0)

    def fromQuat(self, q) -> None:
        # calculate coefficients
        x2 = q.x + q.x
        y2 = q.y + q.y
        z2 = q.z + q.z
        xx = q.x * x2
        xy = q.x * y2
        xz = q.x * z2
        yy = q.y * y2
        yz = q.y * z2
        zz = q.z * z2
        wx = q.w * x2
        wy = q.w * y2
        wz = q.w * z2

        self.a.x = 1.0 - (yy + zz)
        self.a.y = xy + wz
        self.a.z = xz - wy
        self.a.w = 0.0

        self.b.x = xy - wz
        self.b.y = 1.0 - (xx + zz)
        self.b.z = yz + wx
        self.b.w = 0.0

        self.c.x = xz + wy
        self.c.y = yz - wx
        self.c.z = 1.0 - (xx + yy)
        self.c.w = 0.0

        self.d.x = 0.0
        self.d.y = 0.0
        self.d.z = 0.0
        self.d.w = 1.0

    def setTranslation(self, trans) -> None:
        self.d.x = trans.x
        self.d.y = trans.y
        self.d.z = trans.z

    def affineTransform(self, v) -> Vec3:
        x = self.a.x*v.x + self.b.x*v.y + self.c.x*v.z + self.d.x
        y = self.a.y*v.x + self.b.y*v.y + self.c.y*v.z + self.d.y
        z = self.a.z*v.x + self.b.z*v.y + self.c.z*v.z + self.d.z
        return Vec3(x, y, z)

    def vectorTransform(self, v) -> Vec3:
        x = self.a.x*v.x + self.b.x*v.y + self.c.x*v.z
        y = self.a.y*v.x + self.b.y*v.y + self.c.y*v.z
        z = self.a.z*v.x + self.b.z*v.y + self.c.z*v.z
        return Vec3(x, y, z)

    def multiply_vec4(self, v) -> Vec4:
        return Vec4(
            self.a.x*v.x + self.b.x*v.y + self.c.x*v.z + self.d.x*v.w,
            self.a.y*v.x + self.b.y*v.y + self.c.y*v.z + self.d.y*v.w,
            self.a.z*v.x + self.b.z*v.y + self.c.z*v.z + self.d.z*v.w,
            self.a.w*v.x + self.b.w*v.y + self.c.w*v.z + self.d.w*v.w)

    def multiply_mat44(self, src2) -> Mat44:
        mtxOut = Mat44()

        mtxOut.a.x = self.a.x*src2.a.x + self.a.y * \
            src2.b.x + self.a.z*src2.c.x + self.a.w*src2.d.x
        mtxOut.a.y = self.a.x*src2.a.y + self.a.y * \
            src2.b.y + self.a.z*src2.c.y + self.a.w*src2.d.y
        mtxOut.a.z = self.a.x*src2.a.z + self.a.y * \
            src2.b.z + self.a.z*src2.c.z + self.a.w*src2.d.z
        mtxOut.a.w = self.a.x*src2.a.w + self.a.y * \
            src2.b.w + self.a.z*src2.c.w + self.a.w*src2.d.w

        mtxOut.b.x = self.b.x*src2.a.x + self.b.y * \
            src2.b.x + self.b.z*src2.c.x + self.b.w*src2.d.x
        mtxOut.b.y = self.b.x*src2.a.y + self.b.y * \
            src2.b.y + self.b.z*src2.c.y + self.b.w*src2.d.y
        mtxOut.b.z = self.b.x*src2.a.z + self.b.y * \
            src2.b.z + self.b.z*src2.c.z + self.b.w*src2.d.z
        mtxOut.b.w = self.b.x*src2.a.w + self.b.y * \
            src2.b.w + self.b.z*src2.c.w + self.b.w*src2.d.w

        mtxOut.c.x = self.c.x*src2.a.x + self.c.y * \
            src2.b.x + self.c.z*src2.c.x + self.c.w*src2.d.x
        mtxOut.c.y = self.c.x*src2.a.y + self.c.y * \
            src2.b.y + self.c.z*src2.c.y + self.c.w*src2.d.y
        mtxOut.c.z = self.c.x*src2.a.z + self.c.y * \
            src2.b.z + self.c.z*src2.c.z + self.c.w*src2.d.z
        mtxOut.c.w = self.c.x*src2.a.w + self.c.y * \
            src2.b.w + self.c.z*src2.c.w + self.c.w*src2.d.w

        mtxOut.d.x = self.d.x*src2.a.x + self.d.y * \
            src2.b.x + self.d.z*src2.c.x + self.d.w*src2.d.x
        mtxOut.d.y = self.d.x*src2.a.y + self.d.y * \
            src2.b.y + self.d.z*src2.c.y + self.d.w*src2.d.y
        mtxOut.d.z = self.d.x*src2.a.z + self.d.y * \
            src2.b.z + self.d.z*src2.c.z + self.d.w*src2.d.z
        mtxOut.d.w = self.d.x*src2.a.w + self.d.y * \
            src2.b.w + self.d.z*src2.c.w + self.d.w*src2.d.w

        return mtxOut

    def inverse(self) -> Mat44:
        inv = Mat44()
        inv.indentity()

        det = Det3x3(self.a.x, self.b.x, self.c.x,  self.a.y,
                     self.b.y, self.c.y,  self.a.z, self.b.z, self.c.z)
        if det < 0.000000001:
            return inv

        # inverse(A) = adjunct(A) / det(A)
        oodet = 1.0 / det
        inv.a.x = Det2x2(self.b.y, self.b.z, self.c.y, self.c.z) * oodet
        inv.b.x = -Det2x2(self.b.x, self.b.z, self.c.x, self.c.z) * oodet
        inv.c.x = Det2x2(self.b.x, self.b.y, self.c.x, self.c.y) * oodet

        inv.a.y = -Det2x2(self.a.y, self.a.z, self.c.y, self.c.z) * oodet
        inv.b.y = Det2x2(self.a.x, self.a.z, self.c.x, self.c.z) * oodet
        inv.c.y = -Det2x2(self.a.x, self.a.y, self.c.x, self.c.y) * oodet

        inv.a.z = Det2x2(self.a.y, self.a.z, self.b.y, self.b.z) * oodet
        inv.b.z = -Det2x2(self.a.x, self.a.z, self.b.x, self.b.z) * oodet
        inv.c.z = Det2x2(self.a.x, self.a.y, self.b.x, self.b.y) * oodet

        # inverse(C) = -C * inverse(A)
        inv.d.x = -(self.d.x*inv.a.x+self.d.y*inv.b.x+self.d.z*inv.c.x)
        inv.d.y = -(self.d.x*inv.a.y+self.d.y*inv.b.y+self.d.z*inv.c.y)
        inv.d.z = -(self.d.x*inv.a.z+self.d.y*inv.b.z+self.d.z*inv.c.z)

        return (inv)


class Line3D(object):

    def __init__(self, a, b) -> None:
        self.origin: Any = a
        self.dir = a - b
        self.dir.normalize()

    def vector_to(self, p):
        delta = self.origin - p
        dot = delta.dot(self.dir)
        return self.dir.scaled(dot) - delta
