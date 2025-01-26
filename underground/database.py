import contextlib
import databases
import sqlalchemy
from underground.config import TESTING, DATABASE_URL, TEST_DATABASE_URL

metadata = sqlalchemy.MetaData()

if TESTING:
    database = databases.Database(TEST_DATABASE_URL, force_rollback=True)
else:
    database = databases.Database(DATABASE_URL)

@contextlib.asynccontextmanager
async def lifespan(_):
    await database.connect()
    yield
    await database.disconnect()
