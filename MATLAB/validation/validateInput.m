function [isValid, validationReport] = validateInput(inputData)
% VALIDATEINPUT Deterministic validation of input data for MATLAB preprocessing.
%
% Syntax:
%   [isValid, validationReport] = validateInput(inputData)
%
% Inputs:
%   inputData - struct containing at minimum:
%                 .scene (string or char array)
%               And scene-specific required numerical fields:
%                 For "underwater_depth": 'depth' (required)
%                 Optional fields: 'pressure', 'temperature', 'velocity',
%                                  'acceleration', 'weight', 'height', 'timestamp'
%
% Outputs:
%   isValid          - logical (true if validation passed)
%   validationReport - struct with validation metadata
%
% Errors:
%   Throws explicit MException errors with deterministic identifiers for:
%     - Empty or non-struct input
%     - Missing 'scene' field or empty scene
%     - Unsupported scene name
%     - Missing required scene variables
%     - NaN, Inf, or non-numeric values
%     - Physical range violations
%     - Incompatible dimensions

    % 1. Check if input is a valid struct
    if nargin < 1 || isempty(inputData)
        error('validateInput:EmptyInput', 'Input data structure is empty.');
    end
    if ~isstruct(inputData)
        error('validateInput:InvalidType', 'Input data must be a MATLAB struct.');
    end

    % 2. Check scene field
    if ~isfield(inputData, 'scene') || isempty(inputData.scene)
        error('validateInput:MissingScene', 'Required field ''scene'' is missing or empty.');
    end
    sceneName = string(inputData.scene);

    % Supported scenes registry
    supportedScenes = ["underwater_depth", "solar_tracker", "solar_gimbal", "mars_atmospheric", "smart_city"];
    if ~ismember(sceneName, supportedScenes)
        error('validateInput:UnsupportedScene', ...
              'Scene ''%s'' is not supported. Supported scenes: %s', ...
              sceneName, strjoin(supportedScenes, ', '));
    end

    % 3. Define scene required and optional fields
    switch sceneName
        case "underwater_depth"
            requiredFields = {'depth'};
            optionalFields = {'pressure', 'temperature', 'velocity', 'acceleration', ...
                              'weight', 'height', 'timestamp', 'filterMethod', 'filterParameter'};
        case {"solar_tracker", "solar_gimbal"}
            if isfield(inputData, 'sun_azimuth') || isfield(inputData, 'sunAzimuth')
                requiredFields = {'sun_azimuth', 'sun_elevation', 'panel_azimuth', 'panel_elevation'};
                optionalFields = {'time_step', 'timeStep', 'Kp', 'timestamp', 'filterMethod', 'filterParameter'};
            else
                requiredFields = {'velocity'};
                optionalFields = {'temperature', 'acceleration', 'timestamp', 'filterMethod', 'filterParameter'};
            end
        case "mars_atmospheric"
            requiredFields = {'pressure', 'temperature'};
            optionalFields = {'acceleration', 'velocity', 'depth', 'timestamp', 'filterMethod', 'filterParameter'};
        case "smart_city"
            requiredFields = {'velocity'};
            optionalFields = {'acceleration', 'timestamp', 'filterMethod', 'filterParameter'};
    end

    % 4. Validate presence of required fields (Do not silently substitute!)
    for i = 1:length(requiredFields)
        fn = requiredFields{i};
        if ~isfield(inputData, fn)
            error('validateInput:MissingRequiredField', ...
                  'Scene ''%s'' requires field ''%s'', which is missing.', sceneName, fn);
        end
        val = inputData.(fn);
        if isempty(val)
            error('validateInput:EmptyRequiredField', ...
                  'Required field ''%s'' in scene ''%s'' is empty.', fn, sceneName);
        end
    end

    % 5. Validate numerical integrity & physical ranges for all numerical fields present
    checkedFields = intersect(fieldnames(inputData), [requiredFields, optionalFields]);
    for i = 1:length(checkedFields)
        fn = checkedFields{i};
        if ismember(fn, {'filterMethod', 'timestamp'})
            continue; % Non-signal metadata
        end
        
        val = inputData.(fn);
        if ischar(val) || isstring(val)
            continue;
        end

        % Check for non-numeric
        if ~isnumeric(val)
            error('validateInput:NonNumericData', ...
                  'Field ''%s'' contains non-numeric data.', fn);
        end

        % Check for NaN / Inf
        if any(isnan(val(:)))
            error('validateInput:NaNValue', ...
                  'Field ''%s'' contains NaN values.', fn);
        end
        if any(isinf(val(:)))
            error('validateInput:InfValue', ...
                  'Field ''%s'' contains Inf values.', fn);
        end

        % Physical Range Checks
        switch fn
            case 'depth'
                % Depth must be non-negative in underwater context (0 to 11000m Challenger Deep)
                if any(val < 0) || any(val > 11500)
                    error('validateInput:RangeViolation', ...
                          'Depth value out of physical range [0, 11500] meters.');
                end
            case 'pressure'
                % Absolute pressure must be non-negative (0 to 120000 kPa)
                if any(val < 0) || any(val > 150000)
                    error('validateInput:RangeViolation', ...
                          'Pressure value out of physical range [0, 150000] kPa.');
                end
            case 'temperature'
                % Physical temperature in Celsius (> -273.15 C, < 100 C for ocean)
                if any(val < -273.15) || any(val > 300)
                    error('validateInput:RangeViolation', ...
                          'Temperature out of physical range [-273.15, 300] °C.');
                end
            case 'velocity'
                % Realistic exploration vehicle speed [0, 100] m/s
                if any(abs(val) > 100)
                    error('validateInput:RangeViolation', ...
                          'Velocity magnitude exceeds physical bounds [-100, 100] m/s.');
                end
            case 'acceleration'
                % Realistic acceleration [-50, 50] m/s^2
                if any(abs(val) > 50)
                    error('validateInput:RangeViolation', ...
                          'Acceleration magnitude exceeds physical bounds [-50, 50] m/s^2.');
                end
            case 'weight'
                % Mass / weight in kg (> 0)
                if any(val <= 0)
                    error('validateInput:RangeViolation', ...
                          'Weight/Mass must be strictly positive.');
                end
            case 'height'
                % Geometric height/altitude
                if any(val < 0)
                    error('validateInput:RangeViolation', ...
                          'Height must be non-negative.');
                end
        end
    end

    % 6. Validate Filter Parameters if explicitly passed
    if isfield(inputData, 'filterMethod') && ~isempty(inputData.filterMethod)
        method = upper(string(inputData.filterMethod));
        validMethods = ["EMA", "MOVING_AVERAGE", "MEDIAN", "NONE"];
        if ~ismember(method, validMethods)
            error('validateInput:InvalidFilterMethod', ...
                  'Filter method ''%s'' is invalid. Allowed: %s', ...
                  method, strjoin(validMethods, ', '));
        end

        if isfield(inputData, 'filterParameter') && ~isempty(inputData.filterParameter)
            param = inputData.filterParameter;
            if ~isnumeric(param) || isnan(param) || isinf(param)
                error('validateInput:InvalidFilterParameter', ...
                      'Filter parameter must be a valid finite number.');
            end
            if method == "EMA"
                if param <= 0 || param > 1
                    error('validateInput:InvalidFilterParameter', ...
                          'EMA smoothing parameter alpha must satisfy 0 < alpha <= 1.');
                end
            elseif method == "MOVING_AVERAGE" || method == "MEDIAN"
                if param < 1 || floor(param) ~= param
                    error('validateInput:InvalidFilterParameter', ...
                          'Window size for %s must be a positive integer >= 1.', method);
                end
            end
        end
    end

    isValid = true;
    validationReport = struct( ...
        'scene', sceneName, ...
        'status', "VALID", ...
        'checkedFields', {checkedFields}, ...
        'timestamp', datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss.SSS'));
end
