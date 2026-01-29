class Field:
    sql_type = "TEXT"  # this is default, override in subclasses

    def __init__(self, primary_key=False, default=None) -> None:
        self.column_name = None
        self.primary_key = primary_key
        self.default = default

    def __set_name__(self, owner, name) -> None:
        # This gets called when the class is created
        self.column_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.column_name, self.default)

    def __set__(self, instance, value):
        value = self.validate(value)
        instance.__dict__[self.column_name] = value

    def validate(self, value):
        return value


class IntegerField(Field):
    sql_type = "INTEGER"

    def validate(self, value):
        if not isinstance(value, int | None):
            raise ValueError(f"{value} is not an int")
        return value


class PositiveField(IntegerField):
    def validate(self, value):
        return super().validate(value)


class TextField(Field):
    sql_type = "TEXT"
    
    def validate(self, value):
        if not isinstance(value, str | None):
            raise ValueError(f"{value} is not a str")
        return value


class BooleanField(Field):
    sql_type = "BOOLEAN"

    def validate(self, value):
        if not isinstance(value, bool | None):
            raise ValueError(f"{value} is not a bool")
        return value

class RealField(Field):
    sql_type = "REAL"

    def validate(self, value):
        if not isinstance(value, float | None):
            raise ValueError(f"{value} is not a float")
        return value

