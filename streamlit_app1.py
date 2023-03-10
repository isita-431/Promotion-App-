import streamlit as st
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import OrdinalEncoder
from sklearn.preprocessing import KBinsDiscretizer
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from feature_engine.encoding import RareLabelEncoder
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, roc_curve, confusion_matrix
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import export_graphviz
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, roc_auc_score, roc_curve, confusion_matrix
from sklearn.model_selection import train_test_split
import sqlite3
import csv
conn = sqlite3.connect('data.db',check_same_thread=False)
cur = conn.cursor()
cur.execute("""create table if not exists app_form(employee_id text(10),department text(20),region text(20),education text(20),gender text(1),recruitment_channel text(20),
    no_of_trainings int, age int, previous_year_rating int,length_of_service int, KPIs_met int,awards_won int, avg_training_score int,is_promoted int,feedback text(5));""")
conn.commit()

def addData(employee_id,department,region,education,gender,recruitment_channel,no_of_trainings,age,previous_year_rating,length_of_service,KPIs_met,awards_won,avg_training_score,is_promoted,feedback):
	# cur.execute("""create table if not exists app_form(employee_id text(10),department text(20),region text(20),education text(20),gender text(1),recruitment_channel text(20),
    # no_of_trainings int, age int, previous_year_rating int,length_of_service int, KPIs_met int,awards_won int, avg_training_score int,is_promoted int,feedback text(5));""")
	# st.write("""create table if not exists clg_form(name text(10),q1 text(10),q2 text(10),q3 text(10),q4 text(10),q5 text(10));""")
	# st.write("INSERT INTO clg_form values"+str((name,a[0],b[0],c[0],d[0],e[0])))
	cur.execute("INSERT INTO app_form values"+str((employee_id,department,region,education,gender,recruitment_channel,no_of_trainings,age,previous_year_rating,length_of_service,KPIs_met,awards_won,avg_training_score,is_promoted,feedback))+';')
	conn.commit()
	conn.close()
	st.success('Successfully submitted')


# from autoviz.AutoViz_Class import AutoViz_Class

df = pd.read_csv("https://raw.githubusercontent.com/ashish-cell/BADM-211-FA21/main/Data/HR_Promote.csv")

# if st.sidebar.checkbox("Show dataset"):
#     st.write(df.head())

df["is_promoted"] = df["is_promoted"].astype("category")


class DateTransformer(BaseEstimator, TransformerMixin):
    
    def __init__(self):
        pass
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        X = X.copy()
        date_cols = X.select_dtypes(include=['datetime']).columns.tolist()
        for col in date_cols:
            X[col + '_month'] = X[col].dt.month
            X[col + '_dayofweek'] = X[col].dt.dayofweek
            X = X.drop(col, axis=1)
        return X
    
    def set_output(self, transform='numpy'):
        if transform == 'pandas':
            self.transform = self.transform_pandas
        else:
            self.transform = self.transform_numpy
    
    def transform_pandas(self, X):
        X = self.transform(X)
        return pd.DataFrame(X, columns=self.get_feature_names())
    
    def transform_numpy(self, X):
        return self.transform(X)
    
    def get_feature_names(self):
        date_cols = [col for col in self.X.select_dtypes(include=['datetime'])]
        feature_names = []
        for col in date_cols:
            feature_names.append(col + '_month')
            feature_names.append(col + '_dayofweek')
        return feature_names

class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, distance=1.5):
        self.distance = distance
        self.output_dataframe = False  # add output_dataframe attribute

    def set_output(self, transform):
        if transform == "pandas":
            self.output_dataframe = True

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        numeric_cols = X.select_dtypes(include=np.number).columns
        for col in numeric_cols:
            q1 = X[col].quantile(0.25)
            q3 = X[col].quantile(0.75)
            iqr = q3 - q1
            upper_cap = q3 + self.distance * iqr
            lower_cap = q1 - self.distance * iqr
            X[col] = np.where(X[col] > upper_cap, upper_cap, X[col])
            X[col] = np.where(X[col] < lower_cap, lower_cap, X[col])

        if self.output_dataframe:  # check if output_dataframe attribute is True
            X = pd.DataFrame(X, columns=numeric_cols)
        return X

skewed_num_pipe  = Pipeline(steps = [("imp", SimpleImputer(strategy= "median", add_indicator= True)), 
                                     ("out", OutlierCapper())])  

norm_num_pipe = Pipeline(steps = [("imp", SimpleImputer(strategy= "mean", add_indicator= True))]) 

disc_pipe = Pipeline(steps = [("imp", SimpleImputer(strategy= "median", add_indicator= True)),
                              ("disc", KBinsDiscretizer(strategy= "equal_width", encode = "ordinal"))]) 

nom_cat_pipe = Pipeline(steps = [("imp", SimpleImputer(strategy= "constant", fill_value = "missing")), 
                                 ("ohe", OneHotEncoder(sparse=False)),])  


ord_cat_pipe = Pipeline(steps = [("imp", SimpleImputer(strategy= "most_frequent", add_indicator = True)), 
                                 ("ord", OrdinalEncoder())])  


rare_cat_pipe = Pipeline(steps = [("imp", SimpleImputer(strategy= "constant", fill_value = "rare")), ("rare", RareLabelEncoder(tol=0.05, n_categories=4)), ("ohe", OneHotEncoder(sparse=False))])  

