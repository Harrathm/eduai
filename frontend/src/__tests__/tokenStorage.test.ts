import { describe, it, expect, vi, beforeEach } from 'vitest';
import { tokenStorage } from '../utils/tokenStorage';

describe('tokenStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves token', () => {
    tokenStorage.setToken('test-jwt-123');
    expect(tokenStorage.getToken()).toBe('test-jwt-123');
  });

  it('returns null when no token', () => {
    expect(tokenStorage.getToken()).toBeNull();
  });

  it('stores and retrieves refresh token', () => {
    tokenStorage.setRefreshToken('refresh-xyz');
    expect(tokenStorage.getRefreshToken()).toBe('refresh-xyz');
  });

  it('stores and retrieves user', () => {
    const user = { id: 1, email: 'test@test.com' };
    tokenStorage.setUser(user);
    const retrieved = tokenStorage.getUser();
    expect(retrieved).toEqual(user);
  });

  it('clearAll removes everything', () => {
    tokenStorage.setToken('abc');
    tokenStorage.setRefreshToken('xyz');
    tokenStorage.setUser({ id: 1 });
    tokenStorage.clearAll();
    expect(tokenStorage.getToken()).toBeNull();
    expect(tokenStorage.getRefreshToken()).toBeNull();
    expect(tokenStorage.getUser()).toBeNull();
  });
});
