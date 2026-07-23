import sqlite3
from pathlib import Path



class BackgroundRepository:


    def __init__(self, db_path: Path):

        self.db_path = db_path

        self.init_table()



    def connect(self):

        return sqlite3.connect(
            self.db_path
        )




    def init_table(self):

        conn = self.connect()

        cursor = conn.cursor()



        # ==========================
        # 历史生成记录
        # ==========================

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



        # ==========================
        # 背景缓存表
        # ==========================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS background_cache
            (

                id INTEGER PRIMARY KEY AUTOINCREMENT,


                cache_key TEXT UNIQUE NOT NULL,


                category TEXT,

                style TEXT,

                color_hint TEXT,


                bg_url TEXT,


                enhanced_url TEXT,


                created_at DATETIME DEFAULT CURRENT_TIMESTAMP

            )
            """
        )



        conn.commit()

        conn.close()





    # ==================================
    # 保存历史生成记录
    # ==================================

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

                data.get(
                    "user_id",
                    1
                ),

                data["product_category"],

                data.get(
                    "style"
                ),

                data.get(
                    "color_hint"
                ),

                data.get(
                    "prompt_used"
                ),

                data.get(
                    "bg_url"
                ),

                data.get(
                    "enhanced_url"
                ),

                data.get(
                    "scale_factor",
                    2
                )

            )

        )


        conn.commit()


        id = cursor.lastrowid


        conn.close()



        return {

            "id":id,

            **data

        }





    # ==================================
    # 查询缓存
    # ==================================

    def get_cache(
            self,
            cache_key
    ):


        conn=self.connect()

        cursor=conn.cursor()



        row = cursor.execute(
            """
            SELECT
                cache_key,
                category,
                style,
                color_hint,
                bg_url,
                enhanced_url

            FROM background_cache

            WHERE cache_key=?

            """,

            (
                cache_key,
            )

        ).fetchone()



        conn.close()



        if row is None:

            return None



        return {


            "cache_key":row[0],

            "category":row[1],

            "style":row[2],

            "color_hint":row[3],

            "bg_url":row[4],

            "enhanced_url":row[5]

        }





    # ==================================
    # 保存缓存
    # ==================================

    def save_cache(
            self,
            data
    ):


        conn=self.connect()

        cursor=conn.cursor()



        cursor.execute(
            """
            INSERT OR REPLACE INTO background_cache
            (
                cache_key,
                category,
                style,
                color_hint,
                bg_url,
                enhanced_url
            )


            VALUES
            (?,?,?,?,?,?)

            """,

            (

                data["cache_key"],

                data["category"],

                data.get("style"),

                data.get("color_hint"),

                data["bg_url"],

                data["sd_url"]

            )

        )



        conn.commit()

        conn.close()





    # ==================================
    # 查询历史
    # ==================================

    def list(
            self,
            user_id=1
    ):


        conn=self.connect()

        cursor=conn.cursor()



        rows=cursor.execute(
            """
            SELECT *

            FROM history_background

            WHERE user_id=?

            ORDER BY id DESC

            """,

            (
                user_id,
            )

        ).fetchall()



        conn.close()



        return rows


    def get_by_id(self,id):

        conn=self.connect()

        cursor=conn.cursor()

        row = cursor.execute(
            """
            SELECT *
            FROM history_background
            WHERE id=?
            """,
            (id,)
        ).fetchone()

        conn.close()

        return row