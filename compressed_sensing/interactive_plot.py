import plotly.graph_objects as go
import ipywidgets as widgets
from jupyter_jsmol import JsmolView
import numpy as np


def generate_structures (RS_structures, ZB_structures):
    
    for i in range (len(RS_structures)):
        bulk_atoms = RS_structures[i].repeat(rep=3).get_chemical_symbols()
        bulk_positions = RS_structures[i].repeat(rep=3).get_positions()
        formula = RS_structures[i].get_chemical_formula()
        file = open("data/compressed_sensing/structures/RS_structures/"+formula+".xyz","w") 
        file.write ("%d\n\n"%54)
        for j in range (len(bulk_positions)):
            file.write (bulk_atoms[j])
            file.write ("\t%f\t%f\t%f\n"%(bulk_positions[j][0],bulk_positions[j][1],bulk_positions[j][2]))
        file.close()
        
    for i in range (len(ZB_structures)):
        bulk_atoms = ZB_structures[i].repeat(rep=3).get_chemical_symbols()
        bulk_positions = ZB_structures[i].repeat(rep=3).get_positions()
        formula = ZB_structures[i].get_chemical_formula()
        file = open("data/compressed_sensing/structures/ZB_structures/"+formula+".xyz","w") 
        file.write ("%d\n\n"%54)
        for j in range (len(bulk_positions)):
            file.write (bulk_atoms[j])
            file.write ("\t%f\t%f\t%f\n"%(bulk_positions[j][0],bulk_positions[j][1],bulk_positions[j][2]))
        file.close()

def make_plot (df_D, sisso, D_selected_df):
    
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
# Here we create the viewers of the materials structure

    view_RS = JsmolView()
    view_ZB = JsmolView()

    def view_structure_RS ( formula ):
        view_RS.script( "load data/compressed_sensing/structures/RS_structures/" + formula + ".xyz")

    def update_point_RS(trace, points, selector):
        if not points.point_inds:
            return
        point = points.point_inds[0]
        formula = scatter_RS['text'][point][0]
        view_structure_RS(formula)

    def view_structure_ZB ( formula ):
        view_ZB.script( "load data/compressed_sensing/structures/ZB_structures/" + formula + ".xyz")

    def update_point_ZB(trace, points, selector):
        if not points.point_inds:
            return
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

    dropdown_RS = widgets.Dropdown(
        options = D_selected_df['Chem Formula'].tolist(),
        description = 'RS structure '
    )
    dropdown_ZB = widgets.Dropdown(
        options = D_selected_df['Chem Formula'].tolist(),
        description = 'ZB structure '

    )

    viewer_RS = widgets.interactive_output (view_structure_RS, {'formula':dropdown_RS})
    viewer_ZB = widgets.interactive_output (view_structure_ZB, {'formula':dropdown_ZB})


    output_RS = widgets.Output()
    output_ZB = widgets.Output()
    with output_RS:    
        display(dropdown_RS)
        display(view_RS)
    with output_ZB:
        display(dropdown_ZB)
        display(view_ZB)

    visualizers = widgets.HBox([output_RS,output_ZB])
    container = widgets.VBox([fig,visualizers])
    
    return container