# -*- coding: utf-8 -*-
"""Resume_Classifiction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GdHucAW1JkSDO_Y0mgRz2VdqUXvyUPpA
"""

!pip install nltk
!pip install gensim
!pip install wordcloud

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import gensim
import re
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from sklearn.metrics import classification_report, confusion_matrix

import zipfile
zip_ref = zipfile.ZipFile("dataset.zip", 'r')
zip_ref.extractall("/content/dataset")
zip_ref.close()

df = pd.read_csv('/content/dataset/Resume/Resume.csv')
df.head()

df.drop(columns = ['ID', 'Resume_html'], inplace = True)
to_remove = ['CONSULTANT', 'BPO','AUTOMOBILE','ARTS']
df = df[~df['Category'].isin(to_remove)]
df

STEMMER = nltk.stem.porter.PorterStemmer()

def preprocess(txt):
    # convert all characters in the string to lower case
    txt = txt.lower()
    # remove non-english characters, punctuation and numbers
    txt = re.sub('[^a-zA-Z]', ' ', txt)
    # tokenize word
    txt = nltk.tokenize.word_tokenize(txt)
    # remove stop words
    txt = [w for w in txt if not w in nltk.corpus.stopwords.words('english')]
    # stemming
    txt = [STEMMER.stem(w) for w in txt]

    return ' '.join(txt)

import nltk
nltk.download('punkt')
nltk.download('stopwords')

df['Resume'] = df['Resume_str'].apply(lambda w: preprocess(w))
# drop original text column
df.pop('Resume_str')
df

df.info()

df['Category'].value_counts()

df['Category'].value_counts().sort_index().plot(kind='bar', figsize=(12, 6))
plt.show()

df

from matplotlib.gridspec import GridSpec
count=df['Category'].value_counts()
label=df['Category'].value_counts().keys()

plt.figure(1, figsize=(25,25))
grid=GridSpec(2,2)

cmap=plt.get_cmap('coolwarm')

color=[cmap(i) for i in np.linspace(0, 1, 5)]
plt.subplot(grid[0,1], aspect=1, title='Distribution')

pie=plt.pie(count, labels=label, autopct='%1.2f%%')
plt.show()

# create list of all categories
categories = np.sort(df['Category'].unique())
categories

# create new df for corpus and category
df_categories = [df[df['Category'] == category].loc[:, ['Resume', 'Category']] for category in categories]
df_categories[10]

# word frequency for each category
def wordfreq(df):
    count = df['Resume'].str.split(expand=True).stack().value_counts().reset_index()
    count.columns = ['Word', 'Frequency']

    return count.head(10)

fig = plt.figure(figsize=(32, 64))

for i, category in enumerate(np.sort(df['Category'].unique())):
    wf = wordfreq(df_categories[i])

    fig.add_subplot(12, 2, i + 1).set_title(category)
    plt.bar(wf['Word'], wf['Frequency'])
    plt.ylim(0, 3500)

plt.show()
plt.close()

stop_words = stopwords.words('english')

def remove_stop_words (text):
  result = []
  for token in gensim.utils.simple_preprocess(text):
    if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3 and token not in stop_words:
      result.append(token)

  return result

df['clean'] = df['Resume'].apply(remove_stop_words).astype(str)

df['clean'][0]

df

from sklearn.model_selection import train_test_split
X_train, X_test, Y_train, Y_test = train_test_split(df['clean'], df['Category'], test_size = 0.2, stratify=df['Category'])

from sklearn.feature_extraction.text import CountVectorizer

# vectorize text data
vectorizer = CountVectorizer()
conuntvectorizer_train = vectorizer.fit_transform(X_train).astype(float)
conuntvectorizer_test = vectorizer.transform(X_test).astype(float)
conuntvectorizer_train
conuntvectorizer_test

from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import make_scorer, f1_score, precision_score, recall_score


# create the GradientBoostingClassifier model
GBM_Model = GradientBoostingClassifier(random_state=42)

# define the parameter grid to search
param_grid = {
    'n_estimators': [50, 100],
    'learning_rate': [0.1, 0.05],
    'max_depth': [3, 4]
}
# create the scoring functions
scoring = {
    'f1_score': make_scorer(f1_score, average='macro'),
    'precision_score': make_scorer(precision_score, average='macro'),
    'recall_score': make_scorer(recall_score, average='macro')
}

# create the GridSearchCV object
grid_search = GridSearchCV(estimator=GBM_Model, param_grid=param_grid, cv=3, scoring=scoring, refit='f1_score')

# fit the GridSearchCV object to the training data
grid_search.fit(conuntvectorizer_train[:5000], Y_train[:5000])

# print the best hyperparameters and the corresponding mean cross-validated scores
print("Best hyperparameters: ", grid_search.best_params_)
print("Best cross-validated f1 score: ", grid_search.best_score_)
print("Cross-validated precision score: ", grid_search.cv_results_['mean_test_precision_score'])
print("Cross-validated recall score: ", grid_search.cv_results_['mean_test_recall_score'])

# make predictions on the test data using the best model
best_model = grid_search.best_estimator_
y_pred = best_model.predict(conuntvectorizer_test)

# evaluate the model's performance
f1 = f1_score(Y_test, y_pred, average='macro')
precision = precision_score(Y_test, y_pred, average='macro')
recall = recall_score(Y_test, y_pred, average='macro')
print(f"F1 Score: {f1}")
print(f"Precision Score: {precision}")
print(f"Recall Score: {recall}")
accuracy = best_model.score(conuntvectorizer_test, Y_test)
print(f"Accuracy: {accuracy}")

