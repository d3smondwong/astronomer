/**
 * Firebase Admin SDK — server-side Firestore access.
 *
 * Local development: when FIRESTORE_EMULATOR_HOST is set, the Admin SDK connects
 * to the Firestore emulator and needs no credentials (a "demo-" project id keeps
 * it fully offline). Run the emulator with `npm run emulators`.
 *
 * Production (Phase 2): unset FIRESTORE_EMULATOR_HOST and provide service-account
 * credentials via GOOGLE_APPLICATION_CREDENTIALS (or App Hosting's built-in creds).
 */

import { getApps, initializeApp, applicationDefault, cert } from 'firebase-admin/app';
import { getFirestore, type Firestore } from 'firebase-admin/firestore';
import { getAuth } from 'firebase-admin/auth';

const PROJECT_ID =
  process.env.FIREBASE_PROJECT_ID ?? process.env.GOOGLE_CLOUD_PROJECT ?? 'demo-astronomer';

function initAdminApp() {
  if (getApps().length > 0) {
    return getApps()[0];
  }

  // Against the emulator, no credentials are required — just a project id.
  if (process.env.FIRESTORE_EMULATOR_HOST) {
    return initializeApp({ projectId: PROJECT_ID });
  }

  // Production: prefer an explicit service-account JSON, else App Default Credentials.
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    return initializeApp({ credential: cert(serviceAccount), projectId: PROJECT_ID });
  }

  return initializeApp({ credential: applicationDefault(), projectId: PROJECT_ID });
}

let _db: Firestore | null = null;

export function getDb(): Firestore {
  if (!_db) {
    _db = getFirestore(initAdminApp());
  }
  return _db;
}

export async function verifyIdToken(token: string): Promise<string | null> {
  try {
    const decoded = await getAuth(initAdminApp()).verifyIdToken(token);
    return decoded.uid;
  } catch {
    return null;
  }
}
