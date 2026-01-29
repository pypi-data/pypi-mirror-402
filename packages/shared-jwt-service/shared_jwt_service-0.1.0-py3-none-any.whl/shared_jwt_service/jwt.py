import jwt
from fastapi import HTTPException

ALGORITHM = "HS256"

def get_user_id_from_auth_header(auth_header: str, secret_key: str) -> str:
	if not auth_header or not auth_header.startswith("Bearer "):
		raise HTTPException(status_code=401, detail="Missing token")

	token = auth_header.split(" ")[1]

	try:
		payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
		user_id = payload.get("sub")

		if not user_id:
			raise HTTPException(status_code=401, detail="Invalid token payload")

		return user_id

	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail="Token expired")
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail="Invalid token")
