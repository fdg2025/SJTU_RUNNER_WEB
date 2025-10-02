import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000; // Earth's radius in meters
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export function getCurrentEpochMs(): number {
  return Date.now();
}

export const TRACK_POINT_DECIMAL_PLACES = 6;

export interface TrackPoint {
  latLng: {
    latitude: number;
    longitude: number;
  };
  location: string;
  step: number;
  locatetime?: number;
}

export interface Track {
  counts: number;
  distance: number;
  duration: number;
  points: TrackPoint[];
  status: string;
  trid: string;
  tstate: string;
  stime: number;
  etime: number;
}

export interface RunningConfig {
  COOKIE: string;
  USER_ID: string;
  START_LATITUDE: number;
  START_LONGITUDE: number;
  END_LATITUDE: number;
  END_LONGITUDE: number;
  RUNNING_SPEED_MPS: number;
  INTERVAL_SECONDS: number;
  START_TIME_EPOCH_MS?: number | null;
  HOST: string;
  UID_URL: string;
  MY_DATA_URL: string;
  POINT_RULE_URL: string;
  UPLOAD_URL: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ProgressCallback {
  (current: number, total: number, message: string): void;
}

export interface LogCallback {
  (message: string, level?: 'info' | 'warning' | 'error' | 'success'): void;
}
