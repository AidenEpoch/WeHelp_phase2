import json
import mysql.connector
import re
con = mysql.connector.connect(
    user = "root",
    password = "12345",
    host = "localhost",
    database = "phase2"
)
cursor = con.cursor()
with open("data/taipei-attractions.json", mode="r", encoding="utf-8") as file:
    data = json.load(file)
    host_url = data["img_host"]
    for item in data["list"]:
        attraction_id = item.get("_id") or item.get("id")
        name = item.get("stitle") or item.get("name")
        category = item.get("CAT") or item.get("category")
        description = item.get("xbody") or item.get("description")
        address = item.get("address")
        transport = item.get("info") or item.get("direction")
        mrt = item.get("MRT") or item.get("mrt")
        
        lat = float(item["latitude"]) if item.get("latitude") else None
        lng = float(item["longitude"]) if item.get("longitude") else None

        sql_attraction = """
            INSERT INTO attractions (id, name, category, description, address, transport, mrt, lat, lng)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_attraction, [attraction_id, name, category, description, address, transport, mrt, lat, lng])

        file_string = item.get("file") or item.get("imgurls") or ""
        
        image_urls = re.findall(r'https?://[^\s]+\.(?:jpg|JPG|jpeg|JPEG|png|PNG)', file_string)

        if not image_urls:
            image_urls = re.findall(r'/imgs/[^\s/]+\.(?:jpg|JPG|jpeg|JPEG|png|PNG)', file_string)

        sql_image = "INSERT INTO attraction_image (attraction_id, url) VALUES (%s, %s)"
        for url in image_urls:
            url = host_url + url
            cursor.execute(sql_image, [attraction_id, url])
con.commit()
print("已經將所有資料都儲存好了")
cursor.close()
con.close()
            