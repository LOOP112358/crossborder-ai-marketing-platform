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
        "name": "大促爆款 · 折扣突出",
        "preview_url": "/static/templates/template_5.png",
        "config": {
            "purpose": "大促/折扣",
            "layout_mode": "stack",
            "canvas": {"width": 1080, "height": 1080},
            "overlays": [
                {"type": "bottom_fade", "ratio": 0.40, "color": [180, 40, 40, 180]},
                {"type": "vignette"},
            ],
            "product_shadow": True,
            "product": {"x": 260, "y": 140, "w": 560, "h": 560},
            "text_defaults": {
                "title": {"x": 70, "y": 740, "font_size": 40, "color": "#FFFFFF", "art_style": "shadow"},
                "subtitle": {"x": 70, "y": 800, "font_size": 42, "color": "#FFE566", "art_style": "shadow"},
                "selling_point_1": {"x": 70, "y": 860, "font_size": 26, "color": "#FFFFFF", "art_style": "shadow"},
                "selling_point_2": {"x": 70, "y": 900, "font_size": 26, "color": "#FFFFFF", "art_style": "shadow"},
                "cta_text": {
                    "x": 70, "y": 980, "font_size": 30,
                    "color": "#B02828", "button_color": "#FFFFFF", "art_style": "normal",
                },
            },
        },
    },
]


def get_template_by_id(template_id: int):
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    return None