import { describe, it, expect } from 'vitest';
import { isTokenExpired } from '../utils/tokenStorage';

function makeToken(payload: Record<string, unknown>, expired = false): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const exp = Math.floor(Date.now() / 1000) + (expired ? -3600 : 3600);
  const body = btoa(JSON.stringify({ ...payload, exp }));
  return `${header}.${body}.fake-sig`;
}

describe('isTokenExpired', () => {
  it('returns false for a valid future token', () => {
    const token = makeToken({ sub: 1, role: 'student' }, false);
    expect(isTokenExpired(token)).toBe(false);
  });

  it('returns true for an expired token', () => {
    const token = makeToken({ sub: 1, role: 'student' }, true);
    expect(isTokenExpired(token)).toBe(true);
  });

  it('returns true for a malformed token', () => {
    expect(isTokenExpired('not-a-jwt')).toBe(true);
  });

  it('returns true for an empty string', () => {
    expect(isTokenExpired('')).toBe(true);
  });

  it('returns true for a token with missing payload', () => {
    expect(isTokenExpired('header.')).toBe(true);
  });
});
