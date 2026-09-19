from fastapi import *
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import http   #這個跟tappay有關
import httpx  #這個跟tappay有關
from datetime import datetime  #為了生成 orderNumber
app=FastAPI()


# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")




# =================API pages========================

import mysql.connector
from mysql.connector import pooling
from typing import Optional
from fastapi.responses import JSONResponse
from fastapi import Request
import json
import jwt
from datetime import datetime, timedelta, timezone

import hashlib
import secrets

db_config ={
	"user" : "root",
	"password" : "12345",
	"host" : "localhost",
	"database" : "phase2"
}

db_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    **db_config
)


@app.get("/member")
async def member():
    return FileResponse("./static/member.html", media_type="text/html")




@app.get("/api/categories")
async def getCategories():
    con = None
    cursor = None
    try:
        con = db_pool.get_connection()
        cursor = con.cursor()
        cursor.execute("SELECT DISTINCT category FROM attractions WHERE category IS NOT NULL AND category != ''")
        rows = cursor.fetchall()
        categories = [row[0] for row in rows]
        return {"data": categories}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )
    finally:
        if cursor:
            cursor.close()
        if con and con.is_connected():
            con.close()
            

@app.get("/api/mrts")
async def getMrts():
    conn = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT mrt, COUNT(id) as attraction_count 
            FROM attractions 
            WHERE mrt IS NOT NULL AND mrt != '' 
            GROUP BY mrt 
            ORDER BY attraction_count DESC
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        mrts = [row[0] for row in rows]

        return {"data": mrts}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def format_attraction(row, images):
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "address": row["address"],
        "transport": row["transport"],
        "mrt": row["mrt"],
        "lat": row["lat"],
        "lng": row["lng"],
        "images": images
    }


@app.get("/api/attractions")
async def getAttractions(page: int = Query(0, ge=0),keyword: Optional[str] = None,category: Optional[str] = None):
    conn = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        limit = 8
        offset = page * limit

        conditions = []
        params = []

        if category:
            conditions.append("category = %s")
            params.append(category)

        if keyword:
            conditions.append("(name LIKE %s OR mrt = %s)")
            params.append(f"%{keyword}%")
            params.append(keyword)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql_attractions = f"""
            SELECT id, name, category, description, address, transport, mrt, lat, lng
            FROM attractions
            {where_clause}
            ORDER BY id ASC
            LIMIT %s OFFSET %s
        """
        params.extend([limit + 1, offset])
        cursor.execute(sql_attractions, params)
        rows = cursor.fetchall()

        next_page = None
        if len(rows) > limit:
            next_page = page + 1
            rows = rows[:limit] 

        result_data = []
        for row in rows:
            cursor.execute("SELECT url FROM attraction_image WHERE attraction_id = %s ORDER BY id ASC", (row["id"],))
            image_rows = cursor.fetchall()
            images = [img["url"] for img in image_rows]

            result_data.append(format_attraction(row, images))

        return {"nextPage": next_page, "data": result_data}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

            
