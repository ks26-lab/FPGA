function result = processSolarGimbal(inputData, sunEl, panelAz, panelEl, timeStep, Kp)
% PROCESSSOLARGIMBAL Core MATLAB preprocessing & reference calculation for Solar Gimbal.
%
% Architecture Flow:
%   CLI -> Python -> MATLAB (processSolarGimbal) -> Python -> Zynq FPGA
%
% Syntax:
%   result = processSolarGimbal(inputStruct)
%   result = processSolarGimbal(sunAz, sunEl, panelAz, panelEl, timeStep, Kp)
%
% Outputs:
%   result - struct conforming to the Solar Gimbal contract:
%              .scene ("solar_gimbal")
%              .status ("OK")
%              .sunAzimuth
%              .sunElevation
%              .panelAzimuth
%              .panelElevation
%              .azimuthError
%              .elevationError
%              .azimuthDirection
%              .elevationDirection
%              .requiredAzimuthMovement
%              .requiredElevationMovement
%              .timeStep

    % 1. Ensure local functions are on path
    mPath = fileparts(mfilename('fullpath'));
    addpath(mPath);

    % 2. Validate inputs
    if isstruct(inputData)
        [isValid, cleanIn] = validateSolarGimbalInput(inputData);
        if nargin >= 2 && ~isempty(sunEl)
            ctrlGain = double(sunEl);
        else
            if isfield(inputData, 'Kp'), ctrlGain = double(inputData.Kp);
            else, ctrlGain = 1.0; end
        end
    else
        dt = 1.0;
        if nargin >= 5 && ~isempty(timeStep), dt = timeStep; end
        [isValid, cleanIn] = validateSolarGimbalInput(inputData, sunEl, panelAz, panelEl, dt);
        if nargin >= 6 && ~isempty(Kp), ctrlGain = double(Kp);
        else, ctrlGain = 1.0; end
    end

    sAz  = cleanIn.sun_azimuth;
    sEl  = cleanIn.sun_elevation;
    pAz  = cleanIn.panel_azimuth;
    pEl  = cleanIn.panel_elevation;
    tStep = cleanIn.time_step;

    % 3. Calculate Normalized Angular Errors
    [azErr, azDir] = calculateAzimuthError(sAz, pAz);
    [elErr, elDir] = calculateElevationError(sEl, pEl);

    % 4. Calculate Required Movements
    movement = calculateMovement(azErr, elErr, ctrlGain);

    % 5. Assemble Output Contract Struct
    result = struct( ...
        'scene', "solar_gimbal", ...
        'status', "OK", ...
        'sunAzimuth', sAz, ...
        'sunElevation', sEl, ...
        'panelAzimuth', pAz, ...
        'panelElevation', pEl, ...
        'azimuthError', azErr, ...
        'elevationError', elErr, ...
        'azimuthDirection', azDir, ...
        'elevationDirection', elDir, ...
        'requiredAzimuthMovement', movement.requiredAzimuthMovement, ...
        'requiredElevationMovement', movement.requiredElevationMovement, ...
        'controlOutputAzimuth', movement.controlOutputAzimuth, ...
        'controlOutputElevation', movement.controlOutputElevation, ...
        'timeStep', tStep, ...
        'Kp', ctrlGain);
end
