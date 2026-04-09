'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Plus, Users, MessageSquare, User, Trash2, Home } from 'lucide-react';
import { getProfiles, deleteProfile, type BaziProfile } from '@/lib/baziCalculator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [profiles, setProfiles] = useState<BaziProfile[]>([]);

  useEffect(() => {
    loadProfiles();
  }, [pathname]);

  const loadProfiles = () => {
    const loadedProfiles = getProfiles();
    setProfiles(loadedProfiles);
  };

  const handleDeleteProfile = (id: string) => {
    deleteProfile(id);
    loadProfiles();
    toast.success('Profile deleted');

    // If we're on the deleted profile's page, navigate to home
    if (pathname.includes(id)) {
      router.push('/');
    }
  };

  const isActive = (path: string) => {
    return pathname.includes(path);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Left Sidebar */}
      <aside className="w-64 border-r bg-card flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <span className="text-2xl">✨</span>
            Bazi Fortune
          </h1>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6">
            {/* Home */}
            <div>
              <Link href="/">
                <Button
                  variant="ghost"
                  className="w-full justify-start mb-2"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Home
                </Button>
              </Link>
            </div>

            <Separator />

            {/* Profiles Section */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-muted-foreground">PROFILES</h3>
                <Link href="/">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </Link>
              </div>

              <div className="space-y-1">
                {profiles.length === 0 ? (
                  <p className="text-sm text-muted-foreground px-2 py-1">
                    No profiles yet
                  </p>
                ) : (
                  profiles.map((profile) => (
                    <div
                      key={profile.id}
                      className={`flex items-center justify-between group rounded-md hover:bg-accent ${
                        isActive(profile.id) ? 'bg-accent' : ''
                      }`}
                    >
                      <Link href={`/profile/${profile.id}`}>
                        <Button
                          variant="ghost"
                          className="flex-1 justify-start text-sm font-normal"
                        >
                          <User className="w-4 h-4 mr-2" />
                          {profile.name}
                        </Button>
                      </Link>

                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="w-3 h-3 text-destructive" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Profile</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete "{profile.name}"? This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleDeleteProfile(profile.id)}>
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  ))
                )}
              </div>
            </div>

            <Separator />

            {/* Other Sections */}
            <div className="space-y-1">
              <Link href="/compatibility">
                <Button
                  variant="ghost"
                  className={`w-full justify-start ${isActive('compatibility') ? 'bg-accent' : ''}`}
                >
                  <Users className="w-4 h-4 mr-2" />
                  Compatibility
                </Button>
              </Link>

              <Link href="/ai_oracle_chat">
                <Button
                  variant="ghost"
                  className={`w-full justify-start ${isActive('ai_oracle_chat') ? 'bg-accent' : ''}`}
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  AI Oracle Chat
                </Button>
              </Link>
            </div>
          </div>
        </ScrollArea>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
