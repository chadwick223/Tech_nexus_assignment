import json
import base64
import tempfile
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .store import read_cart, update_cart, read_inventory
from .service.billing_pipeline import process_voice_billing, process_text_billing, process_image_billing

@require_http_methods(["GET"])
def pos_ui(request):
    """Renders the main POS frontend interface"""
    return render(request, 'core/pos.html')

@require_http_methods(["GET"])
def inventory_list(request):
    inventory = read_inventory()
    return JsonResponse(inventory)

@require_http_methods(["GET"])
def inventory_detail(request, item_id):
    inventory = read_inventory()
    item = inventory.get(item_id)
    if not item:
        return JsonResponse({"error": "Item not found in inventory"}, status=404)
    return JsonResponse({item_id: item})

@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def cart_detail(request):
    if request.method == "GET":
        cart = read_cart()
        inventory = read_inventory()
        grand_total = 0.0
        
        for item_id, item_data in cart["items"].items():
            inv_item = inventory.get(item_id, {})
            price = inv_item.get("price", 0.0)
            item_data["price"] = price
            item_data["total_price"] = item_data["quantity"] * price
            grand_total += item_data["total_price"]
            
        cart["grand_total"] = grand_total
        return JsonResponse(cart)
    
    elif request.method == "DELETE":
        def clear_items(cart):
            cart["items"] = {}
            
        updated_cart = update_cart(clear_items)
        return JsonResponse(updated_cart)

@csrf_exempt
@require_http_methods(["GET", "POST", "PATCH", "DELETE"])
def cart_item(request, item_id):
    if request.method == "GET":
        cart = read_cart()
        item = cart["items"].get(item_id)
        if item is None:
            return JsonResponse({"error": "Item not found"}, status=404)
            
        inventory = read_inventory()
        inv_item = inventory.get(item_id, {})
        price = inv_item.get("price", 0.0)
        item["price"] = price
        item["total_price"] = item["quantity"] * price
        
        return JsonResponse({item_id: item})

    if request.method in ["POST", "PATCH"]:
        try:
            body = json.loads(request.body)
            quantity = int(body.get("quantity", 0))
            if quantity < 0:
                return JsonResponse({"error": "Quantity cannot be negative"}, status=400)
        except (json.JSONDecodeError, ValueError, TypeError):
            return JsonResponse({"error": "Invalid payload, 'quantity' must be an integer"}, status=400)

    if request.method == "POST":
        def add_item(cart):
            inventory = read_inventory()
            inv_item = inventory.get(item_id, {})
            price = inv_item.get("price", 0.0)

            if item_id in cart["items"]:
                cart["items"][item_id]["quantity"] += quantity
            else:
                cart["items"][item_id] = {"quantity": quantity}
                
            cart["items"][item_id]["price"] = price
            cart["items"][item_id]["total_price"] = cart["items"][item_id]["quantity"] * price
        
        updated_cart = update_cart(add_item)
        return JsonResponse(updated_cart)

    elif request.method == "PATCH":
        def update_item(cart):
            inventory = read_inventory()
            inv_item = inventory.get(item_id, {})
            price = inv_item.get("price", 0.0)

            cart["items"][item_id] = {
                "quantity": quantity,
                "price": price,
                "total_price": quantity * price
            }
            
        updated_cart = update_cart(update_item)
        return JsonResponse(updated_cart)

    elif request.method == "DELETE":
        item_deleted = [False]
        def remove_item(cart):
            if item_id in cart["items"]:
                del cart["items"][item_id]
                item_deleted[0] = True
                
        updated_cart = update_cart(remove_item)
        if not item_deleted[0]:
            return JsonResponse({"error": "Item not found"}, status=404)
            
        return JsonResponse(updated_cart)

@csrf_exempt
@require_http_methods(["POST"])
def process_command(request):
    """
    Unified endpoint to handle voice, image, and text commands.
    It routes to the correct pipeline service, then updates the cart.
    """
    verification_result = None
    
    # 1. SMART ROUTING
    if request.FILES.get('audio'):
        # Handle Audio
        audio_file = request.FILES['audio']
        
        # Save uploaded file to a temporary file for pydub to process
        ext = os.path.splitext(audio_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_path = temp_audio.name
            
        try:
            verification_result = process_voice_billing(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    elif request.FILES.get('image'):
        # Handle Image
        image_file = request.FILES['image']
        text_input = request.POST.get('text', None)
        mime_type = image_file.content_type
        
        # Convert image to base64 for Gemini
        image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
        verification_result = process_image_billing(image_b64=image_b64, mime_type=mime_type, text=text_input)
        
    else:
        # Handle Text (could be form-data or JSON)
        text_input = request.POST.get('text')
        if not text_input and request.content_type == 'application/json':
            try:
                body = json.loads(request.body)
                text_input = body.get("text")
            except json.JSONDecodeError:
                pass
                
        if text_input:
            verification_result = process_text_billing(text_input)
        else:
            return JsonResponse({"error": "No valid audio, image, or text input provided."}, status=400)

    # 2. CHECK VERIFICATION RESULT
    if not verification_result or verification_result.get("status") == "error":
        return JsonResponse(verification_result or {"status": "error", "message": "Unknown error"}, status=400)

    data = verification_result["data"]
    action = data["action"]
    items = data["items"]

    # 3. APPLY TO CART
    def apply_llm_action(cart):
        if action == "clear":
            cart["items"] = {}
            return

        inventory = read_inventory()

        for item in items:
            name = item["item_name"].replace(" ", "_").lower()  # Normalize keys
            qty = item["quantity"]
            
            inv_item = inventory.get(name, {})
            price = inv_item.get("price", 0.0)
            
            if action == "add":
                if name in cart["items"]:
                    cart["items"][name]["quantity"] += qty
                else:
                    cart["items"][name] = {"quantity": qty}
                    
                cart["items"][name]["price"] = price
                cart["items"][name]["total_price"] = cart["items"][name]["quantity"] * price
            
            elif action == "remove":
                if name in cart["items"]:
                    cart["items"][name]["quantity"] = max(0, cart["items"][name]["quantity"] - qty)
                    if cart["items"][name]["quantity"] == 0:
                        del cart["items"][name]
                    else:
                        cart["items"][name]["price"] = price
                        cart["items"][name]["total_price"] = cart["items"][name]["quantity"] * price
                        
            elif action == "set":
                cart["items"][name] = {
                    "quantity": qty,
                    "price": price,
                    "total_price": qty * price
                }

    updated_cart = update_cart(apply_llm_action)
    
    # Return both the LLM's interpretation and the new cart state
    return JsonResponse({
        "interpreted_action": action,
        "interpreted_items": items,
        "cart": updated_cart
    })
