import plotly.graph_objects as go
import ipywidgets as widgets
from jupyter_jsmol import JsmolView
import numpy as np

from bokeh.models import TapTool, CustomJS, ColumnDataSource, HoverTool, ColumnDataSource
from bokeh.io import show, output_notebook
from bokeh.plotting import figure, show
from bokeh.embed import components
import itertools
from bokeh.palettes import Dark2_5 as palette

output_notebook()


def show_scatter_plot(xs, ys, data_point_labels=None, x_label=None, y_label=None, legend=None, unit=None):
    # if xs ist not list of lists/arrays make it so, as later the function iterates over xs and ys
    if not isinstance(xs[0], (list, np.ndarray)):
        xs = [xs]
        ys = [ys]
    # make sure that xs and ys ist list (of lists/arrays) as later the function will 
    # do the list operation xs+ys 
    elif not isinstance(xs, list) or not isinstance(ys, list):
        xs = list(xs)
        ys = list(ys)

    if unit is None:
        unit = ''

    hover = HoverTool(
        tooltips="""
            <div>
                <div>
                    <span style="font-size: 15px; font-weight: bold;">@data_point_labels</span>
                </div>
                <div >
                    <span style="font-size: 10px;">Abs. error = @abs_error %s</span><br>
                </div>
                <div>
                    <span style="font-size: 10px;">Location:</span>
                    <span style="font-size:  10px; color: #696;">($x, $y)</span>
                </div>
            </div>
            """ % unit
    )

    colors = itertools.cycle(palette)

    p = figure(plot_width=600, plot_height=300, tools=[hover, "box_zoom", "pan", "reset"],
               x_axis_label=x_label, y_axis_label=y_label)

    # plot reference diagonal
    xy_min = min([min(arr) for arr in xs + ys])
    xy_max = max([max(arr) for arr in xs + ys])
    p.line([xy_min, xy_max], [xy_min, xy_max])

    for i, color in zip(range(len(xs)), colors):
        source = ColumnDataSource(
            data=dict(
                x=xs[i],
                y=ys[i],
                data_point_labels=data_point_labels[i],
                abs_error=abs(np.array(xs[i]) - np.array(ys[i]))
            )
        )

        p.circle('x', 'y', size=8, source=source, legend=legend[i], color=color)
    p.legend.location = 'top_left'
    show(p)


