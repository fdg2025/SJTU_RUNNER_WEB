import { NextRequest, NextResponse } from 'next/server';
import { getAuthorizationTokenAndRules, uploadRunningData, SportsUploaderError } from '@/lib/api-client';
import { generateRunningDataPayload } from '@/lib/data-generator';
import { RunningConfig, LogCallback, ProgressCallback } from '@/lib/utils';

export async function POST(request: NextRequest) {
  try {
    const config: RunningConfig = await request.json();
    
    // Validate required fields
    if (!config.COOKIE || !config.USER_ID) {
      return NextResponse.json({
        success: false,
        error: 'Cookie 和用户ID不能为空'
      }, { status: 400 });
    }

    const logs: Array<{message: string, level: string, timestamp: number}> = [];
    const logCallback: LogCallback = (message, level = 'info') => {
      logs.push({ message, level, timestamp: Date.now() });
      console.log(`[${level.toUpperCase()}] ${message}`);
    };

    logCallback('--- Starting Sports Upload Process ---');

    // Step 1: Get Authorization Token and Point Rules
    logCallback('Step 1/3: Getting Authorization Token and Point Rules...');
    
    let authTokenForUpload: string;
    let pointRulesData: any;
    let requiredSignpoints: any[] = [];

    try {
      [authTokenForUpload, pointRulesData] = await getAuthorizationTokenAndRules(config, logCallback);
      requiredSignpoints = (pointRulesData.points || []).filter((p: any) => p.isneed === 'Y');
      logCallback(`Required Signpoints for rule: ${JSON.stringify(requiredSignpoints)}`);

      const rulesMeta = pointRulesData.rules || {};
      if (rulesMeta.spmin && rulesMeta.spmax) {
        const minSpSPerKm = rulesMeta.spmin;
        const maxSpSPerKm = rulesMeta.spmax;
        const minSpeedMps = maxSpSPerKm > 0 ? 1000 / maxSpSPerKm : 0;
        const maxSpeedMps = minSpSPerKm > 0 ? 1000 / minSpSPerKm : 0;

        if (config.RUNNING_SPEED_MPS < minSpeedMps) {
          logCallback(
            `Adjusting running speed from ${config.RUNNING_SPEED_MPS.toFixed(2)} m/s to minimum allowed ${minSpeedMps.toFixed(2)} m/s`,
            'warning'
          );
          config.RUNNING_SPEED_MPS = minSpeedMps;
        } else if (config.RUNNING_SPEED_MPS > maxSpeedMps) {
          logCallback(
            `Adjusting running speed from ${config.RUNNING_SPEED_MPS.toFixed(2)} m/s to maximum allowed ${maxSpeedMps.toFixed(2)} m/s`,
            'warning'
          );
          config.RUNNING_SPEED_MPS = maxSpeedMps;
        }

        logCallback(
          `Pace rule: ${(minSpSPerKm / 60).toFixed(0)}'-${(maxSpSPerKm / 60).toFixed(0)}' min/km. Using adjusted speed: ${config.RUNNING_SPEED_MPS.toFixed(2)} m/s`
        );
      } else {
        logCallback('Warning: Could not retrieve pace rules from point-rule response. Using default speed.', 'warning');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      logCallback(`Fatal: Failed during authentication or rule retrieval: ${errorMessage}`, 'error');
      return NextResponse.json({
        success: false,
        error: errorMessage,
        logs
      }, { status: 500 });
    }

    // Step 2: Generate Running Data
    logCallback('Step 2/3: Generating Running Data...');
    
    let runningDataPayload: any[];
    let totalDist: number;
    let totalDur: number;

    try {
      [runningDataPayload, totalDist, totalDur] = generateRunningDataPayload(
        config,
        requiredSignpoints,
        pointRulesData,
        logCallback
      );

      logCallback(`Generated ${runningDataPayload[0].tracks.length} track segments.`);
      logCallback(`Total simulated distance: ${totalDist.toFixed(2)} meters`);
      logCallback(`Total simulated duration: ${totalDur} seconds`);
      logCallback(`Simulated average pace: ${runningDataPayload[0].spavg} min/km`);

      if (runningDataPayload && runningDataPayload[0].tracks.length > 0) {
        const firstPointLocatetimeMs = runningDataPayload[0].tracks[0].points[0].locatetime;
        const firstPointDatetime = new Date(firstPointLocatetimeMs).toLocaleString('zh-CN');
        logCallback(
          `Actual start time of run (from first point): ${firstPointDatetime} (Epoch MS: ${firstPointLocatetimeMs})`
        );
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      logCallback(`Failed to generate running data: ${errorMessage}`, 'error');
      return NextResponse.json({
        success: false,
        error: errorMessage,
        logs
      }, { status: 500 });
    }

    // Step 3: Upload Running Data
    if (runningDataPayload && authTokenForUpload) {
      logCallback('Step 3/3: Sending Running Data...');
      
      try {
        // If using current time, simulate waiting for run completion
        if (config.START_TIME_EPOCH_MS === null || config.START_TIME_EPOCH_MS === undefined) {
          logCallback(`模拟等待跑步完成 ${totalDur} 秒...`);
          // In a real scenario, you might want to implement this differently
          // For now, we'll just add a short delay
          await new Promise(resolve => setTimeout(resolve, 3000));
        } else {
          logCallback('设置了过去的跑步时间，直接准备上传，短暂停顿 3 秒...');
          await new Promise(resolve => setTimeout(resolve, 3000));
        }

        let rt = 0;
        const maxRt = 3;
        
        while (rt < maxRt) {
          logCallback(`Attempting to upload running data (Attempt ${rt + 1}/${maxRt})...`);

          const response = await uploadRunningData(
            config,
            authTokenForUpload,
            runningDataPayload,
            logCallback
          );

          if (response?.code === 0 && response?.data) {
            logCallback('SUCCESS: Running data uploaded successfully with full data response!');
            return NextResponse.json({
              success: true,
              message: '上传成功！',
              data: response,
              logs
            });
          } else if (response?.code === 0) {
            logCallback(
              `WARNING: Uploaded, but response code is 0 with empty data. Server might still process it. Retrying in 3 seconds... (Attempt ${rt + 1}/${maxRt})`,
              'warning'
            );
            rt++;
            if (rt < maxRt) {
              await new Promise(resolve => setTimeout(resolve, 3000));
            }
          } else {
            logCallback(
              `ERROR: Upload returned non-success code (${response?.code || 'N/A'}). No further retries for this attempt.`,
              'error'
            );
            return NextResponse.json({
              success: false,
              error: `上传失败，响应代码: ${response?.code || 'N/A'}`,
              logs
            }, { status: 500 });
          }
        }

        logCallback('ERROR: Upload failed or returned error code after retries.', 'error');
        return NextResponse.json({
          success: false,
          error: '上传失败或返回错误代码 (达到最大重试次数)',
          logs
        }, { status: 500 });

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        logCallback(`Failed to send running data: ${errorMessage}`, 'error');
        return NextResponse.json({
          success: false,
          error: errorMessage,
          logs
        }, { status: 500 });
      }
    } else {
      logCallback('Skipping data upload due to missing generated data or authorization token.', 'error');
      return NextResponse.json({
        success: false,
        error: '数据生成或认证失败，上传被跳过。',
        logs
      }, { status: 500 });
    }

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
