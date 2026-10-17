function result = runReferenceModel(inputData)
% RUNREFERENCEMODEL Primary dispatcher for MATLAB Golden Reference Model calculations.
%
% Architecture Role:
%   In Comparison Mode:
%     CLI -> Python -> Structured Input -> MATLAB Reference Model -> MATLAB Result
%     CLI -> Python -> Structured Input -> Zynq FPGA              -> FPGA Result
%     MATLAB Result + FPGA Result -> Python Comparison Engine     -> CLI Report
%
% Inputs:
%   inputData - struct containing:
%                 .scene (string, e.g. "underwater_depth", "traffic", "space_habitat")
%                 and scene-specific physical variables (depth, velocity, pressure, ...)
%
% Output:
%   result    - Golden reference model result struct containing:
%                 .scene
%                 .status ("OK")
%                 .outputs
%                 .intermediate
%                 .parameters
%                 .precision ("float64")

    % 1. Ensure reference and filtering paths are active
    mPath = fileparts(mfilename('fullpath'));
    baseDir = fileparts(mPath);
    addpath(mPath);
    addpath(fullfile(baseDir, 'filtering'));
    addpath(fullfile(baseDir, 'validation'));

    % 2. Validate input struct
    if nargin < 1 || isempty(inputData)
        error('runReferenceModel:EmptyInput', 'Input data structure is empty.');
    end
    if ~isstruct(inputData)
        error('runReferenceModel:InvalidType', 'Input data must be a MATLAB struct.');
    end
    if ~isfield(inputData, 'scene') || isempty(inputData.scene)
        error('runReferenceModel:MissingScene', 'Required field ''scene'' is missing or empty.');
    end

    sceneName = string(inputData.scene);

    % 3. Dispatch to Scene-Specific Golden Reference Model
    switch sceneName
        case "underwater_depth"
            if ~isfield(inputData, 'depth') || isempty(inputData.depth)
                error('runReferenceModel:MissingField', 'Scene ''underwater_depth'' requires field ''depth''.');
            end
            result = referenceUnderwater(inputData);

        case "traffic"
            if ~isfield(inputData, 'velocity') || isempty(inputData.velocity)
                error('runReferenceModel:MissingField', 'Scene ''traffic'' requires field ''velocity''.');
            end
            result = referenceTraffic(inputData);

        case "space_habitat"
            if ~isfield(inputData, 'pressure') || isempty(inputData.pressure)
                error('runReferenceModel:MissingField', 'Scene ''space_habitat'' requires field ''pressure''.');
            end
            result = referenceSpaceHabitat(inputData);

        case "solar_gimbal"
            addpath(fullfile(baseDir, 'solarGimbal'));
            sgRes = processSolarGimbal(inputData);
            result = struct( ...
                'scene', "solar_gimbal", ...
                'status', "OK", ...
                'outputs', struct( ...
                    'azimuthError', sgRes.azimuthError, ...
                    'elevationError', sgRes.elevationError, ...
                    'azimuthMovement', sgRes.requiredAzimuthMovement, ...
                    'elevationMovement', sgRes.requiredElevationMovement, ...
                    'azimuthDirection', sgRes.azimuthDirection, ...
                    'elevationDirection', sgRes.elevationDirection), ...
                'intermediate', struct( ...
                    'sunAzimuth', sgRes.sunAzimuth, ...
                    'panelAzimuth', sgRes.panelAzimuth, ...
                    'sunElevation', sgRes.sunElevation, ...
                    'panelElevation', sgRes.panelElevation, ...
                    'azimuthError', sgRes.azimuthError, ...
                    'elevationError', sgRes.elevationError), ...
                'parameters', struct('Kp', sgRes.Kp), ...
                'precision', "float64");

        otherwise
            error('runReferenceModel:UnsupportedScene', ...
                  'Scene ''%s'' is not supported by the reference model.', sceneName);
    end
end
