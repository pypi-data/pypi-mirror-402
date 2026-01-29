import dataclasses


class Column:
    def __init__(self, **kwargs):
        self.autoincrement = kwargs.get('autoincrement')

@dataclasses.dataclass
class Base:
    __tablename__ = None