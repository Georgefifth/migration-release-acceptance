"""Two explicit versions of a minimal application's customer repository."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerRepository:
    version: str
    column: str

    def read(self, conn, customer_id):
        # column is an internal constant, never user input.
        return conn.execute(
            f'SELECT {self.column} FROM customers WHERE id = %s', (customer_id,)
        ).fetchone()[0]

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
