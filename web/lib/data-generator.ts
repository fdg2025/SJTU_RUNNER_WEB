import { v4 as uuidv4 } from 'uuid';
import { haversineDistance, getCurrentEpochMs, TRACK_POINT_DECIMAL_PLACES, TrackPoint, Track, RunningConfig, LogCallback } from './utils';
import { SportsUploaderError } from './api-client';

export function interpolatePoints(
  startLat: number,
  startLon: number,
  endLat: number,
  endLon: number,
  speedMps: number,
  intervalSeconds: number
): [TrackPoint[], number, number] {
  const points: TrackPoint[] = [];

  const startLatCalc = parseFloat(startLat.toFixed(14));
  const startLonCalc = parseFloat(startLon.toFixed(14));
  const endLatCalc = parseFloat(endLat.toFixed(14));
  const endLonCalc = parseFloat(endLon.toFixed(14));

  const startLatRad = (startLatCalc * Math.PI) / 180;
  const startLonRad = (startLonCalc * Math.PI) / 180;
  const endLatRad = (endLatCalc * Math.PI) / 180;
  const endLonRad = (endLonCalc * Math.PI) / 180;

  const segmentDistance = haversineDistance(startLatCalc, startLonCalc, endLatCalc, endLonCalc);
  const segmentDurationSeconds = segmentDistance / speedMps;

  let numSteps = Math.ceil(segmentDurationSeconds / intervalSeconds);
  if (numSteps <= 1 && segmentDistance > 0) {
    numSteps = 1;
  } else if (segmentDistance === 0) {
    numSteps = 0;
  }

  if (numSteps === 0) {
    const formattedLat = startLatCalc.toFixed(TRACK_POINT_DECIMAL_PLACES);
    const formattedLon = startLonCalc.toFixed(TRACK_POINT_DECIMAL_PLACES);
    points.push({
      latLng: { latitude: parseFloat(formattedLat), longitude: parseFloat(formattedLon) },
      location: `${formattedLon},${formattedLat}`,
      step: 0
    });
    return [points, segmentDistance, Math.ceil(segmentDurationSeconds)];
  }

  for (let i = 0; i <= numSteps; i++) {
    const fraction = i / numSteps;

    const interpLatRad = startLatRad + fraction * (endLatRad - startLatRad);
    const interpLonRad = startLonRad + fraction * (endLonRad - startLonRad);

    const interpLat = (interpLatRad * 180) / Math.PI;
    const interpLon = (interpLonRad * 180) / Math.PI;

    const formattedLat = interpLat.toFixed(TRACK_POINT_DECIMAL_PLACES);
    const formattedLon = interpLon.toFixed(TRACK_POINT_DECIMAL_PLACES);

    points.push({
      latLng: { latitude: parseFloat(formattedLat), longitude: parseFloat(formattedLon) },
      location: `${formattedLon},${formattedLat}`,
      step: 0
    });
  }

  const finalEndLatFormatted = parseFloat(endLatCalc.toFixed(TRACK_POINT_DECIMAL_PLACES));
  const finalEndLonFormatted = parseFloat(endLonCalc.toFixed(TRACK_POINT_DECIMAL_PLACES));

  if (Math.abs(points[points.length - 1].latLng.latitude - finalEndLatFormatted) > 1e-10 ||
      Math.abs(points[points.length - 1].latLng.longitude - finalEndLonFormatted) > 1e-10) {
    points[points.length - 1] = {
      latLng: { latitude: finalEndLatFormatted, longitude: finalEndLonFormatted },
      location: `${finalEndLonFormatted},${finalEndLatFormatted}`,
      step: 0
    };
  }

  return [points, segmentDistance, Math.ceil(segmentDurationSeconds)];
}

