-- Enable the pg_net extension for HTTP requests
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Function to call the webhook edge function
CREATE OR REPLACE FUNCTION notify_webhook()
RETURNS TRIGGER AS $$
DECLARE
  payload jsonb;
  supabase_url text := current_setting('app.settings.supabase_url', true);
  service_key text := current_setting('app.settings.service_role_key', true);
BEGIN
  payload := jsonb_build_object(
    'type', TG_OP,
    'table', TG_TABLE_NAME,
    'record', CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END,
    'old_record', CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END
  );

  PERFORM net.http_post(
    url := supabase_url || '/functions/v1/webhook-forwarder',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || service_key
    ),
    body := payload
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for recruits table
DROP TRIGGER IF EXISTS recruits_webhook_trigger ON recruits;
CREATE TRIGGER recruits_webhook_trigger
  AFTER INSERT OR UPDATE OR DELETE ON recruits
  FOR EACH ROW
  EXECUTE FUNCTION notify_webhook();

-- Trigger for portal table
DROP TRIGGER IF EXISTS portal_webhook_trigger ON portal;
CREATE TRIGGER portal_webhook_trigger
  AFTER INSERT OR UPDATE OR DELETE ON portal
  FOR EACH ROW
  EXECUTE FUNCTION notify_webhook();
