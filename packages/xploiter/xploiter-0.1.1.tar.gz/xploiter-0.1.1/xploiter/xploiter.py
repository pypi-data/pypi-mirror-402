import pandas as pd

def clean_employee_data(input_csv, output_csv="cleaned_sample_data.csv"):
    """
    Cleans employee data and saves it to a CSV file.

    Parameters:
        input_csv (str): Path to input CSV file
        output_csv (str): Path to output cleaned CSV file
    """

    df = pd.read_csv(input_csv)

    # Strip column names
    df.columns = df.columns.str.strip()

    # Strip string values
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Fill missing values
    if 'age' in df.columns:
        df['age'].fillna(df['age'].mean(), inplace=True)

    if 'salary' in df.columns:
        df['salary'].fillna(df['salary'].median(), inplace=True)

    # Convert date
    if 'date_of_joining' in df.columns:
        df['date_of_joining'] = pd.to_datetime(df['date_of_joining'], errors='coerce')

    # Remove duplicates
    df.drop_duplicates(inplace=True)

    # Normalize performance
    if 'performance' in df.columns:
        df['performance'] = df['performance'].str.capitalize()

    # Drop rows without name
    if 'name' in df.columns:
        df.dropna(subset=['name'], inplace=True)

    df.to_csv(output_csv, index=False)
    return df


'''Load a dataset, calculate descriptive summary statistics, create visualizations 
using different graphs, and identify potential features and target variables '''

#Code: 
#  Import Required Libraries 

'''import pandas as pd 
import matplotlib.pyplot as plt 
 
#  Load Dataset 
data = pd.read_csv("employees.csv") 
 
print("Dataset Loaded Successfully!\n") 
 
#  Display Dataset 
print("First 5 Rows of the Dataset:") 
display(data.head()) 
print("\nLast 5 Rows of the Dataset:") 
display(data.tail()) 
 
#  Dataset Information 
print("\nDataset Information:") 
data.info() 
 
#  Descriptive Statistics 
print("\nDescriptive Summary Statistics:") 
display(data.describe()) 
 
# Age Distribution 
plt.figure() 
plt.hist(data['age'], bins=10) 
plt.xlabel("Age") 
plt.ylabel("Frequency") 
plt.title("Age Distribution of Employees") 
plt.show() 
 
# Salary Distribution 
plt.figure() 
plt.hist(data['salary'], bins=10) 
plt.xlabel("Salary") 
plt.ylabel("Frequency") 
plt.title("Salary Distribution of Employees") 
plt.show() 
 
# Department-wise Employee Count 
plt.figure() 
data['department'].value_counts().plot(kind='bar') 
plt.xlabel("Department") 
plt.ylabel("Number of Employees") 
plt.title("Employees per Department") 
plt.show() 
 
# Performance Distribution 
plt.figure() 
data['performance'].value_counts().plot( 
    kind='pie', 
    autopct='%1.1f%%' 
) 
plt.title("Employee Performance Distribution") 
plt.ylabel("") 
plt.show() 
 
# Age vs Salary Scatter Plot 
plt.figure() 
plt.scatter(data['age'], data['salary']) 
plt.xlabel("Age") 
plt.ylabel("Salary") 
plt.title("Age vs Salary") 
plt.show() 
 
# Feature Variables (Independent Variables) 
features = ['age', 'salary', 'department'] 
 
# Target Variable (Dependent Variable) 
target = 'performance' 
 
print("\nSelected Features (X):", features) 
print("Selected Target (Y):", target) 
'''

#Create or Explore datasets to use all pre-processing routines like label encoding, 
#scaling, and binarization. 

