function testResults = testSolarGimbal()
% TESTSOLARGIMBAL Automated unit tests for Solar Gimbal MATLAB reference model.
%
% Tests:
%   1. Normal tracking calculation (135/42 vs 90/30)
%   2. Azimuth 360-degree wrap-around (Sun 5 vs Panel 355 => +10 deg)
%   3. Reverse wrap-around (Sun 355 vs Panel 5 => -10 deg)
%   4. Zero error / Hold condition
%   5. Elevation downward movement
%   6. Boundary elevations (-90 and +90 deg)
%   7. Input validation: Rejection of out-of-range azimuth
%   8. Input validation: Rejection of out-of-range elevation & non-positive dt
%   9. Optional Kp proportional gain scaling
%  10. FPGA preparation packet format & determinism

    mPath = fileparts(fileparts(mfilename('fullpath')));
    addpath(fullfile(mPath, 'solarGimbal'));
    addpath(fullfile(mPath, 'integration'));

    fprintf('========================================================\n');
    fprintf('         RUNNING SOLAR GIMBAL UNIT TEST SUITE           \n');
    fprintf('========================================================\n\n');

    tests = { ...
        @test_01_NormalTracking, ...
        @test_02_AzimuthWrapAroundPositive, ...
        @test_03_AzimuthWrapAroundNegative, ...
        @test_04_ZeroErrorHold, ...
        @test_05_ElevationDownward, ...
        @test_06_BoundaryElevations, ...
        @test_07_InvalidAzimuthRejection, ...
        @test_08_InvalidElevationAndDtRejection, ...
        @test_09_ProportionalGain, ...
        @test_10_FPGAPacketFormatting ...
    };

    numTests = length(tests);
    passedCount = 0;
    testResults = struct('name', {}, 'passed', {}, 'message', {});

    for i = 1:numTests
        testFn = tests{i};
        fnName = func2str(testFn);
        try
            testFn();
            fprintf('[PASS] %-42s : OK\n', fnName);
            passedCount = passedCount + 1;
            testResults(i).name = fnName;
            testResults(i).passed = true;
            testResults(i).message = "OK";
        catch ME
            fprintf('[FAIL] %-42s : %s\n', fnName, ME.message);
            testResults(i).name = fnName;
            testResults(i).passed = false;
            testResults(i).message = string(ME.message);
        end
    end

    fprintf('\n--------------------------------------------------------\n');
    fprintf('  TEST SUMMARY: %d / %d PASSED\n', passedCount, numTests);
    fprintf('========================================================\n');

    if passedCount ~= numTests
        error('testSolarGimbal:Failed', 'One or more Solar Gimbal tests failed.');
    end
end

% 1. Normal Tracking Test
function test_01_NormalTracking()
    in = struct('sun_azimuth', 135.0, 'sun_elevation', 42.0, ...
                'panel_azimuth', 90.0, 'panel_elevation', 30.0, 'time_step', 1.0);
    res = processSolarGimbal(in);

    assert(abs(res.azimuthError - 45.0) < 1e-6, 'Azimuth error mismatch');
    assert(abs(res.elevationError - 12.0) < 1e-6, 'Elevation error mismatch');
    assert(res.azimuthDirection == "CLOCKWISE", 'Expected CLOCKWISE');
    assert(res.elevationDirection == "UP", 'Expected UP');
    assert(res.requiredAzimuthMovement == 45.0, 'Movement mismatch');
    assert(res.requiredElevationMovement == 12.0, 'Movement mismatch');
end

% 2. Azimuth Wrap-around Positive: Sun 5 deg, Panel 355 deg -> +10 deg
function test_02_AzimuthWrapAroundPositive()
    [err, dir] = calculateAzimuthError(5.0, 355.0);
    assert(abs(err - 10.0) < 1e-6, sprintf('Wrap-around failed: got %f, expected +10.0', err));
    assert(dir == "CLOCKWISE", 'Direction should be CLOCKWISE');
end

% 3. Azimuth Wrap-around Negative: Sun 355 deg, Panel 5 deg -> -10 deg
function test_03_AzimuthWrapAroundNegative()
    [err, dir] = calculateAzimuthError(355.0, 5.0);
    assert(abs(err - (-10.0)) < 1e-6, sprintf('Negative wrap-around failed: got %f, expected -10.0', err));
    assert(dir == "COUNTER_CLOCKWISE", 'Direction should be COUNTER_CLOCKWISE');
