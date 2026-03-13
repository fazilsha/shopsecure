import json, uuid

PRODUCTS = {
    "p001": {"id":"p001","name":"Wireless Headphones",
             "price":79.99,"category":"Electronics","stock":150},
    "p002": {"id":"p002","name":"Running Shoes",
             "price":89.99,"category":"Footwear","stock":75},
    "p003": {"id":"p003","name":"Python Book",
             "price":34.99,"category":"Books","stock":200},
}

def resp(code, body):
    return {"statusCode": code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}

def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path   = event.get("path", "")
    params = event.get("queryStringParameters") or {}
    pp     = event.get("pathParameters") or {}

    if method == "GET" and path == "/products":
        items = list(PRODUCTS.values())
        cat = params.get("category")
        if cat:
            items = [p for p in items
                     if p["category"].lower() == cat.lower()]
        return resp(200, {"products": items, "count": len(items)})

    if method == "GET" and pp.get("id"):
        p = PRODUCTS.get(pp["id"])
        return resp(200, p) if p else resp(404, {"error":"Not found"})

    if method == "POST" and path == "/products":
        try:
            body = json.loads(event.get("body") or "{}")
        except:
            return resp(400, {"error": "Bad JSON"})
        for f in ["name", "price", "category", "stock"]:
            if f not in body:
                return resp(400, {"error": f"Missing: {f}"})
        if float(body["price"]) <= 0:
            return resp(400, {"error": "Price must be positive"})
        pid = "p" + uuid.uuid4().hex[:6]
        PRODUCTS[pid] = {
            "id": pid,
            "name": str(body["name"])[:200],
            "price": round(float(body["price"]), 2),
            "category": str(body["category"]),
            "stock": int(body["stock"])
        }
        return resp(201, PRODUCTS[pid])

    return resp(404, {"error": "Route not found"})
