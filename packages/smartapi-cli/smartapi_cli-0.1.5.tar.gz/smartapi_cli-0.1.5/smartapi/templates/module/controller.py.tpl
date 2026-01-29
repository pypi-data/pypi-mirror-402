from app.shared.controller import BaseController


class {module}Controller(BaseController):

    def __init__(self):
        pass

    async def index(self):
        return {{
            "status": True,
            "message": "{module} module ready",
            "data": None
        }}
