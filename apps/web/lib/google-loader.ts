import { setOptions, importLibrary } from '@googlemaps/js-api-loader';

declare global {
  var __googleMapsInitialized: boolean;
}

/**
 * google-loader.ts — Initialises the Google Maps JS API once at module load time.
 *
 * setOptions() must only be called once per application lifecycle.
 * The globalThis flag survives Next.js hot-reload module re-evaluations.
 *
 * Usage in components:
 *   import { importLibrary } from '@/lib/google-loader';
 *   const { AutocompleteSuggestion } = await importLibrary('places') as google.maps.PlacesLibrary;
 */
if (typeof window !== 'undefined' && !globalThis.__googleMapsInitialized) {
  globalThis.__googleMapsInitialized = true;
  setOptions({
    key: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
    libraries: ['places'],
  });
}

export { importLibrary };
