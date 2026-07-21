import sqlite3
from pathlib import Path


class BackgroundRepository:

    def __init__(self, db_path: Path):

        self.db_path = db_path

        self.init_table()


    def connect(self):

        return sqlite3.connect(self.db_path)


    def init_table(self):

        conn = self.connect()

        cursor = conn.cursor()


        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS history_background
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER DEFAULT 1,

                product_category TEXT NOT NULL,

                style TEXT,

                color_hint TEXT,

                prompt_used TEXT,

                bg_url TEXT,

                enhanced_url TEXT,

                scale_factor INTEGER DEFAULT 2,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


        conn.commit()

        conn.close()



    def create(self,data):

        conn=self.connect()

        cursor=conn.cursor()


        cursor.execute(
            """
            INSERT INTO history_background
            (
                user_id,
                product_category,
                style,
                color_hint,
                prompt_used,
                bg_url,
                enhanced_url,
                scale_factor
            )

            VALUES
            (?,?,?,?,?,?,?,?)
            """,

            (
                data.get("user_id",1),
                data["product_category"],
                data.get("style"),
                data.get("color_hint"),
                data.get("prompt_used"),
                data.get("bg_url"),
                data.get("enhanced_url"),
                data.get("scale_factor",2)
            )

        )


        conn.commit()

        id=cursor.lastrowid

        conn.close()


        return {
            "id":id,
            **data
        }



    def list(self,user_id=1):

        conn=self.connect()

        cursor=conn.cursor()


        rows=cursor.execute(
            """
            SELECT *
            FROM history_background
            WHERE user_id=?
            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()


        conn.close()


        return rows