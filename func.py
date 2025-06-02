from openai import OpenAI
from config import TOKEN,AI_TOKEN,DEEP_SEEK_TOKEN,db_name,db_user,db_password,db_host
import psycopg2
def bot_respond(request,mod):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=AI_TOKEN,
    )

    completion = client.chat.completions.create(
        extra_body={},
        model=mod,
        messages=[
            {
                "role": "user",
                "content": request
            }
        ]
    )
    return completion.choices[0].message.content
def deepseek_respond(request,mod):
    client = OpenAI(
        api_key=DEEP_SEEK_TOKEN,
        base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model=mod ,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": request},
        ],
        stream=False
    )
    return response.choices[0].message.content
def save_to_db(tg_id: int, request: str = None, response: str = None, is_old: bool = False):
    """Сохраняет сообщение в базу данных"""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Получаем ID пользователя
        cur.execute("SELECT id FROM users WHERE tg_id = %s", (tg_id,))
        user_id = cur.fetchone()[0]

        if request:
            # Экранирование кавычек для SQL
            safe_request = request.replace("'", "''")
            cur.execute(
                "INSERT INTO history (user_id, request, is_old) VALUES (%s, %s, %s) RETURNING id",
                (user_id, safe_request, is_old)
            )
            request_id = cur.fetchone()[0]
            conn.commit()
            return request_id

        if response:
            safe_response = response.replace("'", "''")
            # Находим последний запрос без ответа для этого пользователя
            cur.execute(
                "SELECT id FROM history WHERE user_id = %s AND response IS NULL ORDER BY id DESC LIMIT 1",
                (user_id,)
            )
            last_request = cur.fetchone()
            if last_request:
                last_request_id = last_request[0]
                cur.execute(
                    "UPDATE history SET response = %s WHERE id = %s",
                    (safe_response, last_request_id)
                )
                conn.commit()
    except Exception as e:
        print(f"Database error in save_to_db: {e}")
        conn.rollback()
    finally:
        conn.close()
def get_db():
    """Устанавливает соединение с PostgreSQL"""
    return psycopg2.connect(
        dbname = db_name,
        user = db_user,
        password = db_password,
        host = db_host
    )
def get_chat_history(tg_id: int):
    """Возвращает историю текущего диалога"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE tg_id = %s", (tg_id,))
        user_id = cur.fetchone()[0]

        cur.execute(
            "SELECT request, response FROM history WHERE user_id = %s AND is_old = False ORDER BY id",
            (user_id,)
        )
        history = cur.fetchall()
        return history
    except Exception as e:
        print(f"Database error in get_chat_history: {e}")
        return []
    finally:
        conn.close()
def mark_old(tg_id: int):
    """Помечает текущую сессию как старую"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE tg_id = %s", (tg_id,))
        user_id = cur.fetchone()[0]

        cur.execute(
            "UPDATE history SET is_old = True WHERE user_id = %s AND is_old = False",
            (user_id,)
        )
        conn.commit()
    except Exception as e:
        print(f"Database error in mark_old: {e}")
        conn.rollback()
    finally:
        conn.close()
def initilization():
    conn = get_db()
    cursor = conn.cursor()
    with open("create_db.sql") as file:
        sql_script = file.read()
    cursor.execute(sql_script)
    conn.commit()
    conn.close()