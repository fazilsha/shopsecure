import json, os, hashlib, hmac, base64, time
#nothing
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-change-in-prod")
USERS_DB   = {}   # In production: use AWS RDS

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def create_jwt(uid, email):
    h = base64.b64encode(
            json.dumps({"alg":"HS256"}).encode()).decode()
    p = base64.b64encode(json.dumps({
            "sub":uid,"email":email,
            "exp":int(time.time())+3600}).encode()).decode()
    sig = hmac.new(
            JWT_SECRET.encode(),
            f"{h}.{p}".encode(),
            hashlib.sha256).hexdigest()
    return f"{h}.{p}.{sig}"

def verify_jwt(token):
    try:
        h, p, sig = token.split(".")
        expected = hmac.new(
            JWT_SECRET.encode(),
            f"{h}.{p}".encode(),
            hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): return None
        d = json.loads(base64.b64decode(p + "==").decode())
        return None if d["exp"] < time.time() else d
    except:
        return None

def resp(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "X-Content-Type-Options": "nosniff"
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path   = event.get("path", "")
    try:
        body = json.loads(event.get("body") or "{}")
    except:
        return resp(400, {"error": "Invalid JSON"})

    if method == "POST" and path == "/auth/register":
        email = body.get("email", "").strip().lower()
        pw    = body.get("password", "")
        name  = body.get("name", "").strip()
        if "@" not in email:
            return resp(400, {"error": "Valid email required"})
        if len(pw) < 8:
            return resp(400, {"error": "Password must be 8+ chars"})
        if email in USERS_DB:
            return resp(409, {"error": "Email already exists"})
        uid = hashlib.sha256(email.encode()).hexdigest()[:8]
        USERS_DB[email] = {"id": uid, "name": name,
                           "hash": hash_password(pw)}
        return resp(201, {"token": create_jwt(uid, email),
                          "user": {"id": uid, "email": email}})

    if method == "POST" and path == "/auth/login":
        email = body.get("email", "").strip().lower()
        user  = USERS_DB.get(email)
        if not user or user["hash"] != hash_password(
                body.get("password", "")):
            return resp(401, {"error": "Invalid credentials"})
        return resp(200, {"token": create_jwt(user["id"], email)})

    if method == "POST" and path == "/auth/validate":
        d = verify_jwt(body.get("token", ""))
        if not d: return resp(401, {"valid": False})
        return resp(200, {"valid": True, "user_id": d["sub"]})

    return resp(404, {"error": "Not found"})
