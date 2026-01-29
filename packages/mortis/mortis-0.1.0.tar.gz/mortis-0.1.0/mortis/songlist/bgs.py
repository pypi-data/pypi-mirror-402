from __future__ import annotations

from mortis.songlist.types import SideEnum
from mortis.utils import classproperty


__all__ = ['Backgrounds']

class Backgrounds:
	data = {
		SideEnum.Light: (),
		SideEnum.Conflict: (),
		SideEnum.Achromatic: (),
		SideEnum.Lephon: (),
	}

	@classmethod
	def is_official_bg(cls, bg: str) -> bool:
		return any(bg in bgs for bgs in cls.data.values())

	@classmethod
	def matches(cls, side: SideEnum, bg: str) -> bool:
		return bg in cls.data.get(side, ())
	
	@classproperty
	@classmethod
	def light_bgs(cls) -> tuple[str, ...]:
		return cls.data[SideEnum.Light]
	
	@classproperty
	@classmethod
	def conflict_bgs(cls) -> tuple[str, ...]:
		return cls.data[SideEnum.Conflict]
	
	@classproperty
	@classmethod
	def achromatic_bgs(cls) -> tuple[str, ...]:
		return cls.data[SideEnum.Achromatic]
	
	@classproperty
	@classmethod
	def lephon_bgs(cls) -> tuple[str, ...]:
		return cls.data[SideEnum.Lephon]