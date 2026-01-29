import plotly.express as px
import plotly.graph_objects as go

def create_topic_distribution_bar(topic_freq_df):
    """Creates a bar chart for topic frequency."""
    fig = px.bar(
        topic_freq_df, 
        x='Topic', 
        y='Count', 
        title='Topic Frequency Distribution',
        color='Count',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Verdana", size=12)
    )
    return fig

def create_word_cloud_mock(words_freq):
    """
    Creates a scatter plot representing word weights (WordCloud alternative).
    """
    words, freqs = zip(*words_freq)
    fig = go.Figure(data=go.Scatter(
        x=[i for i in range(len(words))],
        y=freqs,
        mode='text+markers',
        text=words,
        marker=dict(
            size=freqs,
            color=freqs,
            colorscale='Spectral',
            showscale=True
        ),
        textfont=dict(
            size=[f * 2 for f in freqs]  # Size based on frequency
        )
    ))
    fig.update_layout(
        title='Top Keywords per Topic (Weighted Scatter)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig