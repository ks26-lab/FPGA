function testResults = testFiltering()
% TESTFILTERING Automated unit & regression test suite for MATLAB preprocessing layer.
%
% Tests:
%   1. Normal input processing (Underwater scene with depth & pressure)
%   2. Noisy input smoothing (EMA and Moving Average)
%   3. Single outlier suppression (Median filter test)
%   4. Constant signal fidelity (Ensures zero drift on constant inputs)
%   5. Empty input rejection (Explicit error validation)
%   6. NaN / Inf input rejection (Explicit error validation)
%   7. Invalid filter parameter rejection (Alpha bounds, negative window)
%   8. Boundary value handling (Normalization with max == min)
%   9. Multiple scene dispatch (Underwater, Solar, Mars, Smart City)
%  10. FPGA preparation output (Datatypes, uint8, single precision, checksum)
%
% Usage in MATLAB:
%   results = testFiltering();

    % Setup paths
    baseDir = fileparts(fileparts(mfilename('fullpath')));
    addpath(baseDir);
    addpath(fullfile(baseDir, 'validation'));
    addpath(fullfile(baseDir, 'filtering'));
    addpath(fullfile(baseDir, 'preprocessing'));
    addpath(fullfile(baseDir, 'fpga'));

    fprintf('========================================================\n');
    fprintf('  RUNNING MATLAB PREPROCESSING & FILTERING TEST SUITE   \n');
    fprintf('========================================================\n\n');

    tests = { ...
        @test_01_NormalInput, ...
        @test_02_NoisyInputSmoothing, ...
        @test_03_SingleOutlierSuppression, ...
        @test_04_ConstantSignalFidelity, ...
        @test_05_EmptyInputRejection, ...
        @test_06_NaNInfRejection, ...
        @test_07_InvalidFilterParamRejection, ...
        @test_08_BoundaryValuesNormalization, ...
        @test_09_MultipleScenesDispatch, ...
        @test_10_FPGAPreparationOutput ...
    };

    numTests = length(tests);
    passedCount = 0;
    testResults = struct('name', {}, 'passed', {}, 'message', {});

    for i = 1:numTests
        testFn = tests{i};
        fnName = func2str(testFn);
        try
            testFn();
            fprintf('[PASS] %-38s : OK\n', fnName);
            passedCount = passedCount + 1;
            testResults(i).name = fnName;
            testResults(i).passed = true;
            testResults(i).message = "OK";
        catch ME
            fprintf('[FAIL] %-38s : %s\n', fnName, ME.message);
            testResults(i).name = fnName;
            testResults(i).passed = false;
            testResults(i).message = string(ME.message);
        end
    end

    fprintf('\n--------------------------------------------------------\n');
    fprintf('  TEST SUMMARY: %d / %d PASSED\n', passedCount, numTests);
    fprintf('========================================================\n');

    if passedCount ~= numTests
        error('testFiltering:TestsFailed', 'One or more tests failed.');
    end
end

% -------------------------------------------------------------------------
% 1. Normal Input Test
% -------------------------------------------------------------------------
function test_01_NormalInput()
    in = struct( ...
        'scene', "underwater_depth", ...
        'depth', [100.0, 102.5, 104.8, 106.2], ...
        'pressure', [1100.0, 1125.0, 1148.0, 1162.0], ...
        'temperature', [4.2, 4.1, 4.0, 3.9], ...
        'velocity', 1.5, ...
        'filterMethod', "EMA", ...
        'filterParameter', 0.5);

    out = processScene(in);

    assert(out.status == "OK", 'Status should be OK');
    assert(out.validForFPGA == true, 'validForFPGA should be true');
    assert(isfield(out.filteredData, 'depth'), 'Depth must be filtered');
    assert(length(out.filteredData.depth.filteredDepth) == 4, 'Output length mismatch');
    assert(abs(out.filteredData.depth.filteredDepth(1) - 100.0) < 1e-4, 'First sample should match initial condition');
end

