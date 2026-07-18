/**
 * Profile document shape, shared by server and client.
 *
 * This type lives here rather than alongside its Firestore accessors because client components
 * (the dashboard shell, the profile page) need it while `lib/profilesDb.ts` is `server-only` —
 * importing the type from there would pull a server module into the client graph.
 */

export interface ProfileRecord {
  profileId: string;
  name: string;
  birthLocation: string;
  birthData: {
    year: number;
    month: number;
    day: number;
    hour: number;
    minute: number;
    gender: number;
    latitude: number;
    longitude: number;
    use_solar_time_correction: boolean;
  };
  createdAt: string;
  chartKey?: string;
  userId?: string;
}
