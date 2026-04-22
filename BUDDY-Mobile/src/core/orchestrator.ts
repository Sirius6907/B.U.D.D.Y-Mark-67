import { generateResponse } from '../services/gemini';
import { speak } from '../services/voice';
import { sendTelegramMessage } from '../services/telegram';

export interface Message {
  role: 'user' | 'buddy';
  content: string;
  timestamp: number;
}

class Orchestrator {
  private history: Message[] = [];
  private onHistoryUpdate: ((history: Message[]) => void) | null = null;

  setUpdateListener(listener: (history: Message[]) => void) {
    this.onHistoryUpdate = listener;
  }

  async processInput(text: string) {
    // 1. Add user message to history
    this.history.push({ role: 'user', content: text, timestamp: Date.now() });
    this.onHistoryUpdate?.([...this.history]);

    // 2. Get AI Response
    const responseText = await generateResponse(text, this.history);

    // 3. Add BUDDY message to history
    this.history.push({ role: 'buddy', content: responseText, timestamp: Date.now() });
    this.onHistoryUpdate?.([...this.history]);

    // 4. Voice synthesis
    await speak(responseText);

    // 5. Sync with Telegram
    await sendTelegramMessage(`Interaction: ${text}\nResponse: ${responseText}`);

    return responseText;
  }

  getHistory() {
    return this.history;
  }
}

export const orchestrator = new Orchestrator();
