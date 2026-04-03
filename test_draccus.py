import draccus
from dataclasses import dataclass, field
import sys

@dataclass
class Config:
    rename_map: dict[str, str] = field(default_factory=dict)

if __name__ == "__main__":
    cfg = draccus.parse(Config)
    print(repr(cfg.rename_map))
    print(type(cfg.rename_map))
