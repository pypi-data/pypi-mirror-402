from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Grid
import os

from .datetimes import dt_to_str

def line(bars_df, x, y, title='', bs_fields=[], extra=[], render_path='.'):
    html_path = render_path


    x_data = bars_df[x].tolist()
    
    mark_point_data = []
    if bs_fields:
        for bs_field_index, bs_field in enumerate(bs_fields[1]):
            bs_df = bars_df[bars_df[bs_fields[0]] == bs_field]
            for bs_index, bs in bs_df.iterrows():
                color = 'rgb(255, 0, 0)'
                mark_point_y_value = bs[bs_fields[2][bs_field_index]]
                text = bs[bs_fields[0]]
                amount_label = 'amount_label'
                mark_point_data.append(opts.MarkPointItem(name=amount_label, coord=[bs.date, mark_point_y_value], value=text, \
                symbol='circle', symbol_size=[12, 12], itemstyle_opts=opts.ItemStyleOpts(color=color)))
        

    line = (
        Line(init_opts=opts.InitOpts(
            width="1000px",
            height="800px",
            animation_opts=opts.AnimationOpts(animation=False),
        ))
        .add_xaxis(xaxis_data=x_data)
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(is_scale = True),
            legend_opts=opts.LegendOpts(pos_left='50%')
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=title))
    )
    
    for field in y:
        line.add_yaxis(
            series_name=field,
            y_axis=bars_df[field].tolist(),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
            markpoint_opts=opts.MarkPointOpts(data=mark_point_data, label_opts=opts.LabelOpts(formatter='{c}',position='bottom',font_size=14)), 
        )

    if extra:
        # Grid Overlap + Bar
        grid_chart = Grid(
            init_opts=opts.InitOpts(
                width="1800px",
                height="1000px",
                animation_opts=opts.AnimationOpts(animation=False),
            )
        )
        grid_chart.add(
            line,
            grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="30%"),
        )

        height = (90-38)/len(extra)

        for index, ex in enumerate(extra):
            line = Line()
            line.add_xaxis(xaxis_data=x_data)
            line.set_global_opts(
                xaxis_opts=opts.AxisOpts(type_="category"),
                yaxis_opts=opts.AxisOpts(is_scale = True),
                legend_opts=opts.LegendOpts(pos_left=f'{(index+2)*10}%')
            )
            for col in ex:
                line.add_yaxis(
                    series_name=col,
                    y_axis=bars_df[col].tolist(),
                    is_smooth=True,
                    is_hover_animation=False,
                    linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
                    label_opts=opts.LabelOpts(is_show=False),
                )

            top = 14 + (index+1)*height
            if index == 1:
                top = top + 4
            grid_chart.add(
                line,
                grid_opts=opts.GridOpts(
                    pos_left="10%", pos_right=f"10%", pos_top=f"{top}%", height=f"{height}%"
                ),
            )
        grid_chart.render(html_path)
    else:
        line.render(html_path)
    
def kline(bars_df, render_path, extra=[], line=[]):
    html_path = render_path

    symbol = bars_df.iloc[0].symbol

    x_data = list(map(lambda x: dt_to_str(x), bars_df['eob'].tolist()))
    y_data = bars_df[['open', 'close', 'low', 'high']].to_dict('split')['data']
    
    mark_point_data = []
    for index, bar in bars_df[(bars_df.gold == True) | (bars_df.dead == True)].iterrows():
        if bar.gold == True:
            color = 'rgb(255, 0, 0)'
            mark_point_y_value = bar.low
            text = '买'
        else:
            color = 'rgb(0, 255, 0)'
            mark_point_y_value = bar.high
            text = '卖'
        
        amount_label = 'amount_label'
        mark_point_data.append(opts.MarkPointItem(name=amount_label, coord=[dt_to_str(bar.eob), mark_point_y_value], value=text, \
        symbol='circle', symbol_size=[12, 12], itemstyle_opts=opts.ItemStyleOpts(color=color)))
        
    kline = (
        Kline(init_opts=opts.InitOpts(width="1800px", height="800px"))
        .add_xaxis(x_data)
        .add_yaxis(symbol, y_data, 
            markpoint_opts=opts.MarkPointOpts(data=mark_point_data, label_opts=opts.LabelOpts(formatter='{c}',position='bottom',font_size=14)), 
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="max", value_dim="close")]),
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ec0000",
                color0="#00da3c",
                border_color="#8A0000",
                border_color0="#008F28"
            )
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                is_show=False, pos_bottom=10, pos_left="center"
            ),
            yaxis_opts=opts.AxisOpts(is_scale = True),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=True,
                    type_="inside",
                    # xaxis_index=[0, 1],
                    range_start=0,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    # xaxis_index=[0, 1],
                    type_="slider",
                    # pos_top="85%",
                    range_start=0,
                    range_end=100,
                ),
            ] if not extra else [
                opts.DataZoomOpts(
                    is_show=True,
                    type_="inside",
                    xaxis_index=[0, 1],
                    range_start=0,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0, 1],
                    type_="slider",
                    # pos_top="85%",
                    range_start=0,
                    range_end=100,
                ),
            ]
        )
    )

    if line:

        line_chart = Line()
        line_chart.add_xaxis(xaxis_data=x_data)
        for col in line:
            line_chart.add_yaxis(
                series_name=col,
                y_axis=bars_df[col],
                is_smooth=True,
                is_hover_animation=False,
                linestyle_opts=opts.LineStyleOpts(width=1, opacity=0.5),
                label_opts=opts.LabelOpts(is_show=False),
            )
        line_chart.set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
        kline = kline.overlap(line_chart)


    #pdb.set_trace()
    if extra:
        # Grid Overlap + Bar
        grid_chart = Grid(
            init_opts=opts.InitOpts(
                width="1800px",
                height="1000px",
                animation_opts=opts.AnimationOpts(animation=False),
            )
        )
        grid_chart.add(
            kline,
            grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="60%"),
        )

        height = (100-38)/len(extra)

        for index, ex in enumerate(extra):
            line = Line()
            line.add_xaxis(xaxis_data=x_data)
            line.set_global_opts(
                xaxis_opts=opts.AxisOpts(type_="category"),
                yaxis_opts=opts.AxisOpts(is_scale = True),
            )
            for col in ex:
                line.add_yaxis(
                    series_name=col,
                    y_axis=bars_df[col].tolist(),
                    is_smooth=True,
                    is_hover_animation=False,
                    linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
                    label_opts=opts.LabelOpts(is_show=False),
                    xaxis_index=1,
                    yaxis_index=1,
                )

            top = 8 + (index+1)*height
            grid_chart.add(
                line,
                grid_opts=opts.GridOpts(
                    pos_left="10%", pos_right=f"10%", pos_top=f"{top}%", height=f"20%"
                ),
            )
        grid_chart.render(html_path)
    else:
        kline.render(html_path)