export function splitTrackIntoSegments(
  allPointsWithTime: TrackPoint[],
  totalDurationSec: number,
  minSegmentPoints: number = 5
): Track[] {
  const tracks: Track[] = [];

  const statusMap = {
    "normal": "0",
    "stop": "0",
    "invalid": "2",
  };

  let currentStartPointIdx = 0;

  if (!allPointsWithTime.length) {
    return tracks;
  }

  while (currentStartPointIdx < allPointsWithTime.length) {
    const remainingPoints = allPointsWithTime.length - currentStartPointIdx;
    let segmentLength: number;
    
    if (remainingPoints <= minSegmentPoints) {
      segmentLength = remainingPoints;
    } else {
      segmentLength = Math.floor(Math.random() * (Math.max(minSegmentPoints, Math.floor(remainingPoints / 3)) - minSegmentPoints + 1)) + minSegmentPoints;
      if (segmentLength === 1 && remainingPoints > 1) {
        segmentLength = minSegmentPoints;
      }
    }

    const segmentPoints = allPointsWithTime.slice(currentStartPointIdx, currentStartPointIdx + segmentLength);
    currentStartPointIdx += segmentLength;

    if (!segmentPoints.length) {
      continue;
    }

    const randVal = Math.random();
    let segmentStatus: string;
    if (randVal < 0.8) {
      segmentStatus = "normal";
    } else if (randVal < 0.9) {
      segmentStatus = "invalid";
    } else {
      segmentStatus = "stop";
    }

    const segmentTstate = statusMap[segmentStatus as keyof typeof statusMap] || "0";

    let segmentDistance = 0;
    if (segmentPoints.length > 1) {
      for (let i = 0; i < segmentPoints.length - 1; i++) {
        const p1 = segmentPoints[i].latLng;
        const p2 = segmentPoints[i + 1].latLng;
        segmentDistance += haversineDistance(p1.latitude, p1.longitude, p2.latitude, p2.longitude);
      }
    }

    const segmentStartTimeMs = segmentPoints[0].locatetime!;
    const segmentEndTimeMs = segmentPoints[segmentPoints.length - 1].locatetime!;
    const segmentDurationSec = Math.ceil((segmentEndTimeMs - segmentStartTimeMs) / 1000);

    tracks.push({
      counts: segmentPoints.length,
      distance: segmentDistance,
      duration: segmentDurationSec,
      points: segmentPoints,
      status: segmentStatus,
      trid: uuidv4(),
      tstate: segmentTstate,
      stime: Math.floor(segmentStartTimeMs / 1000),
      etime: Math.floor(segmentEndTimeMs / 1000)
    });
  }

  return tracks;
}

