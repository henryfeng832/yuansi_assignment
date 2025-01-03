import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host='dbconn.sealoshzh.site',      # 数据库地址
        port='36452',               # 端口号
        database='yuansi_assignment', # 数据库名
        user='root',             # 用户名
        password='t7d4j8m9'  # 密码
    )

    if connection.is_connected():
        db_info = connection.get_server_info()
        print("已成功连接到MySQL数据库，服务器版本:", db_info)
        
        # 获取数据库游标
        cursor = connection.cursor()
        
        # 执行简单的查询来测试连接
        cursor.execute("SELECT DATABASE();")
        database = cursor.fetchone()
        print("当前数据库:", database[0])

except Error as e:
    print("连接MySQL数据库时出错：", e)

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL连接已关闭")