% -------------------------------------------------------------------------
% 2. Noisy Input Smoothing (Moving Average & EMA)
% -------------------------------------------------------------------------
function test_02_NoisyInputSmoothing()
    % Generate deterministic noisy ramp
    t = 1:20;
    clean = 50.0 + 2.0 * t;
    noise = [-1, 2, -2, 1, -1, 2, -2, 1, -1, 2, -2, 1, -1, 2, -2, 1, -1, 2, -2, 1];
    noisy = clean + noise;

    resMA = filterDepth(noisy, "MOVING_AVERAGE", 4);
    resEMA = filterDepth(noisy, "EMA", 0.25);

    % Variance of difference from ramp should be lower after filtering
    varRaw = var(noisy - clean);
    varMA = var(resMA.filteredDepth - clean);
    varEMA = var(resEMA.filteredDepth - clean);

    assert(varMA < varRaw, 'Moving Average failed to smooth noise variance');
    assert(varEMA < varRaw, 'EMA failed to smooth noise variance');
end

% -------------------------------------------------------------------------
% 3. Single Outlier Suppression (Median Filter)
% -------------------------------------------------------------------------
function test_03_SingleOutlierSuppression()
    % Signal with single spike outlier
    sig = [10.0, 10.1, 10.0, 500.0, 10.1, 10.0, 9.9];
    resMed = filterDepth(sig, "MEDIAN", 3);

    % The outlier at index 4 (500.0) should be suppressed by median filter
    assert(resMed.filteredDepth(4) < 15.0, ...
        sprintf('Median filter did not reject spike: got %f', resMed.filteredDepth(4)));
end

% -------------------------------------------------------------------------
% 4. Constant Signal Fidelity
% -------------------------------------------------------------------------
function test_04_ConstantSignalFidelity()
    constVal = 42.0;
    sig = constVal * ones(1, 10);

    resEMA = filterDepth(sig, "EMA", 0.3);
    resMA  = filterDepth(sig, "MOVING_AVERAGE", 5);

    assert(all(abs(resEMA.filteredDepth - constVal) < 1e-9), 'EMA drifted on constant signal');
    assert(all(abs(resMA.filteredDepth - constVal) < 1e-9), 'MA drifted on constant signal');
end

% -------------------------------------------------------------------------
% 5. Empty Input Rejection
% -------------------------------------------------------------------------
function test_05_EmptyInputRejection()
    caught = false;
    try
        processScene(struct());
    catch ME
        caught = true;
        assert(contains(ME.identifier, 'Empty') || contains(ME.identifier, 'Missing'), ...
               'Unexpected error identifier');
    end
    assert(caught, 'processScene failed to reject empty struct');
end

% -------------------------------------------------------------------------
% 6. NaN / Inf Input Rejection
% -------------------------------------------------------------------------
function test_06_NaNInfRejection()
    % Test NaN
    caughtNaN = false;
    try
        inNaN = struct('scene', "underwater_depth", 'depth', [10.0, NaN, 20.0]);
        processScene(inNaN);
    catch ME
        caughtNaN = true;
        assert(contains(ME.identifier, 'NaN'), 'Expected NaN error identifier');
    end
    assert(caughtNaN, 'processScene failed to reject NaN');

    % Test Inf
    caughtInf = false;
    try
        inInf = struct('scene', "underwater_depth", 'depth', [10.0, Inf, 20.0]);
        processScene(inInf);
    catch ME
        caughtInf = true;
        assert(contains(ME.identifier, 'Inf'), 'Expected Inf error identifier');
    end
    assert(caughtInf, 'processScene failed to reject Inf');
end

% -------------------------------------------------------------------------
% 7. Invalid Filter Parameter Rejection
% -------------------------------------------------------------------------
function test_07_InvalidFilterParamRejection()
    % Test alpha <= 0
    caughtAlphaLow = false;
    try
        filterVelocity([1, 2, 3], "EMA", 0.0);
    catch
        caughtAlphaLow = true;
    end
    assert(caughtAlphaLow, 'Failed to reject alpha <= 0');

    % Test alpha > 1
    caughtAlphaHigh = false;
    try
        filterVelocity([1, 2, 3], "EMA", 1.5);
    catch
        caughtAlphaHigh = true;
    end
    assert(caughtAlphaHigh, 'Failed to reject alpha > 1');

    % Test non-integer or negative window size
    caughtWindow = false;
    try
        filterPressure([100, 101, 102], "MOVING_AVERAGE", -3);
    catch
        caughtWindow = true;
    end
    assert(caughtWindow, 'Failed to reject negative window size');
