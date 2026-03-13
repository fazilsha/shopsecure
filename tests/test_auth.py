import json, sys, os
sys.path.insert(0, "services/auth-service")
import app as auth

class Ctx:
    aws_request_id = "test"

def ev(method, path, body=None):
    return {"httpMethod": method, "path": path,
            "body": json.dumps(body) if body else None}

def test_register_ok():
    auth.USERS_DB.clear()
    r = auth.lambda_handler(
        ev("POST", "/auth/register",
           {"email":"a@b.com","password":"pass1234","name":"A"}), Ctx())
    assert r["statusCode"] == 201
    assert "token" in json.loads(r["body"])

def test_weak_password_blocked():
    r = auth.lambda_handler(
        ev("POST", "/auth/register",
           {"email":"b@b.com","password":"abc","name":"B"}), Ctx())
    assert r["statusCode"] == 400

def test_user_enumeration_prevented():
    auth.USERS_DB.clear()
    auth.lambda_handler(
        ev("POST", "/auth/register",
           {"email":"r@b.com","password":"pass1234","name":"R"}), Ctx())
    r1 = auth.lambda_handler(
        ev("POST", "/auth/login",
           {"email":"r@b.com","password":"wrong"}), Ctx())
    r2 = auth.lambda_handler(
        ev("POST", "/auth/login",
           {"email":"fake@b.com","password":"wrong"}), Ctx())
    assert json.loads(r1["body"])["error"] == json.loads(r2["body"])["error"]
