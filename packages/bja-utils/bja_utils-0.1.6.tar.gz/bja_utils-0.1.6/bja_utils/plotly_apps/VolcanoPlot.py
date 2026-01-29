import dash
import numpy as np
import pandas as pd
from dash import html, dcc, Output, Input, State, callback, no_update, ctx, Patch
from plotly import express as px
import dash_ag_grid as dag
# import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from ..utils import calc_ttest_paired, calc_ttest_ind, SimpleLRUCache
from .utils import get_scatter_size, update_figure_base_style


class OmeMetadata:
    def __init__(
            self,
            ome_name: str,
            feature_ids,  # Any iterable of unique feature IDs

            indiv_features_table: pd.DataFrame,
            grouped_features_table: pd.DataFrame,

            indiv_features_table_column_definitions,
            grouped_features_table_column_definitions,

            on_hover_title: str,
            on_hover_data: dict,  # dictionary of {'table_column_name': True, ... }


    ):
        self.ome_name = ome_name
        self.feature_ids = feature_ids
        self.indiv_features_table = indiv_features_table
        self.grouped_features_table = grouped_features_table
        self.indiv_features_table_column_definitions = indiv_features_table_column_definitions
        self.grouped_features_table_column_definitions = grouped_features_table_column_definitions
        self.on_hover_title = on_hover_title
        self.on_hover_data = on_hover_data


class VolcanoPlot:
    def __init__(
            self,
            quants_df,
            sample_metadata,
            feature_metadata: list[OmeMetadata],
            cached_results_size: int = 10,
        ):

        self.quants_df = quants_df
        self.sample_metadata = sample_metadata
        self.feature_metadata = feature_metadata

        self.cached_ttest_results = SimpleLRUCache(capacity=cached_results_size)


sample_metadata = load_data.get_sample_metadata()
bmdf = load_data.get_bamm_metadata()
quants_df = load_data.get_combined_quants()
lmdf = load_data.get_lipid_metadata()
vl_sample_types = sample_metadata['SampleType'].unique()
prot_features = bmdf.loc[bmdf['IsPlasmaOrLymph']].index

protein_indiv_table = load_data.get_volcano_protein_indiv_table()
go_terms_table = load_data.get_go_terms_data()
go_terms_table = go_terms_table.rename({'# in term': 'Number of proteins in GO term'}, axis=1)
go_terms_table['Internal IDs in class'] = go_terms_table['Internal IDs'].apply(lambda entries: entries.split(', '))

lipid_indiv_table = load_data.get_volcano_lipid_indiv_table()
lipid_class_table = load_data.get_lipid_classes_metadata_table()

