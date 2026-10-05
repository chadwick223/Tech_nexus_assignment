import json
import inflect
from .inventory import match_inventory_item, normalize_units

# Initialize the inflect engine
p = inflect.engine()

def verify_billing_action(llm_response_str: str) -> dict:
    """
    Takes the JSON string returned by the LLM and validates it.
    Ensures actions and quantities are valid.
    """
    try:
        data = json.loads(llm_response_str)
    except json.JSONDecodeError:
        return {"status": "error", "message": "LLM returned invalid JSON."}

    # Defensive parsing: if data is a list (e.g. from a hallucination), wrap it.
    if isinstance(data, list):
        commands = data
    else:
        commands = data.get("commands", [])

    if not isinstance(commands, list):
        return {"status": "error", "message": "Commands must be a list."}

    valid_commands = []
    
    for cmd in commands:
        action = cmd.get("action", "add")  # Default to add if missing
        
        if action == "clear":
            valid_commands.append({"action": "clear"})
            continue
            
        if action not in ["add", "remove", "set"]:
            continue
            
        name = cmd.get("item_name")
        qty = cmd.get("quantity")
        
        if not name or not isinstance(name, str):
            continue  # Skip item with invalid name
            
        if not isinstance(qty, (int, float)) or qty < 0:
            continue  # Skip item with invalid quantity

        # Convert to lowercase and replace spaces with underscores
        normalized_name = name.lower().strip().replace(" ", "_")
        
        # Use inflect to forcibly convert plurals to singular
        # p.singular_noun returns False if the word is already singular
        singular_name = p.singular_noun(normalized_name)
        if singular_name:
            normalized_name = singular_name

        # FUZZY MATCH AGAINST INVENTORY
        canonical_key, base_unit = match_inventory_item(normalized_name)
        
        if not canonical_key:
            return {"status": "error", "message": f"Item '{name}' not found in catalogue."}
            
        provided_unit = cmd.get("unit", "")
        
        # QUANTITY CONVERSION
        final_qty = normalize_units(float(qty), provided_unit, base_unit)

        valid_commands.append({
            "action": action,
            "item_name": canonical_key,
            "quantity": final_qty,
            "unit": base_unit
        })

    return {
        "status": "success",
        "data": {
            "commands": valid_commands
        }
    }