nom_cat_vars = ['department','region', 'gender','recruitment_channel']

ord_cat_vars = ['education']

rare_cat_vars = []
disc_num_vars = []

norm_num_vars = ["previous_year_rating"]

skewed_num_vars = []

date_vars = []

preprocessor = ColumnTransformer(transformers = [("nom", nom_cat_pipe, nom_cat_vars),
                                                 ("ord", ord_cat_pipe, ord_cat_vars), 
                                                 ("rare", rare_cat_pipe, rare_cat_vars), 
                                                 ("norm", norm_num_pipe, norm_num_vars),
                                                 ("skew", skewed_num_pipe, skewed_num_vars),
                                                 ("disc", disc_pipe, disc_num_vars),
                                                 ("dt", DateTransformer(), date_vars)], remainder = "passthrough")


preprocessor.set_output(transform = "pandas")


# st.write(preprocessor)
# st.write('<h3>ColumnTransformer Object:</h3>', unsafe_allow_html=True)
# st.write('<pre>{}</pre>'.format(preprocessor), unsafe_allow_html=True)

X = df.drop(columns = ["employee_id","is_promoted"])
y = df["is_promoted"]

train_X, test_X, train_y, test_y = train_test_split(X, y, test_size = 0.2, random_state = 42)

model_pipe_1 = Pipeline(steps = [("pre", preprocessor),  ("clf", DecisionTreeClassifier())])
model_pipe_1.fit(train_X, train_y)

train_pred = model_pipe_1.predict(train_X)
test_pred = model_pipe_1.predict(test_X)

# st.write(str(train_X[))
# print(train_X.iloc[0])
train_accuracy = accuracy_score(train_y, train_pred)
print(confusion_matrix(train_y, train_pred))
print(f"Model Accuracy on the Train Data is {train_accuracy}")

print("*******" * 4)


test_accuracy = accuracy_score(test_y, test_pred)
print(confusion_matrix(test_y, test_pred))
print(f"Model Accuracy on the Test Data is {test_accuracy}")

st.write('Enter the Values : ')
# data = pd.DataFrame({'employee_id':[7513],'department':["Sales & Marketing"],'region':["region_19"],'education':["Bachelor's"],'gender':["m"],'recruitment_channel':["sourcing"],'no_of_trainings':[1],'age':[34],'previous_year_rating':[3],'length_of_service':[7],'KPIs_met >80%':[0],'awards_won?':[0],'avg_training_score':[50]})
# prediction = model_pipe_1.predict(data)

# st.write(prediction)

# Create a form
with st.form(key='my_form'):
    # Add a text input
    employee_id = st.text_input(label='Enter your employee_id : ')

    department = st.text_input(label='Enter your department : ')

    region = st.text_input(label='Enter your region : ')

    education = st.text_input(label='Enter your education qualifications : ')

    # Add a radio button input
    gender = st.radio(label='Select your gender', options=['m', 'f',])

    recruitment_channel = st.text_input(label='Enter the recruitment channel : ')

    no_of_trainings = st.number_input('Enter the no of trainings : ', min_value=0.0, max_value=10.0, value=1.0, step=1.0)

    age = st.number_input("Enter your age:", min_value=0, max_value=100, value=50, step=1)

    previous_year_rating = st.number_input("Enter the previous year rating:", min_value=1, max_value=5, value=1, step=1)

    length_of_service = st.number_input("Enter the length of service:", min_value=1, max_value=50, value=1, step=1)

    KPIs_met = st.number_input("Enter KPIs met:", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

    awards_won= st.number_input("Enter the number of awards won :", min_value=0, max_value=5, value=1, step=1)

    avg_training_score = st.number_input("Enter an avg_training_score  :", min_value=1, max_value=100, value=1, step=1)
    # Add a submit button


    submit_button = st.form_submit_button(label='Submit')


# Process the form submission
p = ' '
if submit_button:
    data = pd.DataFrame({'department':[department],'region':[region],'education':[education],'gender':[gender],'recruitment_channel':[recruitment_channel],'no_of_trainings':[no_of_trainings],'age':[age],'previous_year_rating':[previous_year_rating],'length_of_service':[length_of_service],'KPIs_met >80%':[KPIs_met],'awards_won?':[awards_won],'avg_training_score':[avg_training_score]})
    prediction = model_pipe_1.predict(data)
    p= prediction[0]
    st.write(prediction)
    
with st.form(key='Feedback'):
    # Add a text input
    feedback = st.radio(label='Enter the feedback : is the output correct or not ?', options=['Yes', 'No',])

    submit_btn = st.form_submit_button(label='Submit')
if submit_btn:
    st.write('Your feedback is : '+ str(feedback))
    addData(employee_id ,department,region, education,gender, recruitment_channel, no_of_trainings, age,previous_year_rating,length_of_service,KPIs_met,awards_won,avg_training_score,p,feedback)

conn = sqlite3.connect('data.db',check_same_thread=False)
SQL_Query = pd.read_sql_query(
        '''select
          *
          from app_form''', conn)

df = pd.DataFrame(SQL_Query, columns=['employee_id','department','region','education','gender','recruitment_channel','no_of_trainings','age','previous_year_rating','length_of_service','KPIs_met,awards_won','avg_training_score','is_promoted','feedback'])
print(df)

conn.commit()
conn.close()

