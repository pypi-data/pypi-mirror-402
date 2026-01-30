# -*- coding: utf-8 -*-
# migrate.py - run manually or use bmdb migrate
from .models import Base, engine

if engine:
    Base.metadata.create_all(engine)
    print('Tables created')
else:
    print('Error: DB_CONNECTION not set')