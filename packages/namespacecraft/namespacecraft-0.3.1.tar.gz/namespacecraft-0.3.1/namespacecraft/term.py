class Term(str):
    """A terminal URI value"""
    __slots__ = ()

    def __new__(cls, value: str):
        return super().__new__(cls, value)

    def __repr__(self) -> str:
        return f'Term({super().__repr__()})'
