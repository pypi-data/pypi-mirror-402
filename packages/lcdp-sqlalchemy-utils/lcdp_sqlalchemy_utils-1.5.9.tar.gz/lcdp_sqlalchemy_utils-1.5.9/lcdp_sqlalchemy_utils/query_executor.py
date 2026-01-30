from sqlalchemy import func
import asyncio
import nest_asyncio

# Avoid RuntimeError: This event loop is already running
# https://github.com/erdewit/nest_asyncio
nest_asyncio.apply()


class SearchResult:
    _items: list
    _total_found: int
    _total_visible: int

    def __init__(self, items=None, total_visible=None, total_found=None):
        self._items = items
        self._total_visible = total_visible
        self._total_found = total_found

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items

    @property
    def total_visible(self):
        return self._total_visible

    @total_visible.setter
    def total_visible(self, total_visible):
        self._total_visible = total_visible

    @property
    def total_found(self):
        return self._total_found

    @total_found.setter
    def total_found(self, total_found):
        self._total_found = total_found


class QueryExecutor:
    def __init__(self, model):
        self._model = model

    async def __get_query_count(self, query):
        counter = query.statement.with_only_columns(func.count()).select_from(self._model).order_by(None)
        return query.session.execute(counter).scalar()

    @staticmethod
    async def __get_query_result(query):
        return query.all()

    async def __execute(self, query, order_bys, page, limit):
        if not page:
            page = 0
        if not order_bys:
            order_bys = []

        count_query = query
        if order_bys:
            query = query.order_by(*order_bys)

        if limit:
            query = query.limit(limit).offset(page * limit)

        async with asyncio.TaskGroup() as tg:
            items_task = tg.create_task(self.__get_query_result(query))
            count_task = tg.create_task(self.__get_query_count(count_query))
        return SearchResult(items_task.result(), count_task.result(), count_task.result())

    def execute(self, query, order_bys=None, page=None, limit=None):
        return asyncio.run(self.__execute(query, order_bys, page, limit))


class QueryExecutorAsync:
    def __init__(self, model):
        self._model = model

    async def __get_query_count(self, get_db_session, query):
        counter = query.with_only_columns(func.count()).select_from(self._model).order_by(None)
        result = await get_db_session().execute(counter)
        return result.scalar_one()

    @staticmethod
    async def __get_query_result(get_db_session, query):
        result = await get_db_session().execute(query)
        return result.scalars().all()

    async def __execute(self, get_db_session, query, order_bys, page, limit):
        if not page:
            page = 0
        if not order_bys:
            order_bys = []

        count_query = query
        if order_bys:
            query = query.order_by(*order_bys)

        if limit:
            query = query.limit(limit).offset(page * limit)

        async with asyncio.TaskGroup() as tg:
            count_task = tg.create_task(self.__get_query_count(get_db_session, count_query))
            items = await self.__get_query_result(get_db_session, query)
        # Important note : As count is run in a parallel task, the returned value will not take into account modifications
        # of DB state in the current task session (ex : object have been updated before, without transaction commit)
        await asyncio.shield(count_task)
        return SearchResult(items, count_task.result(), count_task.result())

    # Pass get_db_session as a method because we need to call two distinct session for counts and values
    async def execute(self, get_db_session, query, order_bys=None, page=None, limit=None):
        return await self.__execute(get_db_session, query, order_bys, page, limit)