volcano_plot_dbc_layout = dbc.Container(
    # style={'display': 'flex', 'flexDirection': 'column', 'height': '80vh'},
    fluid=True,
    children=[
        dbc.Row(
            children=[
                html.H1("Volcano Plot with Sample Selection"),
            ]
        ),

        dbc.Row(
            # style={'flex': '0.5', 'margin-right': '10px'},
            children=[
                dbc.Col(
                    width=6,
                    children=[
                        html.Small('Select omics'),

                        dcc.Dropdown(
                            id='omics-selector',
                            options=[{'label': 'Proteomics', 'value': 'Proteomics'},
                                     {'label': 'Lipidomics', 'value': 'Lipidomics'}],
                            value='Proteomics', multi=False)
                    ],
                ),

                dbc.Col(width=6),

            ],
        ),

        dbc.Row(
            className='mb-2',
            align='center',
            children=[
                dbc.Col(
                    width=6,
                    children=[
                        html.Small("Select depots for left side"),
                        dcc.Dropdown(
                            id='left-side-depots-dropdown',
                            multi=True,
                            options=[{'label': sample_type, 'value': sample_type} for sample_type in vl_sample_types],
                            value=['Ileum vein']
                        )
                    ],
                ),

                dbc.Col(
                    width=6,
                    children=[
                        html.Small("Select depots for right side"),
                        dcc.Dropdown(
                            id='right-side-depots-dropdown',
                            multi=True,
                            options=[{'label': sample_type, 'value': sample_type} for sample_type in vl_sample_types],
                            value=['Ileum lymph']
                        )
                    ],
                ),
            ],
        ),

        dbc.Row(
            children=[

                dbc.Col(
                    width=6,
                    children=[
                        html.Small("Select samples for left side"),
                        dcc.Dropdown(
                            id='left-side-samples-dropdown',
                            multi=True,
                            options=[{'label': sample_display_name, 'value': sample_abbrev} for
                                     sample_display_name, sample_abbrev
                                     in zip(sample_metadata['Display name'], sample_metadata.index)],
                            value=[],
                        )
                    ],
                ),

                dbc.Col(
                    width=6,
                    children=[
                        html.Small("Select samples for right side"),
                        dcc.Dropdown(
                            id='right-side-samples-dropdown',
                            multi=True,
                            options=[{'label': sample_display_name, 'value': sample_abbrev} for
                                     sample_display_name, sample_abbrev
                                     in zip(sample_metadata['Display name'], sample_metadata.index)],
                            value=[]
                        )
                    ],
                ),
            ],
        ),

        # dbc.Row(
        #     children=[
        #         # Pre-calculated t-tests selector, to quickly select the comparisons used in the paper
        #         dcc.Dropdown(
        #             id='precalculated-ttest-selector', multi=False,
        #             options=[{'label': 'None', 'value': 'None'},
        #                      {'label': 'Paired, [non-thoracic lymph - SMV plasma]', 'value': 'paired [all lymph except thoracic - SMV plasma]'},
        #                      {'label': 'Paired, [ileum lymph - ileum plasma]', 'value': 'paired [ileum lymph - ileum plasma]'},
        #                      {'label': 'Paired, [prox. bowel lymph - prox. bowel plasma]', 'value': 'paired [prox bowel lymph - prox bowel plasma]'}],
        #             value='None',
        #         )
        #     ],
        # ),



        dbc.Row(
            children=[
                dcc.Checklist(
                    id='paired-or-indep-checkbox',
                    options=[{'label': 'Use paired samples', 'value': 'use_paired'}],
                    value=[],
                    labelStyle={'display': 'flex', 'alignItems': 'center', 'fontSize': '16px', 'gap': '8px'},
                    inputStyle={'margin': '0', 'verticalAlign': 'middle'},
                ),

                dbc.Button(
                    children=[
                        html.Label('Update volcano plot',  style={'fontSize': '18px'}),
                    ],
                    id='update-button',
                    style={'width': '50vw'},
                    n_clicks=1,  # SET TO 1 TO ENSURE IT RUNS AT STARTUP
                ),
                html.Label(
                    id='status-message',
                    children='Select samples or depots and click update.'
                )
            ],
        ),

        dbc.Row(
            style={'minHeight': '300px',
                   # 'flex': '1 1 30vh'
                   },
            children=[
                dcc.Graph(id='volcano-plot'),
            ],
        ),


        dbc.Row(
            children=[
                # dbc.Col(width=1,),
                dbc.Col(
                    # className='me-3',  # me-3 = "Margin-end: 1rem"
                    width=5,
                    children=[
                        html.Div(
                            style={'gap': '10px', 'display': 'flex', 'alignItems': 'center',
                                   'flexDirection': 'row', 'flexWrap': 'wrap', 'minWidth': 0},
                            children=[

                                html.Label(
                                    'Highlight biomolecules',
                                    style={'flex': '0 0 auto', 'fontSize': '18px'},
                                ),

                                dcc.Input(
                                    id='filter-indiv-table-input',
                                    placeholder='Highlight selected biomolecules in volcano plot',
                                    style={'fontSize': '17px', 'flex': '1 1 auto'},
                                ),

                                dbc.Button(
                                    id='clear-indiv-table-button',
                                    children=html.Label('Clear selected features', style={'fontSize': '15px'}),
                                    style={'flex': '0 0 auto', 'marginLeft': 'auto'},
                                ),
                            ],
                        ),

                        html.Div(
                            children=[
                                dag.AgGrid(
                                    id='filter-indiv-table',
                                    dashGridOptions={'pagination': True,
                                                     'animateRows': True,
                                                     'paginationPageSize': 50,
                                                     'rowSelection': 'multiple',
                                                     'rowMultiSelectWithClick': True,
                                                     'suppressCellFocus': True,
                                                     'cacheQuickFilter': True,
                                                     },
                                    columnSize='responsiveSizeToFit',
                                    className="ag-theme-alpine compact",

                                ),
                            ],
                        ),
                    ],
                ),

                dbc.Col(width=1),

                dbc.Col(
                    width=6,
                    children=[
                        html.Div(
                            style={'gap': '10px', 'display': 'flex', 'alignItems': 'center',
                                   'flexDirection': 'row', 'flexWrap': 'wrap', 'minWidth': 0},
                            children=[
                                html.Label(
                                    'Highlight GO terms/lipid classes',
                                    style={'flex': '0 0 auto', 'fontSize': '15px'},
                                ),

                                dcc.Input(
                                    id='filter-classes-table-input',
                                    placeholder='Search for GO terms/lipid classes',
                                    style={'fontSize': '17px', 'flex': '1 1 auto'},
                                ),

                                dbc.Button(
                                    id='clear-classes-table-button',
                                    children=html.Label('Clear selected classes', style={'fontSize': '15px'}),
                                    style={'flex': '0 0 auto', 'marginLeft': 'auto'},
                                ),

                            ],

                        ),

                        html.Div(
                            children=[
                                dag.AgGrid(
                                    id='filter-classes-table',
                                    dashGridOptions={'pagination': True,
                                                     'animateRows': True,
                                                     'paginationPageSize': 50,
                                                     'rowSelection': 'multiple',
                                                     'rowMultiSelectWithClick': True,
                                                     'suppressCellFocus': True,
                                                     'cacheQuickFilter': True,
                                                     },
                                    columnSize='responsiveSizeToFit',
                                    className="ag-theme-alpine compact",
                                ),
                            ],
                        ),
                    ],
                ),

                # dbc.Col(width=1),
            ],
        ),

        dbc.Row(
            children=[
                dbc.Button(children='Download volcano plot data',
                           id='btn-download'),
                dcc.Download(id="download-dataframe-csv")
            ],
        ),

        dcc.Store(id='error-store-1'),
        dcc.Store(id='error-store-2'),
    ],
)


