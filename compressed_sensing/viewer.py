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


def make_interactive_plot(df_D, sisso, D_selected_df):
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
    x_RS = D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[0]].to_numpy()
    y_RS = D_selected_df.loc[D_selected_df['Structure'] == 'RS'][features[1]].to_numpy()
    x_ZB = D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[0]].to_numpy()
    y_ZB = D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][features[1]].to_numpy()
    fig.add_trace(
        (
            go.Scatter(
                mode='markers',
                x=x_RS,
                y=y_RS,
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
                x=x_ZB,
                y=y_ZB,
                customdata=custom_ZB,
                text=D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][['Chem Formula']],
                hovertemplate=
                r"<b>%{text}</b><br><br>" +
                "x axis: %{x:,.2f}<br>" +
                "y axis: %{y:,.2f}<br>" +
                "ΔE reference:  %{customdata[0]:,.4f}<br>" +
                "ΔE predicted:  %{customdata[1]:,.4f}<br>",
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

    x_min = min(min(x_RS), min(x_ZB))
    y_min = min(min(y_RS), min(y_ZB))
    x_max = max(max(x_RS), max(x_ZB))
    y_max = max(max(y_RS), max(y_ZB))
    x_delta = 0.05 * abs(x_max - x_min)
    y_delta = 0.05 * abs(y_max - y_min)

    fig.update_layout(
        xaxis_title=features[0],
        yaxis_title=features[1],
        xaxis_range=[x_min - x_delta, x_max + x_delta],
        yaxis_range=[y_min - y_delta, y_max + y_delta],
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        ),
        width=800,
        height=400,
        margin=dict(
            l=50,
            r=50,
            b=70,
            t=20,
            pad=4
        ),
    )

    scatter_RS = fig.data[0]
    scatter_ZB = fig.data[1]
    scatter_line = fig.data[2]

    RS_npoints = len(D_selected_df.loc[D_selected_df['Structure'] == 'RS'])
    ZB_npoints = len(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'])

    widg_featx = widgets.Dropdown(
        description='x-axis',
        options=features,
        value=features[0]
    )
    widg_featy = widgets.Dropdown(
        description='y-axis',
        options=features,
        value=features[1]
    )
    widg_featmarker = widgets.Dropdown(
        description='Marker size',
        options=['Default'] + features,
        value='Default',
    )
    widg_compound_dropdown = widgets.Dropdown(
        layout=widgets.Layout(width='200px'),
        options=D_selected_df['Chem Formula'].tolist(),
        value = D_selected_df['Chem Formula'].tolist()[0],
        description='Compound: '
    )
    widg_compound_text = widgets.Text(
        placeholder='...',
        description='Compound:',
        disabled=False,
        layout=widgets.Layout(width='200px')
    )
    widg_display_button = widgets.Button(description="Display")

    def set_markers(feature='Default', init=False):
        if feature == 'Default':
            scatter_RS.marker.size = [marker_size] * RS_npoints
            scatter_ZB.marker.size = [marker_size] * ZB_npoints
        else:
            min_value = min(min(D_selected_df.loc[D_selected_df['Structure'] == 'RS'][feature]),
                            min(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][feature]))
            max_value = max(max(D_selected_df.loc[D_selected_df['Structure'] == 'RS'][feature]),
                            max(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][feature]))
            coeff = 2 * marker_size / (max_value - min_value)
            scatter_RS.marker.size = marker_size / 2 + coeff * D_selected_df.loc[D_selected_df['Structure'] == 'RS'][
                feature]
            scatter_ZB.marker.size = marker_size / 2 + coeff * D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][
                feature]
        if init:
            scatter_RS.marker.symbol = ["circle"] * RS_npoints
            scatter_ZB.marker.symbol = ["circle"] * ZB_npoints
        else:
            try:
                point = scatter_RS.marker['symbol'].index('x')
                sizes_RS = list(scatter_RS.marker.size)
                sizes_RS[point] = cross_size
                with fig.batch_update():
                    scatter_RS.marker.size = sizes_RS
            except ValueError:
                pass
            try:
                point = scatter_ZB.marker['symbol'].index('x')
                sizes_ZB = list(scatter_ZB.marker.size)
                sizes_ZB[point] = cross_size
                with fig.batch_update():
                    scatter_ZB.marker.size = sizes_ZB
            except ValueError:
                pass

    def handle_xfeat_change(change):
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
        min_x = min(min(scatter_RS['x']), min(scatter_ZB['x']))
        max_x = max(max(scatter_RS['x']), max(scatter_ZB['x']))
        min_delta = 0.05*abs(max_x - min_x)
        fig.layout['xaxis'].range = [min_x - min_delta, max_x + min_delta]

    def handle_yfeat_change(change):
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
        min_y = min(min(scatter_RS['y']), min(scatter_ZB['y']))
        max_y = max(max(scatter_RS['y']), max(scatter_ZB['y']))
        min_delta = 0.05*abs(max_y - min_y)
        fig.layout['yaxis'].range = [min_y - min_delta, max_y + min_delta]

    def handle_markerfeat_change(change):
        set_markers(feature=change.new)

    def handle_compound_change(change):
        structure = D_selected_df[D_selected_df['Chem Formula'] == widg_compound_dropdown.value]['Structure'].values[0]
        viewer_dd.script(
            "load data/compressed_sensing/structures/" + structure + "_structures/"
            + widg_compound_dropdown.value + ".xyz")

    def display_button_clicked(button):
        # Actions are performed only if the string inserted in the text widget corresponds to an exhisting comppund
        if widg_compound_text.value in D_selected_df['Chem Formula'].tolist():
            structure = D_selected_df[D_selected_df['Chem Formula'] == widg_compound_text.value]['Structure'].values[0]
            viewer_plot.script(
                "load data/compressed_sensing/structures/" + structure + "_structures/"
                + widg_compound_text.value + ".xyz")
            set_markers(feature=widg_featmarker.value, init=True)
            if structure == 'RS':
                point = np.where(scatter_RS['text'] == widg_compound_text.value)[0][0]
                symbols_RS = list(scatter_RS.marker.symbol)
                sizes_RS = list(scatter_RS.marker.size)
                symbols_RS[point] = 'x'
                sizes_RS[point] = 15
                with fig.batch_update():
                    scatter_RS.marker.symbol = symbols_RS
                    scatter_RS.marker.size = sizes_RS
            if structure == 'ZB':
                point = np.where(scatter_ZB['text'] == widg_compound_text.value)[0][0]
                symbols_ZB = list(scatter_ZB.marker.symbol)
                sizes_ZB = list(scatter_ZB.marker.size)
                symbols_ZB[point] = 'x'
                sizes_ZB[point] = 15
                with fig.batch_update():
                    scatter_ZB.marker.symbol = symbols_ZB
                    scatter_ZB.marker.size = sizes_ZB

    widg_featx.observe(handle_xfeat_change, names='value')
    widg_featy.observe(handle_yfeat_change, names='value')
    widg_featmarker.observe(handle_markerfeat_change, names='value')

    output_plot = widgets.Output()
    output_dd = widgets.Output()
    output_plot.layout = widgets.Layout(width="400px", height='350px')
    output_dd.layout = widgets.Layout(width="400px", height='350px')

    viewer_plot = JsmolView()
    viewer_dd = JsmolView()

    with output_plot:
        display(viewer_plot)
    with output_dd:
        display(viewer_dd)

    marker_size = 7
    cross_size = 15
    set_markers(init=True)
    structure = D_selected_df[D_selected_df['Chem Formula'] == widg_compound_dropdown.value]['Structure'].values[0]
    viewer_dd.script(
        "load data/compressed_sensing/structures/" + structure + "_structures/"
        + widg_compound_dropdown.value + ".xyz")

    widg_compound_dropdown.observe(handle_compound_change)

    widg_display_button.on_click(display_button_clicked)

    box_features = widgets.HBox([widgets.VBox([widg_featx, widg_featy]), widg_featmarker])
    container = widgets.VBox([box_features, fig,
                              widgets.HBox([widgets.VBox([widgets.HBox([widg_compound_text, widg_display_button]),
                                                          output_plot]),
                                            widgets.VBox([widg_compound_dropdown,
                                                          output_dd])])])

    # -------------------------------------------------------------------------------------------------------------------
    # Here we define the interaction with the jsmol viewer

    def view_structure_RS(formula):
        viewer_plot.script("load data/compressed_sensing/structures/RS_structures/" + formula + ".xyz")

    def update_point_RS(trace, points, selector):
        if not points.point_inds:
            return
        set_markers(feature=widg_featmarker.value, init=True)
        sizes_RS = list(scatter_RS.marker.size)
        symbols_RS = list(scatter_RS.marker.symbol)
        sizes_ZB = list(scatter_ZB.marker.size)
        symbols_ZB = list(scatter_ZB.marker.symbol)
        for i in points.point_inds:
            sizes_RS[i] = cross_size
            symbols_RS[i] = 'x'
        with fig.batch_update():
            scatter_RS.marker.size = sizes_RS
            scatter_RS.marker.symbol = symbols_RS
            scatter_ZB.marker.size = sizes_ZB
            scatter_ZB.marker.symbol = symbols_ZB
        point = points.point_inds[0]
        formula = trace['text'][point][0]
        widg_compound_text.value = formula
        view_structure_RS(formula)

    def view_structure_ZB(formula):
        viewer_plot.script("load data/compressed_sensing/structures/ZB_structures/" + formula + ".xyz")

    def update_point_ZB(trace, points, selector):
        if not points.point_inds:
            return
        set_markers(feature=widg_featmarker.value, init=True)
        sizes_RS = list(scatter_RS.marker.size)
        symbols_RS = list(scatter_RS.marker.symbol)
        sizes_ZB = list(scatter_ZB.marker.size)
        symbols_ZB = list(scatter_ZB.marker.symbol)
        for i in points.point_inds:
            sizes_ZB[i] = cross_size
            symbols_ZB[i] = 'x'
        with fig.batch_update():
            scatter_RS.marker.size = sizes_RS
            scatter_RS.marker.symbol = symbols_RS
            scatter_ZB.marker.size = sizes_ZB
            scatter_ZB.marker.symbol = symbols_ZB
        point = points.point_inds[0]
        formula = scatter_ZB['text'][point][0]
        widg_compound_text.value = formula
        view_structure_ZB(formula)

    scatter_RS.on_click(update_point_RS)
    scatter_ZB.on_click(update_point_ZB)

    text_RS = []
    for material in D_selected_df['Chem Formula'].tolist():
        text_RS.append(material + ' - RS structure')
    text_ZB = []
    for material in D_selected_df['Chem Formula'].tolist():
        text_ZB.append(material + ' - ZB structure')

    return container


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
