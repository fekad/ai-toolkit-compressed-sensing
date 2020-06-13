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
               x_axis_label=x_label,  y_axis_label=y_label)
    
    # plot reference diagonal
    xy_min = min([min(arr) for arr in xs+ys])
    xy_max = max([max(arr) for arr in xs+ys])
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
    p.legend.location='top_left'
    show(p)



def make_interactive_plot (df_D, sisso, D_selected_df, viewer):
    
    # the features of the plot are taken from the SissoRegressor object
    feat_x = df_D.columns[sisso.l0_selected_indices[1]][0]
    feat_y = df_D.columns[sisso.l0_selected_indices[1]][1]

    # coefficients and intercept used to create the line separating the RS vs ZB materials
    coeff_x = sisso.coefs[sisso.l0_selected_indices[1][0]]
    coeff_y = sisso.coefs[sisso.l0_selected_indices[1][1]]
    intercept = sisso.intercept

    def f_y ( y, coeff_x, coeff_y , intercept):

        return -y*coeff_y/coeff_x - intercept/coeff_x     

    # initial and final points of the separating line
    y_0 = D_selected_df[feat_y].min()
    x_0 = f_y(y_0, coeff_x, coeff_y, intercept)
    y_1 = D_selected_df[feat_y].max()
    x_1 = f_y(y_1, coeff_x, coeff_y, intercept)

    # the interactive plot is constructed with a figure widget
    fig = go.FigureWidget()

    # the final plot is the sum of two traces, respectively containing the RS vs ZB materials
    fig.add_trace(
        (
        go.Scatter(
            mode='markers',
            x=D_selected_df.loc[D_selected_df['Structure']=='RS'][feat_x], 
            y=D_selected_df.loc[D_selected_df['Structure']=='RS'][feat_y],
            customdata = np.dstack((D_selected_df.loc[D_selected_df['Structure']=='RS']['energy_diff'],
                          D_selected_df.loc[D_selected_df['Structure']=='RS']['P_predict']))[0],
            text = D_selected_df.loc[D_selected_df['Structure']=='RS'][['Chem Formula']],
            hovertemplate = 
            r"<b>%{text}</b><br><br>" +
            "x axis: %{x:,.2f}<br>" +
            "y axis: %{y:,.2f}<br>" +
            "ΔE reference:  %{customdata[0]:,.4f}<br>"+
            "ΔE predicted:  %{customdata[1]:,.4f}<br>",
            name = 'RS'
        )
        ))
    fig.add_trace(
        (
        go.Scatter(
            mode='markers',
            x=D_selected_df.loc[D_selected_df['Structure']=='ZB'][feat_x], 
            y=D_selected_df.loc[D_selected_df['Structure']=='ZB'][feat_y],
            customdata = np.dstack((D_selected_df.loc[D_selected_df['Structure']=='ZB']['energy_diff'],
                          D_selected_df.loc[D_selected_df['Structure']=='ZB']['P_predict']))[0],
            text = D_selected_df.loc[D_selected_df['Structure']=='ZB'][['Chem Formula']],
            hovertemplate = 
            r"<b>%{text}</b><br><br>" +
            "x axis: %{x:,.2f}<br>" +
            "y axis: %{y:,.2f}<br>" +
            "ΔE reference:  %{customdata[0]:,.4f}<br>"+
            "ΔE predicted:  %{customdata[1]:,.4f}<br>",
            name='ZB'
        )
        ))
    
    # add the separating line onto the plot
    fig.layout = {    
        'shapes': [
            {
                'type': 'line',
                'x0': x_0,
                'y0': y_0,
                'x1': x_1,
                'y1': y_1,
                'line': {
                    'color': 'grey',
                    'width': 2,
                    'dash': "dashdot"
                },
            }
        ],
        'showlegend': True
    }

    fig.update_layout(
        xaxis_title= feat_x,
        yaxis_title= feat_y,
        hoverlabel=dict(
            bgcolor="white", 
            font_size=16, 
            font_family="Rockwell"
        )
    )

    scatter_RS = fig.data[0]
    scatter_ZB = fig.data[1]

#-------------------------------------------------------------------------------------------------------------------------------
# Here we define the interaction with the jsmol viewer

    marker_size = 7
    RS_npoints = len(D_selected_df.loc[D_selected_df['Structure']=='RS'])
    ZB_npoints = len(D_selected_df.loc[D_selected_df['Structure']=='ZB'])

    scatter_RS.marker.size = [marker_size] * RS_npoints
    scatter_RS.marker.symbol = ["circle"] * RS_npoints

    def view_structure_RS ( formula ):
        viewer.script( "load data/compressed_sensing/structures/RS_structures/" + formula + ".xyz")
  
    def update_point_RS(trace, points, selector):
        if not points.point_inds:
            return
        scatter_RS.marker.size = [marker_size] * RS_npoints
        scatter_RS.marker.symbol = ["circle"] * RS_npoints
        scatter_ZB.marker.size = [marker_size] * ZB_npoints
        scatter_ZB.marker.symbol = ["circle"] * ZB_npoints
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
        viewer.script( "load data/compressed_sensing/structures/ZB_structures/" + formula + ".xyz")

    def update_point_ZB(trace, points, selector):
        if not points.point_inds:
            return
        scatter_RS.marker.size = [marker_size] * RS_npoints
        scatter_RS.marker.symbol = ["circle"] * RS_npoints
        scatter_ZB.marker.size = [marker_size] * ZB_npoints
        scatter_ZB.marker.symbol = ["circle"] * ZB_npoints
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
        text_RS.append(material +  ' - RS structure')
    text_ZB = []
    for material in D_selected_df['Chem Formula'].tolist():
        text_ZB.append(material +  ' - ZB structure')
   
    return fig



def viewer_dd ( viewer, D_selected_df ):
    
    dropdown_compounds = widgets.Dropdown(
        options = D_selected_df['Chem Formula'].tolist(),
        description = 'Compound '
    )

    dropdown_structure = widgets.Dropdown(
        options = ['RS','ZB'],
        description = 'Structure '
    )

    button = widgets.Button(description="Visualize")

    def on_button_clicked(button):
        viewer.script( "load data/compressed_sensing/structures/"+ dropdown_structure.value +"_structures/" + dropdown_compounds.value + ".xyz")

    button.on_click(on_button_clicked)
    container = widgets.HBox([dropdown_compounds,dropdown_structure,button])

    return container