import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.helpers import format_timestamp

def create_hourly_chart(forecast_list, tz_offset: int, temp_unit: str = "°C", is_dark: bool = True):
    """Create interactive Plotly area chart with dynamic Light/Dark mode themes."""
    hourly = forecast_list[:10]
    
    times = [format_timestamp(x["dt"], tz_offset, "%H:%M") for x in hourly]
    temps = [x["temp"] for x in hourly]
    pops = [x["pop"] for x in hourly]
    feels = [x["feels_like"] for x in hourly]

    # Theme colors based on Light vs Dark Mode
    if is_dark:
        line_color = "#60A5FA"
        fill_color = "rgba(96, 165, 250, 0.15)"
        bar_color = "rgba(34, 211, 238, 0.35)"
        bar_border = "rgba(34, 211, 238, 0.8)"
        text_color = "#F8FAFC"
        subtext_color = "#94A3B8"
        grid_color = "rgba(51, 65, 85, 0.4)"
        plotly_theme = "plotly_dark"
    else:
        line_color = "#3B82F6"
        fill_color = "rgba(59, 130, 246, 0.12)"
        bar_color = "rgba(6, 182, 212, 0.3)"
        bar_border = "rgba(6, 182, 212, 0.8)"
        text_color = "#0F172A"
        subtext_color = "#475569"
        grid_color = "rgba(226, 232, 240, 0.8)"
        plotly_theme = "plotly_white"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Rain probability bars
    fig.add_trace(
        go.Bar(
            x=times,
            y=pops,
            name="Rain Chance (%)",
            marker=dict(color=bar_color, line=dict(color=bar_border, width=1)),
            hovertemplate="%{y}% chance of rain<extra></extra>"
        ),
        secondary_y=True
    )

    # Temperature spline curve
    fig.add_trace(
        go.Scatter(
            x=times,
            y=temps,
            name=f"Temp ({temp_unit})",
            mode="lines+markers",
            line=dict(color=line_color, width=3, shape="spline"),
            marker=dict(size=8, color=line_color, symbol="circle"),
            fill="tozeroy",
            fillcolor=fill_color,
            customdata=feels,
            hovertemplate=f"Temp: %{{y}}{temp_unit}<br>Feels like: %{{customdata}}{temp_unit}<extra></extra>"
        ),
        secondary_y=False
    )

    fig.update_layout(
        template=plotly_theme,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        height=320,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=text_color, family="Plus Jakarta Sans")
        ),
        hovermode="x unified",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(color=subtext_color, family="Plus Jakarta Sans")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            tickfont=dict(color=subtext_color, family="Plus Jakarta Sans"),
            title=dict(text=f"Temp ({temp_unit})", font=dict(color=subtext_color, family="Plus Jakarta Sans"))
        ),
        yaxis2=dict(
            showgrid=False,
            zeroline=False,
            range=[0, 100],
            tickfont=dict(color=subtext_color, family="Plus Jakarta Sans"),
            title=dict(text="Rain %", font=dict(color=subtext_color, family="Plus Jakarta Sans"))
        )
    )

    return fig

def create_daily_chart(daily_summary, temp_unit: str = "°C", is_dark: bool = True):
    """Create min/max temperature comparison bar chart."""
    days = [x["day_name"] + " (" + x["full_date"] + ")" for x in daily_summary]
    mins = [x["temp_min"] for x in daily_summary]
    maxs = [x["temp_max"] for x in daily_summary]

    if is_dark:
        min_color = "rgba(96, 165, 250, 0.75)"
        min_border = "#60A5FA"
        max_color = "rgba(248, 113, 113, 0.75)"
        max_border = "#F87171"
        text_color = "#F8FAFC"
        subtext_color = "#94A3B8"
        grid_color = "rgba(51, 65, 85, 0.4)"
        plotly_theme = "plotly_dark"
    else:
        min_color = "rgba(59, 130, 246, 0.75)"
        min_border = "#3B82F6"
        max_color = "rgba(239, 68, 68, 0.75)"
        max_border = "#EF4444"
        text_color = "#0F172A"
        subtext_color = "#475569"
        grid_color = "rgba(226, 232, 240, 0.8)"
        plotly_theme = "plotly_white"

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=days,
        y=mins,
        name=f"Min Temp ({temp_unit})",
        marker=dict(color=min_color, line=dict(color=min_border, width=1)),
        hovertemplate=f"Min: %{{y}}{temp_unit}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=days,
        y=maxs,
        name=f"Max Temp ({temp_unit})",
        marker=dict(color=max_color, line=dict(color=max_border, width=1)),
        hovertemplate=f"Max: %{{y}}{temp_unit}<extra></extra>"
    ))

    fig.update_layout(
        barmode="group",
        template=plotly_theme,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        height=320,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=text_color, family="Plus Jakarta Sans")
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(color=subtext_color, family="Plus Jakarta Sans")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            tickfont=dict(color=subtext_color, family="Plus Jakarta Sans"),
            title=dict(text=f"Temp ({temp_unit})", font=dict(color=subtext_color, family="Plus Jakarta Sans"))
        )
    )

    return fig
