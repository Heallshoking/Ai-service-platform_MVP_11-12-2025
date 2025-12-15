import { GoogleIntegrationSettings } from '@/types/electrical';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const GOOGLE_REDIRECT_URI = `${window.location.origin}/google-callback`;
const SCOPES = [
  'https://www.googleapis.com/auth/calendar.events',
  'https://www.googleapis.com/auth/keep',
].join(' ');

export class GoogleAuthService {
  private static instance: GoogleAuthService;
  private settings: GoogleIntegrationSettings | null = null;

  private constructor() {
    this.loadSettings();
  }

  static getInstance(): GoogleAuthService {
    if (!GoogleAuthService.instance) {
      GoogleAuthService.instance = new GoogleAuthService();
    }
    return GoogleAuthService.instance;
  }

  private loadSettings(): void {
    const stored = localStorage.getItem('google_integration_settings');
    if (stored) {
      this.settings = JSON.parse(stored);
    }
  }

  private saveSettings(): void {
    if (this.settings) {
      localStorage.setItem('google_integration_settings', JSON.stringify(this.settings));
    }
  }

  getSettings(): GoogleIntegrationSettings | null {
    return this.settings;
  }

  updateSettings(settings: Partial<GoogleIntegrationSettings>): void {
    this.settings = { ...this.settings, ...settings } as GoogleIntegrationSettings;
    this.saveSettings();
  }

  initiateOAuth(): void {
    const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    authUrl.searchParams.set('client_id', GOOGLE_CLIENT_ID);
    authUrl.searchParams.set('redirect_uri', GOOGLE_REDIRECT_URI);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', SCOPES);
    authUrl.searchParams.set('access_type', 'offline');
    authUrl.searchParams.set('prompt', 'consent');

    window.location.href = authUrl.toString();
  }

  async handleCallback(code: string): Promise<boolean> {
    try {
      const response = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          code,
          client_id: GOOGLE_CLIENT_ID,
          client_secret: import.meta.env.VITE_GOOGLE_CLIENT_SECRET || '',
          redirect_uri: GOOGLE_REDIRECT_URI,
          grant_type: 'authorization_code',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to exchange code for token');
      }

      const data = await response.json();
      
      this.updateSettings({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        tokenExpiry: Date.now() + (data.expires_in * 1000),
        calendarEnabled: true,
        keepEnabled: true,
        autoSyncCalendar: true,
        autoSyncKeep: true,
      });

      return true;
    } catch (error) {
      console.error('OAuth callback error:', error);
      return false;
    }
  }

  async refreshAccessToken(): Promise<boolean> {
    if (!this.settings?.refreshToken) {
      return false;
    }

    try {
      const response = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          refresh_token: this.settings.refreshToken,
          client_id: GOOGLE_CLIENT_ID,
          client_secret: import.meta.env.VITE_GOOGLE_CLIENT_SECRET || '',
          grant_type: 'refresh_token',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to refresh token');
      }

      const data = await response.json();
      
      this.updateSettings({
        accessToken: data.access_token,
        tokenExpiry: Date.now() + (data.expires_in * 1000),
      });

      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  }

  async getValidAccessToken(): Promise<string | null> {
    if (!this.settings?.accessToken) {
      return null;
    }

    if (this.settings.tokenExpiry && Date.now() >= this.settings.tokenExpiry - 300000) {
      const refreshed = await this.refreshAccessToken();
      if (!refreshed) {
        return null;
      }
    }

    return this.settings.accessToken;
  }

  isAuthenticated(): boolean {
    return !!this.settings?.accessToken;
  }

  disconnect(): void {
    this.settings = null;
    localStorage.removeItem('google_integration_settings');
  }
}

export const googleAuth = GoogleAuthService.getInstance();