#Code: 
'''import pandas as pd 
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler, Binarizer 
 
# Load dataset 
df = pd.read_csv('employees.csv') 
 
print("Initial Dataset:\n") 
display(df.head()) 
 
# ==================== Step 1: Handle Missing Values =================== 
df['age'].fillna(df['age'].median(), inplace=True) 
df['salary'].fillna(df['salary'].median(), inplace=True) 
df['name'].fillna('Unknown', inplace=True) 
df['department'].fillna(df['department'].mode()[0], inplace=True) 
df['performance'].fillna(df['performance'].mode()[0], inplace=True) 
 
# Convert date column 
df['date_of_joining'] = pd.to_datetime(df['date_of_joining'], errors='coerce') 
 
# ==================== Step 2: Label Encoding ==================== 
label_encoder = LabelEncoder() 
 
df['department_encoded'] = label_encoder.fit_transform(df['department']) 
df['performance_encoded'] = label_encoder.fit_transform(df['performance']) 
 
# ==================== Step 3: Feature Scaling ==================== 
# Min-Max Scaling 
min_max_scaler = MinMaxScaler() 
df[['age_scaled', 'salary_scaled']] = min_max_scaler.fit_transform( 
    df[['age', 'salary']] 
) 
 
# Standardization (Z-score normalization) 
std_scaler = StandardScaler() 
df[['age_standardized', 'salary_standardized']] = std_scaler.fit_transform( 
    df[['age', 'salary']] 
) 
 
# ==================== Step 4: Binarization ==================== 
# Binarize Age (Threshold = 30 years) 
binarizer = Binarizer(threshold=30) 
df['age_binarized'] = binarizer.fit_transform(df[['age']]) 
 
# ==================== Step 5: Save Preprocessed Data ==================== 
df.to_csv('preprocessed_employees_data.csv', index=False) 
df.to_excel('preprocessed_employees_data.xlsx', index=False) 
 
print("Processed Dataset:\n") 
display(df.head())
'''

#demonstrate the FIND-S algorithm for finding the most specific hypothesis based on a given set of training data samples. 
#Code: 
'''
import pandas as pd 
 
# Load training data 
data = pd.read_csv("employees_50_records.csv") 
 
print("Training Data:\n") 
print(data) 
 
# Handle missing values 
data.fillna("", inplace=True) 
 
# Select attributes (features) 
X = data[['name', 'age', 'salary', 'date_of_joining', 'department']] 
 
# Target attribute 
y = data['performance'] 
 
# Initialize most specific hypothesis 
specific_hypothesis = ["?" for _ in range(len(X.columns))] 
 
# FIND-S Algorithm 
for i in range(len(y)): 
    if y.iloc[i] == 'Excellent':   # Positive example 
        if all(val == "?" for val in specific_hypothesis): 
            specific_hypothesis = X.iloc[i].values.tolist() 
        else: 
            for j in range(len(specific_hypothesis)): 
                if specific_hypothesis[j] != X.iloc[i, j]: 
                    specific_hypothesis[j] = "?" 
 
# Output final hypothesis 
print("\nFinal Specific Hypothesis:") 
print(specific_hypothesis)
'''

#Simple Linear Regression 

#Code : 
# Import Required Libraries 
'''
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LinearRegression 
from sklearn.metrics import mean_squared_error, r2_score 
 
# Load Dataset 
data = pd.read_csv("employees.csv") 
 
print("Dataset Preview:") 
display(data.head()) 
 
#  Select Feature (X) and Target (Y) 
X = data[['age']]       # Independent variable 
y = data['salary']     # Dependent variable 
 
# Split Data into Training and Testing Sets 
X_train, X_test, y_train, y_test = train_test_split( 
    X, y, test_size=0.2, random_state=42 
) 
 
#  Create and Train Linear Regression Model 
model = LinearRegression() 
model.fit(X_train, y_train) 
 
# Model Coefficients 
print("Intercept:", model.intercept_) 
print("Coefficient (Slope):", model.coef_[0]) 
 
# Make Predictions 
y_pred = model.predict(X_test) 
 
#  Model Evaluation 
mse = mean_squared_error(y_test, y_pred) 
r2 = r2_score(y_test, y_pred) 
 
print("\nModel Performance:") 
print("Mean Squared Error (MSE):", mse) 
print("R-squared (R²):", r2) 
 
#  Visualization 
plt.figure() 
plt.scatter(X_test, y_test, label="Actual Salary") 
plt.plot(X_test, y_pred, label="Predicted Salary") 
plt.xlabel("Age") 
plt.ylabel("Salary") 
plt.title("Simple Linear Regression (Age vs Salary)") 
plt.legend() 
plt.show()
'''

#Discriminative Models 

