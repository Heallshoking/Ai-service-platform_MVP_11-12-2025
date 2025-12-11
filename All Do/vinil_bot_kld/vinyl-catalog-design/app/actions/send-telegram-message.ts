"use server"

export async function sendTelegramBooking(data: {
  recordId: string
  recordTitle: string
  recordArtist: string
  recordPrice: number
  name: string
  phone: string
  address: string
  comment: string
}) {
  const telegramMessage = `
🎵 Новая бронь!

Пластинка: ${data.recordArtist} - ${data.recordTitle}
Артикул: ${data.recordId}
Цена: ${data.recordPrice.toLocaleString("ru-RU")} ₽

👤 Клиент:
Имя: ${data.name}
Телефон: ${data.phone}
Адрес: ${data.address}
Комментарий: ${data.comment || "—"}
  `.trim()

  try {
    const botToken = process.env.TELEGRAM_BOT_TOKEN
    const chatId = process.env.TELEGRAM_CHAT_ID

    if (!botToken || !chatId) {
      console.error("[v0] Missing Telegram credentials")
      return { success: false, error: "Telegram not configured" }
    }

    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text: telegramMessage,
        parse_mode: "HTML",
      }),
    })

    if (!response.ok) {
      throw new Error("Telegram API error")
    }

    return { success: true }
  } catch (error) {
    console.error("[v0] Telegram send error:", error)
    return { success: false, error: "Failed to send message" }
  }
}
