import { initializeApp, getApps } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? 'demo-key',
  authDomain: `${process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? 'demo-astronomer'}.firebaseapp.com`,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? 'demo-astronomer',
};

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
export const auth = getAuth(app);

let _emulatorConnected = false;
if (
  typeof window !== 'undefined' &&
  process.env.NEXT_PUBLIC_USE_EMULATOR === 'true' &&
  !_emulatorConnected
) {
  connectAuthEmulator(auth, 'http://localhost:9099', { disableWarnings: true });
  _emulatorConnected = true;
}
