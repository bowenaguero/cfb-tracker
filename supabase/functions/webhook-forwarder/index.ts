import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

interface WebhookPayload {
  type: "INSERT" | "UPDATE" | "DELETE"
  table: string
  record: Record<string, unknown>
  old_record: Record<string, unknown>
}

serve(async (req) => {
  try {
    const payload: WebhookPayload = await req.json()

    const webhookUrls: Record<string, string | undefined> = {
      recruits: Deno.env.get("RECRUITS_WEBHOOK_URL"),
      portal: Deno.env.get("PORTAL_WEBHOOK_URL"),
    }

    const webhookUrl = webhookUrls[payload.table]

    if (!webhookUrl) {
      console.error(`No webhook URL configured for table: ${payload.table}`)
      return new Response(JSON.stringify({ error: "No webhook URL configured" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      })
    }

    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: payload.type.toLowerCase(),
        table: payload.table,
        record: payload.type === "DELETE" ? payload.old_record : payload.record,
        old_record: payload.old_record,
        timestamp: new Date().toISOString(),
      }),
    })

    if (!response.ok) {
      console.error(`Webhook failed: ${response.status} ${response.statusText}`)
      return new Response(JSON.stringify({ error: "Webhook delivery failed" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      })
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  } catch (error) {
    console.error("Error processing webhook:", error)
    return new Response(JSON.stringify({ error: "Internal error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    })
  }
})
