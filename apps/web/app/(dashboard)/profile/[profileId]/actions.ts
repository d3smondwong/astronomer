'use server';

import { deleteProfile } from '@/lib/profilesDb';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

export async function deleteProfileAction(profileId: string) {
  try {
    await deleteProfile(profileId);
    revalidatePath('/(dashboard)');
    redirect('/');
  } catch (error) {
    console.error('Error deleting profile:', error);
    throw new Error('Failed to delete profile');
  }
}
