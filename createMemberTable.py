import mysql.connector

con = mysql.connector.connect(
    user = "root",
    password = "12345",
    host = "localhost",
    database = "phase2"
)

cursor = con.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS members(id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(300), email VARCHAR(1000), password VARCHAR(1000));""")
con.commit()
print("已經創建好memberTable了")
cursor.close()
con.close()