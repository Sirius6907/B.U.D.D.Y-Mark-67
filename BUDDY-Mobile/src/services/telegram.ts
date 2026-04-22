const BOT_TOKEN = process.env.EXPO_PUBLIC_TELEGRAM_BOT_TOKEN || "";
const USER_ID = process.env.EXPO_PUBLIC_TELEGRAM_USER_ID || "";

export const sendTelegramMessage = async (text: string) => {
  if (!BOT_TOKEN || !USER_ID) return;

  try {
    await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chat_id: USER_ID,
        text: `[BUDDY Mobile]: ${text}`,
        parse_mode: "Markdown",
      }),
    });
  } catch (error) {
    console.error("Telegram Send Error:", error);
  }
};

export const pollTelegramUpdates = async (onMessage: (text: string) => void) => {
    let lastUpdateId = 0;
    
    // This is a simple polling loop. In a real production app, 
    // we would use webhooks or a background task.
    const poll = async () => {
        try {
            const response = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?offset=${lastUpdateId + 1}&timeout=30`);
            const data = await response.json();
            
            if (data.ok && data.result.length > 0) {
                for (const update of data.result) {
                    lastUpdateId = update.update_id;
                    if (update.message && update.message.chat.id.toString() === USER_ID) {
                        onMessage(update.message.text);
                    }
                }
            }
        } catch (error) {
            console.error("Telegram Poll Error:", error);
        }
        // Poll again after 5 seconds
        setTimeout(poll, 5000);
    };

    poll();
};
