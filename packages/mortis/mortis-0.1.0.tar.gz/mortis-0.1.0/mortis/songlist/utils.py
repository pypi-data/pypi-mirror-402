from __future__ import annotations

from mortis.songlist.diffs import Difficulty


__all__ = [
	'get_audio_name',
	'get_preview_name',
	'get_jacket_names',
	'get_aff_name'
]

def get_audio_name(diff: Difficulty) -> str:
	return f'{diff.rating_class.value}.ogg' if diff.audio_override else 'base.ogg'

def get_preview_name(diff: Difficulty) -> str:
	return f'{diff.rating_class.value}_preview.ogg' if diff.audio_override else 'preview.ogg'

def get_jacket_names(diff: Difficulty) -> tuple[str, ...]:
	rtcls = diff.rating_class if diff.jacket_override else 'base'
	return f'{rtcls}.jpg', f'{rtcls}_256.jpg', f'1080_{rtcls}.jpg', f'1080_{rtcls}_256.jpg'

def get_aff_name(diff: Difficulty) -> str:
	return f'{diff.rating_class.value}.aff'