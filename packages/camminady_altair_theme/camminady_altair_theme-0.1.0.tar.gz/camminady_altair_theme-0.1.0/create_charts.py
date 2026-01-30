import altair as alt
from vega_datasets import data

from camminady_altair_theme import camminady  # noqa

alt.theme.enable("camminady")

if __name__ == "__main__":
    source = data.stocks()
    base = (
        alt.Chart(source)
        .mark_line(strokeWidth=3)
        .encode(
            x="date:T",
            y="price:Q",
            color="symbol:N",
            strokeDash="symbol:N",
        )
        .properties(title="This is the chart title")
    )

    base.save("assets/single_chart.png", scale_factor=4)
    base.encode(row="symbol:N").properties(height=100).save(
        "assets/facet_chart.png", scale_factor=4
    )
