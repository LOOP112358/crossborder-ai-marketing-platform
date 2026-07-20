TEMPLATES = [
    {
        "id": 1,
        "name": "商品居中模板",
        "preview_url": "/static/templates/template_1.png",
        "config": {
            "canvas": {"width": 1080, "height": 1080},
            "product": {"x": 260, "y": 360, "w": 560, "h": 560},
            "title": {"x": 80, "y": 90, "font_size": 64, "color": "#FFFFFF"},
            "discount": {"x": 80, "y": 180, "font_size": 84, "color": "#FFD700"},
            "price": {"x": 80, "y": 290, "font_size": 56, "color": "#FFFFFF"}
        }
    },
    {
        "id": 2,
        "name": "左文右图模板",
        "preview_url": "/static/templates/template_2.png",
        "config": {
            "canvas": {"width": 1080, "height": 1080},
            "product": {"x": 520, "y": 300, "w": 480, "h": 480},
            "title": {"x": 80, "y": 160, "font_size": 58, "color": "#FFFFFF"},
            "discount": {"x": 80, "y": 300, "font_size": 76, "color": "#FFEA00"},
            "price": {"x": 80, "y": 430, "font_size": 54, "color": "#FFFFFF"}
        }
    },
    {
        "id": 3,
        "name": "上文下图模板",
        "preview_url": "/static/templates/template_3.png",
        "config": {
            "canvas": {"width": 1080, "height": 1080},
            "product": {"x": 240, "y": 420, "w": 600, "h": 600},
            "title": {"x": 120, "y": 80, "font_size": 66, "color": "#FFFFFF"},
            "discount": {"x": 120, "y": 180, "font_size": 80, "color": "#FF4444"},
            "price": {"x": 120, "y": 300, "font_size": 54, "color": "#FFFFFF"}
        }
    },
    {
        "id": 4,
        "name": "竖版短视频模板",
        "preview_url": "/static/templates/template_4.png",
        "config": {
            "canvas": {"width": 1080, "height": 1920},
            "product": {"x": 190, "y": 680, "w": 700, "h": 700},
            "title": {"x": 90, "y": 160, "font_size": 72, "color": "#FFFFFF"},
            "discount": {"x": 90, "y": 300, "font_size": 96, "color": "#FFD700"},
            "price": {"x": 90, "y": 450, "font_size": 66, "color": "#FFFFFF"}
        }
    },
    {
        "id": 5,
        "name": "折扣突出模板",
        "preview_url": "/static/templates/template_5.png",
        "config": {
            "canvas": {"width": 1080, "height": 1080},
            "product": {"x": 300, "y": 360, "w": 500, "h": 500},
            "title": {"x": 80, "y": 80, "font_size": 58, "color": "#FFFFFF"},
            "discount": {"x": 80, "y": 720, "font_size": 92, "color": "#FFDD00"},
            "price": {"x": 80, "y": 850, "font_size": 60, "color": "#FFFFFF"}
        }
    }
]


def get_template_by_id(template_id: int):
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    return None