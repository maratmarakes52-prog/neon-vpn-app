const APP_URL = process.env.APP_URL;
const BOT_TOKEN = process.env.BOT_TOKEN;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;

const API = `https://api.telegram.org/bot${8396467823:AAGkpBmRASv6jPF3wyKjo4rg6suEHqHXirE}`;

async function sendMessage(chatId, text, keyboard) {
  const response = await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: "HTML",
      reply_markup: keyboard
    })
  });

  if (!response.ok) {
    console.error("Telegram sendMessage error:", await response.text());
  }
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).send("Method not allowed");
  }

  if (!BOT_TOKEN || !APP_URL || !WEBHOOK_SECRET) {
    return res.status(500).send("Server configuration error");
  }

  if (
    req.headers["x-telegram-bot-api-secret-token"] !== WEBHOOK_SECRET
  ) {
    return res.status(401).send("Unauthorized");
  }

  const update = req.body;
  const message = update?.message;

  if (!message?.chat?.id || typeof message.text !== "string") {
    return res.status(200).json({ ok: true });
  }

  const chatId = message.chat.id;
  const text = message.text.trim();

  if (/^\/start(?:@\w+)?(?:\s|$)/i.test(text)) {
    await sendMessage(
      chatId,
      [
        "<b>NOIR MARKET</b>",
        "",
        "Добро пожаловать в маркет Telegram-подарков!",
        "Открой каталог, чтобы посмотреть доступные предложения.",
        "",
        "Нажимая кнопку запуска, ты открываешь мини-приложение NOIR MARKET."
      ].join("\n"),
      {
        inline_keyboard: [
          [
            {
              text: "🖤 Открыть NOIR MARKET",
              web_app: { url: APP_URL }
            }
          ],
          [
            {
              text: "🔒 Политика конфиденциальности",
              url: `${APP_URL.replace(/\/$/, "")}/privacy.html`
            }
          ]
        ]
      }
    );
  }

  return res.status(200).json({ ok: true });
}