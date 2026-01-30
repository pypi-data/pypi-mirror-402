from __future__ import annotations

from typing import Optional, TypeAlias

MultipartFile: TypeAlias = tuple[
	str | None,
	bytes,
	Optional[str]
] # (filename, file_content, mime_type)

MultipartFiles: TypeAlias = dict[str, MultipartFile]
