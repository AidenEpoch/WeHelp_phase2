import mysql.connector

con = mysql.connector.connect(
    user = "root",
    password = "12345",
    host = "localhost",
    database = "phase2"
)

cursor = con.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS orders(id INT PRIMARY KEY AUTO_INCREMENT, member_email VARCHAR(255), 
               member_phone VARCHAR(20), status INT DEFAULT 0, order_number VARCHAR(100), attraction_id INT, date DATE, time VARCHAR(20), price INT);""")
con.commit()
print("已經創建好order table了")
cursor.close()
con.close()