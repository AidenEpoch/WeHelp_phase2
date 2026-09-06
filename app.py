from fastapi import *
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
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


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

