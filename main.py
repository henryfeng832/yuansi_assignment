import streamlit as st
import mysql.connector
from mysql.connector import Error
import uuid
from datetime import datetime, timedelta

# 配置页面
st.set_page_config(page_title="登录系统", layout="centered")

# 数据库连接函数
def get_database_connection():
    try:
        connection = mysql.connector.connect(
            host='dbconn.sealoshzh.site',
            port='36452',
            database='yuansi_assignment',
            user='root',
            password='t7d4j8m9'
        )
        return connection
    except Error as e:
        st.error(f"数据库连接错误：{e}")
        return None

# 创建新会话
def create_session(username):
    session_id = str(uuid.uuid4())
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            # 删除该用户的旧会话
            cursor.execute("DELETE FROM sessions WHERE username = %s", (username,))
            # 创建新会话，设置1小时后过期
            expire_time = datetime.now() + timedelta(hours=1)
            cursor.execute("""
                INSERT INTO sessions (session_id, username, expire_time) 
                VALUES (%s, %s, %s)
            """, (session_id, username, expire_time))
            connection.commit()
            return session_id
        except Error as e:
            st.error(f"创建会话错误：{e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

# 验证会话是否有效
def verify_session(session_id):
    if not session_id:
        return None
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT username FROM sessions 
                WHERE session_id = %s AND expire_time > NOW()
            """, (session_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            st.error(f"验证会话错误：{e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

# 验证用户登录
def verify_login(username, password):
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                         (username, password))
            user = cursor.fetchone()
            return user is not None
        except Error as e:
            st.error(f"查询错误：{e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

# 删除会话
def delete_session(session_id):
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
            connection.commit()
        except Error as e:
            st.error(f"删除会话错误：{e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
def main():
    # 检查会话状态
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = None
    
    # 验证现有会话
    username = verify_session(st.session_state['session_id'])
    
    if not username:
        st.title("系统登录页")
        # 显示登录表单
        with st.form("login_form"):
            input_username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submit_button = st.form_submit_button("登录")
            
            if submit_button:
                if input_username.strip() == "" or password.strip() == "":
                    st.warning("请输入用户名和密码")
                else:
                    if verify_login(input_username, password):
                        # 创建新会话
                        session_id = create_session(input_username)
                        if session_id:
                            st.session_state['session_id'] = session_id
                            st.success("登录成功！")
                            st.rerun()
                    else:
                        st.error("用户名或密码错误")
    else:
        st.title("数据分析页")
        st.write(f"### 欢迎回来，{username}！")
        st.write("您已成功登录系统。")
        
        # 退出登录按钮
        if st.button("退出登录"):
            delete_session(st.session_state['session_id'])
            st.session_state['session_id'] = None
            st.rerun()

if __name__ == "__main__":
    main()

