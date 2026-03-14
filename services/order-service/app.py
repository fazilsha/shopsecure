CARTS  = {}

PRODUCTS = {
    "p001": {"name":"Wireless Headphones","price":79.99,"stock":150},
    "p002": {"name":"Running Shoes",      "price":89.99,"stock":75},
    "p003": {"name":"Python Book",        "price":34.99,"stock":200},
}

def resp(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "X-Content-Type-Options": "nosniff",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body)
    }


def get_user(event):
    return (event.get("requestContext", {})
                 .get("authorizer", {})
                 .get("user_id", "demo-user"))

def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return resp(200, {})
    method  = event.get("httpMethod", "")
    path    = event.get("path", "")
    pp      = event.get("pathParameters") or {}
    user_id = get_user(event)
    try:
        body = json.loads(event.get("body") or "{}")
    except:
        return resp(400, {"error": "Bad JSON"})

    if method == "GET" and path == "/orders/cart":
        cart  = CARTS.get(user_id, [])
        total = sum(i["price"] * i["qty"] for i in cart)
        return resp(200, {"items": cart, "total": round(total, 2)})

    if method == "POST" and path == "/orders/cart":
        pid = body.get("product_id")
        qty = body.get("quantity", 1)
        if not pid: return resp(400, {"error": "product_id required"})
        if not isinstance(qty, int) or qty < 1 or qty > 99:
            return resp(400, {"error": "Qty must be 1-99"})
        p = PRODUCTS.get(pid)
        if not p: return resp(404, {"error": "Product not found"})
        cart = CARTS.setdefault(user_id, [])
        ex = next((i for i in cart if i["product_id"] == pid), None)
        if ex: ex["qty"] += qty
        else:  cart.append({"product_id":pid,"name":p["name"],
                             "price":p["price"],"qty":qty})
        total = sum(i["price"] * i["qty"] for i in cart)
        return resp(200, {"cart_total": round(total, 2)})

    if method == "POST" and path == "/orders/checkout":
        cart = CARTS.get(user_id, [])
        if not cart: return resp(400, {"error": "Cart is empty"})
        if not body.get("shipping_address"):
            return resp(400, {"error": "Shipping address required"})
        sub  = sum(i["price"] * i["qty"] for i in cart)
        tax  = sub * 0.18
        ship = 0 if sub > 500 else 49
        oid  = "ORD-" + uuid.uuid4().hex[:8].upper()
        ORDERS[oid] = {
            "id": oid, "user_id": user_id, "items": cart.copy(),
            "total": round(sub + tax + ship, 2),
            "address": body["shipping_address"],
            "status": "confirmed",
            "created": datetime.utcnow().isoformat()
        }
        CARTS[user_id] = []
        return resp(201, {"order_id": oid,
                          "total": round(sub + tax + ship, 2)})

    if method == "GET" and pp.get("id"):
        order = ORDERS.get(pp["id"])
        if not order: return resp(404, {"error": "Order not found"})
        # SECURITY: users can only see their OWN orders
        if order["user_id"] != user_id:
            return resp(403, {"error": "Access denied"})
        return resp(200, order)

    return resp(404, {"error": "Route not found"})