def make_interactive_plot(df_D, sisso, D_selected_df, viewer):
    # features are obtained from the SissoRegressor object
    total_features = sisso.n_nonzero_coefs

    features = []
    for i in range(total_features):
        features.append(df_D.columns[sisso.l0_selected_indices[total_features - 1]][i])

    # coefficients and intercept used to create the line separating the RS vs ZB materials
    coefficients = []
    for i in range(total_features):
        coefficients.append(sisso.coefs[sisso.l0_selected_indices[total_features - 1][i]])
    intercept = sisso.intercept

    current_features = [0, 1]

    def f_x(x):

        if current_features[0] == current_features[1]:
            return x
        else:
            return -x * coefficients[current_features[0]] / coefficients[current_features[1]] - \
                   intercept / coefficients[current_features[1]]

    line_x = np.linspace(D_selected_df[features[0]].min(), D_selected_df[features[0]].max(), 1000)
    line_y = f_x(line_x)

    # the interactive plot is constructed with a figure widget
    fig = go.FigureWidget()

    custom_RS = np.dstack((D_selected_df.loc[D_selected_df['Structure'] == 'RS']['energy_diff'],
                           D_selected_df.loc[D_selected_df['Structure'] == 'RS']['P_predict']))[0]
    custom_ZB = np.dstack((D_selected_df.loc[D_selected_df['Structure'] == 'ZB']['energy_diff'],
                           D_selected_df.loc[D_selected_df['Structure'] == 'ZB']['P_predict']))[0]

    # the final plot is the sum of two traces, respectively containing the RS vs ZB materials
    fig.add_trace(
        (
            go.Scatter(
                mode='markers',
                x=D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[0]].to_numpy(),
                y=D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[1]].to_numpy(),
                customdata=custom_RS,
                text=D_selected_df.loc[D_selected_df['Structure'] == 'RS'][['Chem Formula']],
                hovertemplate=
                r"<b>%{text}</b><br><br>" +
                "x axis: %{x:,.2f}<br>" +
                "y axis: %{y:,.2f}<br>" +
                "ΔE reference:  %{customdata[0]:,.4f}<br>" +
                "ΔE predicted:  %{customdata[1]:,.4f}<br>",
                name='RS',
            )
        ))
    fig.add_trace(
        (
            go.Scatter(
                mode='markers',
                x=D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[0]].to_numpy(),
                y=D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[1]].to_numpy(),
                customdata=custom_ZB,
                text=D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][['Chem Formula']],
                hovertemplate=
                r"<b>%{text}</b><br><br>" +
                "x axis: %{x:,.2f}<br>" +
                "y axis: %{y:,.2f}<br>" +
                "ΔE reference:  %{customdata[0]:,.4f}<br>" +
                "ΔE predicted:  %{customdata[1]:,.4f}<br>",
                # meta = tuple([0,1]),
                name='ZB',
            )
        ))
    fig.add_trace(
        (
            go.Scatter(
                x=line_x,
                y=line_y,
                marker=dict(color='Grey'),
                name='Separation line'
            )
        )
    )

    fig.update_layout(
        xaxis_title=features[0],
        yaxis_title=features[1],
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        ),
        width=800,
        height=600,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=150,
            pad=4
        ),
    )

    scatter_RS = fig.data[0]
    scatter_ZB = fig.data[1]
    scatter_line = fig.data[2]
    RS_npoints = len(D_selected_df.loc[D_selected_df['Structure'] == 'RS'])
    ZB_npoints = len(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'])

    feat_x = widgets.Dropdown(
        description='x-axis',
        options=features,
        value=features[0]
    )

    feat_y = widgets.Dropdown(
        description='y-axis',
        options=features,
        value=features[1]
    )

    feat_marker = widgets.Dropdown(
        description='Marker size',
        options=['None'] + features,
        value='None',
    )


    marker_size = 7

    def set_markers(feature='None'):
        print(feature)
        if feature == 'None':
            scatter_RS.marker.size = [marker_size] * RS_npoints
            scatter_ZB.marker.size = [marker_size] * ZB_npoints
        else:
            min_value = min(min(D_selected_df.loc[D_selected_df['Structure'] == 'RS'][feature]),
                            min(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][feature]))
            max_value = max(max(D_selected_df.loc[D_selected_df['Structure'] == 'RS'][feature]),
                            max(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][feature]))
            coeff = 2*marker_size/(max_value - min_value)
            scatter_RS.marker.size = marker_size/2+coeff*D_selected_df.loc[D_selected_df['Structure'] == 'RS'][feature]
            scatter_ZB.marker.size = marker_size/2+coeff*D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][feature]

        scatter_RS.marker.symbol = ["circle"] * RS_npoints
        scatter_ZB.marker.symbol = ["circle"] * ZB_npoints

    set_markers()

    def handle_xfeat_change (change):
        if features.index(change.new) != current_features[1]:
            fig.update_layout(
                xaxis_title=change.new,
            )
            current_features[0] = features.index(change.new)
            scatter_RS['x'] = D_selected_df.loc[D_selected_df['Structure'] == 'RS'][change.new].to_numpy()
            scatter_ZB['x'] = D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][change.new].to_numpy()
            line_x = np.linspace(D_selected_df[change.new].min(), D_selected_df[change.new].max(), 1000)
            line_y = f_x(line_x)
            scatter_line['x'] = line_x
            scatter_line['y'] = line_y

    def handle_yfeat_change(change):
        if features.index(change.new) != current_features[0]:
            fig.update_layout(
                yaxis_title=change.new,
            )
            current_features[1] = features.index(change.new)
            scatter_RS['y'] = D_selected_df.loc[D_selected_df['Structure'] == 'RS'][change.new].to_numpy()
            scatter_ZB['y'] = D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][change.new].to_numpy()
            line_x = np.linspace(D_selected_df[features[current_features[0]]].min(),
                                 D_selected_df[features[current_features[0]]].max(), 1000)
            line_y = f_x(line_x)
            scatter_line['x'] = line_x
            scatter_line['y'] = line_y

    def handle_markerfeat_change(change):
        set_markers(change.new)

    feat_x.observe(handle_xfeat_change, names='value')
    feat_y.observe(handle_yfeat_change, names='value')
    feat_marker.observe(handle_markerfeat_change, names='value')

    box_features = widgets.HBox([widgets.VBox([feat_x, feat_y]), feat_marker])
    container = widgets.VBox([box_features, fig])

    # -------------------------------------------------------------------------------------------------------------------
    # Here we define the interaction with the jsmol viewer

    def view_structure_RS ( formula ):
        viewer.script( "load data/compressed_sensing/structures/RS_structures/" + formula + ".xyz")

    def update_point_RS(trace, points, selector):
        if not points.point_inds:
            return
        set_markers()
        sizes = list(scatter_RS.marker.size)
        symbols = list(scatter_RS.marker.symbol)
        for i in points.point_inds:
            sizes[i] = 15
            symbols[i] = 'x'
            with fig.batch_update():
                scatter_RS.marker.size = sizes
                scatter_RS.marker.symbol = symbols
        point = points.point_inds[0]
        formula = trace['text'][point][0]
        view_structure_RS(formula)

    def view_structure_ZB ( formula ):
        viewer.script("load data/compressed_sensing/structures/ZB_structures/" + formula + ".xyz")

    def update_point_ZB(trace, points, selector):
        if not points.point_inds:
            return
        set_markers()
        sizes = list(scatter_RS.marker.size)
        symbols = list(scatter_RS.marker.symbol)
        for i in points.point_inds:
            sizes[i] = 15
            symbols[i] = 'x'
            with fig.batch_update():
                scatter_ZB.marker.size = sizes
                scatter_ZB.marker.symbol = symbols
        point = points.point_inds[0]
        formula = scatter_ZB['text'][point][0]
        view_structure_ZB(formula)

    botton_RS = scatter_RS.on_click(update_point_RS)
    botton_ZB = scatter_ZB.on_click(update_point_ZB)

    text_RS = []
    for material in D_selected_df['Chem Formula'].tolist():
        text_RS.append(material + ' - RS structure')
    text_ZB = []
    for material in D_selected_df['Chem Formula'].tolist():
        text_ZB.append(material + ' - ZB structure')

    return container


