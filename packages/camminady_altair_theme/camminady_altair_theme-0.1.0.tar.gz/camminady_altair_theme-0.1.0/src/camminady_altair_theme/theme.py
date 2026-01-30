from dataclasses import dataclass

import altair as alt


@dataclass
class Config:
    color_primary: str = "dimgray"
    color_secondary: str = "gray"
    font_weight: str = "normal"
    size_small: int = 12
    size_medium: int = 14
    size_large: int = 20
    height: int = 400
    width: int = 800
    spacing_facet: int = 40
    spacing_concat: int = 40


config = Config()


@alt.theme.register("camminady", enable=True)
def camminady() -> alt.theme.ThemeConfig:
    return {
        "config": {
            "text": {
                "color": config.color_primary,
                "fontSize": config.size_small,
            },
            "title": {
                "anchor": "middle",
                "fontWeight": config.font_weight,
                "fontSize": config.size_large,
                "color": config.color_primary,
            },
            "header": {
                "titleFontSize": config.size_large,
                "labelFontSize": config.size_medium,
                "titleColor": config.color_primary,
                "labelColor": config.color_primary,
                "titleFontWeight": config.font_weight,
                "labelFontWeight": config.font_weight,
            },
            "view": {
                "height": config.height,
                "width": config.width,
                "strokeWidth": 0,
                "fill": "white",
            },
            "facet": {
                "color": "red",
                "spacing": config.spacing_facet,
            },
            "concat": {
                "spacing": config.spacing_concat,
            },
            "headerRow": (
                subplotheader := {
                    "labelColor": config.color_secondary,
                    "labelFontSize": config.size_small,
                    "titleColor": config.color_primary,
                    "titleFontSize": config.size_medium,
                }
            ),
            "headerFacet": subplotheader,
            "headerColumn": subplotheader,
            "axis": {
                "domain": True,
                "domainColor": config.color_secondary,
                "domainWidth": 1,
                "gridWidth": 1,
                "labelAngle": 0,
                "tickSize": 5,
                "gridCap": "round",
                "gridDash": [2, 4],
                "titleFontWeight": config.font_weight,
                "labelFontWeight": config.font_weight,
                "titleFontSize": config.size_medium,
                "labelFontSize": config.size_small,
                "titleColor": config.color_primary,
                "labelColor": config.color_secondary,
                "tickColor": config.color_secondary,
            },
            "axisX": {
                "titleAnchor": "end",
                "titleAlign": "center",
            },
            "axisY": {
                "titleAnchor": "end",
                "titleAngle": 0,
                "titleAlign": "center",
                "titleY": -15,
                "titleX": 0,
            },
            "legend": {
                "titleFontWeight": config.font_weight,
                "labelFontWeight": config.font_weight,
                "titleFontSize": config.size_medium,
                "labelFontSize": config.size_small,
                "labelLimit": 0,
                "titleColor": config.color_primary,
                "labelColor": config.color_primary,
            },
        }
    }
