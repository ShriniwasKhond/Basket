from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from mlxtend.frequent_patterns import apriori, association_rules
from plotly.offline import init_notebook_mode, plot

init_notebook_mode(connected=True)

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_rules', methods=['POST', 'GET'])
def generate_rules():
    # Retrieve data from the uploaded file
    file = request.files['data_file']
    data = pd.read_csv(file, encoding='ansi')

    # Data_preprocessing
    data['Product Name'] = data['Product Name'].str.strip()  # removes spaces from beginning and end
    data.dropna(axis=0, subset=['Invoice No.'], inplace=True)  # removes duplicate invoice
    data['Invoice No.'] = data['Invoice No.'].astype('str')  # converting invoice number to be string
    data = data[~data['Invoice No.'].str.contains('C')]  # remove the credit transactions

    # grouping invoice no and products
    mybasket = (data.groupby(['Invoice No.', 'Product Name'])['QTY'].sum().unstack().reset_index().fillna(0).set_index(
        'Invoice No.'))

    def my_encode_units(x):
        if x <= 0:
            return 0
        if x >= 1:
            return 1

    my_basket_sets = mybasket.applymap(my_encode_units)

    # Run the Apriori algorithm
    my_frequent_itemsets = apriori(my_basket_sets.astype('bool'), min_support=0.002, use_colnames=True)
    my_rules = association_rules(my_frequent_itemsets, metric="lift", min_threshold=1)

    modified_rules = my_rules.sort_values('lift', ascending=False)
    modified_rules

    # Generate the sunburst chart
    # Generate the sunburst chart
    fig = px.sunburst(modified_rules, path=['antecedents', 'consequents'],
                      labels={'antecedents': 'Antecedents', 'consequents': 'Consequents'})

    # Modify the labels
    fig.update_traces(textinfo='label+percent entry')
    fig.update_layout(title='Most Associated Products')

    # Set custom label formatting function
    def format_label(label):
        if isinstance(label, frozenset):
            label = ', '.join(label)
        return label

    # Convert frozenset objects to strings
    modified_rules['antecedents'] = modified_rules['antecedents']  # .apply(lambda x: ", ".join(x))
    modified_rules['consequents'] = modified_rules['consequents']  # .apply(lambda x: ", ".join(x))

    # Modify the labels in the DataFrame
    modified_rules['antecedents'] = modified_rules['antecedents'].apply(format_label)
    modified_rules['consequents'] = modified_rules['consequents'].apply(format_label)

    # Update the sunburst chart with modified DataFrame
    fig.data[0].labels = modified_rules['antecedents'].tolist() + modified_rules['consequents'].tolist()

    # Set the chart layout
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    # Generate the second bar chart
    itemFrequency = data['Product Name'].value_counts().sort_values(ascending=False)
    fig1 = px.bar(itemFrequency.head(25),
                  # title='25 Most Frequent Items',
                  color=itemFrequency.head(25),
                  color_continuous_scale=px.colors.sequential.Magenta)
    fig1.update_layout(margin=dict(t=50, b=0, l=0, r=0), titlefont=dict(size=20), xaxis_tickangle=-45,
                       plot_bgcolor='white', coloraxis_showscale=False)
    fig1.update_yaxes(showticklabels=False, title=' ')
    fig1.update_xaxes(title=' ')
    fig1.update_traces(texttemplate='%{y}', textposition='outside',
                       hovertemplate='<b>%{x}</b><br>No. of Transactions: %{y}')


    # Generate the third bar chart
    # line chart
    # Group data by date and calculate the total number of transactions
    transactions_by_date = data.groupby('Invoice Date')['Invoice No.'].count().reset_index()

    # Create the line chart
    fig2 = go.Figure(data=go.Scatter(x=transactions_by_date['Invoice Date'], y=transactions_by_date['Invoice No.'],
                                     mode='lines+markers', line=dict(color='blue'), marker=dict(size=8),
                                     name='Transactions'))
    # Customize the chart layout
    fig2.update_layout(title='Total Number of Transactions by Date', xaxis_title='Date',
                       yaxis_title='Number of Transactions')
    # Set the chart layout
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    # Generate the fourth chart
    product_rates = data.groupby('Product Name').sum().reset_index()
    product_rates = product_rates.sort_values('RATE', ascending=False).head(
        15)  # Sort by RATE and select top 15 products

    # Modify the text attribute to include properly formatted revenue values
    text_labels = product_rates['RATE'][::-1].apply(lambda x: '{:,.0f}'.format(x))

    fig3 = px.scatter(
        product_rates, # Data
        x='RATE',  # Column containing x values
        y='Product Name',  # Column containing y values
        size='RATE',  # Column containing bubble size values
        color='RATE',  # Column containing bubble color values
        hover_name='Product Name',  # Column containing hover name values
        title='Top 15 revenue generated products',  # Title of the plot
        template='plotly_white'  # Specify plot theme
    )

    fig3.update_traces(textposition='middle right', marker=dict(size=10))  # Specify hover text formatting

    # Update the layout
    fig3.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),  # Set margin
        showlegend=False,  # Remove legend
        xaxis=dict(showgrid=False),  # Remove the x-axis grid lines
        yaxis=dict(showgrid=False),  # Remove the y-axis grid lines
        plot_bgcolor='beige'  # Set plot background color
    )

    annotations = [
        dict(
            x=x_val, # Position of text on x-axis
            y=y_val, # Position of text on y-axis
            text=text_label, # Text to be displayed
            font=dict(size=10), # Set the font size
            showarrow=False, # Do not show arrow head and line
            xanchor='left', # Left align text horizontally
            yanchor='middle', # Vertically align text vertically
            xshift=10 # Shift text slightly to right
        ) for x_val, y_val, text_label in zip(product_rates['RATE'][::-1], product_rates['Product Name'][::-1], text_labels) # Iterate over RATE, Product Name and text labels
    ]

    # Add annotations to the plot
    fig3.update_layout(annotations=annotations)
    # fig3 = go.Figure(data=go.Scatter(
    #     x=product_rates['RATE'][::-1],  # Reverse the order of x-axis values
    #     y=product_rates['Product Name'][::-1],  # Reverse the order of y-axis values
    #     mode='markers',
    #     marker=dict(
    #         color=product_rates['RATE'][::-1],  # Reverse the order of x-axis values
    #         size=10  # specify size of markers
    #     ),
    #     text=text_labels,  # Use the reversed order of text labels
    #     textposition='middle right',  # Set the position of the labels
    # ))

    # fig3.update_layout(
    #     # title='Top 15 revenue generated products',
    #     xaxis=dict(range=[3400, 30000]),
    #     yaxis=dict(
    #         categoryorder='array',
    #         categoryarray=product_rates['Product Name'][::-1]  # Arrange categories based on reversed product names
    #     ),
    #     margin=dict(l=100)  # Add space between scatter plot and count numbers
    # )

    # # Add count labels to the scatter plot
    # annotations = [
    #     dict(
    #         x=x_val,
    #         y=y_val,
    #         text=text_label,
    #         showarrow=False,
    #         font=dict(size=10),
    #         xanchor='left',
    #         yanchor='middle',
    #         xshift=10  # Adjust the x-coordinate for spacing
    #     )
    #     for x_val, y_val, text_label in
    #     zip(product_rates['RATE'][::-1], product_rates['Product Name'][::-1], text_labels)
    # ]

    # fig3.update_layout(annotations=annotations)

    # plot(fig3)

    # # Extract and modify the association rules table
    # association_df = modified_rules[['antecedents', 'consequents', 'lift']]
    # association_df['Item A'] = association_df['antecedents'].str.replace(',', '')
    # association_df['Item B'] = association_df['consequents'].str.replace(',', '')
    # association_df['Strength Category'] = association_df['lift'].apply(lambda
    #                                                                        x: 'Strongly associated' if x > 20 else 'Moderately associated' if 10 <= x <= 20 else 'Mildly associated')
    # strength_order = ['Strongly associated', 'Moderately associated', 'Mildly associated']
    # association_df['Strength Category'] = pd.Categorical(association_df['Strength Category'], categories=strength_order,
    #                                                      ordered=True)
    # modified_association_df = association_df[['Item A', 'Item B', 'Strength Category']].sort_values('Strength Category')

    # Set the chart layout
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    # Strongly associated table
    # Extract the desired columns from my_rules
    association_df = modified_rules[['antecedents', 'consequents', 'lift']]

    # Convert frozensets to strings for better readability
    association_df['Item A'] = association_df['antecedents']
    association_df['Item B'] = association_df['consequents']

    # Remove the comma between Item A and Item B
    association_df['Item A'] = association_df['Item A'].str.replace(',', '')
    association_df['Item B'] = association_df['Item B'].str.replace(',', '')

    # Calculate the strength category based on the lift value
    association_df['Strength Category'] = association_df['lift'].apply(lambda
                                                                           x: 'Strongly associated' if x > 20 else 'Moderately associated' if 10 <= x <= 20 else 'Mildly associated')

    # Filter the association rules table for strongly associated items
    strongly_associated_df = association_df[association_df['Strength Category'] == 'Strongly associated']

    # Remove the 'Strength Category' column
    strongly_associated_df = strongly_associated_df[['Item A', 'Item B']]

    # Display the strongly associated items table with a title
    strongly_associated_df.to_string(index=False)
    strongly_associated_products = strongly_associated_df.values.tolist()

    # Calculate the most productive days
    mpd = data.groupby('Invoice Date')['Product Name'].count().sort_values(ascending=False).head(25)

    # Filter the data for the most productive days
    most_productive_days = data[data['Invoice Date'].isin(mpd.index)]

    # Group by 'Invoice Date' and 'Product Name', count the occurrences
    most_sold_products = most_productive_days.groupby(['Invoice Date', 'Product Name']).size().reset_index(name='Count')

    # Sort the table by count in descending order 
    most_sold_products = most_sold_products.sort_values(by='Count', ascending=False)

    # Display only the top 10 most sold products
    top_10_most_sold_products = most_sold_products.head(18)

    # Display the resulting table of top 10 most sold products on the most productive days

    # Assuming you have the itemFrequency data as a pandas Series
    itemFrequency = data['Product Name'].value_counts().sort_values(ascending=False)

    # Get the top 10 most frequent items
    top_items = itemFrequency.head(18)

    # Create a DataFrame from the top_items data
    table_data = pd.DataFrame({'Product Name': top_items.index, 'Total Sale(Qty)': top_items.values})

    # Display the table without the index column
    # table_data.to_string(index=False)

    # Assuming you have the data DataFrame with columns 'Product Name' and 'RATE'
    product_rates = data.groupby('Product Name').sum().reset_index()
    product_rates = product_rates.sort_values('RATE', ascending=False).head(
        18)  # Sort by RATE and select top 18 products

    # Create the table with selected columns
    table_data_1 = product_rates[['Product Name', 'RATE']].rename(columns={'RATE': 'Revenue'})

    # Display the table without the index column
    # table_data.to_string(index=False)

    # Save the chart as HTML

    chart_html = fig.to_html(full_html=False)
    chart_html1 = fig1.to_html(full_html=False)
    chart_html2 = fig2.to_html(full_html=False)
    chart_html3 = fig3.to_html(full_html=False)
    # Render the results template with the charts
    return render_template('results.html', chart_html=fig.to_html(full_html=False),
                           chart_html1=fig1.to_html(full_html=False), chart_html2=fig2.to_html(full_html=False),
                           chart_html3=fig3.to_html(full_html=False),
                           # modified_association_df=modified_association_df.to_html(index=False),
                           strongly_associated_products = strongly_associated_products,
                           top_10_most_sold_products=top_10_most_sold_products.to_html(index=False),
                           table_data=table_data.to_html(index=False),
                           table_data_1=table_data_1.to_html(index=False))


if __name__ == '__main__':
    app.run(debug=True)