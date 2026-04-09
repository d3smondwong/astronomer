'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Info, Sparkles, CalendarIcon } from 'lucide-react';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { format, parse, isValid } from 'date-fns';
import { calculateBazi, saveProfile, type BaziProfile } from '@/lib/baziCalculator';
import { toast } from 'sonner';

export default function Landing() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [birthDate, setBirthDate] = useState<Date>();
  const [dateInputValue, setDateInputValue] = useState('');
  const [birthTime, setBirthTime] = useState('12:00');
  const [birthLocation, setBirthLocation] = useState('');
  const [gender, setGender] = useState<'male' | 'female'>('male');
  const [useTrueSolarTime, setUseTrueSolarTime] = useState(true);
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  const handleDateInputChange = (value: string) => {
    setDateInputValue(value);
    
    // Try to parse the date in various formats
    const formats = ['MM/dd/yyyy', 'M/d/yyyy', 'yyyy-MM-dd', 'dd/MM/yyyy'];
    
    for (const formatStr of formats) {
      const parsedDate = parse(value, formatStr, new Date());
      if (isValid(parsedDate)) {
        setBirthDate(parsedDate);
        return;
      }
    }
  };

  const handleCalendarSelect = (date: Date | undefined) => {
    setBirthDate(date);
    if (date) {
      setDateInputValue(format(date, 'MM/dd/yyyy'));
    }
    setIsCalendarOpen(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !birthDate || !birthTime || !birthLocation) {
      toast.error('Please fill in all fields');
      return;
    }

    const profileId = `profile-${Date.now()}`;
    
    const profileData = {
      name,
      birthDate,
      birthTime,
      birthLocation,
      gender,
      useTrueSolarTime,
    };

    const baziChart = calculateBazi(profileData);
    
    const profile: BaziProfile = {
      id: profileId,
      ...profileData,
      baziChart,
    };

    saveProfile(profile);
    toast.success('Bazi chart generated successfully!');
    router.push(`/profile/${profileId}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl shadow-2xl">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center mb-2">
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-3 rounded-full">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-3xl">Bazi Fortune Telling</CardTitle>
          <CardDescription className="text-base">
            Discover your destiny through the ancient art of Four Pillars of Destiny
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Profile Name</Label>
              <Input
                id="name"
                placeholder="Enter name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Birthday</Label>
              <div className="flex gap-2">
                <Input
                  id="dateInput"
                  type="text"
                  value={dateInputValue}
                  onChange={(e) => handleDateInputChange(e.target.value)}
                  placeholder="MM/DD/YYYY"
                  className="flex-1"
                />
                <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="shrink-0"
                    >
                      <CalendarIcon className="h-4 w-4" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="end">
                    <Calendar
                      mode="single"
                      selected={birthDate}
                      onSelect={handleCalendarSelect}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="birthTime">Birth Time</Label>
              <Input
                id="birthTime"
                type="time"
                value={birthTime}
                onChange={(e) => setBirthTime(e.target.value)}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="trueSolarTime"
                  checked={useTrueSolarTime}
                  onCheckedChange={(checked) => setUseTrueSolarTime(checked as boolean)}
                />
                <Label htmlFor="trueSolarTime" className="cursor-pointer">
                  Use True Solar Time
                </Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="w-4 h-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p>
                        True Solar Time adjusts your birth time based on your location's longitude,
                        providing a more accurate reading of the sun's position at your birth.
                        This accounts for timezone and daylight saving time discrepancies.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="birthLocation">Birth Location</Label>
              <Input
                id="birthLocation"
                placeholder="City, Country"
                value={birthLocation}
                onChange={(e) => setBirthLocation(e.target.value)}
              />
            </div>

            <div className="space-y-3">
              <Label>Gender</Label>
              <RadioGroup value={gender} onValueChange={(value) => setGender(value as 'male' | 'female')}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="male" id="male" />
                  <Label htmlFor="male" className="cursor-pointer font-normal">Male</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="female" id="female" />
                  <Label htmlFor="female" className="cursor-pointer font-normal">Female</Label>
                </div>
              </RadioGroup>
            </div>

            <Button type="submit" className="w-full" size="lg">
              Generate Bazi Report
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}