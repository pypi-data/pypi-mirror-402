
#### 3. `topicminer/__init__.py`
```python
from .auth import AuthManager
from .core import TopicMinerEngine

class TopicMiner:
    def __init__(self):
        self.auth = AuthManager()
        self.engine = TopicMinerEngine(self.auth)

    def request_token(self, user_email):
        """Step 1: Request a verification token sent to your email."""
        success, message = self.auth.send_token_email(user_email)
        if success:
            print(f"✅ Token sent to {user_email}. Check your inbox.")
            print("Please run: tm.login('YOUR_TOKEN') to verify.")
        else:
            print(f"❌ Error sending email: {message}")

    def login(self, token):
        """Step 2: Verify the token to unlock library features."""
        if self.auth.verify_token(token):
            print("🚀 Access Granted! You can now use the analysis methods.")
            return True
        else:
            print("❌ Invalid Token. Access Denied.")
            return False

    def analyze_dataframe(self, df, text_column):
        """Step 3: Perform topic modeling on the DataFrame."""
        try:
            return self.engine.analyze(df, text_column)
        except PermissionError as e:
            print(f"Access Denied: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_report(self):
        """Step 4: Generate a detailed text report."""
        try:
            report = self.engine.generate_report()
            footer = self.auth.get_usage_metrics()
            return report + footer
        except Exception as e:
            return f"Error generating report: {e}"

    def show_plots(self):
        """Step 5: Display interactive Plotly visualizations."""
        try:
            figs = self.engine.get_visualizations()
            for name, fig in figs.items():
                fig.show()
            print(self.auth.get_usage_metrics())
        except Exception as e:
            print(f"Error displaying plots: {e}")