import { setOptions, importLibrary } from '@googlemaps/js-api-loader';

/**
 * google-loader.ts — Initialises the Google Maps JS API once at module load time.
 *
 * setOptions() must only be called once per application lifecycle.
 * By calling it here at the top level, it runs exactly once when this module
 * is first imported, regardless of how many components use importLibrary().
 *
 * Usage in components:
 *   import { importLibrary } from '@/lib/google-loader';
 *   const { AutocompleteSuggestion } = await importLibrary('places') as google.maps.PlacesLibrary;
 */
setOptions({
  key: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
  libraries: ['places'],
});

export { importLibrary };
