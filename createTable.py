import mysql.connector

con = mysql.connector.connect(
    user = "root",
    password = "12345",
    host = "localhost",
    database = "phase2"
)

cursor = con.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS attractions(id INT PRIMARY KEY, name VARCHAR(255), category VARCHAR(255), description TEXT, address TEXT, transport TEXT,
               mrt TEXT, lat DOUBLE, lng DOUBLE);""")
cursor.execute("""CREATE TABLE IF NOT EXISTS attraction_image(id INT AUTO_INCREMENT PRIMARY KEY, attraction_id INT, url TEXT, FOREIGN KEY (attraction_id) REFERENCES attractions(id) ON DELETE CASCADE);""")
con.commit()
print("已經創建好兩個table了")
cursor.close()
con.close()
