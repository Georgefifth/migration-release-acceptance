-- Keep both application versions working during the expansion window.
ALTER TABLE customers ADD COLUMN contact_email text;
UPDATE customers SET contact_email = email;

CREATE FUNCTION sync_customer_email() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.email IS NOT NULL AND NEW.contact_email IS NOT NULL
       AND NEW.email IS DISTINCT FROM NEW.contact_email THEN
      RAISE EXCEPTION 'Conflicting email representations';
    END IF;
    NEW.email := COALESCE(NEW.email, NEW.contact_email);
    NEW.contact_email := NEW.email;
  ELSE
    IF NEW.email IS DISTINCT FROM OLD.email
       AND NEW.contact_email IS DISTINCT FROM OLD.contact_email
       AND NEW.email IS DISTINCT FROM NEW.contact_email THEN
      RAISE EXCEPTION 'Conflicting email representations';
    ELSIF NEW.email IS DISTINCT FROM OLD.email THEN
      NEW.contact_email := NEW.email;
    ELSIF NEW.contact_email IS DISTINCT FROM OLD.contact_email THEN
      NEW.email := NEW.contact_email;
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER sync_customer_email BEFORE INSERT OR UPDATE ON customers
FOR EACH ROW EXECUTE FUNCTION sync_customer_email();
ALTER TABLE customers ALTER COLUMN contact_email SET NOT NULL;
