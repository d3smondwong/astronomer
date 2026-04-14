import { setOptions } from '@googlemaps/js-api-loader';

// Initialize Google Maps API once, globally
export function initGoogleMapsAPI() {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  if (!apiKey || apiKey === 'your_google_maps_api_key_here') {
    console.warn('Google Maps API key not configured');
    return false;
  }

  setOptions({
    key: apiKey,
    libraries: ['places'],
  });

  return true;
}
