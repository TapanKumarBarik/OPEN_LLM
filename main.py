from app import create_app, db
from config.development import DevelopmentConfig

app = create_app(DevelopmentConfig)

@app.cli.command()
def db_setup():
    """Set up the database."""
    from app import db
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)