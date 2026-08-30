/**
 * Firebase Admin SDK — server-side Firestore access.
 *
 * Local development: when FIRESTORE_EMULATOR_HOST is set, the Admin SDK connects
 * to the Firestore emulator and needs no credentials (a "demo-" project id keeps
 * it fully offline). Run the emulator with `npm run emulators`.
 *
 * Production (Phase 2): unset FIRESTORE_EMULATOR_HOST and provide service-account
 * credentials via GOOGLE_APPLICATION_CREDENTIALS (or App Hosting's built-in creds).
 *
 * `server-only` because this holds privileged credentials and the Admin SDK bypasses every
 * Firestore security rule. Client-side Firebase belongs in lib/firebaseClient.ts.
 */

import 'server-only';

import { getApps, initializeApp, applicationDefault, cert } from 'firebase-admin/app';
import { getFirestore, type Firestore } from 'firebase-admin/firestore';
import { getAuth, type Auth } from 'firebase-admin/auth';

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
let _auth: Auth | null = null;

export function getDb(): Firestore {
  if (!_db) {
    _db = getFirestore(initAdminApp());
  }
  return _db;
}

/** The Admin Auth instance — used for token verification and session cookies. */
export function getAdminAuth(): Auth {
  if (!_auth) {
    _auth = getAuth(initAdminApp());
  }
  return _auth;
}

export async function verifyIdToken(token: string): Promise<string | null> {
  try {
    const decoded = await getAdminAuth().verifyIdToken(token);
    return decoded.uid;
  } catch {
    return null;
  }
}

/** Verified caller identity, including whether the token came from an anonymous sign-in. */
export interface VerifiedUser {
  uid: string;
  isAnonymous: boolean;
}

/**
 * Verify an ID token and report whether it is an anonymous sign-in. Anonymous users own their
 * (guest) profiles but are gated from account-only features (e.g. insights, >1 chart).
 */
export async function verifyToken(token: string): Promise<VerifiedUser | null> {
  try {
    const decoded = await getAdminAuth().verifyIdToken(token);
    return { uid: decoded.uid, isAnonymous: decoded.firebase?.sign_in_provider === 'anonymous' };
  } catch {
    return null;
  }
}
