from app.shared.controller import BaseController
from app.modules.{module_snake}.service.{entity_snake}_service import {entity}Service


class {controller_name}Controller(BaseController):

    def __init__(self):
        self.service = {entity}Service()
