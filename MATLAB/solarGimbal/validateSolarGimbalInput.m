function [isValid, cleanInput] = validateSolarGimbalInput(inputData, sunEl, panelAz, panelEl, dt)
% VALIDATESOLARGIMBALINPUT Validates numerical inputs for the Solar Gimbal model.
%
% Syntax:
%   [isValid, cleanInput] = validateSolarGimbalInput(inputStruct)
%   [isValid, cleanInput] = validateSolarGimbalInput(sunAz, sunEl, panelAz, panelEl, dt)
%
% Validations:
%   - sun_azimuth, panel_azimuth: finite numbers within [0.0, 360.0] degrees
%   - sun_elevation, panel_elevation: finite numbers within [-90.0, 90.0] degrees
%   - time_step: strictly positive finite number (time_step > 0)
%
% Output:
%   isValid    - logical true if all constraints are met
%   cleanInput - normalized double-precision struct ready for processing

    cleanInput = struct();

    % 1. Support both struct input and separate argument list
    if isstruct(inputData)
        fn = fieldnames(inputData);
        % Map potential case variations (e.g. sun_azimuth or sunAzimuth)
        function val = getField(name1, name2)
            if isfield(inputData, name1)
                val = inputData.(name1);
            elseif isfield(inputData, name2)
                val = inputData.(name2);
            else
                error('validateSolarGimbalInput:MissingField', ...
                      'Required field ''%s'' is missing.', name1);
            end
        end

        sAz = getField('sun_azimuth', 'sunAzimuth');
        sEl = getField('sun_elevation', 'sunElevation');
        pAz = getField('panel_azimuth', 'panelAzimuth');
        pEl = getField('panel_elevation', 'panelElevation');
        if isfield(inputData, 'time_step')
            tStep = inputData.time_step;
        elseif isfield(inputData, 'timeStep')
            tStep = inputData.timeStep;
        else
            tStep = 1.0; % Default 1 second
        end
    else
        if nargin < 4
            error('validateSolarGimbalInput:InsufficientArgs', ...
                  'Must provide sunAz, sunEl, panelAz, panelEl, and optionally timeStep.');
        end
        sAz = inputData;
        sEl = sunEl;
        pAz = panelAz;
        pEl = panelEl;
        if nargin >= 5 && ~isempty(dt)
            tStep = dt;
        else
            tStep = 1.0;
        end
    end

    % 2. Type & Finiteness Checks
    signals = {sAz, sEl, pAz, pEl, tStep};
    sigNames = {'sun_azimuth', 'sun_elevation', 'panel_azimuth', 'panel_elevation', 'time_step'};
    for i = 1:length(signals)
        val = signals{i};
        if ~isnumeric(val) || isempty(val)
            error('validateSolarGimbalInput:NonNumeric', ...
                  'Input ''%s'' must be a non-empty numeric scalar.', sigNames{i});
        end
        if isnan(val) || isinf(val)
            error('validateSolarGimbalInput:InvalidValue', ...
                  'Input ''%s'' contains NaN or Inf.', sigNames{i});
        end
    end

    sAz = double(sAz);
    sEl = double(sEl);
    pAz = double(pAz);
    pEl = double(pEl);
    tStep = double(tStep);

    % 3. Azimuth Physical Range Checks [0, 360]
    if sAz < 0.0 || sAz > 360.0
        error('validateSolarGimbalInput:AzimuthOutOfRange', ...
              'sun_azimuth (%f) must be within [0, 360] degrees.', sAz);
    end
    if pAz < 0.0 || pAz > 360.0
        error('validateSolarGimbalInput:AzimuthOutOfRange', ...
              'panel_azimuth (%f) must be within [0, 360] degrees.', pAz);
    end

    % Normalize 360.0 to 0.0 for modulo consistency
    if sAz == 360.0, sAz = 0.0; end
    if pAz == 360.0, pAz = 0.0; end

    % 4. Elevation Physical Range Checks [-90, 90]
    if sEl < -90.0 || sEl > 90.0
        error('validateSolarGimbalInput:ElevationOutOfRange', ...
              'sun_elevation (%f) must be within [-90, 90] degrees.', sEl);
    end
    if pEl < -90.0 || pEl > 90.0
        error('validateSolarGimbalInput:ElevationOutOfRange', ...
              'panel_elevation (%f) must be within [-90, 90] degrees.', pEl);
    end

    % 5. Time step check
    if tStep <= 0.0
        error('validateSolarGimbalInput:InvalidTimeStep', ...
              'time_step (%f) must be strictly positive.', tStep);
    end

    isValid = true;
    cleanInput = struct( ...
        'scene', "solar_gimbal", ...
        'sun_azimuth', sAz, ...
        'sun_elevation', sEl, ...
        'panel_azimuth', pAz, ...
        'panel_elevation', pEl, ...
        'time_step', tStep);
end
