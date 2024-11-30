import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output

# Read the data and preprocess
df = pd.read_csv("melb_data2.csv")
df['Date'] = pd.to_datetime(df['Date'])
df['year'] = df['Date'].dt.year
b = df.groupby(['year', 'Date']).agg(price=pd.NamedAgg('Price', 'sum'),
                                      land=pd.NamedAgg('Landsize', 'sum'),
                                      area=pd.NamedAgg('BuildingArea', 'sum')).reset_index()

# Initialize Dash app
app = dash.Dash(__name__)

# Introduction tab layout
intro_tab_layout = html.Div([
    html.Div([
        html.H1("Introduction"),
        html.P("Welcome to Our Dash Application ! This interactive dashboard provides insightful visualizations and analysis of real estate data from Melbourne."),
        html.P("Explore various tabs to discover trends, correlations, and key insights about housing prices, property features, and market trends. Use interactive components to customize your viewing experience and gain valuable information for real estate decision-making"),
        html.P("Enjoy exploring the data and uncovering the story behind Melbourne's housing market!"),
    ], style={'margin': '50px auto', 'max-width': '800px'})
])

# Tab 01 
tab_1_layout = html.Div([
    html.Div([
        html.H1("Melbourne Housing Snapshot"),
    ], id='T1title'),

    html.Div([
        html.Div([
            html.H4("Select the Year"),
            dcc.RangeSlider(
                id='T1slider',
                min=df["year"].min(),
                max=df["year"].max(),
                step=1,
                value=[df["year"].min(), df["year"].max()],
                marks={str(i): str(i) for i in df["year"].unique()},
            )
        ], id='T11slider'),

        html.Div([
            html.H4("Opt for the variables"),
            dcc.Dropdown(
                id='T1D1',
                options=[
                    {'label': 'Price', 'value': 'price'},
                    {'label': 'Land', 'value': 'land'},
                    {'label': 'Area', 'value': 'area'},
                ],
                value=None,
                multi=True,
                clearable=True,
                searchable=True,
            ),
        ], id='T11drop'),

        html.Br(),
        html.Br(),
        html.Br(),

        html.Div([
            dcc.Graph(id='T1graph')
        ])
    ])
])

@app.callback(
    Output(component_id='T1graph', component_property='figure'),
    Input(component_id='T1slider', component_property='value'),
    Input(component_id='T1D1', component_property='value')
)
def update_t1_graph(year_range, T1D1):
    T1df = b[(b['year'] >= year_range[0]) & (b['year'] <= year_range[1])]
    fig1 = px.line(T1df, x="Date", y=T1D1,
                   hover_data={"Date": "|%B %d, %Y"},
                   title='Custom Tick Labels')
    return fig1

# Tab 02
X = 'Price'
variables = ['Landsize', 'BuildingArea', 'Propertycount']  # Define variables here

tab_2_layout = html.Div([
    html.Div([
        html.H1("Scatter Plot"),
    ], id='T2title'),

    html.Div([
        html.H4("Choose the variable to assess its correlation with price "),
        dcc.RadioItems(
            id='T2radio',
            options=[
                {'label': variable, 'value': variable} for variable in variables
            ],
            value=variables[0],  # Default value
            labelStyle={'display': 'block'},
        ),
    ], id='T21radio'),

    html.Br(),

    html.Div([
        dcc.Graph(id='T2graph')
    ]),

    # Display the correlation value
    html.Div(id='correlation-value', style={'margin-top': '20px'})
])

# Callback to update scatter plot and correlation value
@app.callback(
    [Output(component_id='T2graph', component_property='figure'),
     Output(component_id='correlation-value', component_property='children')],
    Input(component_id='T2radio', component_property='value')
)
def update_t2_graph(selected_variable):
    fig = px.scatter(df, x=X, y=selected_variable,
                     title=f"Scatter Plot: {X} vs {selected_variable}")
    
    # Calculate the correlation between X and the selected variable
    correlation_value = df[X].corr(df[selected_variable])
    correlation_text = f"Correlation between {X} and {selected_variable}: {correlation_value:.2f}"

    return fig, html.H4(correlation_text)
# Tab 03 
# Define custom colors for the pie chart
custom_colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
tab_3_layout = html.Div([
    html.Div([
        html.H1("Interactive Charts"),
    ], id='T3title'),

    # Pie chart
    html.Div([
        dcc.Graph(id='pie-chart')
    ], style={'width': '48%', 'display': 'inline-block'}),

    # Histogram
    html.Div([
        dcc.Graph(id='histogram')
    ], style={'width': '48%', 'display': 'inline-block'}),

    # Hidden div to store click data
    html.Div(id='click-data', style={'display': 'none'}),
])

# Callback to update pie chart based on click data from histogram
@app.callback(
    Output('pie-chart', 'figure'),
    Input('histogram', 'clickData')
)
def update_pie_chart(clickData):
    if clickData is not None:
        selected_data = clickData['points'][0]
        selected_value = selected_data['x']
        filtered_df = df[df['Price'] == selected_value]  # Replace 'Price' with your actual column name
        pie_fig = px.pie(filtered_df, names='Type', values='Price', title=f"Pie Chart: {selected_value}",
                         color_discrete_sequence=custom_colors)
        return pie_fig
    else:
        return px.pie(df, names='Type', values='Price', title="House Type Distribution",
                      color_discrete_sequence=custom_colors)

# Callback to update histogram based on selection from pie chart
@app.callback(
    Output('histogram', 'figure'),
    Input('pie-chart', 'clickData')
)
def update_histogram(clickData):
    if clickData is not None:
        selected_data = clickData['points'][0]
        selected_value = selected_data['label']
        filtered_df = df[df['Type'] == selected_value]  # Replace 'Type' with your actual column name
        hist_fig = px.histogram(filtered_df, x='Price', title=f"Histogram: {selected_value}")
        return hist_fig
    else:
        return px.histogram(df, x='Price', title="Price Range Distribution of Houses")

# Tab 04 
map_layout = html.Div([
    html.H1("Property Distribution Map"),
    dcc.Graph(id='property-map'),
    html.Div(id='property-details')
])

@app.callback(
    Output('property-map', 'figure'),
    Output('property-details', 'children'),
    Input('property-map', 'clickData')
)
def update_property_map(clickData):
    # Create the map
    fig = px.scatter_mapbox(df, lat='Lattitude', lon='Longtitude', color='Type',
                             hover_name='Suburb', hover_data=['Rooms', 'Price'],
                             zoom=10, height=600)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Update property details


    # Update property details
    details = html.Div()
    if clickData:
        property_id = clickData['points'][0]['pointIndex']
        property_info = df.iloc[property_id]
        details = html.Div([
            html.H2("Property Details"),
            html.P(f"Address: {property_info['Address']}"),
            html.P(f"Method of Sale: {property_info['Method']}"),
            html.P(f"Seller: {property_info['SellerG']}"),
            html.P(f"Date of Sale: {property_info['Date']}"),
        ])
    
    return fig, details

# Update the app layout to include all four tabs
app.layout = html.Div(style={'backgroundColor': 'Lavender'}, children=[
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Introduction', value='intro', children=intro_tab_layout),
        dcc.Tab(label='Trend Analysis', value='tab-1', children=tab_1_layout),
        dcc.Tab(label='Correlation Plot', value='tab-2', children=tab_2_layout),
        dcc.Tab(label='Interactive Comparison', value='tab-3', children=tab_3_layout),
        dcc.Tab(label='Custom Insights', value='tab-4', children=map_layout),
    ]),
])

if __name__ == '__main__':
    app.run_server(debug=True)
