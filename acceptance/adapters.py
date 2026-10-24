"""Two explicit versions of a minimal application's customer repository."""
from dataclasses import dataclass


class RecordMissing(LookupError):
    """An expected fixture record was explicitly observed to be absent."""


@dataclass(frozen=True)
class CustomerRepository:
    version: str
    column: str

    def read(self, conn, customer_id):
        # column is an internal constant, never user input.
        row = conn.execute(
            f'SELECT {self.column} FROM customers WHERE id = %s', (customer_id,)
        ).fetchone()
        if row is None:
            raise RecordMissing()
        return row[0]

    def create(self, conn, customer_id, email):
        conn.execute(
            f'INSERT INTO customers (id, {self.column}) VALUES (%s, %s)',
            (customer_id, email),
        )

    def update(self, conn, customer_id, email):
        conn.execute(
            f'UPDATE customers SET {self.column} = %s WHERE id = %s',
            (email, customer_id),
        )


OLD = CustomerRepository('v1', 'email')
NEW = CustomerRepository('v2', 'contact_email')