def viewer_dd(viewer, D_selected_df):
    dropdown_compounds = widgets.Dropdown(
        options=D_selected_df['Chem Formula'].tolist(),
        description='Compound '
    )

    dropdown_structure = widgets.Dropdown(
        options=['RS', 'ZB'],
        description='Structure '
    )

    button = widgets.Button(description="Visualize")

    def on_button_clicked( button ):
        viewer.script(
            "load data/compressed_sensing/structures/" + dropdown_structure.value + "_structures/" + dropdown_compounds.value + ".xyz")

    button.on_click(on_button_clicked)
    container = widgets.HBox([dropdown_compounds, dropdown_structure, button])

    return container



   # ------------------------------------------------------------------------------------------------------------------
    # Here we define the button update

    # updatemenus = list([
    #
    #     dict(
    #         buttons=list([
    #
    #             # x-axis contains the feature 0
    #             dict(method='update',
    #                  # vaar='d',
    #                  label="x-axis0:  " + features[0],
    #                  args=[{
    #                      # 'customdata': [custom_RS, custom_ZB, [0, fig['data'][2].customdata[1]]],
    #                      # 'meta'[2]: [0, fig['data'][2].meta[1]],
    #                      # 'meta': [fig['data'][1].meta, fig['data'][0].meta, fig['data'][2].meta],
    #                      'x': [D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[0]].to_numpy(),
    #                            D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[0]].to_numpy(),
    #                            np.linspace(D_selected_df[features[0]].min(), D_selected_df[features[0]].max(), 1000)
    #                            ],
    #                      'y': [
    #                          # fig['data'][0].y, fig['data'][1].y,
    #                          D_selected_df.loc[D_selected_df['Structure'] == 'RS'][
    #                              features[fig['data'][2].customdata[1]]].to_numpy(),
    #                          D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][
    #                              features[fig['data'][2].customdata[1]]].to_numpy(),
    #                          f_x(np.linspace(D_selected_df[features[0]].min(),
    #                                          D_selected_df[features[0]].max(), 1000), xfeat_loc=0)
    #                      ],
    #                  },
    #                  ],
    #                  name='x',
    #                  ),
    #
    #             # x-axis contains the feature 1
    #             dict(method='update',
    #                  label="x-axis1:  " + features[1],
    #                  args=[{
    #                      'meta': [fig['data'][1].meta, fig['data'][0].meta, fig['data'][2].meta],
    #                      'customdata': [custom_RS, custom_ZB, [1, fig['data'][2].customdata[1]]],
    #                      'x': [D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[1]].to_numpy(),
    #                            D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[1]].to_numpy(),
    #                            np.linspace(D_selected_df[features[1]].min(), D_selected_df[features[1]].max(), 1000)
    #                            ],
    #                      'y': [
    #                          # fig['data'][0].y, fig['data'][1].y,
    #                          D_selected_df.loc[D_selected_df['Structure'] == 'RS'][
    #                              features[fig['data'][2].customdata[1]]].to_numpy(),
    #                          D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][
    #                              features[fig['data'][2].customdata[1]]].to_numpy(),
    #                          f_x(np.linspace(D_selected_df[features[1]].min(),
    #                                          D_selected_df[features[1]].max(), 1000), yfeat_loc=1)
    #                      ],
    #                  },
    #                  ],
    #                  name='y'),
    #         ]),
    #         showactive=True,
    #         pad={'l': 0, 't': -100},
    #     ),
    #
    #     dict(
    #         buttons=list([
    #
    #             # y-axis contains the feature 1
    #             dict(method='update',
    #                  label="y-axis1:  " + features[1],
    #                  args=[{
    #                      'meta': [fig['data'][1].meta, fig['data'][0].meta, fig['data'][2].meta],
    #
    #                      # 'meta': [tuple([fig['data'][2].meta[0], 1]),tuple([fig['data'][2].meta[0], 1]),tuple([fig['data'][2].meta[0], 1])],
    #                      # 'customdata': [custom_RS, custom_ZB, [fig['data'][2].customdata[0], 1]],
    #
    #                      # 'y': [D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[1]].to_numpy(),
    #                      #          D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[1]].to_numpy(),
    #                      #          f_x(np.linspace(D_selected_df[features[fig['data'][2].customdata[0]]].min(),
    #                      #                          D_selected_df[features[fig['data'][2].customdata[0]]].max(), 1000),
    #                      #              fig['data'][2].customdata[0], 1, intercept)],
    #                      # 'x': [
    #                      #     # fig['data'][0].x, fig['data'][1].x,
    #                      #     D_selected_df.loc[D_selected_df['Structure'] == 'RS'][
    #                      #         features[fig['data'][2].customdata[0]]].to_numpy(),
    #                      #     D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][
    #                      #         features[fig['data'][2].customdata[0]]].to_numpy(),
    #                      #     np.linspace(D_selected_df[features[fig['data'][2].customdata[0]]].min(),
    #                      #                         D_selected_df[features[fig['data'][2].customdata[0]]].max(), 1000),
    #                      #       ],
    #                  },
    #                  ],
    #                  name='y'),
    #
    #             # y-axis contains the feature 0
    #             dict(method='update',
    #                  label="y-axis0:  " + features[0],
    #                  args=[{
    #                      'meta': [fig['data'][1].meta, fig['data'][0].meta, fig['data'][2].meta],
    #
    #                      # 'meta': [tuple([fig['data'][2].meta[0], 0]),tuple([fig['data'][2].meta[0], 0]),tuple([fig['data'][2].meta[0], 0])],
    #                      # 'customdata': [custom_RS, custom_ZB, [fig['data'][2].customdata[0], 0]],
    #                      # 'y': [D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[0]].to_numpy(),
    #                      #          D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[0]].to_numpy(),
    #                      #          f_x(np.linspace(D_selected_df[features[fig['data'][2].customdata[0]]].min(),
    #                      #                          D_selected_df[features[fig['data'][2].customdata[0]]].max(), 1000),
    #                      #              fig['data'][2].customdata[0], 0, intercept)],
    #                      # 'x': [
    #                      #     #fig['data'][0].x, fig['data'][1].x,
    #                      #     D_selected_df.loc[D_selected_df['Structure'] == 'RS'][
    #                      #         features[fig['data'][2].customdata[0]]].to_numpy(),
    #                      #     D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][
    #                      #         features[fig['data'][2].customdata[0]]].to_numpy(),
    #                      #     np.linspace(D_selected_df[features[fig['data'][2].customdata[0]]].min(),
    #                      #                       D_selected_df[features[fig['data'][2].customdata[0]]].max(), 1000),
    #                      #       ],
    #                  },
    #                  ],
    #                  name='x'),
    #
    #         ]),
    #         name='y-axis',
    #         showactive=True,
    #         pad={'l': 0, 't': -50},
    #
    #     )
    # ])
    # pad = {'r': 0, 't': 50}
    # fig.update_layout(updatemenus=updatemenus)
    # # print(fig['data'][0])