end

% -------------------------------------------------------------------------
% 8. Boundary Values & Division-by-Zero in Normalization
% -------------------------------------------------------------------------
function test_08_BoundaryValuesNormalization()
    % Max == Min condition
    flatSig = [15.0, 15.0, 15.0];
    [normFlat, pFlat] = normalizeData(flatSig, 15.0, 15.0);

    assert(all(normFlat == 0.0), 'Normalized output should be 0 when max == min');
    assert(pFlat.range == 0.0, 'Range should be zero');

    % Standard clipping
    outOfBounds = [-10.0, 50.0, 120.0];
    [normClipped, ~] = normalizeData(outOfBounds, 0.0, 100.0);
    assert(normClipped(1) == 0.0, 'Lower bound clipping failed');
    assert(normClipped(2) == 0.5, 'Middle scaling mismatch');
    assert(normClipped(3) == 1.0, 'Upper bound clipping failed');
end

% -------------------------------------------------------------------------
% 9. Multiple Scenes Dispatch
% -------------------------------------------------------------------------
function test_09_MultipleScenesDispatch()
    % Solar Tracker
    inSolar = struct('scene', "solar_tracker", 'velocity', 2.4, 'temperature', 45.0);
    outSolar = processScene(inSolar);
    assert(outSolar.status == "OK", 'Solar tracker scene failed');

    % Mars Atmospheric
    inMars = struct('scene', "mars_atmospheric", 'pressure', 0.65, 'temperature', -60.0);
    outMars = processScene(inMars);
    assert(outMars.status == "OK", 'Mars scene failed');
    assert(isfield(outMars.derivedData, 'atmosphericDensityEst'), 'Mars density derived missing');

    % Smart City
    inCity = struct('scene', "smart_city", 'velocity', 13.88); % ~50 km/h
    outCity = processScene(inCity);
    assert(outCity.status == "OK", 'Smart city scene failed');
    assert(abs(outCity.derivedData.speedKmh - 50.0) < 0.1, 'Speed conversion mismatch');
end

% -------------------------------------------------------------------------
% 10. FPGA Preparation Output Format & Determinism
% -------------------------------------------------------------------------
function test_10_FPGAPreparationOutput()
    inData = struct( ...
        'scene', "underwater_depth", ...
        'depth', 150.25, ...
        'pressure', 1600.5, ...
        'velocity', 2.5, ...
        'acceleration', -0.2, ...
        'temperature', 5.5, ...
        'weight', 850.0, ...
        'height', 1.8);

    out = processScene(inData);
    fpgaData = prepareFPGAInput(out);

    % Verify types
    assert(isa(fpgaData.sceneID, 'uint8'), 'sceneID must be uint8');
    assert(fpgaData.sceneID == uint8(1), 'underwater_depth sceneID must be 1');
    assert(isa(fpgaData.depth, 'single'), 'depth must be single');
    assert(isa(fpgaData.velocity, 'single'), 'velocity must be single');
    assert(isa(fpgaData.acceleration, 'single'), 'acceleration must be single');
    assert(isa(fpgaData.temperature, 'single'), 'temperature must be single');
    assert(isa(fpgaData.pressure, 'single'), 'pressure must be single');
    assert(isa(fpgaData.weight, 'single'), 'weight must be single');
    assert(isa(fpgaData.height, 'single'), 'height must be single');
    assert(isa(fpgaData.statusByte, 'uint8'), 'statusByte must be uint8');
    assert(isa(fpgaData.checksum, 'uint16'), 'checksum must be uint16');

    % Verify determinism: Running second time produces exact bitwise match
    fpgaData2 = prepareFPGAInput(out);
    assert(isequal(fpgaData, fpgaData2), 'FPGA preparation must be 100% deterministic');
end