@callback(
    Output('status-message', 'children'),
    Input('error-store-1', 'data'),
    Input('error-store-2', 'data'),

    prevent_initial_call=True,
)
def error_store_write_error_to_status(store1, store2):
    if ctx.triggered_id == 'error-store-1':
        return store1
    if ctx.triggered_id == 'error-store-2':
        return store2
    raise ValueError



@callback(
    [
        Output('volcano-plot', 'figure'),
        # Output('status-message', 'children', allow_duplicate=True)
        Output('error-store-1', 'data'),
    ],
    Input('update-button', 'n_clicks'),
    Input('filter-indiv-table', 'selectedRows'),
    Input('filter-classes-table', 'selectedRows'),

    State('omics-selector', 'value'),
    State('left-side-depots-dropdown', 'value'),
    State('right-side-depots-dropdown', 'value'),
    State('left-side-samples-dropdown', 'value'),
    State('right-side-samples-dropdown', 'value'),
    State('paired-or-indep-checkbox', 'value'),

    # prevent_initial_call=True,

    running=[
        # (Output('status-message', 'children'),
        #  'Processing, please wait. This may take up to 30 seconds.',
        #  no_update),   # Set the message "Processing please wait" at the start of Running, but send no_update at the end, to ensure that the custom message
        # that is also returned gets displayed, otherwise the message at the end will overwrite.
        # Putting no_update for the finished message does give an error:
        #     "Objects are not valid as a React child (found: object with keys {_dash_no_update}).
        #     If you meant to render a collection of children, use an array instead."
        # However, this error does not seem to affect anything
        (Output('update-button', 'disabled'), True, False),
    ],

    # on_error=TESTING_ERROR_HANDLING,

)
def update_volcano_plot(
        n_clicks,
        indiv_selected_rows,
        classes_selected_rows,

        omics_selection,
        left_side_depots,
        right_side_depots,
        left_side_samples,
        right_side_samples,
        use_paired,
):

    # return no_update, 'ASDFASDF'

    # use_paired comes in as a list of strings that could be empty, so switch it to a boolean for my sanity
    if use_paired and use_paired[0] == 'use_paired':
        use_paired = True
    else:
        use_paired = False

    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    #     if n_clicks == 0:
    #         return px.scatter(title='Select samples and update plot.')

    if (not left_side_depots and not left_side_samples) or (not right_side_depots and not right_side_samples):
        return no_update, "Select at least two samples, or a depot with at least two samples for both sides."

    subset = quants_df.copy()
    if omics_selection == 'Proteomics':
        subset = subset[prot_features]
    elif omics_selection == 'Lipidomics':
        subset = subset[lmdf.index]
    elif omics_selection == 'Both':
        subset = subset

    total_left_side_samples = list(sample_metadata.loc[sample_metadata['SampleType'].isin(left_side_depots)].index)
    total_right_side_samples = list(sample_metadata.loc[sample_metadata['SampleType'].isin(right_side_depots)].index)

    # Add any additional samples if they were selected separately from the depots

    left_additional_samples = [sample for sample in left_side_samples if sample not in total_left_side_samples]
    right_additional_samples = [sample for sample in right_side_samples if sample not in total_right_side_samples]

    total_left_side_samples += left_additional_samples
    total_right_side_samples += right_additional_samples

    if use_paired:
        if not left_side_samples or not right_side_samples:
            return no_update, "You must choose individual Samples for the paired test. Any Depot selections are ignored."
        # Check whether there are equal length lists of samples in the dropdowns
        if len(left_side_samples) != len(right_side_samples):
            return no_update, ("You must select an equal number of samples in the sample selectors for the paired test. "
                          "Note that depot selections are ignored for paired test.")

        # Overwrite the total_left or right samples from above
        total_left_side_samples = left_side_samples
        total_right_side_samples = right_side_samples

    # Cache the results for the t-test results for this combo of samples in proteome/lipidome
    sorted_left_samples = sorted(total_left_side_samples)
    sorted_right_samples = sorted(total_right_side_samples)
    unique_results_string = ''.join(sorted_left_samples + sorted_right_samples) + omics_selection  # make a string with the sample IDs and the omics type that ensures uniqueness

    global scatter_df

    if unique_results_string in cached_ttest_results:
        scatter_df = cached_ttest_results[unique_results_string]

        print('Using cached data')

    else:
        scatter_df = []
        for feature_col in subset:
            if use_paired:
                diff_mean, pval = calc_ttest_paired(subset[feature_col], leftsamples=total_left_side_samples,
                                                    rightsamples=total_right_side_samples)
            else:
                diff_mean, pval = calc_ttest_ind(subset[feature_col], leftsamples=total_left_side_samples,
                                                 rightsamples=total_right_side_samples)
            scatter_df.append({'feature': feature_col, 'Log2 fold change': diff_mean, 'p-value': pval})

        scatter_df = pd.DataFrame(scatter_df).set_index('feature')

        cached_ttest_results[unique_results_string] = scatter_df


    scatter_df['-Log10(p-value)'] = -np.log10(scatter_df['p-value'])

    if omics_selection == 'Proteomics':
        scatter_df = scatter_df.join(bmdf.loc[prot_features])

        hover_name = 'Gene ID'
        hover_data = {'size': False,  # remove size
                      'color': False,
                      'Protein names': True,
                      'Gene Names': True,}
        labels = {'Entry': 'Uniprot accession'}
        title = f"Proteomics volcano plot"


    elif omics_selection == 'Lipidomics':
        scatter_df = scatter_df.join(lmdf)

        hover_name = 'Annotation'
        hover_data = {'size': False,  # remove the size label
                      'color': False,
                      'LipidClass': True,
                      'LipidSuperClass': True,
                      }
        labels = {'LipidClass': 'Lipid class', 'LipidSuperClass': 'Lipid category'}
        title = 'Lipidomics volcano plot'

    else:
        raise ValueError('omics_selection is not valid')


    test = scatter_df

    ids_indiv_to_highlight = [x['Internal ID'] for x in indiv_selected_rows]
    ids_in_classes_to_highlight = [x for list_of_ids_in_class in classes_selected_rows
                                   for x in list_of_ids_in_class['Internal IDs in class']]
    all_ids_to_highlight = ids_indiv_to_highlight + ids_in_classes_to_highlight

    scatter_df['is_highlighted'] = False
    scatter_df.loc[all_ids_to_highlight, 'is_highlighted'] = True  # will not fail, even if all_ids is empty

    smallsize, medsize, largesize, extralargesize = 1, 2.5, 5, 8
    size_to_signif = {smallsize: 'ns', medsize: 'below f.c. cutoff', largesize: 'signif.', extralargesize: 'Selected'}
    signif_to_color = {'Selected': '#222222', 'signif.': '#CD5460', 'below f.c. cutoff': '#9BA7C0', 'ns': '#AAAAAA'}

    scatter_df['size'] = scatter_df.apply(
        lambda row: get_scatter_size(pvalue=row['p-value'], effectsize=row['Log2 fold change'],
                                     is_highlighted=row['is_highlighted'],
                                     smallsize=smallsize, medsize=medsize,
                                     largesize=largesize, extralargesize=extralargesize),
        axis=1, )
    scatter_df['color'] = scatter_df['size'].map(size_to_signif)

    scatter_df = scatter_df.sort_values('size')  # SORT ON SIZE TO ENSURE CORRECT PLOTTING ORDER

    fig = px.scatter(
        scatter_df,
        x = 'Log2 fold change',
        y = '-Log10(p-value)',
        size='size',
        size_max=10,
        color='color',
        color_discrete_map=signif_to_color,
        hover_name=hover_name,
        hover_data=hover_data,
        labels=labels,
        title=title,
    )

    fig.update_layout(height=600, autosize=True)
    max_y_lim = scatter_df['-Log10(p-value)'].max()
    fig.update_yaxes(range=[-0.1, max_y_lim*1.1], constrain='range')  # constrain=range limits the y-axis zoom to the y-limits
    update_figure_base_style(fig)

    return fig, "Processing complete."


