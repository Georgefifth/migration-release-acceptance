-- The target schema is valid, but the old adapter still queries email.
ALTER TABLE customers RENAME COLUMN email TO contact_email;
