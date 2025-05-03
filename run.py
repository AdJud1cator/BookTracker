from app import create_app

app = create_app()

# To run the application, use the command: python run.py
if __name__ == '__main__':
    app.run(debug=True)