@app.post("/api/user")
async def addNewMember(request: Request):
    body = await request.json()
    name = body["name"]
    email = body["email"]
    password = body["password"]
    conn = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
        SELECT email FROM members WHERE email = %s               
        """, (email,))
        result = cursor.fetchone()
        if result != None:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": f"註冊失敗，重複的email"}
        )

        cursor.execute("""
            INSERT INTO members(name, email, password)VALUES(%s, %s, %s)
        """, (name, email, password))
        conn.commit()
        return JSONResponse(
            status_code = 200,
            content = {"ok": True}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.get("/api/user/auth")
async def getMemberInformation(request: Request):
    auth = request.headers.get("Authorization")
    #print(f"auth:{auth.split(" ")[1]}")
    token = auth.split(" ")[1]
    try:
        result = jwt.decode(token, "secret", algorithms=["HS256"])
        member_id = result["id"]
        member_name = result["name"]
        member_email = result["email"]
        return JSONResponse(
            status_code = 200,
            content = {"data":{"id": member_id, "name": member_name, "email": member_email}}
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return JSONResponse(status_code=200, content={"data": None})
    
    

@app.put("/api/user/auth")
async def signIn(request: Request):
    body = await request.json()
    email = body["email"]
    password = body["password"]
    conn = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
        SELECT * FROM members WHERE email = %s AND password = %s            
        """, (email, password,))
        result = cursor.fetchone()
        if result == None:
            return JSONResponse(
                status_code = 400,
                content = {"error": True, "message": "信箱或密碼錯誤"}
            )
        else:
            now = datetime.now(timezone.utc)
            payload = {
                "id": result["id"],
                "name": result["name"],
                "email": result["email"],
                "iat": now,
                "exp": now + timedelta(days=7)
            }
            token = jwt.encode(payload, "secret", algorithm="HS256")   #聽說實務上會將secret key藏在某個pem當中，然後pem檔不能讓前端看到
            return JSONResponse(
                status_code = 200,
                content = {"token": token}
            )

    except Exception as e:
        return JSONResponse(
            status_code = 500,
            content = {"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()



@app.get("/api/attraction/{attraction_id}")
async def getAttractionById(attraction_id: int):
    conn = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, category, description, address, transport, mrt, lat, lng
            FROM attractions
            WHERE id = %s
        """, (attraction_id,))
        row = cursor.fetchone()

        if not row:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "景點編號不正確"}
            )

        cursor.execute("SELECT url FROM attraction_image WHERE attraction_id = %s ORDER BY id ASC", (attraction_id,))
        image_rows = cursor.fetchall()
        images = [img["url"] for img in image_rows]

        return {"data": format_attraction(row, images)}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/api/booking")
async def getOrder(request: Request):
    token = request.headers["Authorization"].split(" ")[1]
    if token == None:
        return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統"})
    try:
        result = jwt.decode(token, "secret", algorithms=["HS256"])
        member_id = result["id"]
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, a.id as a_id, a.name, a.address
            FROM booking b
            JOIN attractions a ON b.attraction_id = a.id
            WHERE b.member_id = %s
        """, (member_id,))
        result = cursor.fetchone()
        if not result:
            return JSONResponse(status_code=200, content={"data": None})
        cursor.execute("SELECT url FROM attraction_image WHERE attraction_id = %s LIMIT 1", (result["attraction_id"],))
        img = cursor.fetchone()
        image_url = img["url"] if img else ""
        return JSONResponse(
            status_code = 200,
            content = {"data": {"attraction": {
                                "id": result["attraction_id"],
                                "name": result["name"],
                                "address": result["address"],
                                "image": image_url
                                }, 
                                "date": str(result["date"]), 
                                "time": result["time"], 
                                "price": result["price"]}}
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統"})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.post("/api/booking")
async def setSchedule(request: Request):
    token = request.headers["Authorization"].split(" ")[1]
    try:
        result = jwt.decode(token, "secret", algorithms=["HS256"])
        member_id = result["id"]
        member_name = result["name"]
        member_email = result["email"]
        body = await request.json()
        attraction_id = body["attractionId"]
        date = body["date"]
        time = body["time"]
        price = body["price"]
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM booking WHERE member_id = %s", (member_id,))
        cursor.execute("""
            INSERT INTO booking(member_id, attraction_id, date, time, price)VALUES(%s, %s, %s, %s, %s)
        """, (member_id, attraction_id, date, time, price,))
        conn.commit()
        print("已經建立好預定資訊了")
        return JSONResponse(
            status_code = 200,
            content = {"ok": True}
        )
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統"})

    except Exception as e:
        return JSONResponse(
            status_code = 400,
            content = {"error": True, "message": f"{str(e)}"}
        )
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.delete("/api/booking")
async def deleteSchedule(request: Request):
    token = request.headers["Authorization"].split(" ")[1]
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        member_id = payload["id"]
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM booking WHERE member_id = %s", (member_id,))
        conn.commit()
        return JSONResponse(
            status_code = 200,
            content = {"ok": True}
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統"})
    
    except Exception as e:
        return JSONResponse(
            status_code = 403,
            content = {"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.post("/api/orders")
async def createOrder(request: Request):
    auth = request.headers.get("Authorization")
    partnerkey = request.headers.get("x-api-key")
    if auth == None:
        return JSONResponse(
            status_code = 403,
            content = {"error": True, "message": "未登入系統"}
        )
    token = auth.split(" ")[1]
    orderNumber = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""SELECT order_number, status FROM orders WHERE order_number = %s;""", (orderNumber,))
    row = cursor.fetchone()
    print(f"row = {row}")
    if row != None:
        print(f"row = {row}")
        if row["status"] == 1:
            return JSONResponse(
                status_code = 403,
                content = {"error": True, "message": "此訂單已經付款，勿重複付款"}
            )
    else:
        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
            body = await request.json()
            name = payload["name"]
            email = payload["email"]
            id = payload["id"]
            phoneNumber = body["phoneNumber"]
            prime = body["prime"]
            details = body["details"]
            cursor.execute("""SELECT price, attraction_id, date, time FROM booking WHERE member_id = %s;""", (id,))
            row = cursor.fetchone()
            price = int(row["price"])
            attraction_id = int(row["attraction_id"])
            date = row["date"]
            time = row["time"]

            ###########   彭彭說，在送出 tappay api 之前，先建立訂單的 datum，這樣到時候無論是成功的或是失敗的訂單都能在 database 中找到 ###############
            
            cursor.execute("""INSERT INTO orders(member_email, member_phone, order_number, attraction_id, date, time, price)VALUES(%s, %s, %s, %s, %s, %s, %s);""", (email, phoneNumber, orderNumber, attraction_id, date, time, price,))
            conn.commit()
            print(f"成功建立訂單")
            ####################################### 

            ###########   以下是向 TapPay發起付款的部分    #################

            tappay_url = "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": partnerkey
            }

            tappay_body = {
                "prime": prime,
                "partner_key": partnerkey,
                "merchant_id": "epoch1217_CTBC",
                "details": details,
                "amount": price,
                "cardholder": {
                    "phone_number": phoneNumber,
                    "name": name,
                    "email": email
                },
                "remember": False
            }

            async with httpx.AsyncClient() as client:
                tappay_response = await client.post(
                    tappay_url,
                    json=tappay_body,
                    headers=headers
                )
                tappay_result = tappay_response.json()
            print(f"成功呼叫")
            print(f"status = {tappay_result['status']}")
            print(f"TapPay 回傳：{tappay_result}")
            if tappay_result["status"] != 0:
                return JSONResponse(
                    status_code=200,
                    content={"data":{
                        "number": orderNumber,
                        "payment":{
                            "status": 0,
                            "message": "付款失敗"
                        }
                    }}
                )
            ##############################################################
            cursor.execute("""UPDATE orders SET status = 1 WHERE order_number = %s;""", (orderNumber,))
            conn.commit()
            print(f"付款成功了喔~~~~~")
            return JSONResponse(
                status_code = 200,
                content = {"data":{
                    "number": orderNumber,
                    "payment":{
                        "status": 0,
                        "message": "付款成功"
                    }
                }}
            )
        except Exception as e:
            return JSONResponse(
                status_code = 400,
                content = {"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
            )
    if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/api/order/{orderNumber}")            
async def getOrder(request:Request):
    token = request.headers["Authorization"].split(" ")[1]
    if token == None:
        return JSONResponse(
            status_code = 403,
            content = {"error": True, "message": "未登入系統"}
        )
    try:
        payload = jwt.decode(token, "secret", algorithms = ["HS256"])
        name = payload["name"]
        email = payload["email"]
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""SELECT * FROM orders WHERE member_email = %s;""", (email,))
        row = cursor.fetchone()
        print(row)
        return JSONResponse(
            status_code = 200,
            content = {"data": {
                                "number": "20210425121135",
                                "price": 2000,
                                "trip": {
                                "attraction": {
                                    "id": 10,
                                    "name": "平安鐘",
                                    "address": "臺北市大安區忠孝東路 4 段",
                                    "image": "https://yourdomain.com/images/attraction/10.jpg"
                                },
                                "date": "2022-01-31",
                                "time": "afternoon"
                                },
                                "contact": {
                                "name": "彭彭彭",
                                "email": "ply@ply.com",
                                "phone": "0912345678"
                                },
                                "status": 1
                        }

            }
        )
    except Exception as e:
        return JSONResponse(
            status_code = 403,
            content = {"error": True, "message": f"伺服器內部錯誤: {str(e)}"}
        )


####################### 以下是 fastMCP 的部分 ####################

from fastmcp import FastMCP, Context
from typing import Optional

@app.get("/api/token")
async def getToken(request:Request):
     token = request.headers["Authorization"].split(" ")[1]
     if token == None:
        return JSONResponse(
            status_code = 403,
            content = {"error": True, "message": "未登入系統"}
        )
     result = jwt.decode(token, "secret", algorithms=["HS256"])
     name = result["name"]
     email = result["email"]
     random_bytes = secrets.token_bytes(32)
     access_token = hashlib.sha256(random_bytes).hexdigest()
     conn = db_pool.get_connection()
     cursor = conn.cursor(dictionary=True)
     cursor.execute("""UPDATE members SET token = %s WHERE name = %s AND email = %s""", (access_token,name, email,))
     conn.commit()
     cursor.close()
     conn.close()

     return JSONResponse(
         status_code = 200,
         content = {"ok": True, "token": access_token}
     )


mcp = FastMCP("台北一日遊")

@mcp.tool()
def search(keyword: str) -> dict:
    """透過關鍵字和捷運站名搜尋台北市一日旅遊的景點"""
    conn = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, description 
            FROM attractions 
            WHERE name LIKE %s OR mrt = %s
            LIMIT 10
        """, (f"%{keyword}%", keyword))
        rows = cursor.fetchall()
        return {"data": list(rows)}
    except Exception as e:
        return {"error": True}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@mcp.tool()
def add_to_cart(
    attractionId: int,
    date: str,
    time: str,
    price: int,
    token: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    根據景點編號、日期、時間、價格，預定一個景點導覽行程。
    
    參數說明：
    - time: 必須為 "morning" 或 "afternoon"
    - price: "morning" 固定為 2000，"afternoon" 固定為 2500
    """
    conn = None
    try:
        incoming_mcp_token = token

        # 1. 若參數沒有拿到 token，嘗試從 Context Header 擷取
        if not incoming_mcp_token and ctx and ctx.request_context:
            meta = getattr(ctx.request_context, "meta", None)
            if meta:
                headers = getattr(meta, "headers", {}) or {}
                if isinstance(headers, dict):
                    auth_header = headers.get("authorization", "") or headers.get("Authorization", "")
                else:
                    auth_header = getattr(headers, "authorization", "") or getattr(headers, "Authorization", "")

                if auth_header.startswith("Bearer "):
                    incoming_mcp_token = auth_header.split(" ")[1]

        # 2. 如果兩種方式都拿不到 Token
        if not incoming_mcp_token:
            return {"error": True, "message": "未提供 Bearer Token，請確認 MCP 設定檔 (mcp.json) 包含 Authorization Header"}

        # 3. 自動校正時間與價格
        if time == "morning":
            price = 2000
        elif time == "afternoon":
            price = 2500
        else:
            return {"error": True, "message": "時間格式不正確"}

        # 4. 比對資料庫 members.token 欄位
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM members WHERE token = %s", (incoming_mcp_token,))
        member = cursor.fetchone()

        if not member:
            return {"error": True, "message": "Token 驗證失敗，無效的金鑰"}

        member_id = member["id"]

        # 5. 刪除舊預訂並新增新預訂
        cursor.execute("DELETE FROM booking WHERE member_id = %s", (member_id,))
        cursor.execute("""
            INSERT INTO booking (member_id, attraction_id, date, time, price)
            VALUES (%s, %s, %s, %s, %s)
        """, (member_id, attractionId, date, time, price))
        conn.commit()

        return {
            "ok": True,
            "message": "台北導覽行程，預定成功，請到 http://3.235.200.209:8000/booking 完成付款。"
        }

    except Exception as e:
        print(f"預訂失敗: {str(e)}")
        return {"error": True, "message": str(e)}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


mcp_app = mcp.http_app(path='/')
app.router.lifespan_context = mcp_app.lifespan


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

app.mount("/mcp", mcp_app)

