class CancerClassifier:
    def __init__(self, model_type="random_forest", random_state=42):
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
    
    def fit(self, X, y):
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=self.random_state)
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        return self.model.predict(X)
    
    def predict_proba(self, X):
        return self.model.predict_proba(X)
