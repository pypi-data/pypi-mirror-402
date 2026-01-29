    async def list_{entity_snake}s(self, db):
        return await self.service.list(db)

    async def get_{entity_snake}(self, db, entity_id: int):
        return await self.service.get(db, entity_id)

    async def create_{entity_snake}(self, db, data):
        return await self.service.create(db, data.dict())

    async def update_{entity_snake}(self, db, entity_id: int, data):
        return await self.service.update(db, entity_id, data.dict())
        
    async def delete_{entity_snake}(self, db, entity_id: int):
        return await self.service.delete(db, entity_id)
