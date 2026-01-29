# {entity} CRUD
@router.get("/{entity_snake}s")
async def list_{entity_snake}s(db=Depends(get_db)):
    return await controller.list_{entity_snake}s(db)

@router.get("/{entity_snake}s/{{entity_id}}")
async def get_{entity_snake}(entity_id: int, db=Depends(get_db)):
    return await controller.get_{entity_snake}(db, entity_id)

@router.post("/{entity_snake}s")
async def create_{entity_snake}(data: {entity}Create, db=Depends(get_db)):
    return await controller.create_{entity_snake}(db, data)

@router.put("/{entity_snake}s/{{entity_id}}")
async def update_{entity_snake}(entity_id: int, data: {entity}Update, db=Depends(get_db)):
    return await controller.update_{entity_snake}(db, entity_id, data)

@router.delete("/{entity_snake}s/{{entity_id}}")
async def delete_{entity_snake}(entity_id: int, db=Depends(get_db)):
    return await controller.delete_{entity_snake}(db, entity_id)
