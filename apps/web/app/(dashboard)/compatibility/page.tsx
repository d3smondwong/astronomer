'use client';

import { useState, useEffect } from 'react';
import { Card, Select, Tag } from 'antd';
import type { BaziProfile } from '@/lib/baziOrchestrator';
import { getProfiles } from '@/lib/baziStorage';
import { Heart, Zap } from 'lucide-react';
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
      return 'Excellent compatibility! These two profiles have harmonious element distributions and complement each other well.';
    } else if (score >= 60) {
      return 'Good compatibility. The profiles show positive element interactions with some areas of natural harmony.';
    } else if (score >= 45) {
      return 'Fair compatibility. There are some complementary elements, but also areas that may require understanding and compromise.';
    } else {
      return 'Challenging compatibility. The profiles have very different element distributions and may require significant effort to harmonize.';
    }
  };

  const compatibility = calculateCompatibility();

  const profileOptions = profiles.map(p => ({
    label: p.name,
    value: p.id,
  }));

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold mb-2 font-serif text-gold-deep">Bazi Compatibility</h1>
        <p className="font-serif italic text-bronze-muted/70">Compare the compatibility between two Bazi charts</p>
      </div>

      <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium font-serif text-bronze-muted/70">First Person</label>
              <Select
                value={profile1 || undefined}
                onChange={setProfile1}
                placeholder="Select a profile"
                options={profileOptions}
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium font-serif text-bronze-muted/70">Second Person</label>
              <Select
                value={profile2 || undefined}
                onChange={setProfile2}
                placeholder="Select a profile"
                options={profileOptions.filter(p => p.value !== profile1)}
              />
            </div>
          </div>
        </div>
      </Card>

      {compatibility && selectedProfile1 && selectedProfile2 && (
        <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <div>
                <h2 className="text-2xl font-semibold mb-2 font-serif text-gold-deep">
                  {selectedProfile1.name} & {selectedProfile2.name}
                </h2>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div className="p-4 bg-gold-deep/5 border border-gold-deep/10 rounded-lg">
                  <div className="text-4xl font-bold text-gold-deep mb-2">{compatibility.score}%</div>
                  <Tag color={
                    compatibility.score >= 75 ? 'green' :
                    compatibility.score >= 60 ? 'blue' :
                    compatibility.score >= 45 ? 'orange' :
                    'red'
                  }>
                    {compatibility.rating}
                  </Tag>
                </div>

                <div className="p-4 bg-gold-deep/5 border border-gold-deep/10 rounded-lg">
                  <div className="text-center">
                    <Heart className="w-8 h-8 text-gold-deep mx-auto mb-2" />
                    <p className="font-semibold text-bronze-muted">Emotional Connection</p>
                    <p className="text-sm text-bronze-muted/70">Based on element balance</p>
                  </div>
                </div>

                <div className="p-4 bg-gold-deep/5 border border-gold-deep/10 rounded-lg">
                  <div className="text-center">
                    <Zap className="w-8 h-8 text-gold-deep mx-auto mb-2" />
                    <p className="font-semibold text-bronze-muted">Energy Alignment</p>
                    <p className="text-sm text-bronze-muted/70">Element harmony</p>
                  </div>
                </div>
              </div>

              <div className="pt-4">
                <p className="text-base leading-relaxed text-gray-700">
                  {compatibility.description}
                </p>
              </div>
            </div>

            {selectedProfile1.baziChart && selectedProfile2.baziChart && (
              <div className="border-t border-gold-deep/10 pt-6">
                <h3 className="text-lg font-semibold mb-4 font-serif text-gold-deep">Element Comparison</h3>
                <svg viewBox="0 0 600 400" className="w-full">
                  <VictoryChart
                    standalone={false}
                    width={600}
                    height={400}
                    domainPadding={40}
                    theme={VictoryTheme.material}
                  >
                    <VictoryAxis />
                    <VictoryAxis dependentAxis />
                    <VictoryGroup offset={15}>
                      <VictoryBar
                        data={Object.entries(selectedProfile1.baziChart.elements).map(([k, v]) => ({
                          x: k,
                          y: v,
                        }))}
                        style={{ data: { fill: '#1f77b4' } }}
                      />
                      <VictoryBar
                        data={Object.entries(selectedProfile2.baziChart.elements).map(([k, v]) => ({
                          x: k,
                          y: v,
                        }))}
                        style={{ data: { fill: '#ff7f0e' } }}
                      />
                    </VictoryGroup>
                  </VictoryChart>
                </svg>
              </div>
            )}
          </div>
        </Card>
      )}

      {!compatibility && (profile1 || profile2) && (
        <Card style={{ borderColor: 'rgba(115, 92, 0, 0.1)' }}>
          <p className="text-center text-bronze-muted/70">
            Please select both profiles to view compatibility analysis
          </p>
        </Card>
      )}
    </div>
  );
}
