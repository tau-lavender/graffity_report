class SingletonClass(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SingletonClass, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        # Список заявок (каждая заявка — dict)
        self.applications = []
        # photos: mapping report_id -> list of photo dicts {id, s3_key}
        self.photos = {}
        # Автоинкремент id для тестовой БД
        self._next_report_id = 1

    def next_report_id(self):
        rid = self._next_report_id
        self._next_report_id += 1
        return rid
