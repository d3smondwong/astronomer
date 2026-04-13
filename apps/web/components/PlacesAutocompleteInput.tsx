/// <reference types="google.maps" />
'use client';

import { FC, useEffect, useRef } from 'react';
import { initGoogleMapsAPI } from '@/lib/google-loader';

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
  const inputRef = useRef<HTMLInputElement | null>(null);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);

  useEffect(() => {
    let isMounted = true;

    if (autocompleteRef.current || !inputRef.current) return;

    const init = async () => {
      try {
        if (!initGoogleMapsAPI()) return;
        await google.maps.importLibrary('places');

        if (!isMounted || !inputRef.current) return;

        const autocomplete = new google.maps.places.Autocomplete(inputRef.current, {
          fields: ['geometry', 'formatted_address', 'name'],
          bounds: new google.maps.LatLngBounds(
            { lat: -11.0, lng: 95.0 },  // SW: Southern Indonesia / Western Sumatra
            { lat: 20.0,  lng: 141.0 }, // NE: Northern Thailand / Indonesia-Papua border
          ),
          strictBounds: false,
        });

        autocompleteRef.current = autocomplete;

        autocomplete.addListener('place_changed', () => {
          const place = autocomplete.getPlace();
          if (!place.geometry?.location) return;

          const lat = place.geometry.location.lat();
          const lng = place.geometry.location.lng();
          const address = place.formatted_address ?? place.name ?? '';

          onPlaceSelect(lat, lng, address);
          onChange?.(address);

          // Reflect the chosen address back into the input
          if (inputRef.current) inputRef.current.value = address;
        });

      } catch (err) {
        console.error('Autocomplete init error:', err);
      }
    };

    init();

    return () => {
      isMounted = false;
      if (autocompleteRef.current) {
        google.maps.event.clearInstanceListeners(autocompleteRef.current);
        autocompleteRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Sync placeholder and disabled dynamically
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.placeholder = placeholder;
      inputRef.current.disabled = !!disabled;
    }
  }, [placeholder, disabled]);

  // Sync controlled value from outside (e.g. Form reset / pre-fill)
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.value = value ?? '';
    }
  }, [value]);

  return (
    <input
      ref={inputRef}
      type="text"
      defaultValue={value ?? ''}
      placeholder={placeholder}
      disabled={!!disabled}
      className={`gmp-autocomplete-input ${className ?? ''}`}
      onChange={(e) => {
        onChange?.(e.target.value);
        if (!e.target.value && onClear) onClear();
      }}
    />
  );
};

export default PlacesAutocompleteInput;
