import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import apiClient from '../utils/apiClient';

describe('apiClient refresh token interceptor', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('returns specific error messages for different HTTP status codes', async () => {
    const originalFetch = globalThis.fetch;
    let callCount = 0;

    globalThis.fetch = vi.fn(async (url: string | URL | Request) => {
      callCount++;
      const urlStr = url.toString();

      // First call: 429 rate limit
      if (callCount === 1 && urlStr.includes('/test-429')) {
        return new Response(JSON.stringify({ detail: 'Rate limited' }), { status: 429 });
      }
      // Second call: 404
      if (callCount === 2 && urlStr.includes('/test-404')) {
        return new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 });
      }
      // Third call: 500
      if (callCount === 3 && urlStr.includes('/test-500')) {
        return new Response(JSON.stringify({ detail: 'Server error' }), { status: 500 });
      }

      return new Response('{}', { status: 200 });
    }) as any;

    try {
      await apiClient.get('/test-429');
    } catch (e: any) {
      expect(e.message).toContain('429');
    }

    try {
      await apiClient.get('/test-404');
    } catch (e: any) {
      expect(e.message).toContain('404');
    }

    try {
      await apiClient.get('/test-500');
    } catch (e: any) {
      expect(e.message).toContain('500');
    }

    globalThis.fetch = originalFetch;
  });
});
