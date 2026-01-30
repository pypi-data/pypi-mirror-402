from pydantic_settings import BaseSettings, SettingsConfigDict 
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_DIR =  BASE_DIR / ".env"

assert ENV_DIR.exists(), f"{ENV_DIR} not found"

class AppSettings(BaseSettings):
	DB_HOST: str | None = None
	DB_USER: str | None = None
	DB_PORT: str | None = None
	DB_NAME: str | None = None
	DB_PASSWORD: str | None = None
	SQLITE_URL: str |  None = None

	# JWT 
	SECRET_KEY: str 
	ALGORITHM: str
	DEFAULT_TOKEN_EXPIRE_MINUT: int

	model_config = SettingsConfigDict(
		env_file=ENV_DIR, 
		env_file_encoding = 'utf-8'
	)

	@property
	def DB_URL(self) -> str: 
		if self.SQLITE_URL:
			return self.SQLITE_URL
		
		if not all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_PORT, self.DB_NAME]):
			raise ValueError("PostgreSQL uchun DB_* ozgaruvchilar toliq emas")
		
		return (
			f"postgresql+psycopg2://"
			f"{self.DB_USER}:{self.DB_PASSWORD}"
			f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
		)
		

settings = AppSettings()