-- Keep both application versions working during the expansion window.
ALTER TABLE item ADD COLUMN display_title text;
UPDATE item SET display_title = title;

CREATE FUNCTION sync_item_title() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.title IS NOT NULL AND NEW.display_title IS NOT NULL
       AND NEW.title IS DISTINCT FROM NEW.display_title THEN
      RAISE EXCEPTION 'Conflicting title representations';
    END IF;
    NEW.title := COALESCE(NEW.title, NEW.display_title);
    NEW.display_title := NEW.title;
  ELSE
    IF NEW.title IS DISTINCT FROM OLD.title
       AND NEW.display_title IS DISTINCT FROM OLD.display_title
       AND NEW.title IS DISTINCT FROM NEW.display_title THEN
      RAISE EXCEPTION 'Conflicting title representations';
    ELSIF NEW.title IS DISTINCT FROM OLD.title THEN
      NEW.display_title := NEW.title;
    ELSIF NEW.display_title IS DISTINCT FROM OLD.display_title THEN
      NEW.title := NEW.display_title;
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER sync_item_title BEFORE INSERT OR UPDATE ON item
FOR EACH ROW EXECUTE FUNCTION sync_item_title();
ALTER TABLE item ALTER COLUMN display_title SET NOT NULL;
