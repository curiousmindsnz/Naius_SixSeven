import random
from dataclasses import dataclass

START_GOLD = 20
ROUND_INCOME = 5
MAX_UNITS = 6

UNIT_CATALOG = [
    {"name": "Swordsman", "cost": 4, "max_hp": 24, "attack": 7, "defense": 2, "crit": 0.05, "speed": 5},
    {"name": "Archer", "cost": 5, "max_hp": 18, "attack": 9, "defense": 1, "crit": 0.10, "speed": 7},
    {"name": "Guardian", "cost": 6, "max_hp": 32, "attack": 6, "defense": 4, "crit": 0.03, "speed": 3},
    {"name": "Rogue", "cost": 5, "max_hp": 20, "attack": 8, "defense": 1, "crit": 0.15, "speed": 8},
]

UPGRADES = [
    {"key": "damage", "label": "+2 Weapon Damage", "cost": 6, "value": 2},
    {"key": "crit", "label": "+5% Crit Chance", "cost": 5, "value": 0.05},
    {"key": "speed", "label": "+1 Weapon Speed", "cost": 4, "value": 1},
]


@dataclass
class Weapon:
    damage_bonus: int = 0
    crit_bonus: float = 0.0
    speed_bonus: int = 0


@dataclass
class Unit:
    name: str
    max_hp: int
    attack: int
    defense: int
    crit: float
    speed: int
    is_hero: bool = False
    weapon: Weapon | None = None
    hp: int = 0

    def __post_init__(self) -> None:
        self.hp = self.max_hp

    def is_alive(self) -> bool:
        return self.hp > 0

    def effective_attack(self) -> int:
        if self.is_hero and self.weapon:
            return self.attack + self.weapon.damage_bonus
        return self.attack

    def effective_crit(self) -> float:
        if self.is_hero and self.weapon:
            return min(0.75, self.crit + self.weapon.crit_bonus)
        return self.crit

    def effective_speed(self) -> int:
        if self.is_hero and self.weapon:
            return self.speed + self.weapon.speed_bonus
        return self.speed

    def take_hit(self, raw_damage: int) -> int:
        mitigated = max(1, raw_damage - self.defense)
        self.hp = max(0, self.hp - mitigated)
        return mitigated


@dataclass
class Team:
    name: str
    units: list[Unit]

    def alive_units(self) -> list[Unit]:
        return [unit for unit in self.units if unit.is_alive()]

    def is_defeated(self) -> bool:
        return all(not unit.is_alive() for unit in self.units)


def prompt_choice(prompt: str, valid: set[str]) -> str:
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid:
            return choice
        print("Invalid choice. Try again.")


def create_hero(name: str, weapon: Weapon) -> Unit:
    return Unit(
        name=name,
        max_hp=30,
        attack=8,
        defense=2,
        crit=0.1,
        speed=6,
        is_hero=True,
        weapon=weapon,
    )


def create_unit(template: dict) -> Unit:
    return Unit(
        name=template["name"],
        max_hp=template["max_hp"],
        attack=template["attack"],
        defense=template["defense"],
        crit=template["crit"],
        speed=template["speed"],
    )


def run_prematch_shop(gold: int, team: Team) -> int:
    print("\n=== Pre-Match Shop ===")
    while True:
        print(f"Gold: {gold} | Units: {len(team.units)}/{MAX_UNITS}")
        for idx, unit in enumerate(UNIT_CATALOG, start=1):
            print(
                f"{idx}) {unit['name']} - Cost {unit['cost']} | "
                f"HP {unit['max_hp']} ATK {unit['attack']} DEF {unit['defense']} "
                f"CRIT {int(unit['crit'] * 100)}% SPD {unit['speed']}"
            )
        print("D) Done")

        if len(team.units) >= MAX_UNITS:
            print("Max units reached.")
            return gold

        choice = input("Buy a unit (1-4) or D to finish: ").strip().lower()
        if choice == "d":
            return gold
        if not choice.isdigit() or not (1 <= int(choice) <= len(UNIT_CATALOG)):
            print("Invalid choice.")
            continue

        pick = UNIT_CATALOG[int(choice) - 1]
        if gold < pick["cost"]:
            print("Not enough gold.")
            continue

        team.units.append(create_unit(pick))
        gold -= pick["cost"]


