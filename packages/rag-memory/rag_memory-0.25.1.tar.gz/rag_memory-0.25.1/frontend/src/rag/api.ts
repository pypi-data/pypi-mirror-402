/**
 * ChatSSEClient - SSE client for streaming chat responses
 *
 * Following Lumentor pattern from agent-architecture-platform
 * Uses fetch API with Server-Sent Events (SSE) for real-time streaming
 */

import type { SSEEvent } from './types';

export interface ChatSSEClientOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onMessage?: (event: SSEEvent) => void;
  onError?: (error: Error) => void;
}

export class ChatSSEClient {
  private baseUrl: string;
  private getToken: () => Promise<string | null>;
  private options: ChatSSEClientOptions;
  private abortController: AbortController | null = null;
  private isOpen = false;

  constructor(
    baseUrl: string,
    getToken: () => Promise<string | null>,
    options: ChatSSEClientOptions = {}
  ) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
    this.options = options;
  }

  async send(requestBody: string): Promise<void> {
    if (this.abortController) {
      // Cancel previous request if still ongoing
      this.abortController.abort();
    }

    this.abortController = new AbortController();

    try {
      const token = await this.getToken();
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers,
        body: requestBody,
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // SSE connection established
      if (!this.isOpen) {
        this.isOpen = true;
        this.options.onOpen?.();
      }

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const event: SSEEvent = JSON.parse(data);
              this.options.onMessage?.(event);

              if (event.type === 'done') {
                // Stream completed
                this.isOpen = false;
                return;
              }
            } catch (error) {
              console.error('Failed to parse SSE data:', data, error);
            }
          }
        }
      }

      this.isOpen = false;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        // Request was aborted (user sent new message)
        return;
      }

      this.isOpen = false;
      this.options.onError?.(error);
      this.options.onMessage?.({
        type: 'error',
        error: error.message || 'Unknown error occurred',
      });
    }
  }

  close(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }

    if (this.isOpen) {
      this.isOpen = false;
      this.options.onClose?.();
    }
  }

  getIsOpen(): boolean {
    return this.isOpen;
  }
}
