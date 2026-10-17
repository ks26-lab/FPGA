function output = processScene(inputData)
% PROCESSSCENE Dispatcher for MATLAB preprocessing and filtering layer.
%
% Architecture Pipeline:
%   CLI -> Python -> MATLAB (processScene) -> Python -> Zynq FPGA
%
% Responsibilities:
%   1. Ensure all MATLAB subpackages (validation, filtering, preprocessing, fpga)
%      are available on the search path.
%   2. Validate the structured numerical input.
%   3. Dispatch to scene-specific filtering pipelines.
%   4. Compute derived / refined values required for FPGA processing.
%   5. Return a clean, serializable struct conforming to the output contract.
%
% Input:
%   inputData - struct containing:
%                 .scene (string, e.g. "underwater_depth")
%                 and relevant signals (depth, pressure, temperature, velocity, ...)
%                 optional: .filterMethod ('EMA', 'MOVING_AVERAGE', 'MEDIAN')
%                 optional: .filterParameter (alpha or window size)
%
% Output:
%   output    - struct conforming to the output contract:
%                 .scene
%                 .status ("OK")
%                 .rawData
%                 .filteredData
%                 .derivedData
%                 .filterMethod
%                 .parameters
%                 .validForFPGA (true)

    % 1. Ensure subpackages are on MATLAB path
    mPath = fileparts(mfilename('fullpath'));
    addpath(fullfile(mPath, 'validation'));
    addpath(fullfile(mPath, 'filtering'));
    addpath(fullfile(mPath, 'preprocessing'));
    addpath(fullfile(mPath, 'fpga'));
    addpath(fullfile(mPath, 'solarGimbal'));
    addpath(fullfile(mPath, 'integration'));

    % 2. Validate input struct
    [isValid, report] = validateInput(inputData);
    if ~isValid
        error('processScene:ValidationFailed', 'Input validation failed.');
    end

    sceneName = string(inputData.scene);

    % Determine filter configuration
    if isfield(inputData, 'filterMethod') && ~isempty(inputData.filterMethod)
        filterMethod = upper(string(inputData.filterMethod));
    else
        filterMethod = "EMA"; % Default FPGA-friendly filter
    end

    if isfield(inputData, 'filterParameter') && ~isempty(inputData.filterParameter)
        filterParam = inputData.filterParameter;
    else
        if filterMethod == "EMA"
            filterParam = 0.25; % 2^-2 bit-shift friendly
        elseif filterMethod == "MOVING_AVERAGE"
            filterParam = 4;    % 2^2 power of 2
        else
            filterParam = 3;    % 3-point median
        end
    end

    % 3. Dispatch to scene-specific processing
    filteredResults = struct();
    rawResults = struct();

    switch sceneName
        case "underwater_depth"
            % Primary signal: depth
            rawResults.depth = inputData.depth;
            filteredResults.depth = filterDepth(inputData.depth, filterMethod, filterParam);

            % Secondary optional signals
            if isfield(inputData, 'pressure')
                rawResults.pressure = inputData.pressure;
                filteredResults.pressure = filterPressure(inputData.pressure, filterMethod, filterParam);
            end
            if isfield(inputData, 'temperature')
                rawResults.temperature = inputData.temperature;
                filteredResults.temperature = filterTemperature(inputData.temperature, filterMethod, filterParam);
            end
            if isfield(inputData, 'velocity')
                rawResults.velocity = inputData.velocity;
                filteredResults.velocity = filterVelocity(inputData.velocity, filterMethod, filterParam);
            end
            if isfield(inputData, 'acceleration')
                rawResults.acceleration = inputData.acceleration;
                filteredResults.acceleration = filterAcceleration(inputData.acceleration, filterMethod, filterParam);
            end
            if isfield(inputData, 'weight')
                rawResults.weight = inputData.weight;
            end
            if isfield(inputData, 'height')
                rawResults.height = inputData.height;
            end

        case "solar_tracker"
            rawResults.velocity = inputData.velocity;
            filteredResults.velocity = filterVelocity(inputData.velocity, filterMethod, filterParam);
            if isfield(inputData, 'temperature')
                rawResults.temperature = inputData.temperature;
                filteredResults.temperature = filterTemperature(inputData.temperature, filterMethod, filterParam);
            end
            if isfield(inputData, 'acceleration')
                rawResults.acceleration = inputData.acceleration;
                filteredResults.acceleration = filterAcceleration(inputData.acceleration, filterMethod, filterParam);
            end

        case "solar_gimbal"
            % Direct Solar Gimbal mathematical tracking model
            sgRes = processSolarGimbal(inputData);
            output = sgRes;
            output.validForFPGA = true;
            return;

        case "mars_atmospheric"
            rawResults.pressure = inputData.pressure;
            rawResults.temperature = inputData.temperature;
            filteredResults.pressure = filterPressure(inputData.pressure, filterMethod, filterParam);
            filteredResults.temperature = filterTemperature(inputData.temperature, filterMethod, filterParam);
            if isfield(inputData, 'acceleration')
                rawResults.acceleration = inputData.acceleration;
                filteredResults.acceleration = filterAcceleration(inputData.acceleration, filterMethod, filterParam);
            end

        case "smart_city"
            rawResults.velocity = inputData.velocity;
            filteredResults.velocity = filterVelocity(inputData.velocity, filterMethod, filterParam);
            if isfield(inputData, 'acceleration')
                rawResults.acceleration = inputData.acceleration;
                filteredResults.acceleration = filterAcceleration(inputData.acceleration, filterMethod, filterParam);
            end
    end

    % 4. Compute Derived Values
    derivedResults = calculateDerivedValues(inputData, filteredResults);

    % 5. Assemble Output Contract Struct
    output = struct( ...
        'scene', sceneName, ...
        'status', "OK", ...
        'rawData', rawResults, ...
        'filteredData', filteredResults, ...
        'derivedData', derivedResults, ...
        'filterMethod', filterMethod, ...
        'parameters', struct('filterParameter', filterParam), ...
        'validForFPGA', true);
end
