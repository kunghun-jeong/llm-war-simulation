"""
unit.py - 유닛 클래스 (군인 3종 + 민간인)
팀당 구성: 민간인 50명 + 원거리4 + 근거리4 + 중장갑2 = 60유닛
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Tuple, Optional
from terrain import TerrainType, get_terrain_effect

class UnitType(Enum):
    CIVILIAN    = "civilian"     # 민간인 (비전투)
    RANGED      = "ranged"       # 원거리 공격 (사거리 6)
    MELEE       = "melee"        # 근거리 공격 (사거리 1)
    HEAVY_MELEE = "heavy_melee"  # 강력 근거리 (사거리 1, 고HP·고공격)

# 유닛 타입별 기본 스펙
UNIT_STATS = {
    UnitType.CIVILIAN: {
        "hp": 50,  "attack": 0,  "base_range": 0,
        "move_max": 1, "vision": 3,
        "description": "민간인: 비전투, 보호 대상"
    },
    UnitType.RANGED: {
        "hp": 80,  "attack": 15, "base_range": 6,
        "move_max": 2, "vision": 7,
        "description": "원거리: 사거리6, 약한 공격"
    },
    UnitType.MELEE: {
        "hp": 100, "attack": 25, "base_range": 1,
        "move_max": 3, "vision": 5,
        "description": "근거리: 사거리1, 중간 공격, 빠른 이동"
    },
    UnitType.HEAVY_MELEE: {
        "hp": 200, "attack": 50, "base_range": 1,
        "move_max": 1, "vision": 4,
        "description": "중장갑: 사거리1, 매우 강한 공격, 느린 이동"
    },
}

@dataclass
class Unit:
    unit_id:   int
    team:      str
    unit_type: UnitType
    row:       int
    col:       int
    hp:        int  = field(init=False)
    max_hp:    int  = field(init=False)
    attack_power: int = field(init=False)
    base_range:   int = field(init=False)
    move_max:     int = field(init=False)
    vision:       int = field(init=False)
    alive:     bool = True
    action_log: list = field(default_factory=list)

    def __post_init__(self):
        stats = UNIT_STATS[self.unit_type]
        self.hp           = stats["hp"]
        self.max_hp       = stats["hp"]
        self.attack_power = stats["attack"]
        self.base_range   = stats["base_range"]
        self.move_max     = stats["move_max"]
        self.vision       = stats["vision"]

    @property
    def is_combatant(self) -> bool:
        return self.unit_type != UnitType.CIVILIAN

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.row, self.col)

    def effective_attack(self, terrain: TerrainType) -> float:
        bonus = get_terrain_effect(terrain, "attack_bonus", 1.0)
        return self.attack_power * bonus

    def effective_range(self, terrain: TerrainType) -> int:
        extra = int(get_terrain_effect(terrain, "range_bonus", 0))
        return self.base_range + extra

    def effective_vision(self, terrain: TerrainType) -> int:
        return get_terrain_effect(terrain, "vision_range", self.vision)

    def effective_move(self, terrain: TerrainType) -> int:
        speed = get_terrain_effect(terrain, "move_speed", 1.0)
        return max(1, int(self.move_max * speed))

    def take_damage(self, damage: float, own_terrain: TerrainType) -> int:
        defense = get_terrain_effect(own_terrain, "defense_bonus", 1.0)
        actual  = max(1, int(damage * defense))
        self.hp = max(0, self.hp - actual)
        if self.hp == 0:
            self.alive = False
        return actual

    def can_attack(self, target: "Unit", terrain: TerrainType) -> bool:
        if not self.is_combatant:
            return False
        dist = abs(self.row - target.row) + abs(self.col - target.col)
        return dist <= self.effective_range(terrain)

    def can_see(self, target: "Unit",
                own_terrain: TerrainType, target_terrain: TerrainType) -> bool:
        vision = self.effective_vision(own_terrain)
        dist   = abs(self.row - target.row) + abs(self.col - target.col)
        if target_terrain == TerrainType.FOREST:
            vision = vision // 2
        return dist <= vision

    def log_action(self, action: str, detail: str = ""):
        self.action_log.append({
            "action": action, "detail": detail,
            "pos": self.pos, "hp": self.hp
        })

    def __repr__(self):
        t = {"civilian":"민","ranged":"원","melee":"근",
             "heavy_melee":"중"}[self.unit_type.value]
        s = "✓" if self.alive else "✗"
        return f"[{self.team[0].upper()}{t}{self.unit_id}|{s}HP:{self.hp}]"
