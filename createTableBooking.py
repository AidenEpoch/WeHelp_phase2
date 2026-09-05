import mysql.connector

con = mysql.connector.connect(
    user = "root",
    password = "12345",
    host = "localhost",
    database = "phase2"
)

cursor = con.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS booking(id INT PRIMARY KEY AUTO_INCREMENT, member_id INT, attraction_id INT, date DATE, time VARCHAR(20), price INT);""")
con.commit()
print("已經創建好bookingTable了")
cursor.close()
con.close()