@callback(
    [
        Output('filter-indiv-table', 'rowData'),
        Output('filter-indiv-table', 'columnDefs'),
        Output('filter-indiv-table', 'selectedRows'),

        Output('filter-classes-table', 'rowData'),
        Output('filter-classes-table', 'columnDefs'),
        Output('filter-classes-table', 'selectedRows'),
    ],

    Input('omics-selector', 'value'),

    Input('clear-indiv-table-button', 'n_clicks'),
    Input('clear-classes-table-button', 'n_clicks'),

    # prevent_initial_call = True,
)
def update_tables_on_changes(ome_value, clear_indiv_table_n_clicks, clear_classes_table_n_clicks):
    triggered_id = ctx.triggered_id
    if triggered_id == 'clear-indiv-table-button':
        return (
            no_update,
            no_update,
            [],
            no_update,
            no_update,
            no_update,
        )
    elif triggered_id == 'clear-classes-table-button':
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            [],
        )

    if ome_value == 'Proteomics':
        return (
            protein_indiv_table.to_dict('records'), # protein_indiv_table,
            [{'field': col} for col in ['Gene ID', 'Uniprot accession', 'Internal ID']],
            [],
            go_terms_table.to_dict('records'), # protein_go_terms_table,
            [{'field': col} for col in ['GO term name', 'GO ID', 'Number of proteins in GO term']],
            [],
        )
    elif ome_value == 'Lipidomics':
        return (
            lipid_indiv_table,
            [{'field': col} for col in ['Annotation', 'Lipid class', 'Lipid category', 'Internal ID']],
            [],
            lipid_class_table,
            [{'field': col} for col in ['Lipid class or sub-class', 'Number of IDs in class']],
            [],
        )
    else:
        raise ValueError('ome_value is not valid')



