from .fields import Field


class ModelMeta(type):
    def __new__(mcls, name, bases, attrs):
        # ignore base model class itself
        if name == "BaseModel":
            return super().__new__(mcls, name, bases, attrs)

        # Collect field objects from namespaces
        fields = {}
        primary_key = None

        for attr_name, attr_value in list(attrs.items()):
            if isinstance(attr_value, Field):
                fields[attr_name] = attr_value
                if attr_value.primary_key:
                    if primary_key is not None:
                        raise ValueError(
                            "Multiple primary keys are not allowed"
                        )
                    primary_key = attr_value

        if primary_key is None:
            # optional: auto-add id primary key
            from .fields import IntegerField
            pk = IntegerField(primary_key=True)
            attrs["id"] = pk
            fields["id"] = pk
            primary_key = pk

        cls = super().__new__(mcls, name, bases, attrs)
        cls._meta = {
            "fields": fields,
            "primary_key": primary_key,
            "table_name": name.lower()
        }
        return cls


class BaseModel(metaclass=ModelMeta):
    _verbose = False

    def __init__(self, **kwargs):
        fields = self._meta["fields"]
        for name in fields:
            setattr(self, name, kwargs.get(name))

    def __repr__(self) -> str:
        attrs = [f"{name}={self.__dict__.get(name, None)!r}"
                 for name in self.__dict__.keys()]
        return f"{self.__class__.__name__}({', '.join(attrs)})"

    @classmethod
    def create_table(cls, session):
        fields = cls._meta["fields"]
        tablename = cls._meta["table_name"]

        col_defs = []

        for name, field in fields.items():
            col = f"{name} {field.sql_type}"
            if field.primary_key:
                col += " PRIMARY KEY"
            col_defs.append(col)

        sql = f"""
        CREATE TABLE IF NOT EXISTS {tablename} (
            {", ".join(col for col in col_defs)}
        );
        """
        session.execute(sql)
        session.commit()
        if cls._verbose:
            print(sql)

    def save(self, session):
        fields = self._meta["fields"]
        tablename = self._meta["table_name"]
        pk_field = self._meta["primary_key"]
        pk_name = pk_field.column_name

        values = {name: getattr(self, name) for name in fields}
        sql = ""
        if pk_value := values[pk_name] is None:
            column_names = ", ".join(fields.keys())
            placeholders = ", ".join(["?"] * len(fields))
            params = [values[name] for name in fields]
            sql += f"""INSERT INTO {tablename}({column_names})
            VALUES ({placeholders})"""
        else:
            cols = [f"{name}=?" for name in fields if name != pk_name]
            column_names = ", ".join(cols)
            params = [values[name] for name in fields if name != pk_name]
            params.append(pk_value)
            sql += f"UPDATE {tablename} SET {column_names} WHERE {pk_name} = ?"
        cursor = session.execute(sql, params)
        session.commit()
        if pk_field.sql_type.upper() == "INTEGER" and pk_field.primary_key:
            new_id = cursor.lastrowid
            setattr(self, pk_name, new_id)
        return self

    @classmethod
    def all(cls, session):
        tablename = cls._meta["table_name"]
        fields = cls._meta["fields"]

        sql = f"SELECT * FROM {tablename}"
        cursor = session.execute(sql)
        rows = cursor.fetchall()
        data = []
        for row in rows:
            row_info = {}
            for idx, name in enumerate(fields.keys()):
                row_info[name] = row[idx]
            data.append(cls(**row_info))
        return data

    def delete(self, session):
        tablename = self._meta["table_name"]
        pk_field = self._meta["primary_key"]
        pk_name = pk_field.column_name
        pk_value = getattr(self, pk_name)
        sql = f"DELETE FROM {tablename} WHERE id = ?"
        params = [pk_value]
        session.execute(sql, params)
        session.commit()
        setattr(self, pk_name, None)
        return True
