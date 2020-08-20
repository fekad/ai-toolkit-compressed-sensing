import plotly.graph_objects as go
import ipywidgets as widgets
from jupyter_jsmol import JsmolView
import numpy as np

# from bokeh.models import TapTool, CustomJS, ColumnDataSource, HoverTool, ColumnDataSource
# from bokeh.io import show, output_notebook
# from bokeh.plotting import figure, show
# from bokeh.embed import components
# import itertools
# from bokeh.palettes import Dark2_5 as palette
#
# output_notebook()


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

    marker_size_default = 7
    cross_size_default = 15
    font_size = 12
    font_family = 'Helvetica'
    bg_color = 'rgb(229, 236, 246)'
    marker_symbol = 'circle'

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
        description="Marker",
        options=['Default size'] + features,
        value='Default size',
    )
    widg_compound_text_l = widgets.Text(
        placeholder='...',
        description='Compound:',
        disabled=False,
        layout=widgets.Layout(width='200px')
    )
    widg_compound_text_r = widgets.Text(
        placeholder='...',
        description='Compound:',
        disabled=False,
        layout=widgets.Layout(width='200px')
    )
    widg_display_button_l = widgets.Button(
        description="Display",
        layout=widgets.Layout(width='100px')
    )
    widg_display_button_r = widgets.Button(
        description="Display",
        layout=widgets.Layout(width='100px')
    )
    widg_checkbox_l = widgets.Checkbox(
        value=True,
        indent=False,
        layout=widgets.Layout(width='20px')
    )
    widg_checkbox_r = widgets.Checkbox(
        value=False,
        indent=False,
        layout=widgets.Layout(width='20px'),
        description='+'
    )
    widg_markersize = widgets.Text(
        placeholder=str(marker_size_default),
        description='Marker size',
        value=str(marker_size_default)
    )
    widg_fontsize = widgets.Text(
        placeholder=str(font_size),
        description='Font size',
        value=str(font_size)
    )
    widg_fontfamily = widgets.Text(
        placeholder=str(font_family),
        description='Font family',
        value='Helvetica'
    )
    widg_bgcolor = widgets.Text(
        placeholder=str(bg_color),
        description='BG color',
        value='rgb(229, 236, 246)'
    )
    widg_markersymbol = widgets.Text(
        placeholder=str(marker_symbol),
        description='Symbol',
        value=str(marker_symbol)
    )
    widg_update_button = widgets.Button(
        description='Update',
        layout=widgets.Layout(width='100px')
    )

    file1 = open("./assets/compressed_sensing/cross.png", "rb")
    image1 = file1.read()
    widg_img1 = widgets.Image(
        value=image1,
        format='png',
        width=30,
        height=30,
    )
    file2 = open("./assets/compressed_sensing/cross2.png", "rb")
    image2 = file2.read()
    widg_img2 = widgets.Image(
        value=image2,
        format='png',
        width=30,
        height=30,
    )

    def set_markers_size(feature='Default size', marker_size=marker_size_default):
        # Defines the size of the markers based on the input feature.
        # In case of default feature all markers have the same size.
        # Points marked with x/cross are set with a specific size

        if feature == 'Default size':

            sizes_RS = scatter_RS.marker.size = [marker_size] * RS_npoints
            sizes_ZB = scatter_ZB.marker.size = [marker_size] * ZB_npoints

            symbols_RS = list(scatter_RS.marker.symbol)
            symbols_ZB = list(scatter_ZB.marker.symbol)
            try:
                point = symbols_RS.index('x')
                sizes_RS[point] = cross_size_default
            except:
                try:
                    point = symbols_ZB.index('x')
                    sizes_ZB[point] = cross_size_default
                except:
                    pass
            try:
                point = symbols_RS.index('cross')
                sizes_RS[point] = cross_size_default
            except:
                try:
                    point = symbols_ZB.index('cross')
                    sizes_ZB[point] = cross_size_default
                except:
                    pass
            with fig.batch_update():
                scatter_RS.marker.size = sizes_RS
                scatter_ZB.marker.size = sizes_ZB
        else:

            min_value = min(min(D_selected_df.loc[D_selected_df['Structure'] == 'RS'][feature]),
                            min(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][feature]))
            max_value = max(max(D_selected_df.loc[D_selected_df['Structure'] == 'RS'][feature]),
                            max(D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][feature]))
            coeff = 2 * marker_size / (max_value - min_value)
            sizes_RS = marker_size / 2 + coeff * D_selected_df.loc[D_selected_df['Structure'] == 'RS'][
                feature]
            sizes_ZB = marker_size / 2 + coeff * D_selected_df.loc[D_selected_df['Structure'] == 'ZB'][
                feature]
            with fig.batch_update():
                scatter_RS.marker.size = sizes_RS
                scatter_ZB.marker.size = sizes_ZB

    def handle_xfeat_change(change):
        # changes the feature plotted on the x-axis
        # separating line is modified accordingly
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
        min_delta = 0.05 * abs(max_x - min_x)
        fig.layout['xaxis'].range = [min_x - min_delta, max_x + min_delta]

    def handle_yfeat_change(change):
        # changes the feature plotted on the x-axis
        # separating line is modified accordingly
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
        min_delta = 0.05 * abs(max_y - min_y)
        fig.layout['yaxis'].range = [min_y - min_delta, max_y + min_delta]

    def handle_markerfeat_change(change):
        set_markers_size(feature=change.new)

    def display_button_l_clicked(button):

        # Actions are performed only if the string inserted in the text widget corresponds to an existing compound
        if widg_compound_text_l.value in D_selected_df['Chem Formula'].tolist():
            structure_l = D_selected_df[D_selected_df['Chem Formula'] ==
                                        widg_compound_text_l.value]['Structure'].values[0]
            viewer_l.script(
                "load data/compressed_sensing/structures/" + structure_l + "_structures/"
                + widg_compound_text_l.value + ".xyz")

            symbols_RS = list(scatter_RS.marker.symbol)
            symbols_ZB = list(scatter_ZB.marker.symbol)
            try:
                point = symbols_RS.index('x')
                symbols_RS[point] = marker_symbol
            except:
                try:
                    point = symbols_ZB.index('x')
                    symbols_ZB[point] = marker_symbol
                except:
                    pass
            if structure_l == 'RS':
                point = np.where(scatter_RS['text'] == widg_compound_text_l.value)[0][0]
                symbols_RS[point] = 'x'
            if structure_l == 'ZB':
                point = np.where(scatter_ZB['text'] == widg_compound_text_l.value)[0][0]
                symbols_ZB[point] = 'x'
            with fig.batch_update():
                scatter_RS.marker.symbol = symbols_RS
                scatter_ZB.marker.symbol = symbols_ZB
            set_markers_size(feature=widg_featmarker.value)

    def display_button_r_clicked(button):

        # Actions are performed only if the string inserted in the text widget corresponds to an existing compound
        if widg_compound_text_r.value in D_selected_df['Chem Formula'].tolist():
            structure_r = D_selected_df[D_selected_df['Chem Formula'] ==
                                        widg_compound_text_r.value]['Structure'].values[0]
            viewer_r.script(
                "load data/compressed_sensing/structures/" + structure_r + "_structures/"
                + widg_compound_text_r.value + ".xyz")

            symbols_RS = list(scatter_RS.marker.symbol)
            symbols_ZB = list(scatter_ZB.marker.symbol)
            try:
                point = symbols_RS.index('cross')
                symbols_RS[point] = marker_symbol
            except:
                try:
                    point = symbols_ZB.index('cross')
                    symbols_ZB[point] = marker_symbol
                except:
                    pass
            if structure_r == 'RS':
                point = np.where(scatter_RS['text'] == widg_compound_text_r.value)[0][0]
                symbols_RS[point] = 'cross'
            if structure_r == 'ZB':
                point = np.where(scatter_ZB['text'] == widg_compound_text_r.value)[0][0]
                symbols_ZB[point] = 'cross'
            with fig.batch_update():
                scatter_RS.marker.symbol = symbols_RS
                scatter_ZB.marker.symbol = symbols_ZB
            set_markers_size(feature=widg_featmarker.value)

    def update_button_clicked(button):

        try:
            fig.update_layout(
                plot_bgcolor=widg_bgcolor.value,
                font=dict(
                    size=int(widg_fontsize.value),
                    family=widg_fontfamily.value
                )
            )
        except:
            pass

    def handle_checkbox_l(change):
        if change.new:
            widg_checkbox_r.value = False
        else:
            widg_checkbox_r.value = True

    def handle_checkbox_r(change):
        if change.new:
            widg_checkbox_l.value = False
        else:
            widg_checkbox_l.value = True

    widg_featx.observe(handle_xfeat_change, names='value')
    widg_featy.observe(handle_yfeat_change, names='value')
    widg_featmarker.observe(handle_markerfeat_change, names='value')
    widg_checkbox_l.observe(handle_checkbox_l, names='value')
    widg_checkbox_r.observe(handle_checkbox_r, names='value')
    widg_display_button_l.on_click(display_button_l_clicked)
    widg_display_button_r.on_click(display_button_r_clicked)
    widg_update_button.on_click(update_button_clicked)

    output_l = widgets.Output()
    output_r = widgets.Output()
    output_l.layout = widgets.Layout(width="400px", height='350px')
    output_r.layout = widgets.Layout(width="400px", height='350px')

    viewer_l = JsmolView()
    viewer_r = JsmolView()

    with output_l:
        display(viewer_l)
    with output_r:
        display(viewer_r)

    scatter_RS.marker.symbol = [marker_symbol] * RS_npoints
    scatter_ZB.marker.symbol = [marker_symbol] * ZB_npoints
    set_markers_size()

    box_layout = widgets.Layout(
        border='dashed 1px',
    )
    box_features = widgets.HBox([
        widgets.VBox([widg_featx, widg_featy, widg_featmarker]),
        widgets.VBox([widgets.HBox([widg_markersize, widg_markersymbol]),
                      widgets.HBox([widg_fontsize, widg_fontfamily]),
                      widg_bgcolor, widg_update_button], layout=box_layout),
    ])

    container = widgets.VBox([box_features, fig,
                              widgets.HBox([
                                  widgets.VBox(
                                      [widgets.HBox([widg_compound_text_l, widg_display_button_l, widg_img1,
                                                     widg_checkbox_l]),
                                       output_l]),
                                  widgets.VBox(
                                      [widgets.HBox([widg_compound_text_r, widg_display_button_r, widg_img2,
                                                     widg_checkbox_r]),
                                       output_r]),
                              ])
                              ])

    # -------------------------------------------------------------------------------------------------------------------
    # Here we define the interaction with the jsmol viewer

    def view_structure_RS_l(formula):
        viewer_l.script("load data/compressed_sensing/structures/RS_structures/" + formula + ".xyz")

    def view_structure_RS_r(formula):
        viewer_r.script("load data/compressed_sensing/structures/RS_structures/" + formula + ".xyz")

    def view_structure_ZB_l(formula):
        viewer_l.script("load data/compressed_sensing/structures/ZB_structures/" + formula + ".xyz")

    def view_structure_ZB_r(formula):
        viewer_r.script("load data/compressed_sensing/structures/ZB_structures/" + formula + ".xyz")

    def update_point_RS(trace, points, selector):
        # changes the points labeled with a cross on the map.
        if not points.point_inds:
            return

        symbols_RS = list(scatter_RS.marker.symbol)
        symbols_ZB = list(scatter_ZB.marker.symbol)

        # The element previously marked with x/cross is marked with circle as default value
        if widg_checkbox_l.value:
            try:
                point = symbols_RS.index('x')
                symbols_RS[point] = marker_symbol
            except:
                try:
                    point = symbols_ZB.index('x')
                    symbols_ZB[point] = marker_symbol
                except:
                    pass
        if widg_checkbox_r.value:
            try:
                point = symbols_RS.index('cross')
                symbols_RS[point] = marker_symbol
            except:
                try:
                    point = symbols_ZB.index('cross')
                    symbols_ZB[point] = marker_symbol
                except:
                    pass

        if widg_checkbox_l.value:
            symbols_RS[points.point_inds[0]] = 'x'
        if widg_checkbox_r.value:
            symbols_RS[points.point_inds[0]] = 'cross'

        with fig.batch_update():
            scatter_RS.marker.symbol = symbols_RS
            scatter_ZB.marker.symbol = symbols_ZB

        set_markers_size(feature=widg_featmarker.value)
        formula = trace['text'][points.point_inds[0]][0]

        if widg_checkbox_l.value:
            widg_compound_text_l.value = formula
            view_structure_RS_l(formula)
        if widg_checkbox_r.value:
            widg_compound_text_r.value = formula
            view_structure_RS_r(formula)

    def update_point_ZB(trace, points, selector):
        if not points.point_inds:
            return

        symbols_RS = list(scatter_RS.marker.symbol)
        symbols_ZB = list(scatter_ZB.marker.symbol)

        # The element previously marked with x/cross is marked with circle as default value
        if widg_checkbox_l.value:
            try:
                point = symbols_RS.index('x')
                symbols_RS[point] = marker_symbol
            except:
                try:
                    point = symbols_ZB.index('x')
                    symbols_ZB[point] = marker_symbol
                except:
                    pass
        if widg_checkbox_r.value:
            try:
                point = symbols_RS.index('cross')
                symbols_RS[point] = marker_symbol
            except:
                try:
                    point = symbols_ZB.index('cross')
                    symbols_ZB[point] = marker_symbol
                except:
                    pass

        if widg_checkbox_l.value:
            symbols_ZB[points.point_inds[0]] = 'x'
        if widg_checkbox_r.value:
            symbols_ZB[points.point_inds[0]] = 'cross'

        with fig.batch_update():
            scatter_RS.marker.symbol = symbols_RS
            scatter_ZB.marker.symbol = symbols_ZB

        set_markers_size(feature=widg_featmarker.value)
        formula = trace['text'][points.point_inds[0]][0]

        if widg_checkbox_l.value:
            widg_compound_text_l.value = formula
            view_structure_ZB_l(formula)
        if widg_checkbox_r.value:
            widg_compound_text_r.value = formula
            view_structure_ZB_r(formula)

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
