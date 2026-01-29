import plotly.graph_objects as go


def custom_legend_plotly(
        fig,
        entries,
        palette,
        markers='circle',
        sizes=8,
        lines=False,
        line_widths=2,
        edgecolors=None,
        alphas=1.0,
        sort=False,
        labels=None,
        legend_name='legend',
        ncol=1,
        columnspacing=0.8,
        entry_fontsize=12,
        entry_fontweight='normal',
        title_text=None,
        title_fontsize=14,
        title_fontweight='bold',
        legend_x=1,
        legend_y=1,
        xanchor='left',
        yanchor='top',
        legend_bgcolor='rgba(255,255,255,0.8)',
        legend_bordercolor='black',
        legend_borderwidth=1
):
    """
    Customize plotly legends with an interface similar to the helper method `customize_legend`, above.

    Note: Currently, ncol and columnspacing are ignored.
    """

    # Prepare entries and labels
    if labels is not None:
        entries = {entry: label for entry, label in zip(entries, labels)}
    if sort:
        if isinstance(entries, dict):
            entries = dict(sorted(entries.items()))
        else:
            entries = sorted(entries)

    if isinstance(entries, dict):
        labels = list(entries.values())
        keys = list(entries.keys())
    else:
        labels = entries
        keys = entries

    # Normalize markers, sizes, lines, alphas, edgecolors
    if isinstance(markers, str):
        markers = [markers] * len(keys)
    if isinstance(lines, bool):
        lines = [lines] * len(keys)
    if isinstance(sizes, (int, float)):
        sizes = [sizes] * len(keys)
    if isinstance(alphas, (int, float)):
        alphas = [alphas] * len(keys)
    if edgecolors is None:
        edgecolors = [None] * len(keys)

    # Add dummy traces for legend
    for k, label, marker, size, is_line, alpha, ec in zip(keys, labels, markers, sizes, lines, alphas, edgecolors):
        color = palette[k]
        if is_line:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                line=dict(color=color, width=line_widths),
                name=label,
                showlegend=True,
                legend=legend_name,
                opacity=alpha
            ))
        else:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(symbol=marker, size=size, color=color,
                            line=dict(color=ec or color, width=line_widths)),
                name=label,
                showlegend=True,
                legend=legend_name,
                opacity=alpha
            ))

    # Configure the legend layout to float over the figure
    layout_dict = dict(
        x=legend_x,
        y=legend_y,
        xref='paper',
        yref='paper',
        xanchor=xanchor,
        yanchor=yanchor,
        font=dict(size=entry_fontsize, weight=entry_fontweight, family='Arial'),
        title=dict(text=title_text, font=dict(size=title_fontsize, weight=title_fontweight, family='Arial')),
        # title_side='top',
        indentation=-5,
        bgcolor=legend_bgcolor,
        bordercolor=legend_bordercolor,
        borderwidth=legend_borderwidth,
        itemclick=False,
        itemdoubleclick=False,
    )
    fig.update_layout({legend_name: layout_dict})

    return fig


def update_figure_base_style(fig: go.Figure):
    """
    Cleans up the format of the default plotly figure formatting.
    White background, subtle gridlines, black spines, height=600.
    """
    fig.update_layout(
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showline=True,
            linewidth=1,
            linecolor='black',
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            zerolinecolor='lightgray',
            zerolinewidth=1,
            zeroline=True,
            mirror=False
        ),
        yaxis=dict(
            showline=True,
            linewidth=1,
            linecolor='black',
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            zerolinecolor='lightgray',
            zerolinewidth=1,
            zeroline=True,
            mirror=False
        )
    )


def get_scatter_size(pvalue, effectsize, pvalue_cutoff=0.05, effectsize_cutoff=0.5, is_highlighted=False,
                     smallsize=1, medsize=2, largesize=3, extralargesize=4):
    if is_highlighted:
        return extralargesize
    if pvalue > pvalue_cutoff:
        return smallsize
    if pvalue < pvalue_cutoff and abs(effectsize) < effectsize_cutoff:
        return medsize
    return largesize