from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, f1_score, precision_score, recall_score,accuracy_score

# create the SVM model
svm_model = SVC(kernel='linear')

# define the parameter grid to search
param_grid = {
    'C': [0.1, 1, 10],
    'kernel': ['linear', 'rbf'],
    'gamma': ['scale', 'auto']
}

# create the scoring functions
scoring = {
    'f1_score': make_scorer(f1_score, average='macro'),
    'precision_score': make_scorer(precision_score, average='macro'),
    'recall_score': make_scorer(recall_score, average='macro'),
    'accuracy_score': make_scorer(accuracy_score, average='macro')
}

# create the GridSearchCV object
grid_search = GridSearchCV(estimator=svm_model, param_grid=param_grid, cv=3, scoring=scoring, refit='f1_score')

# fit the GridSearchCV object to the training data
grid_search.fit(conuntvectorizer_train, Y_train)

# print the best hyperparameters and the corresponding mean cross-validated scores
print("Best hyperparameters: ", grid_search.best_params_)
print("Best cross-validated f1 score: ", grid_search.best_score_)
print("Cross-validated precision score: ", grid_search.cv_results_['mean_test_precision_score'])
print("Cross-validated recall score: ", grid_search.cv_results_['mean_test_recall_score'])

# make predictions on the test data using the best model
best_model = grid_search.best_estimator_
svm_pred = best_model.predict(conuntvectorizer_test)

# evaluate the model's performance
f1 = f1_score(Y_test, svm_pred, average='macro')
precision = precision_score(Y_test, svm_pred, average='macro')
accuracy = accuracy_score(Y_test, svm_pred)
print(f"F1 Score: {f1}")
print(f"Precision Score: {precision}")
print(f"Recall Score: {recall}")
accuracy = best_model.score(conuntvectorizer_test, Y_test)
print(f"Accuracy: {accuracy}")

from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score, precision_score, recall_score

# define the parameter grid
parameter_grid = {'hidden_layer_sizes': [(50,), (50,50), (50,50,50)],
                  'max_iter': [100, 200, 300],
                  'activation': ['relu', 'tanh', 'logistic'],
                  'solver': ['adam', 'sgd']}

# create the MLP classifier
MLP_Model = MLPClassifier(random_state=42)

# create the GridSearchCV object
grid_search = GridSearchCV(MLP_Model, param_grid=parameter_grid, cv=3, scoring=['accuracy', 'f1', 'precision', 'recall'], refit=False)

# fit the GridSearchCV object to the training data
grid_search.fit(conuntvectorizer_train[:5000], Y_train[:5000])

# print the best parameters and score
print("Best parameters: ", grid_search.best_params_)
print("Best cross-validated F1-score: ", grid_search.best_score_)

# print the cross-validated scores for other metrics
print("Cross-validated precision score: ", grid_search.cv_results_['mean_test_precision'])
print("Cross-validated recall score: ", grid_search.cv_results_['mean_test_recall'])
print("Cross-validated accuracy: ", grid_search.cv_results_['mean_test_accuracy'])

# make predictions on the test data using the best estimator
y_pred = grid_search.predict(conuntvectorizer_test)

# evaluate the model's performance
accuracy = grid_search.score(conuntvectorizer_test, Y_test)
f1 = f1_score(Y_test, y_pred)
precision = precision_score(Y_test, y_pred)
recall = recall_score(Y_test, y_pred)

print(f"Accuracy: {accuracy}")
print(f"F1-score: {f1}")
print(f"Precision: {precision}")
print(f"Recall: {recall}")

from sklearn.ensemble import RandomForestClassifier

RF_Model = RandomForestClassifier(random_state=42, max_features='auto', n_estimators=500, max_depth=8, criterion='gini')
RF_Model.fit(conuntvectorizer_train, Y_train)

prediction = RF_Model.predict(conuntvectorizer_test)
print("Training Score: {:.2f}".format(RF_Model.score(conuntvectorizer_train, Y_train)))
print("Test Score: {:.2f}".format(RF_Model.score(conuntvectorizer_test, Y_test)))

from sklearn.metrics import classification_report, accuracy_score, f1_score, precision_score, recall_score

print("Accuracy: {:.3f}".format(accuracy_score(Y_test, prediction)))
print("F1-Score: {:.3f}".format(f1_score(Y_test, prediction, average='weighted')))
print("Precision: {:.3f}".format(precision_score(Y_test, prediction, average='weighted')))
print("Recall: {:.3f}".format(recall_score(Y_test, prediction, average='weighted')))
print("Classification Report: \n", classification_report(Y_test, prediction))

from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# Train the model
NB = MultinomialNB()
NB.fit(conuntvectorizer_train, Y_train)

# Make predictions
Y_pred = NB.predict(conuntvectorizer_test)

# Evaluate the model
accuracy = accuracy_score(Y_test, Y_pred)
f1 = f1_score(Y_test, Y_pred, average='weighted')
precision = precision_score(Y_test, Y_pred, average='weighted')
recall = recall_score(Y_test, Y_pred, average='weighted')

print("Accuracy:", accuracy)
print("F1-Score:", f1)
print("Precision:", precision)
print("Recall:", recall)