#Code:
''' 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
 
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LogisticRegression 
from sklearn.preprocessing import LabelEncoder 
from sklearn.metrics import accuracy_score, precision_score, recall_score, 
confusion_matrix, roc_curve, auc 
 
# Step 2: Load Dataset 
data = pd.read_csv("employees.csv") 
print("Dataset Preview:\n") 
display(data.head()) 
 
# Step 3: Encode Categorical Features 
le_dept = LabelEncoder() 
data['department_encoded'] = le_dept.fit_transform(data['department']) 
 
# Convert 'performance' to binary (1 = Excellent, 0 = others) 
data['performance_binary'] = data['performance'].apply(lambda x: 1 if x == 'Excellent' else 
0) 
 
# Step 4: Select Features and Target 
X = data[['age', 'department_encoded']]  # You can include more features if needed 
y = data['performance_binary'] 
 
# Step 5: Train-Test Split 
X_train, X_test, y_train, y_test = train_test_split( 
    X, y, test_size=0.2, random_state=42 
) 
 
# Step 6: Train Logistic Regression Model 
model = LogisticRegression() 
model.fit(X_train, y_train) 
 
# Step 7: Make Predictions 
y_pred = model.predict(X_test) 
y_prob = model.predict_proba(X_test)[:,1]  # Probabilities for ROC curve 
 
# Step 8: Evaluate Model 
accuracy = accuracy_score(y_test, y_pred) 
precision = precision_score(y_test, y_pred) 
recall = recall_score(y_test, y_pred) 
cm = confusion_matrix(y_test, y_pred) 
 
print("Confusion Matrix:\n", cm) 
print(f"Accuracy: {accuracy:.2f}") 
print(f"Precision: {precision:.2f}") 
print(f"Recall: {recall:.2f}") 
 
# Step 9: Plot ROC Curve 
fpr, tpr, thresholds = roc_curve(y_test, y_prob) 
roc_auc = auc(fpr, tpr) 
 
plt.figure(figsize=(8,6)) 
plt.plot(fpr, tpr, color='blue', label=f'ROC curve (AUC = {roc_auc:.2f})') 
plt.plot([0,1],[0,1], color='red', linestyle='--') 
plt.xlabel("False Positive Rate") 
plt.ylabel("True Positive Rate") 
plt.title("ROC Curve") 
plt.legend(loc="lower right") 
plt.show()
'''

#Generative Models

'''A. Implement and demonstrate the working of a Naive Bayesian classifier using a 
sample data set. Build the model to classify a test sample. '''

#Code: 
# Import necessary libraries 
'''
import numpy as np 
import pandas as pd 
from sklearn.model_selection import train_test_split 
from sklearn.naive_bayes import GaussianNB 
from sklearn.datasets import load_iris 
from sklearn.metrics import accuracy_score, classification_report 
 
# Load the Iris dataset 
iris = load_iris() 
X = iris.data  # Features (sepal & petal length/width) 
y = iris.target  # Target labels (0, 1, 2 representing different iris species) 
 
# Split the dataset into training and testing sets (80% train, 20% test) 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42) 
 
# Create and train the Naive Bayes classifier 
nb_classifier = GaussianNB() 
nb_classifier.fit(X_train, y_train) 
 
# Predict on the test set 
y_pred = nb_classifier.predict(X_test) 
 
# Calculate and display accuracy 
accuracy = accuracy_score(y_test, y_pred) 
print(f"Model Accuracy: {accuracy * 100:.2f}%") 
 
# Display classification report 
print("\nClassification Report:\n", classification_report(y_test, y_pred)) 
 
# Test on a new sample 
sample = np.array([[5.1, 3.5, 1.4, 0.2]])  # A sample flower with sepal/petal dimensions 
predicted_class = nb_classifier.predict(sample) 
print("\nPredicted Class for the sample:", iris.target_names[predicted_class[0]]) 
'''

