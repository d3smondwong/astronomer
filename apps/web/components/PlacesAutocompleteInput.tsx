/// <reference types="google.maps" />
'use client';

import React, { useEffect, useRef } from 'react';
import { Input } from 'antd';
import { initGoogleMapsAPI } from '@/lib/google-loader';
import { MapPin } from 'lucide-react';

interface PlacesAutocompleteInputProps {
  value?: string;
  onChange?: (value: string) => void;
  onPlaceSelect: (lat: number, lng: number, formattedAddress: string) => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

// Define fields outside to keep the reference stable
const AUTOCOMPLETE_FIELDS = ['geometry', 'formatted_address', 'name'];

const PlacesAutocompleteInput: React.FC<PlacesAutocompleteInputProps> = ({
  value,
  onChange,
  onPlaceSelect,
  onClear,
  placeholder,
  className,
  disabled,
}) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);

  useEffect(() => {
    // 1. Guard: Don't re-init if we already have an instance
    if (autocompleteRef.current) return;

    const initAutocomplete = async () => {
      try {
        // Initialize Google Maps API globally (first call sets options, subsequent calls are no-ops)
        if (!initGoogleMapsAPI()) return;

        // Import the Places library
        await google.maps.importLibrary('places');

        if (!inputRef.current) return;

        // 2. The Widget handles the "Session Token" automatically
        const instance = new google.maps.places.Autocomplete(inputRef.current, {
          fields: AUTOCOMPLETE_FIELDS,
          types: [],
          locationBias: {
            north: 20.0,   // Northern Thailand/Vietnam
            south: -11.0,  // Southern Indonesia
            east: 141.0,   // Indonesia/Papua border
            west: 95.0,    // Western tip of Sumatra/Thailand
          },
        } as any);

        instance.addListener('place_changed', () => {
          const place = instance.getPlace();
          if (!place.geometry?.location) return;

          const lat = place.geometry.location.lat();
          const lng = place.geometry.location.lng();
          const address = place.formatted_address || place.name || '';

          onPlaceSelect(lat, lng, address);
          onChange?.(address);
        });

        autocompleteRef.current = instance;
      } catch (err) {
        console.error('Google Autocomplete Error:', err);
      }
    };

    initAutocomplete();

    // 3. Cleanup: Remove listeners and orphaned Google dropdown container
    return () => {
      if (autocompleteRef.current) {
        google.maps.event.clearInstanceListeners(autocompleteRef.current);
      }
      // Remove the Google Places dropdown container from the DOM if it's orphaned
      const pacContainers = document.querySelectorAll('.pac-container');
      pacContainers.forEach(container => container.remove());
    };
  }, []); // Empty dependency array ensures this runs ONCE

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange?.(newValue);
    if (!newValue && onClear) {
      onClear();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Prevent Enter key from submitting the form if Google dropdown is open
    if (e.key === 'Enter') {
      const pacContainer = document.querySelector('.pac-container');
      if (pacContainer && window.getComputedStyle(pacContainer).display !== 'none') {
        e.preventDefault();
      }
    }
  };

  return (
    <Input
      ref={(antInputRef) => {
        // Ant Design wraps the DOM input; access it via the nativeElement or input property
        const el = (antInputRef as any)?.input ?? (antInputRef as any)?.nativeElement;
        inputRef.current = el ?? null;
      }}
      value={value}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      className={className}
      disabled={disabled}
      suffix={<MapPin className="w-4 h-4 text-bronze-muted/40" />}
      autoComplete="off"
    />
  );
};

export default PlacesAutocompleteInput;
