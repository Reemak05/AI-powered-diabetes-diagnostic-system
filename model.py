import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn import svm
from sklearn.metrics import accuracy_score
import pickle
#laoding the diabetes dataset to a pandas DataFrame
diabetes_d=pd.read_csv('diabetes.csv')
#printing the first 5 rows of the dataset
diabetes_d.head()
#number of rows and Columns in this dataset
diabetes_d.shape
#getting the statistical measures of the data
diabetes_d.describe()
diabetes_d['Outcome'].value_counts()
# Replace 0s with NaN in selected columns (invalid zeros)
cols_with_zeros = ['Glucose', 'BloodPressure', 'Insulin', 'BMI']
diabetes_d[cols_with_zeros] = diabetes_d[cols_with_zeros].replace(0, np.nan)

# Option 1: Replace NaN values with the column median
diabetes_d.fillna(diabetes_d.median(), inplace=True)

# Remove 'SkinThickness' if you want to exclude it
diabetes_d = diabetes_d.drop(columns='SkinThickness')
#separating the data and labels
X=diabetes_d.drop(columns='Outcome',axis=1)
Y=diabetes_d['Outcome']
scaler=StandardScaler()
scaler.fit(X)
stand_data=scaler.transform(X)
print(stand_data)
X=stand_data
Y=diabetes_d['Outcome']
X_train,X_test,Y_train,Y_test=train_test_split(X,Y,test_size=0.2,stratify=Y,random_state=2)
print(X.shape,X_train.shape,X_test.shape)
classifier=svm.SVC(kernel='linear')
#traing the support vector machine classifier
classifier.fit(X_train,Y_train)

from collections import Counter
predictions = classifier.predict(X_test)
print(Counter(predictions))


#Make pickle file of out model
# Save both model and scaler
with open("model.pkl", "wb") as f:
    pickle.dump((scaler, classifier), f)

