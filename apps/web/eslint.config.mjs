import next from 'eslint-config-next/core-web-vitals';

// eslint-config-next's flat config already supplies the TS parser, the
// **/*.{ts,tsx} file globs, and the .next/out/build ignores.
const config = [...next];

export default config;
