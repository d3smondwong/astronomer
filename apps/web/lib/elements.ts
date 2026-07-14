/**
 * elements.ts — shared Five Elements (五行) presentation constants.
 *
 * Single source for the element → icon / English label / color mappings that
 * the profile cards render. Chinese keys are canonical (see project CLAUDE.md).
 */
import type { ComponentType } from 'react';
import Forest from '@mui/icons-material/Forest';
import LocalFireDepartment from '@mui/icons-material/LocalFireDepartment';
import Terrain from '@mui/icons-material/Terrain';
import StopCircleOutlined from '@mui/icons-material/StopCircleOutlined';
import Waves from '@mui/icons-material/Waves';

export type ElementKey = '木' | '火' | '土' | '金' | '水';

export const ELEMENT_ICONS: Record<string, ComponentType<Record<string, unknown>>> = {
  '木': Forest,
  '火': LocalFireDepartment,
  '土': Terrain,
  '金': StopCircleOutlined,
  '水': Waves,
};

export const ELEMENT_EN: Record<string, string> = {
  '木': 'Wood',
  '火': 'Fire',
  '土': 'Earth',
  '金': 'Metal',
  '水': 'Water',
};

export const ELEMENT_COLOR: Record<string, string> = {
  '木': '#2d6a2d',
  '火': '#b42424',
  '土': '#8a6200',
  '金': '#666666',
  '水': '#1e5a9a',
};
