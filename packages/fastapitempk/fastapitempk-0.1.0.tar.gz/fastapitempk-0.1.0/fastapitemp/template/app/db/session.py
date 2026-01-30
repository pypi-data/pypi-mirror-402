from sqlalchemy.engine import create_engine 
from sqlalchemy.orm import sessionmaker
from app.settings import settings 

DATABSE_URL = settings.DB_URL

engine = create_engine(DATABSE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db():
	db = SessionLocal()
	try: 
		yield db
	finally:
		db.close()