def run_upgrade_shop(gold: int, weapon: Weapon, owner: str) -> int:
    print(f"\n=== Upgrade Shop ({owner}) ===")
    while True:
        print(
            f"Gold: {gold} | Weapon: DMG+{weapon.damage_bonus} "
            f"CRIT+{int(weapon.crit_bonus * 100)}% SPD+{weapon.speed_bonus}"
        )
        for idx, upgrade in enumerate(UPGRADES, start=1):
            print(f"{idx}) {upgrade['label']} - Cost {upgrade['cost']}")
        print("D) Done")

        choice = input("Choose upgrade (1-3) or D to finish: ").strip().lower()
        if choice == "d":
            return gold
        if not choice.isdigit() or not (1 <= int(choice) <= len(UPGRADES)):
            print("Invalid choice.")
            continue

        upgrade = UPGRADES[int(choice) - 1]
        if gold < upgrade["cost"]:
            print("Not enough gold.")
            continue

        gold -= upgrade["cost"]
        if upgrade["key"] == "damage":
            weapon.damage_bonus += upgrade["value"]
        elif upgrade["key"] == "crit":
            weapon.crit_bonus = min(0.75, weapon.crit_bonus + upgrade["value"])
        elif upgrade["key"] == "speed":
            weapon.speed_bonus += upgrade["value"]


def ai_buy_units(gold: int, team: Team) -> int:
    choices = UNIT_CATALOG[:]
    while gold >= min(unit["cost"] for unit in choices) and len(team.units) < MAX_UNITS:
        pick = random.choice(choices)
        if pick["cost"] > gold:
            continue
        team.units.append(create_unit(pick))
        gold -= pick["cost"]
    return gold


def ai_upgrade_weapon(gold: int, weapon: Weapon) -> int:
    affordable = [u for u in UPGRADES if u["cost"] <= gold]
    if not affordable:
        return gold
    upgrade = random.choice(affordable)
    gold -= upgrade["cost"]
    if upgrade["key"] == "damage":
        weapon.damage_bonus += upgrade["value"]
    elif upgrade["key"] == "crit":
        weapon.crit_bonus = min(0.75, weapon.crit_bonus + upgrade["value"])
    elif upgrade["key"] == "speed":
        weapon.speed_bonus += upgrade["value"]
    return gold


def fight_round(player: Team, enemy: Team, round_num: int) -> str:
    print(f"\n=== Round {round_num} ===")
    fighters = player.alive_units() + enemy.alive_units()
    fighters.sort(key=lambda unit: unit.effective_speed(), reverse=True)

    for attacker in fighters:
        if not attacker.is_alive():
            continue
        targets = enemy.alive_units() if attacker in player.units else player.alive_units()
        if not targets:
            break
        target = random.choice(targets)
        damage = attacker.effective_attack()
        if random.random() < attacker.effective_crit():
            damage = int(damage * 1.8)
            crit_text = " CRIT!"
        else:
            crit_text = ""
        dealt = target.take_hit(damage)
        print(f"{attacker.name} hits {target.name} for {dealt}.{crit_text}")

    player_alive = len(player.alive_units())
    enemy_alive = len(enemy.alive_units())

    if enemy_alive == 0 and player_alive == 0:
        return "draw"
    if enemy_alive == 0:
        return "player"
    if player_alive == 0:
        return "enemy"
    return "continue"


def display_team(team: Team) -> None:
    print(f"\n{team.name} team:")
    for unit in team.units:
        status = "ALIVE" if unit.is_alive() else "DEAD"
        print(
            f"- {unit.name}: HP {unit.hp}/{unit.max_hp} "
            f"ATK {unit.attack} DEF {unit.defense} CRIT {int(unit.crit * 100)}% "
            f"SPD {unit.speed} [{status}]"
        )


def main() -> None:
    random.seed()
    print("1v1 Battle Arena\n")

    player_weapon = Weapon()
    enemy_weapon = Weapon()

    player_team = Team("Player", [create_hero("Hero", player_weapon)])
    enemy_team = Team("Enemy", [create_hero("Warlord", enemy_weapon)])

    player_gold = START_GOLD
    enemy_gold = START_GOLD

    player_gold = run_prematch_shop(player_gold, player_team)
    enemy_gold = ai_buy_units(enemy_gold, enemy_team)

    round_num = 1
    while True:
        result = fight_round(player_team, enemy_team, round_num)
        display_team(player_team)
        display_team(enemy_team)

        if result == "player":
            print("\nYou win the match!")
            break
        if result == "enemy":
            print("\nEnemy wins the match!")
            break
        if result == "draw":
            print("\nBoth teams wiped out. It's a draw!")
            break

        player_gold += ROUND_INCOME + 2
        enemy_gold += ROUND_INCOME + 2
        player_gold = run_upgrade_shop(player_gold, player_weapon, "Player")
        enemy_gold = ai_upgrade_weapon(enemy_gold, enemy_weapon)

        round_num += 1

    print("\nGame over.")


if __name__ == "__main__":
    main()