export function generateRunningDataPayload(
  config: RunningConfig,
  requiredSignpoints: any[],
  pointRulesData: any,
  logCb?: LogCallback
): [any[], number, number] {
  const allPathSegments: Array<{latitude: number, longitude: number}> = [];
  allPathSegments.push({ latitude: config.START_LATITUDE, longitude: config.START_LONGITUDE });

  const extractedSignpointsCoords: Array<{latitude: number, longitude: number}> = [];
  for (const sp of requiredSignpoints) {
    const [lonStr, latStr] = sp.location.split(',');
    const formattedSpLat = parseFloat(parseFloat(latStr).toFixed(TRACK_POINT_DECIMAL_PLACES));
    const formattedSpLon = parseFloat(parseFloat(lonStr).toFixed(TRACK_POINT_DECIMAL_PLACES));
    extractedSignpointsCoords.push({ latitude: formattedSpLat, longitude: formattedSpLon });
  }

  extractedSignpointsCoords.sort((a, b) => {
    const distA = haversineDistance(config.START_LATITUDE, config.START_LONGITUDE, a.latitude, a.longitude);
    const distB = haversineDistance(config.START_LATITUDE, config.START_LONGITUDE, b.latitude, b.longitude);
    return distA - distB;
  });
  
  allPathSegments.push(...extractedSignpointsCoords);
  allPathSegments.push({ latitude: config.END_LATITUDE, longitude: config.END_LONGITUDE });

  const fullInterpolatedPointsWithTime: TrackPoint[] = [];
  let totalOverallDistance = 0;

  let currentLocatetimeMs = config.START_TIME_EPOCH_MS ?? getCurrentEpochMs();

  for (let i = 0; i < allPathSegments.length - 1; i++) {
    const p1Coord = allPathSegments[i];
    const p2Coord = allPathSegments[i + 1];

    const [segmentInterpolatedPoints, segmentDistance] = interpolatePoints(
      p1Coord.latitude, p1Coord.longitude, p2Coord.latitude, p2Coord.longitude,
      config.RUNNING_SPEED_MPS, config.INTERVAL_SECONDS
    );

    if (fullInterpolatedPointsWithTime.length && segmentInterpolatedPoints.length) {
      const lastPointInFull = fullInterpolatedPointsWithTime[fullInterpolatedPointsWithTime.length - 1].latLng;
      const firstPointInSegment = segmentInterpolatedPoints[0].latLng;

      if (Math.abs(lastPointInFull.latitude - firstPointInSegment.latitude) < 1e-10 &&
          Math.abs(lastPointInFull.longitude - firstPointInSegment.longitude) < 1e-10) {
        segmentInterpolatedPoints.shift();
      }
    }

    for (const point of segmentInterpolatedPoints) {
      point.locatetime = currentLocatetimeMs;
      fullInterpolatedPointsWithTime.push(point);
      currentLocatetimeMs += config.INTERVAL_SECONDS * 1000;
    }

    totalOverallDistance += segmentDistance;
  }

  let actualTotalDurationSec = 0;
  if (fullInterpolatedPointsWithTime.length) {
    const firstPointTimeMs = fullInterpolatedPointsWithTime[0].locatetime!;
    const lastPointTimeMs = fullInterpolatedPointsWithTime[fullInterpolatedPointsWithTime.length - 1].locatetime!;
    actualTotalDurationSec = Math.ceil((lastPointTimeMs - firstPointTimeMs + config.INTERVAL_SECONDS * 1000) / 1000);
  }

  const tracksList = splitTrackIntoSegments(fullInterpolatedPointsWithTime, actualTotalDurationSec);
  const actualTotalDistance = tracksList.reduce((sum, t) => sum + t.distance, 0);

  let runId = pointRulesData?.rules?.id || 6;
  if (runId === 6) {
    runId = 9;
  }

  let spAvg = 0;
  if (actualTotalDistance > 0 && actualTotalDurationSec > 0) {
    spAvg = actualTotalDurationSec / (actualTotalDistance / 1000) / 60;
    spAvg = Math.round(spAvg);
  }

  const rulesMeta = pointRulesData?.rules || {};
  const minSpSPerKm = rulesMeta.spmin || 180;
  const maxSpSPerKm = rulesMeta.spmax || 540;

  const spAvgSPerKm = spAvg * 60;

  if (actualTotalDistance > 0) {
    if (spAvgSPerKm < minSpSPerKm) {
      logCb?.(`Warning: Calculated pace ${spAvg} min/km (${spAvgSPerKm.toFixed(0)} s/km) is faster than ${(minSpSPerKm / 60).toFixed(0)} min/km (${minSpSPerKm.toFixed(0)} s/km). Adjusting to minimum allowed pace.`, 'warning');
      spAvg = Math.ceil(minSpSPerKm / 60);
    } else if (spAvgSPerKm > maxSpSPerKm) {
      logCb?.(`Warning: Calculated pace ${spAvg} min/km (${spAvgSPerKm.toFixed(0)} s/km) is slower than ${(maxSpSPerKm / 60).toFixed(0)} min/km (${maxSpSPerKm.toFixed(0)} s/km). Adjusting to maximum allowed pace.`, 'warning');
      spAvg = Math.floor(maxSpSPerKm / 60);
    }
  }

  const requestBody = [
    {
      fravg: 0,
      id: runId,
      sid: uuidv4(),
      signpoints: [],
      spavg: spAvg,
      state: "0",
      tracks: tracksList,
      userId: config.USER_ID
    }
  ];

  return [requestBody, actualTotalDistance, actualTotalDurationSec];
}