end

% 4. Zero Error Hold Condition
function test_04_ZeroErrorHold()
    in = struct('sun_azimuth', 180.0, 'sun_elevation', 45.0, ...
                'panel_azimuth', 180.0, 'panel_elevation', 45.0);
    res = processSolarGimbal(in);
    assert(res.azimuthError == 0.0, 'Azimuth error should be 0');
    assert(res.elevationError == 0.0, 'Elevation error should be 0');
    assert(res.azimuthDirection == "HOLD", 'Azimuth direction should be HOLD');
    assert(res.elevationDirection == "HOLD", 'Elevation direction should be HOLD');
end

% 5. Elevation Downward
function test_05_ElevationDownward()
    [err, dir] = calculateElevationError(20.0, 55.0);
    assert(abs(err - (-35.0)) < 1e-6, 'Down error mismatch');
    assert(dir == "DOWN", 'Elevation direction should be DOWN');
end

% 6. Boundary Elevations (-90 and +90 deg)
function test_06_BoundaryElevations()
    inMin = struct('sun_azimuth', 0.0, 'sun_elevation', -90.0, ...
                   'panel_azimuth', 0.0, 'panel_elevation', 0.0);
    resMin = processSolarGimbal(inMin);
    assert(resMin.elevationError == -90.0, 'Min elevation error mismatch');

    inMax = struct('sun_azimuth', 0.0, 'sun_elevation', 90.0, ...
                   'panel_azimuth', 0.0, 'panel_elevation', 0.0);
    resMax = processSolarGimbal(inMax);
    assert(resMax.elevationError == 90.0, 'Max elevation error mismatch');
end

% 7. Invalid Azimuth Rejection (> 360 or < 0)
function test_07_InvalidAzimuthRejection()
    caught = false;
    try
        in = struct('sun_azimuth', 390.0, 'sun_elevation', 40.0, ...
                    'panel_azimuth', 90.0, 'panel_elevation', 30.0);
        processSolarGimbal(in);
    catch
        caught = true;
    end
    assert(caught, 'Failed to reject azimuth > 360');
end

% 8. Invalid Elevation & dt Rejection
function test_08_InvalidElevationAndDtRejection()
    caughtEl = false;
    try
        in = struct('sun_azimuth', 100.0, 'sun_elevation', 120.0, ...
                    'panel_azimuth', 90.0, 'panel_elevation', 30.0);
        processSolarGimbal(in);
    catch
        caughtEl = true;
    end
    assert(caughtEl, 'Failed to reject elevation > 90');

    caughtDt = false;
    try
        in = struct('sun_azimuth', 100.0, 'sun_elevation', 40.0, ...
                    'panel_azimuth', 90.0, 'panel_elevation', 30.0, 'time_step', -2.0);
        processSolarGimbal(in);
    catch
        caughtDt = true;
    end
    assert(caughtDt, 'Failed to reject negative time_step');
end

% 9. Proportional Gain Scaling
function test_09_ProportionalGain()
    mv = calculateMovement(10.0, -5.0, 2.5);
    assert(abs(mv.controlOutputAzimuth - 25.0) < 1e-6, 'Azimuth control gain mismatch');
    assert(abs(mv.controlOutputElevation - (-12.5)) < 1e-6, 'Elevation control gain mismatch');
end

% 10. FPGA Packet Formatting
function test_10_FPGAPacketFormatting()
    in = struct('sun_azimuth', 135.0, 'sun_elevation', 42.0, ...
                'panel_azimuth', 90.0, 'panel_elevation', 30.0);
    res = processSolarGimbal(in);
    pkt = prepareFPGAInput(res);

    assert(isa(pkt.scene_id, 'uint8'), 'scene_id must be uint8');
    assert(pkt.scene_id == uint8(2), 'scene_id must be 2 for Solar Gimbal');
    assert(isa(pkt.sun_azimuth, 'single'), 'sun_azimuth must be single');
    assert(isa(pkt.azimuth_error, 'single'), 'azimuth_error must be single');
    assert(isa(pkt.status_byte, 'uint8'), 'status_byte must be uint8');
    assert(isa(pkt.checksum, 'uint16'), 'checksum must be uint16');
end
