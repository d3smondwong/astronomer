'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { getProfiles, type BaziProfile } from '@/lib/baziCalculator';
import { Heart, Zap, ShieldAlert } from 'lucide-react';
import { VictoryChart, VictoryBar, VictoryTheme, VictoryAxis, VictoryGroup } from 'victory';

export default function CompatibilityPage() {
  const [profiles, setProfiles] = useState<BaziProfile[]>([]);
  const [profile1, setProfile1] = useState<string>('');
  const [profile2, setProfile2] = useState<string>('');

  useEffect(() => {
    const loadedProfiles = getProfiles();
    setProfiles(loadedProfiles);
  }, []);

  const selectedProfile1 = profiles.find(p => p.id === profile1);
  const selectedProfile2 = profiles.find(p => p.id === profile2);

  const calculateCompatibility = () => {
    if (!selectedProfile1?.baziChart || !selectedProfile2?.baziChart) return null;

    const elements1 = selectedProfile1.baziChart.elements;
    const elements2 = selectedProfile2.baziChart.elements;

    // Calculate element harmony (simplified)
    let harmony = 0;
    let total = 0;

    Object.keys(elements1).forEach((element) => {
      const val1 = elements1[element as keyof typeof elements1];
      const val2 = elements2[element as keyof typeof elements2];
      harmony += Math.min(val1, val2);
      total += Math.max(val1, val2);
    });

    const compatibilityScore = Math.round((harmony / total) * 100);

    return {
      score: compatibilityScore,
      rating: compatibilityScore >= 75 ? 'Excellent' : compatibilityScore >= 60 ? 'Good' : compatibilityScore >= 45 ? 'Fair' : 'Challenging',
      description: getCompatibilityDescription(compatibilityScore),
    };
  };

  const getCompatibilityDescription = (score: number) => {
    if (score >= 75) {
      return 'Your charts show excellent harmony! Your elements complement each other beautifully, creating a balanced and supportive relationship.';
    } else if (score >= 60) {
      return 'There is good compatibility between your charts. While there are some differences, they can create growth opportunities when approached with understanding.';
    } else if (score >= 45) {
      return 'Your charts show moderate compatibility. Success requires conscious effort to understand and respect each other\'s elemental natures.';
    } else {
      return 'Your charts present challenges in compatibility. This relationship may require extra patience and compromise, but can lead to significant personal growth.';
    }
  };

  const compatibility = calculateCompatibility();

  const chartData = selectedProfile1?.baziChart && selectedProfile2?.baziChart
    ? Object.keys(selectedProfile1.baziChart.elements).map((element) => ({
        element: element.charAt(0).toUpperCase() + element.slice(1),
        profile1: selectedProfile1.baziChart!.elements[element as keyof typeof selectedProfile1.baziChart.elements],
        profile2: selectedProfile2.baziChart!.elements[element as keyof typeof selectedProfile2.baziChart.elements],
      }))
    : [];

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Compatibility Analysis</h1>
          <p className="text-muted-foreground">
            Compare two Bazi charts to understand relationship dynamics and harmony
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Select Profiles to Compare</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">First Person</label>
                <Select value={profile1} onValueChange={setProfile1}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a profile" />
                  </SelectTrigger>
                  <SelectContent>
                    {profiles.map((p) => (
                      <SelectItem key={p.id} value={p.id} disabled={p.id === profile2}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Second Person</label>
                <Select value={profile2} onValueChange={setProfile2}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a profile" />
                  </SelectTrigger>
                  <SelectContent>
                    {profiles.map((p) => (
                      <SelectItem key={p.id} value={p.id} disabled={p.id === profile1}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {compatibility && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Compatibility Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center gap-8">
                  <div className="text-center">
                    <div className="text-6xl font-bold text-primary mb-2">
                      {compatibility.score}%
                    </div>
                    <Badge
                      variant={
                        compatibility.rating === 'Excellent'
                          ? 'default'
                          : compatibility.rating === 'Good'
                          ? 'secondary'
                          : 'outline'
                      }
                      className="text-lg px-4 py-1"
                    >
                      {compatibility.rating}
                    </Badge>
                  </div>
                </div>
                <p className="text-center text-muted-foreground mt-6 max-w-2xl mx-auto">
                  {compatibility.description}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Element Comparison</CardTitle>
                <CardDescription>
                  Comparing the five elements between {selectedProfile1?.name} and {selectedProfile2?.name}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <svg viewBox="0 0 600 400" className="w-full max-w-3xl">
                    <VictoryChart
                      standalone={false}
                      width={600}
                      height={400}
                      domainPadding={{ x: 50 }}
                      theme={VictoryTheme.material}
                    >
                      <VictoryAxis />
                      <VictoryAxis dependentAxis />
                      <VictoryGroup offset={20} colorScale={['#3b82f6', '#f59e0b']}>
                        <VictoryBar
                          data={chartData.map(d => ({ x: d.element, y: d.profile1 }))}
                        />
                        <VictoryBar
                          data={chartData.map(d => ({ x: d.element, y: d.profile2 }))}
                        />
                      </VictoryGroup>
                    </VictoryChart>
                  </svg>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-[#3b82f6] rounded"></div>
                    <span className="text-sm">{selectedProfile1?.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-[#f59e0b] rounded"></div>
                    <span className="text-sm">{selectedProfile2?.name}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid md:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="w-5 h-5 text-red-500" />
                    Strengths
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <span className="text-green-500 mt-1">✓</span>
                      <span>Shared elemental balance creates mutual understanding</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-500 mt-1">✓</span>
                      <span>Complementary energies support personal growth</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-500 mt-1">✓</span>
                      <span>Natural harmony in communication styles</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-500" />
                    Opportunities
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-500 mt-1">→</span>
                      <span>Learning from each other's strengths</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-500 mt-1">→</span>
                      <span>Balancing contrasting elements together</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-500 mt-1">→</span>
                      <span>Growing through differences in perspective</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-orange-500" />
                    Considerations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <span className="text-orange-500 mt-1">!</span>
                      <span>Be mindful of element clashes during conflicts</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-orange-500 mt-1">!</span>
                      <span>Respect different approaches to life challenges</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-orange-500 mt-1">!</span>
                      <span>Practice patience during imbalanced periods</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </>
        )}

        {!compatibility && profiles.length < 2 && (
          <Card>
            <CardContent className="py-12">
              <p className="text-center text-muted-foreground">
                You need at least 2 profiles to perform compatibility analysis.
                <br />
                Create more profiles from the home page.
              </p>
            </CardContent>
          </Card>
        )}

        {!compatibility && profiles.length >= 2 && (
          <Card>
            <CardContent className="py-12">
              <p className="text-center text-muted-foreground">
                Select two profiles above to see their compatibility analysis
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
