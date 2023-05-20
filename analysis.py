import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
import plotly.express as px
import plotly
# import plotly.figure_factory as ff


def input_data():
    data = pd.read_csv("March2022SalesReport.csv", encoding='latin-1')
    data['Product Name'] = data['Product Name'].str.strip() #removes spaces from beginning and end
    data.dropna(axis=0, subset=['Invoice No.'], inplace=True) #removes duplicate invoice
    data['Invoice No.'] = data['Invoice No.'].astype('str') #converting invoice number to be string
    data = data[~data['Invoice No.'].str.contains('C')] #remove the credit transactions
    return data
    # data = data.head(5)
    # df = ff.create_table(data,height_constant=20)
    # return plotly.offline.plot(df,output_type='div')

def my_encode_units(x):
    if x <= 0:
        return 0
    if x >= 1:
        return 1
data=input_data()

mybasket = (data
          .groupby(['Invoice No.', 'Product Name'])['QTY']
          .sum().unstack().reset_index().fillna(0)
          .set_index('Invoice No.'))

def plot1():
   # data=input_data()
    my_basket_sets = mybasket.applymap(my_encode_units)
    my_frequent_itemsets = apriori(my_basket_sets.astype('bool'), min_support=0.002, use_colnames=True)
    my_rules = association_rules(my_frequent_itemsets, metric="lift", min_threshold=1)
    fig = px.sunburst(my_rules, path=['antecedents','consequents'])#, values='support', color='confidence')
    fig.update_layout(title='Most Associated Products')
    return plotly.offline.plot(fig,output_type='div')