#B. Implement Hidden Markov Models using hmmlearn 
#Code: 
'''
import numpy as np 
from hmmlearn import hmm 
model = hmm.MultinomialHMM(n_components=2, random_state=42) 
model.startprob_ = np.array([0.6, 0.4])  
model.transprob_ = np.array([ 
    [0.7, 0.3],  
    [0.4, 0.6] ]) 
model.emissionprob_ = np.array([ 
    [0.8, 0.2],   
    [0.1, 0.9]   ]) 
observations = np.array([[0], [1], [1], [0], [1]]) 
model.fit(observations) 
logprob, hidden_states = model.decode(observations, algorithm="viterbi") 
print("Predicted weather states:", hidden_states) 
prob = model.score(observations) 
print(f"Log likelihood of the observations: {prob}") 
# Calculate and display accuracy 
accuracy = accuracy_score(y_test, y_pred) 
print(f"Model Accuracy: {accuracy * 100:.2f}%") 
# Display classification report 
print("\nClassification Report:\n", classification_report(y_test, y_pred)) 
# Test on a new sample 
sample = np.array([[5.1, 3.5, 1.4, 0.2]])  # A sample flower with sepal/petal dimensions 
predicted_class = nb_classifier.predict(sample) 
print("\nPredicted Class for the sample:", iris.target_names[predicted_class[0]])
'''

#A.   Implement Bayesian Linear Regression to explore prior and posterior distribution 
#Code : 
# Importing necessary libraries 
'''
import numpy as np 
import matplotlib.pyplot as plt 
import pymc as pm 
import seaborn as sns 
 
# Step 1: Generate synthetic data for linear regression 
np.random.seed(42) 
 
# True model parameters 
true_slope = 2.5 
true_intercept = 1.0 
 
# Generate synthetic data with noise 
n_samples = 100 
X = np.linspace(0, 10, n_samples) 
y_true = true_slope * X + true_intercept 
y = y_true + np.random.normal(0, 2, size=n_samples)  # Add some noise 
 
# Step 2: Visualize the synthetic data 
plt.figure(figsize=(8, 6)) 
plt.scatter(X, y, color='b', label='Observed Data') 
plt.plot(X, y_true, color='r', label='True Line') 
plt.xlabel('X') 
plt.ylabel('y') 
plt.title('Synthetic Data with True Line') 
plt.legend() 
plt.show() 
 
# Step 3: Define the Bayesian Linear Regression model using PyMC3 
with pm.Model() as model: 
    # Define priors for slope and intercept (the initial belief about the parameters) 
    slope = pm.Normal('slope', mu=0, sigma=10)  # Prior for the slope 
    intercept = pm.Normal('intercept', mu=0, sigma=10)  # Prior for the intercept 
     
    # Define the likelihood (data generation model) 
    sigma = pm.HalfNormal('sigma', sigma=1)  # Prior for the error term (standard deviation) 
    likelihood = pm.Normal('y', mu=slope * X + intercept, sigma=sigma, observed=y) 
     
    # Step 4: Sample from the posterior distribution using MCMC (Markov Chain Monte Carlo) 
    trace = pm.sample(2000, return_inferencedata=False) 
 
# Step 5: Visualize the prior and posterior distributions for the parameters 
plt.figure(figsize=(12, 6)) 
 
# Plot the prior distributions for slope and intercept 
sns.histplot(np.random.normal(0, 10, 10000), kde=True, color='blue', label='Prior for slope', 
stat='density') 
sns.histplot(np.random.normal(0, 10, 10000), kde=True, color='red', label='Prior for intercept', 
stat='density') 
 
plt.legend() 
plt.title('Prior Distributions for Slope and Intercept') 
plt.show() 
 
# Step 6: Visualize the posterior distributions of the parameters (slope and intercept) 
plt.figure(figsize=(12, 6)) 
# Plot the posterior distributions of slope and intercept 
sns.histplot(trace['slope'], kde=True, color='blue', label='Posterior of slope', stat='density') 
sns.histplot(trace['intercept'], kde=True, color='red', label='Posterior of intercept', 
stat='density') 
 
plt.legend() 
plt.title('Posterior Distributions for Slope and Intercept') 
plt.show() 
 
# Step 7: Visualize the posterior predictive distribution (predictions based on posterior) 
plt.figure(figsize=(8, 6)) 
plt.scatter(X, y, color='b', label='Observed Data') 
 
# Plot posterior predictive lines 
for i in range(100):  # Plot 100 lines from the posterior predictive distribution 
    y_pred = trace['slope'][i] * X + trace['intercept'][i] 
    plt.plot(X, y_pred, color='gray', alpha=0.1) 
 
plt.plot(X, y_true, color='r', label='True Line') 
plt.xlabel('X') 
plt.ylabel('y') 
plt.title('Posterior Predictive Distribution of Linear Model') 
plt.legend() 
plt.show() 
 
# Step 8: Extract the posterior means for slope and intercept 
posterior_slope_mean = np.mean(trace['slope']) 
posterior_intercept_mean = np.mean(trace['intercept']) 
print(f"Posterior Mean of Slope: {posterior_slope_mean:.2f}") 
print(f"Posterior Mean of Intercept: {posterior_intercept_mean:.2f}")
'''

