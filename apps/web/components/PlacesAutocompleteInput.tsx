/// <reference types="google.maps" />
'use client';

import { FC, useEffect, useRef, useState } from 'react';
import { AutoComplete, Input } from 'antd';
import type { DefaultOptionType } from 'antd/es/select';
import { importLibrary } from '@/lib/google-loader';

interface PlacesAutocompleteInputProps {
  value?: string;
  onChange?: (value: string) => void;
  onPlaceSelect: (lat: number, lng: number, formattedAddress: string) => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

const PlacesAutocompleteInput: FC<PlacesAutocompleteInputProps> = ({
  value,
  onChange,
  onPlaceSelect,
  onClear,
  placeholder = 'City, Country',
  className,
  disabled,
}) => {
  const [inputValue, setInputValue] = useState(value ?? '');
  const [options, setOptions] = useState<DefaultOptionType[]>([]);
  const sessionTokenRef = useRef<google.maps.places.AutocompleteSessionToken | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Initialise session token on mount
  useEffect(() => {
    importLibrary('places').then((lib) => {
      const { AutocompleteSessionToken } = lib as google.maps.PlacesLibrary;
      sessionTokenRef.current = new AutocompleteSessionToken();
    });
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  // Sync controlled value from outside (form reset / pre-fill)
  useEffect(() => {
    setInputValue(value ?? '');
  }, [value]);

  const handleSearch = (text: string) => {
    setInputValue(text);
    onChange?.(text);

    if (!text) {
      setOptions([]);
      onClear?.();
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      const { AutocompleteSuggestion } = await importLibrary('places') as google.maps.PlacesLibrary;
      try {
        const { suggestions } = await AutocompleteSuggestion.fetchAutocompleteSuggestions({
          input: text,
          sessionToken: sessionTokenRef.current!,
          locationBias: {
            west:  95.0,   // SW longitude — Western Sumatra
            south: -11.0,  // SW latitude  — Southern Indonesia
            east:  141.0,  // NE longitude — Indonesia-Papua border
            north: 20.0,   // NE latitude  — Northern Thailand
          },
        });

        setOptions(suggestions.map(s => ({
          value: s.placePrediction.text.text,
          label: (
            <div className="flex flex-col">
              <span className="font-serif text-bronze-muted">{s.placePrediction.mainText.text}</span>
              <span className="text-xs opacity-50">{s.placePrediction.secondaryText?.text}</span>
            </div>
          ),
          suggestion: s,
        })));
      } catch (err) {
        console.error('Google Places error:', err);
      }
    }, 300);
  };

  const handleSelect = async (_: string, option: DefaultOptionType) => {
    const place = (option as DefaultOptionType & { suggestion: google.maps.places.AutocompleteSuggestion }).suggestion.placePrediction.toPlace();
    await place.fetchFields({ fields: ['location', 'formattedAddress', 'displayName'] });

    const lat     = place.location!.lat();
    const lng     = place.location!.lng();
    const address = place.formattedAddress ?? place.displayName ?? '';

    setInputValue(address);
    onChange?.(address);
    onPlaceSelect(lat, lng, address);

    // Reset session token — one token covers all predictions + one fetchFields (billing requirement)
    const { AutocompleteSessionToken } = await importLibrary('places') as google.maps.PlacesLibrary;
    sessionTokenRef.current = new AutocompleteSessionToken();
  };

  return (
    <AutoComplete
      value={inputValue}
      options={options}
      onSearch={handleSearch}
      onSelect={handleSelect}
      style={{ width: '100%' }}
      disabled={disabled}
    >
      <Input
        placeholder={placeholder}
        className={`bazi-input ${className ?? ''}`}
        allowClear
        onClear={onClear}
      />
    </AutoComplete>
  );
};

export default PlacesAutocompleteInput;
