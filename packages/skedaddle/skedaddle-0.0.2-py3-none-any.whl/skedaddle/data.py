SOLUTIONS = {
    "pdf_1": """# 1. Linear Regression
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

tem=np.array([20,22,24,26,28,30,32]).reshape(-1,1)
sal=np.array([100,120,150,170,200,230,260])

model=LinearRegression()
model.fit(tem,sal)

print("slope(m):",model.coef_[0])
print("intercept(c):",model.intercept_)

new_tem=27
predicted_sales=model.predict([[new_tem]])

print(f'prdicted ice-cream sales at:',predicted_sales)

plt.scatter(tem,sal,label="data points")
plt.plot(tem,model.predict(tem),label="best fit lines")
plt.xlabel("temperature")
plt.ylabel("ice-cream sales")
plt.title("linear regression:temp vs sales")
plt.legend()
plt.show()
""",
    "pdf_10": """# 10. Train Test Split
from sklearn.model_selection import train_test_split

x=[[1],[2],[3],[4],[5]]
y=[40,50,60,70,80]

x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42)

print("x_train:",x_train)
print("y_train:",y_train)
print("x_test:",x_test)
print("y_test:",y_test)
""",
    "pdf_11": """# 11. Mean Median Std
import pandas as pd

data={'age':[20,21,22,24,25,20],'height':[144,155,160,140,164,170],'weight':[45,50,80,64,50,46]}
df=pd.DataFrame(data)

mean_val=df.mean()
meadian_val=df.median()
std_values=df.std()

print("mean value:",mean_val)
print("median value:",meadian_val)
print("standard value:",std_values)
""",
    "pdf_12": """# 12. Correlation Matrix
from sklearn.datasets import load_iris
import pandas as pd

data=load_iris()
df=pd.DataFrame(data.data,columns=data.feature_names)

print(df.corr())
""",
    "pdf_13": """# 13. RMSE R2
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

Y_true = [3.0, -0.5, 2.0, 7.0]
Y_pred = [2.5, 0.0, 2.1, 7.8]

Rmse = np.sqrt(mean_squared_error(Y_true, Y_pred))
R2 = r2_score(Y_true, Y_pred)

print(f"Root Mean Squared Error (RMSE): {Rmse}")
print(f"R-squared (R^2): {R2}")
""",
    "pdf_14": """# 14. Metrics
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score

y_true=[0,1,1,0,0,1,0]
y_pred=[0,1,0,0,1,1,1]

acc=accuracy_score(y_true,y_pred)
pre=precision_score(y_true,y_pred)
recall=recall_score(y_true,y_pred)
f1=f1_score(y_true,y_pred)

print("accuracy:",acc)
print("precision:",pre)
print("recall:",recall)
print("f1:",f1)
""",
    "pdf_15": """# 15. Confusion Matrix
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

X, y = make_classification(n_samples=200, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

clf = LogisticRegression().fit(X_train, y_train)
ConfusionMatrixDisplay.from_estimator(clf, X_test, y_test, cmap="Blues")
plt.show()
""",
    "pdf_2": """# 2. Logistic Regression
import numpy as np
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt

tem=np.array([20,22,24,26,28,30,32]).reshape(-1,1)
sal=np.array([100,120,150,170,200,230,260])
y=(sal>200).astype(int)

model=LogisticRegression()
model.fit(tem,y)

new_tem=27
pred=model.predict([[new_tem]])[0]

print("temp:",new_tem)
print("high sales:",pred)
""",
    "pdf_3a": """# 3(A). SVM 2 Features
import numpy as np
import matplotlib.pyplot as plt
from sklearn.svm import SVC

X = np.array([[2,400],[3,450],[5,300],[6,520],[7,580],[8,220]])
y = np.array([0,0,0,0,1,1])

model = SVC(kernel='linear')
model.fit(X, y)

plt.scatter(X[:,0], X[:,1], c=y, cmap='coolwarm', s=80)
plt.xlabel("annual income (in lakhs)")
plt.ylabel("credit score")
plt.title("svm for loan approval")

w = model.coef_[0]
b = model.intercept_[0]
x_vals = np.linspace(1, 10, 100)
y_vals = -(w[0]*x_vals + b) / w[1]

plt.plot(x_vals, y_vals, 'k--', linewidth=2)
plt.show()
""",
    "pdf_3b": """# 3(B). SVM 3 Features
import numpy as np
import matplotlib.pyplot as plt
from sklearn.svm import SVC
from mpl_toolkits.mplot3d import axes3d

x = np.array([[30,120,180],[35,125,190],[40,130,200],[45,135,210],[50,150,240],[55,155,240]])
y = np.array([0,0,0,0,1,1])

model = SVC(kernel='linear')
model.fit(x, y)

w = model.coef_[0]
b = model.intercept_[0]

fig=plt.figure()
ax=fig.add_subplot(111,projection="3d")

ax.scatter(x[y==0,0],x[y==0,1],x[y==0,2],label='no disease')
ax.scatter(x[y==1,0],x[y==1,1],x[y==1,2],label='disease')
ax.set_xlabel('age')
ax.set_ylabel('bp')
ax.set_zlabel('ch')
ax.set_title("3 feature svm")
plt.show()
plt.legend()
""",
    "pdf_3c": """# 3(C). Non-Linear SVM
import numpy as np
import matplotlib.pyplot as plt
from sklearn.svm import SVC

X=np.array([[1,2],[2,3],[3,1],[3,3],[6,6],[7,8],[8,6],[9,7]])
y=np.array([0,0,0,0,1,1,1,1])

model=SVC(kernel='rbf',gamma='scale',C=10)
model.fit(X,y)

plt.scatter(X[:,0], X[:,1], c=y, cmap='coolwarm', s=80)
plt.xlabel("feature 1:")
plt.ylabel("feature 2:")
plt.title("non linear svm:")

ax=plt.gca()
xlim=ax.get_xlim()
ylim=ax.get_ylim()

xx=np.linspace(xlim[0],xlim[1],200)
yy=np.linspace(ylim[0],ylim[1],200)
YY,XX=np.meshgrid(yy,xx)
xy=np.vstack([XX.ravel(),YY.ravel()]).T
Z=model.decision_function(xy).reshape(XX.shape)

ax.contour(XX,YY,Z,levels=[0],linewidths=2)
plt.show()
""",
    "pdf_4a": """# 4(A). KNN Iris
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier

iris = load_iris()
X = iris.data
y = iris.target

knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X, y)

pred = knn.predict(X)
print("Correct predictions:")
for i in range(len(y)):
    if y[i] == pred[i]:
        print(i, y[i], pred[i])

print("\nWrong predictions:")
for i in range(len(y)):
    if y[i] != pred[i]:
        print(i, y[i], pred[i])
""",
    "pdf_4b": """# 4(B). KNN Train Test
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split

iris = load_iris()
X = iris.data
y = iris.target
target_names = iris.target_names

X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.3,random_state=42)

knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X_train,y_train)
y_pred=knn.predict(X_test)

print("correct prediction:")
for i in range(len(y_test)):
    if y_test[i]==y_pred[i]:
        print(f"sample{i}:actual={target_names[y_test[i]]},predicted={target_names[y_pred[i]]}")
""",
    "pdf_5a": """# 5(A). Perceptron
X=[(0,0),(0,1),(1,0),(1,1)]
y=[0,0,0,1]
w=[0,0]
b=0
lr=1

for i in range(len(X)):
    net=X[i][0]*w[0]+X[i][1]*w[1]+b
    out=1 if net >=0 else 0
    error=y[i]-out
    w[0]+=lr*error*X[i][0]
    w[1]+=lr*error*X[i][1]
    b+=lr*error
    print("weights:",w)
    print("bias:",b)
""",
    "pdf_5b": """# 5(B). Single Layer Perceptron
X=[(0,0),(0,1),(1,0),(1,1)]
y=[0,0,0,1]
w1,w2=0,0
b=0
lr=0.1

for epoch in range(10):
    print("epoch:",epoch+1)
    for i in range (len(X)):
        x1,x2=X[i]
        target=y[i]
        net=x1*w1+x2*w2+b
        out=1 if net >=0 else 0
        error=target-out
        w1+=lr*error*x1
        w2+=lr*error*x2
        b+=lr*error
        print(X[i],"output:",out,"target:",target)
    print("final weight:",w1,w2)
    print("final bias:",b)
""",
    "pdf_6a": """# 6(A). MLP Predict
import numpy as np
X=np.array([[0,0],[0,1],[1,0],[1,1]])
y=np.array([[0],[1],[1],[0]])
np.random.seed(1)
w1=np.random.rand(2,2)
w2=np.random.rand(2,1)

def sigmoid(x):
    return 1/(1+np.exp(-x))

for i in range(10000):
    h=sigmoid(np.dot(X,w1))
    output=sigmoid(np.dot(h,w2))

print("predicted output:")
print(np.round(output))
""",
    "pdf_6b": """# 6(B). MLP Train
import numpy as np
X=np.array([[0,0],[0,1],[1,0],[1,1]])
y=np.array([[0],[1],[1],[0]])
np.random.seed(1)
w1=np.random.rand(2,2)
w2=np.random.rand(2,1)
lr=0.1

def sigmoid(x):
    return 1/(1+np.exp(-x))

def sigmoid_derivative(x):
    return x*(1-x)

for _ in range(10000):
    h=sigmoid(np.dot(X,w1))
    output=sigmoid(np.dot(h,w2))
    error=y-output
    d_output=error*sigmoid_derivative(output)
    error_hidden=d_output.dot(w2.T)
    d_hidden=error_hidden*sigmoid_derivative(h)
    w2+=h.T.dot(d_output)*lr
    w1+=X.T.dot(d_hidden)*lr

print("predicted output:")
print(np.round(output))
""",
    "pdf_7": """# 7. Naive Bayes
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score,classification_report

iris=load_iris()
X=iris.data
y=iris.target

X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.4,random_state=42)

nb=GaussianNB()
nb.fit(X_train,y_train)
y_pred=nb.predict(X_test)

acc=accuracy_score(y_test,y_pred)
print("accuracy:",acc*100)
print(classification_report(y_test,y_pred))
""",
    "pdf_8": """# 8. CSV Dataset
import pandas as pd
# Note: 'sample_101.csv' is required for this script to run successfully.
try:
    df = pd.read_csv("sample_101.csv")
    print(df.head(10))
except FileNotFoundError:
    print("Error: 'sample_101.csv' not found. Please provide the file.")
""",
    "pdf_9": """# 9. Scatter Plot
import matplotlib.pyplot as plt

hours=[1,2,3,4,5,6,7]
marks=[40,45,56,66,70,88,94]

plt.scatter(hours,marks)
plt.xlabel("study hour")
plt.ylabel("marks")
plt.title("relationship b/w hours and marks")
plt.show()
""",
}

TITLES = {
    "pdf_1": "1. Linear Regression",
    "pdf_10": "10. Train Test Split",
    "pdf_11": "11. Mean Median Std",
    "pdf_12": "12. Correlation Matrix",
    "pdf_13": "13. RMSE R2",
    "pdf_14": "14. Metrics",
    "pdf_15": "15. Confusion Matrix",
    "pdf_2": "2. Logistic Regression",
    "pdf_3a": "3(A). SVM 2 Features",
    "pdf_3b": "3(B). SVM 3 Features",
    "pdf_3c": "3(C). Non-Linear SVM",
    "pdf_4a": "4(A). KNN Iris",
    "pdf_4b": "4(B). KNN Train Test",
    "pdf_5a": "5(A). Perceptron",
    "pdf_5b": "5(B). Single Layer Perceptron",
    "pdf_6a": "6(A). MLP Predict",
    "pdf_6b": "6(B). MLP Train",
    "pdf_7": "7. Naive Bayes",
    "pdf_8": "8. CSV Dataset",
    "pdf_9": "9. Scatter Plot",
}