#b.  Implement Gaussian Mixture Models for density estimation and unsupervised clustering 
#CODE –
''' 
import numpy as np 
import matplotlib.pyplot as plt 
import seaborn as sns 
from sklearn.mixture import GaussianMixture 
from sklearn.datasets import make_blobs 
 
# Step 1: Generate synthetic dataset with 3 Gaussian-distributed clusters 
np.random.seed(42) 
X, y_true = make_blobs(n_samples=300, centers=3, cluster_std=[1.0, 1.5, 0.8], 
random_state=42) 
 
# Step 2: Visualize the original data distribution 
plt.figure(figsize=(8, 6)) 
plt.scatter(X[:, 0], X[:, 1], s=30, color='gray', alpha=0.6) 
plt.xlabel("Feature 1") 
plt.ylabel("Feature 2") 
plt.title("Original Data Distribution") 
plt.show() 
 
# Step 3: Fit the GMM model 
gmm = GaussianMixture(n_components=3, covariance_type='full', random_state=42) 
gmm.fit(X) 
labels = gmm.predict(X)  # Assign clusters 
 
# Step 4: Visualize clustered data 
plt.figure(figsize=(8, 6)) 
sns.scatterplot(x=X[:, 0], y=X[:, 1], hue=labels, palette="viridis", s=50, alpha=0.8) 
plt.scatter(gmm.means_[:, 0], gmm.means_[:, 1], c='red', marker='x', s=200, 
label="Centroids") 
plt.xlabel("Feature 1") 
plt.ylabel("Feature 2") 
plt.title("Gaussian Mixture Model Clustering") 
plt.legend() 
plt.show() 
 
# Step 5: Density Estimation - Generate a meshgrid for PDF visualization 
x, y = np.meshgrid(np.linspace(np.min(X[:, 0])-1, np.max(X[:, 0])+1, 100), 
                   np.linspace(np.min(X[:, 1])-1, np.max(X[:, 1])+1, 100)) 
XY = np.array([x.ravel(), y.ravel()]).T 
Z = -gmm.score_samples(XY)  # Compute negative log-likelihood 
 
# Reshape and plot density estimation 
Z = Z.reshape(x.shape) 
plt.figure(figsize=(8, 6)) 
plt.contourf(x, y, Z, levels=30, cmap="coolwarm") 
plt.scatter(X[:, 0], X[:, 1], s=30, alpha=0.5, label="Data points") 
plt.colorbar(label="Density") 
plt.xlabel("Feature 1") 
plt.ylabel("Feature 2") 
plt.title("GMM Density Estimation") 
plt.legend() 
plt.show()
'''

#a.  Implement cross-validation techniques (k-fold, stratified, etc.) for robust model evaluation 

#CODE – 
'''
import numpy as np 
import pandas as pd 
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score 
from sklearn.linear_model import LogisticRegression 
from sklearn.datasets import make_classification 
from sklearn.metrics import accuracy_score 
 
# Generate a synthetic classification dataset 
X, y = make_classification(n_samples=1000, n_features=10, n_classes=2, random_state=42) 
 
# Define the model 
model = LogisticRegression() 
 
# ---------------------------- K-Fold Cross-Validation ----------------------------  
kfold = KFold(n_splits=5, shuffle=True, random_state=42) 
kf_scores = cross_val_score(model, X, y, cv=kfold, scoring='accuracy') 
 
print(f'K-Fold Cross-Validation Accuracy Scores: {kf_scores}') 
print(f'Average Accuracy: {kf_scores.mean():.4f}') 
 
# ---------------------- Stratified K-Fold Cross-Validation ----------------------  
stratified_kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42) 
skf_scores = cross_val_score(model, X, y, cv=stratified_kfold, scoring='accuracy') 
 
print(f'\nStratified K-Fold Accuracy Scores: {skf_scores}') 
print(f'Average Accuracy: {skf_scores.mean():.4f}') 
# -------------------------- Leave-One-Out Cross-Validation ---------------------- 
from sklearn.model_selection import LeaveOneOut 
loo = LeaveOneOut() 
loo_scores = cross_val_score(model, X, y, cv=loo, scoring='accuracy') 
print(f'\nLeave-One-Out Cross-Validation Accuracy: {loo_scores.mean():.4f}') 
# --------------------- Repeated K-Fold Cross-Validation ------------------------ 
from sklearn.model_selection import RepeatedKFold 
repeated_kfold = RepeatedKFold(n_splits=5, n_repeats=3, random_state=42) 
rkf_scores = cross_val_score(model, X, y, cv=repeated_kfold, scoring='accuracy') 
 
print(f'\nRepeated K-Fold Accuracy Scores: {rkf_scores}') 
print(f'Average Accuracy: {rkf_scores.mean():.4f}') 
'''

