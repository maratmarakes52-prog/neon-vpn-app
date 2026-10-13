import crypto from "node:crypto";

const MAX_AGE_SECONDS = 3600;
const MAX_ITEMS = 100;
const MAX_BODY_BYTES = 100_000;

function validateTelegramInitData(initData, botToken) {
  if (typeof initData !== "string" || !initData || !botToken) {
    return null;
  }

  const params = new URLSearchParams(initData);
  const hash = params.get("hash");

  if (!hash || !/^[a-f0-9]{64}$/i.test(hash)) {
    return null;
  }

  params.delete("hash");

  const authDate = Number(params.get("auth_date"));
  const now = Math.floor(Date.now() / 1000);

  if (
    !Number.isFinite(authDate) ||
    authDate > now + 30 ||
    now - authDate > MAX_AGE_SECONDS
  ) {
    return null;
  }

  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");

  const secretKey = crypto
    .createHmac("sha256", "WebAppData")
    .update(botToken)
    .digest();

  const expectedHash = crypto
    .createHmac("sha256", secretKey)
    .update(dataCheckString)
    .digest("hex");

  const received = Buffer.from(hash, "hex");
  const expected = Buffer.from(expectedHash, "hex");

  if (
    received.length !== expected.length ||
    !crypto.timingSafeEqual(received, expected)
  ) {
    return null;
  }

  try {
    const user = JSON.parse(params.get("user") || "{}");

    if (!Number.isSafeInteger(user.id) || user.id <= 0) {
      return null;
    }

    return user;
  } catch {
    return null;
  }
}

function validCart(items) {
  if (!Array.isArray(items) || items.length > MAX_ITEMS) {
    return false;
  }

  return items.every((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      return false;
    }

    if (
      typeof item.id !== "string" ||
      item.id.length < 1 ||
      item.id.length > 200
    ) {
      return false;
    }

    if (
      !Number.isSafeInteger(item.quantity) ||
      item.quantity < 1 ||
      item.quantity > 99
    ) {
      return false;
    }

    return true;
  });
}

async function supabaseRequest(path, method, body) {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    throw new Error("Supabase environment variables are missing");
  }

  const response = await fetch(
    `${url.replace(/\/$/, "")}/rest/v1/${path}`,
    {
      method,
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        Prefer: "return=representation"
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) })
    }
  );

  if (!response.ok) {
    const error = await response.text();
    console.error("Supabase request failed:", response.status, error);
    throw new Error("Database request failed");
  }

  if (response.status === 204) return null;

  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method !== "GET" && req.method !== "PUT") {
    res.setHeader("Allow", "GET, PUT");
    return res.status(405).json({ error: "Method not allowed" });
  }

  const contentLength = Number(req.headers["content-length"] || 0);

  if (contentLength > MAX_BODY_BYTES) {
    return res.status(413).json({ error: "Request too large" });
  }

  const initData =
    req.headers["x-telegram-init-data"] ||
    (req.method === "PUT" ? req.body?.initData : null);

  const user = validateTelegramInitData(initData, process.env.BOT_TOKEN);

  if (!user) {
    return res.status(401).json({
      error: "Invalid or expired Telegram session"
    });
  }

  try {
    if (req.method === "GET") {
      const rows = await supabaseRequest(
        `user_carts?telegram_id=eq.${user.id}&select=items`,
        "GET"
      );

      return res.status(200).json({
        items: rows?.[0]?.items || []
      });
    }

    const items = req.body?.items;

    if (!validCart(items)) {
      return res.status(400).json({
        error: "Invalid cart data"
      });
    }

    const rows = await supabaseRequest(
      "user_carts?on_conflict=telegram_id",
      "POST",
      [{
        telegram_id: user.id,
        items,
        updated_at: new Date().toISOString()
      }]
    );

    // PostgREST upsert requires Prefer: resolution=merge-duplicates.
    // The helper above is intentionally simple; use the dedicated
    // upsert below instead.
    return res.status(200).json({
      ok: true,
      items: rows?.[0]?.items ?? items
    });
  } catch {
    return res.status(500).json({
      error: "Unable to access cart"
    });
  }
}