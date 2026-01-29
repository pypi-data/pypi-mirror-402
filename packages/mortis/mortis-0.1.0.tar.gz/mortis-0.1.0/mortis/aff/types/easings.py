from __future__ import annotations

from enum import StrEnum
from math import cos, pi, sin
from typing import final


__all__ = [
	'BaseEasing', 'EasingLinear', 'EasingSineIn', 'EasingSineOut', 'EasingBezierDefault', 'EasingSineInOut',
	'ArcEasing', 'get_easing_x', 'get_easing_y'
]

class BaseEasing:
	@staticmethod
	def _at_unit(ratio: float) -> float:
		"""Implementation of the easing curve, typically the y=f(x) expression of it."""
		raise NotImplementedError

	@final
	@classmethod
	def at_unit(cls, ratio: float, /) -> float:
		if ratio < 0 or ratio > 1:
			raise ValueError(f'ratio must be within [0, 1]')
		return cls._at_unit(ratio)
	
	@final
	def at(self, value: float, /) -> float:
		ratio = (value - self.begin_input) / (self.end_input - self.begin_input)
		if ratio < 0 or ratio > 1:
			raise ValueError(f'Param must be within the range between {self.begin_input} and {self.end_input}')
		
		eased_ratio = self.at_unit(ratio)
		return self.begin_input + eased_ratio * (self.end_output - self.begin_output)
	
	def __init__(
			self,
			begin_input: float,
			end_input: float,
			begin_output: float,
			end_output: float,
		):
		self.begin_input = begin_input
		self.end_input = end_input
		self.begin_output = begin_output
		self.end_output = end_output
	
class EasingLinear(BaseEasing):
	@staticmethod
	def _at_unit(ratio: float) -> float:
		return ratio

class EasingSineIn(BaseEasing):
	@staticmethod
	def _at_unit(ratio: float) -> float:
		return sin(pi * ratio / 2)

class EasingSineOut(BaseEasing):
	@staticmethod
	def _at_unit(ratio: float) -> float:
		return 1 - cos(pi * ratio / 2)

class EasingBezierDefault(BaseEasing):
	"""Bezier curve, starts from (0, 0), ends at (1, 1), with 1st and 2nd control points (1/3, 0) and (2/3, 1)."""
	@staticmethod
	def _at_unit(ratio: float) -> float:
		return 3 * ratio ** 2 - 2 * ratio ** 3 # Simplified formula. Gives exact value.

class EasingSineInOut(BaseEasing):
	@staticmethod
	def _at_unit(ratio: float) -> float:
		return (1 - cos(pi * ratio)) / 2
	
class ArcEasing(StrEnum):
	S = s = Straight = 's'
	B = b = Bezier = 'b'
	Si = si = SineIn = 'si'
	So = so = SineOut = 'so'
	SiSi = sisi = 'sisi'
	SiSo = siso = 'siso'
	SoSi = sosi = 'sosi'
	SoSo = soso = 'soso'

def get_easing_x(arc_easing: ArcEasing) -> type[BaseEasing]:
	if arc_easing in [ArcEasing.S]:
		return EasingLinear
	elif arc_easing in [ArcEasing.B]:
		return EasingBezierDefault
	elif arc_easing in [ArcEasing.Si, ArcEasing.SiSi, ArcEasing.SiSo]:
		return EasingSineIn
	elif arc_easing in [ArcEasing.So, ArcEasing.SoSi, ArcEasing.SoSo]:
		return EasingSineOut
	assert False

def get_easing_y(arc_easing: ArcEasing) -> type[BaseEasing]:
	if arc_easing in [ArcEasing.S, ArcEasing.Si, ArcEasing.So]:
		return EasingLinear
	elif arc_easing in [ArcEasing.B]:
		return EasingBezierDefault
	elif arc_easing in [ArcEasing.SiSi, ArcEasing.SoSi]:
		return EasingSineIn
	elif arc_easing in [ArcEasing.SiSo, ArcEasing.SoSo]:
		return EasingSineOut
	assert False