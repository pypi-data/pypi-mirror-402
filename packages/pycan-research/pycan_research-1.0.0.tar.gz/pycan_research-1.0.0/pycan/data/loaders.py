import numpy as np

class CancerDataset:
    def __init__(self):
        self.X = None
        self.y = None
    
    @staticmethod
    def load_breast_cancer():
        from sklearn.datasets import load_breast_cancer
        data = load_breast_cancer()
        ds = CancerDataset()
        ds.X = data.data
        ds.y = data.target
        return ds
    
    def get_data(self):
        return self.X, self.y

class DataLoader:
    def __init__(self, normalize=True, test_size=0.2, random_state=42):
        self.normalize = normalize
        self.test_size = test_size
        self.random_state = random_state
    
    def load_and_split(self, dataset_name="breast_cancer"):
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        ds = CancerDataset.load_breast_cancer()
        X, y = ds.get_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=self.test_size, random_state=self.random_state, stratify=y)
        if self.normalize:
            sc = StandardScaler()
            X_train = sc.fit_transform(X_train)
            X_test = sc.transform(X_test)
        return X_train, X_test, y_train, y_test