@callback(
    Output("download-dataframe-csv", "data"),
    Output('status-message', 'children', allow_duplicate=True),
    Input("btn-download", "n_clicks"),
    prevent_initial_call=True
)
def download_csv(n_clicks):
    """Convert the DataFrame to a CSV file. Store the CSV in memory, and then start the download."""

    try:
        if scatter_df is None or not isinstance(scatter_df, pd.DataFrame):
            raise ValueError('No data available to download.')

        # Drop the size column if it's in the columns
        return (dcc.send_data_frame((scatter_df.drop('size', axis=1) if 'size' in scatter_df.columns else scatter_df).to_csv, filename='volcano_data.csv'),
                "Volcano data downloaded.")

    except Exception as e:
        return None, f"Could not download data. Error message: {str(e)}"


    # return dcc.send_string(csv_string.getvalue(), filename="dataframe.csv")


@callback(Output('filter-indiv-table', "dashGridOptions"),
    Input("filter-indiv-table-input", "value"))
def update_indiv_table_filter(filter_value):
    newFilter = Patch()
    newFilter['quickFilterText'] = filter_value
    return newFilter


@callback(Output('filter-classes-table', "dashGridOptions"),
    Input("filter-classes-table-input", "value"))
def update_classes_table_filter(filter_value):
    newFilter = Patch()
    newFilter['quickFilterText'] = filter_value
    return newFilter