#Bayesian Learning

#Code:  
'''
import numpy as np 
import pymc as pm 
import matplotlib.pyplot as plt 
import arviz as az 
 
# Generate synthetic dataset 
np.random.seed(42) 
X = np.linspace(0, 10, 100) 
true_slope = 2.5 
true_intercept = 5.0 
y = true_slope * X + true_intercept + np.random.normal(0, 2, size=len(X))  # Add noise 
 
# Bayesian Model 
with pm.Model() as model: 
    # Prior distributions (initial beliefs) 
    slope = pm.Normal("slope", mu=0, sigma=10)  # Prior belief about slope 
    intercept = pm.Normal("intercept", mu=0, sigma=10)  # Prior belief about intercept 
    sigma = pm.HalfNormal("sigma", sigma=1)  # Prior for noise 
 
    # Likelihood (how data is generated) 
    y_pred = slope * X + intercept 
    likelihood = pm.Normal("y", mu=y_pred, sigma=sigma, observed=y) 
 
    # Perform Inference using MCMC 
    trace = pm.sample(2000, return_inferencedata=True) 
 
# Plot posterior distributions 
az.plot_posterior(trace, figsize=(10, 4)) 
plt.show() 
'''

'''A] Set up a generator network to produce samples and a discriminator network to 
distinguish between real and generated data. (Use a simple small dataset)''' 
#CODE – 
'''
import tensorflow as tf 
import numpy as np 
import matplotlib.pyplot as plt 
 
# Build Generator 
generator = tf.keras.Sequential([ 
    tf.keras.layers.Dense(16, activation="relu", input_dim=10), 
    tf.keras.layers.Dense(2, activation="tanh") 
]) 
 
# Build Discriminator 
discriminator = tf.keras.Sequential([ 
    tf.keras.layers.Dense(16, activation="relu", input_dim=2), 
    tf.keras.layers.Dense(1, activation="sigmoid") 
]) 
discriminator.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"]) 
 
# Combine into GAN 
discriminator.trainable = False 
gan = tf.keras.Sequential([generator, discriminator]) 
gan.compile(loss="binary_crossentropy", optimizer="adam") 
 
# Training 
def train(epochs=5000, batch_size=64): 
    for epoch in range(epochs): 
        # Generate real and fake data 
        X_real, y_real = np.random.randn(batch_size//2, 2), np.ones((batch_size//2, 1)) 
        X_fake = generator.predict(np.random.randn(batch_size//2, 10)) 
        y_fake = np.zeros((batch_size//2, 1)) 
 
        # Train Discriminatorc 
 
        discriminator.train_on_batch(X_real, y_real) 
        discriminator.train_on_batch(X_fake, y_fake) 
 
        # Train Generator 
        noise = np.random.randn(batch_size, 10) 
        gan.train_on_batch(noise, np.ones((batch_size, 1))) 
 
        if epoch % 1000 == 0: 
            print(f"Epoch {epoch}: Generator Training") 
            plot_generated() 
# Function to visualize generated samples 
def plot_generated(n=100): 
    X_fake = generator.predict(np.random.randn(n, 10)) 
    plt.scatter(X_fake[:, 0], X_fake[:, 1], color="red", label="Generated Data") 
    plt.legend() 
    plt.show() 
train()
'''