import json

from .database import Base, engine, SessionLocal
from .db_models import Template
from .templates_data import TEMPLATES


def init_db():
    # 如果表已经用 SQL 建好了，这句不会影响；如果没建，会自动建
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        count = db.query(Template).count()

        if count > 0:
            print("templates 表已有数据，不重复插入。")
            return

        for item in TEMPLATES:
            template = Template(
                id=item["id"],
                name=item["name"],
                preview_url=item["preview_url"],
                config_json=json.dumps(item["config"], ensure_ascii=False),
                usage_count=0,
                is_active=True
            )
            db.add(template)

        db.commit()
        print("5 个模板已成功写入 MySQL。")

    except Exception as e:
        db.rollback()
        print("初始化失败：", e)

    finally:
        db.close()


if __name__ == "__main__":
    init_db()