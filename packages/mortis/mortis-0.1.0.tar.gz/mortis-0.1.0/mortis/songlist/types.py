from __future__ import annotations

from enum import IntEnum
from typing import Annotated, Any, Generic, TypeVar, final
from typing_extensions import Self

import annotated_types
from pydantic import AfterValidator, Field, model_validator

from mortis.globcfg import GlobalConfig
from mortis.songlist.base import SonglistPartModel


__all__ = [
	'LowerAsciiId', 'SingleLineStr',
	'Localized', 'LocalizedReqEn', 'StrLocalizedSLRE',
	'SideEnum', 'RatingClassEnum',
	'RTCLS_STR_MAP', 'RatingInt'
]


def ensure_lower_ascii_id(s: str) -> str:
	if s.isidentifier() and s.isascii() and s.lower() == s:
		return s
	raise ValueError(f'Value must be a lowercase ASCII identifier')
LowerAsciiId = Annotated[str, AfterValidator(ensure_lower_ascii_id)]


def ensure_single_line(s: str) -> str:
	if '\n' not in s:
		return s
	raise ValueError(f'Value must be in one line (contain no \'\\n\')')
SingleLineStr = Annotated[str, AfterValidator(ensure_single_line)]


@final
class GuardinaError(ValueError, KeyError):
	__instance__ = None
	def __new__(cls) -> Self:
		if cls.__instance__ is None:
			cls.__instance__ = super().__new__(cls)
		return cls.__instance__
	
	def __init__(self) -> None:
		pass

	def __str__(self) -> str:
		return f'\'kr\' is not a valid language code; do you mean \'ko\'?'
	
	def __repr__(self) -> str:
		return f'{self.__class__.__name__}()'

T = TypeVar('T')
class Localized(SonglistPartModel, Generic[T]):
	en: T | None = None
	ja: T | None = None
	ko: T | None = None
	zh_Hans: T | None = Field(default=None, alias='zh-Hans')
	zh_Hant: T | None = Field(default=None, alias='zh-Hant')

	@model_validator(mode='before')
	def _before_validation(cls, data: Any) -> Any:
		if not isinstance(data, dict):
			return data
		if 'kr' in data:
			if GlobalConfig.allows_kr_langcode:
				if 'ko' not in data:
					data['ko'] = data['kr']
				del data['kr']
			else:
				raise GuardinaError
		return data

	def __bool__(self) -> bool:
		return bool(self.nondefault_fields)

class LocalizedReqEn(Localized[T]):
	en: T  # pyright: ignore[reportGeneralTypeIssues, reportIncompatibleVariableOverride] | intended behaviour

	def __bool__(self) -> bool:
		return True

StrLocalizedSLRE = LocalizedReqEn[SingleLineStr]


class SideEnum(IntEnum):
	Light = 0
	Conflict = 1
	Achromatic = 2
	Lephon = 3

class RatingClassEnum(IntEnum):
	Past = 0
	Present = 1
	Future = 2
	Beyond = 3
	Eternal = 4
RTCLS_STR_MAP = {e: e.name.lower() for e in RatingClassEnum}


RatingInt = Annotated[int, annotated_types.Ge(-1)]
