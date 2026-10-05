from thefuzz import process
from ..store import read_inventory

UNIT_CONVERSIONS = {
    "kg": {"g": 0.001, "gram": 0.001, "grams": 0.001, "kg": 1, "kilo": 1, "kilogram": 1},
    "liter": {"ml": 0.001, "milliliter": 0.001, "l": 1, "liter": 1, "litre": 1},
    "piece": {"piece": 1, "pcs": 1, "pc": 1, "item": 1, "": 1}
}

def normalize_units(qty: float, provided_unit: str, base_unit: str) -> float:
    """Converts the provided unit into the inventory's base unit if possible."""
    if not provided_unit:
        return qty # Assume default base unit if not explicitly stated
        
    provided_unit = provided_unit.lower().strip()
    if base_unit in UNIT_CONVERSIONS and provided_unit in UNIT_CONVERSIONS[base_unit]:
        return qty * UNIT_CONVERSIONS[base_unit][provided_unit]
    
    # If we can't safely convert it, we just return the original quantity
    return qty

def match_inventory_item(normalized_name: str) -> tuple:
    """
    Attempts to fuzzy match the normalized name against the inventory.
    Returns (canonical_key, base_unit) if successful (similarity >= 80%), else (None, None).
    """
    inventory = read_inventory()
    inventory_keys = list(inventory.keys())
    
    if not inventory_keys:
        return None, None
        
    best_match = process.extractOne(normalized_name, inventory_keys)
    
    if not best_match or best_match[1] < 80:
        return None, None
        
    canonical_key = best_match[0]
    base_unit = inventory[canonical_key].get("unit", "piece")
    
    return canonical_key, base_unit
