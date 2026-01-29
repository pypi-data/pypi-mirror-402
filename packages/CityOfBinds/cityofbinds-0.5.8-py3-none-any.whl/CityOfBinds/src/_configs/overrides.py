from dataclasses import dataclass
from typing import Optional


@dataclass
class OverrideConfigs:
    pass


@dataclass
class PublisherOverrides:
    is_silent: Optional[bool] = None
    absolute_path_links: Optional[bool] = None
    max_files_per_folder: Optional[int] = None
    enable_path_padding: Optional[bool] = None
