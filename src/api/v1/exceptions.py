from fastapi import HTTPException, status

class DatabaseError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code=status_code, detail=detail)

class ConflictError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code=status_code, detail=detail) 