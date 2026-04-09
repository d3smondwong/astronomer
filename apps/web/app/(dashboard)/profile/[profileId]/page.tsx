'use client';

import { useEffect, useState } from 'react';
import { getProfile, type BaziProfile } from '@/lib/baziCalculator';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { format } from 'date-fns';
import { Calendar, Clock, MapPin, User } from 'lucide-react';
import { VictoryPie, VictoryChart, VictoryBar, VictoryTheme, VictoryAxis, VictoryLabel } from 'victory';

interface PageProps {
  params: {
    profileId: string;
  };
}

export default function ProfilePage({ params }: PageProps) {
  const [profile, setProfile] = useState<BaziProfile | null>(null);

  useEffect(() => {
    if (params.profileId) {
      const loadedProfile = getProfile(params.profileId);
      setProfile(loadedProfile || null);
    }
  }, [params.profileId]);

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Profile not found</p>
      </div>
    );
  }

  const { baziChart } = profile;
  if (!baziChart) return null;

  // Prepare data for charts
  const elementData = Object.entries(baziChart.elements).map(([element, value]) => ({
    x: element.charAt(0).toUpperCase() + element.slice(1),
    y: value,
    label: `${element.charAt(0).toUpperCase() + element.slice(1)}: ${value}`,
  }));

  const elementColors = {
    Wood: '#22c55e',
    Fire: '#ef4444',
    Earth: '#f59e0b',
    Metal: '#94a3b8',
    Water: '#3b82f6',
  };

  const pieData = elementData.map(item => ({
    ...item,
    fill: elementColors[item.x as keyof typeof elementColors],
  }));

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Profile Header */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-3xl mb-2">{profile.name}</CardTitle>
                <CardDescription className="space-y-2">
                  <div className="flex items-center gap-4 text-sm">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {format(profile.birthDate, 'PPP')}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {profile.birthTime}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      {profile.birthLocation}
                    </span>
                    <span className="flex items-center gap-1">
                      <User className="w-4 h-4" />
                      {profile.gender.charAt(0).toUpperCase() + profile.gender.slice(1)}
                    </span>
                  </div>
                </CardDescription>
              </div>
              <Badge variant={profile.useTrueSolarTime ? 'default' : 'secondary'}>
                {profile.useTrueSolarTime ? 'True Solar Time' : 'Standard Time'}
              </Badge>
            </div>
          </CardHeader>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="pillars" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="pillars">Four Pillars</TabsTrigger>
            <TabsTrigger value="elements">Elements</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>

          {/* Four Pillars Tab */}
          <TabsContent value="pillars" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Year Pillar */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Year Pillar</CardTitle>
                  <CardDescription>Ancestry & Childhood</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-primary mb-2">
                        {baziChart.yearPillar.heavenlyStem.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.yearPillar.heavenlyStem}
                      </p>
                    </div>
                    <div className="text-center border-t pt-2">
                      <div className="text-4xl font-bold text-secondary mb-2">
                        {baziChart.yearPillar.earthlyBranch.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.yearPillar.earthlyBranch}
                      </p>
                      <Badge variant="outline" className="mt-2">
                        {baziChart.yearPillar.animal}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Month Pillar */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Month Pillar</CardTitle>
                  <CardDescription>Parents & Early Life</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-primary mb-2">
                        {baziChart.monthPillar.heavenlyStem.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.monthPillar.heavenlyStem}
                      </p>
                    </div>
                    <div className="text-center border-t pt-2">
                      <div className="text-4xl font-bold text-secondary mb-2">
                        {baziChart.monthPillar.earthlyBranch.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.monthPillar.earthlyBranch}
                      </p>
                      <Badge variant="outline" className="mt-2">
                        {baziChart.monthPillar.animal}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Day Pillar */}
              <Card className="border-2 border-primary">
                <CardHeader>
                  <CardTitle className="text-lg">Day Pillar</CardTitle>
                  <CardDescription>Self & Spouse</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-primary mb-2">
                        {baziChart.dayPillar.heavenlyStem.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.dayPillar.heavenlyStem}
                      </p>
                      <Badge className="mt-2">Day Master</Badge>
                    </div>
                    <div className="text-center border-t pt-2">
                      <div className="text-4xl font-bold text-secondary mb-2">
                        {baziChart.dayPillar.earthlyBranch.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.dayPillar.earthlyBranch}
                      </p>
                      <Badge variant="outline" className="mt-2">
                        {baziChart.dayPillar.animal}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Hour Pillar */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Hour Pillar</CardTitle>
                  <CardDescription>Children & Later Life</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-primary mb-2">
                        {baziChart.hourPillar.heavenlyStem.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.hourPillar.heavenlyStem}
                      </p>
                    </div>
                    <div className="text-center border-t pt-2">
                      <div className="text-4xl font-bold text-secondary mb-2">
                        {baziChart.hourPillar.earthlyBranch.split(' ')[0]}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {baziChart.hourPillar.earthlyBranch}
                      </p>
                      <Badge variant="outline" className="mt-2">
                        {baziChart.hourPillar.animal}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Elements Tab */}
          <TabsContent value="elements" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Element Distribution</CardTitle>
                  <CardDescription>Your Five Element Balance</CardDescription>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <svg viewBox="0 0 400 400" className="w-full max-w-md">
                    <VictoryPie
                      standalone={false}
                      width={400}
                      height={400}
                      data={pieData}
                      colorScale={pieData.map(d => d.fill)}
                      labels={({ datum }) => `${datum.x}\n${datum.y}`}
                      style={{
                        labels: { fontSize: 16, fill: 'white' },
                      }}
                      innerRadius={80}
                    />
                  </svg>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Element Strength</CardTitle>
                  <CardDescription>Comparative View</CardDescription>
                </CardHeader>
                <CardContent>
                  <svg viewBox="0 0 450 300" className="w-full">
                    <VictoryChart
                      standalone={false}
                      width={450}
                      height={300}
                      domainPadding={30}
                      theme={VictoryTheme.material}
                    >
                      <VictoryAxis />
                      <VictoryAxis dependentAxis />
                      <VictoryBar
                        data={elementData}
                        style={{
                          data: {
                            fill: ({ datum }) => elementColors[datum.x as keyof typeof elementColors],
                          },
                        }}
                      />
                    </VictoryChart>
                  </svg>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Lucky Elements</CardTitle>
                <CardDescription>Elements that can bring balance to your chart</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  {baziChart.luckyElements.map((element) => (
                    <Badge
                      key={element}
                      className="text-lg px-4 py-2"
                      style={{
                        backgroundColor: elementColors[element as keyof typeof elementColors],
                      }}
                    >
                      {element}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Personality Analysis</CardTitle>
                <CardDescription>Based on your Day Master</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-base leading-relaxed">{baziChart.personality}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Life Aspects</CardTitle>
                <CardDescription>Key areas influenced by your Bazi chart</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">Career & Wealth</h4>
                    <p className="text-sm text-muted-foreground">
                      Your {baziChart.dayPillar.element} day master suggests a career path that allows
                      for creativity and personal expression. Lucky elements can guide career choices.
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">Relationships</h4>
                    <p className="text-sm text-muted-foreground">
                      The Day Pillar's earthly branch represents your spouse palace. Understanding this
                      helps in relationship compatibility and harmony.
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">Health & Wellness</h4>
                    <p className="text-sm text-muted-foreground">
                      Element imbalances can indicate areas of health to watch. Strengthening weak
                      elements through lifestyle choices promotes wellbeing.
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">Personal Growth</h4>
                    <p className="text-sm text-muted-foreground">
                      Your chart reveals natural talents and areas for development. Focus on cultivating
                      your lucky elements for optimal growth.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
