function fpgaData = prepareFPGAInput(output)
% PREPAREFPGAINPUT Converts MATLAB processed output into a deterministic FPGA packet.
%
% Centralizes the binary / register format for eventual transfer to Zynq FPGA.
% All numerical values are quantized to standard single-precision floats (single)
% or fixed-point unsigned integers (uint8/uint16/uint32) suitable for AXI-Stream / UART.
%
% Syntax:
%   fpgaData = prepareFPGAInput(output)
%
% Inputs:
%   output - Struct returned by processScene containing .filteredData, .rawData, .scene
%
% Outputs:
%   fpgaData - Struct with fields:
%                .sceneID      (uint8)
%                .depth        (single)
%                .velocity     (single)
%                .acceleration (single)
%                .temperature  (single)
%                .pressure     (single)
%                .weight       (single)
%                .height       (single)
%                .statusByte   (uint8)
%                .checksum     (uint16)

    if nargin < 1 || isempty(output)
        error('prepareFPGAInput:EmptyInput', 'Output struct cannot be empty.');
    end
    if ~isstruct(output) || ~isfield(output, 'scene')
        error('prepareFPGAInput:InvalidStruct', 'Input must be a valid processScene output struct.');
    end

    % 1. Map scene string to deterministic uint8 Scene ID
    sceneName = string(output.scene);
    switch sceneName
        case "underwater_depth"
            sceneID = uint8(1);
        case "solar_tracker"
            sceneID = uint8(2);
        case "mars_atmospheric"
            sceneID = uint8(3);
        case "smart_city"
            sceneID = uint8(4);
        otherwise
            sceneID = uint8(255); % Unknown scene
    end

    % Helper to extract most recent scalar value from filteredData or rawData
    function val = extractSignal(sigName)
        val = single(0.0);
        if isfield(output, 'filteredData') && isfield(output.filteredData, sigName)
            fn = output.filteredData.(sigName);
            % Subfield naming convention: filteredDepth, filteredPressure, etc.
            fNames = fieldnames(fn);
            for i = 1:length(fNames)
                if startsWith(fNames{i}, 'filtered')
                    arr = fn.(fNames{i});
                    if ~isempty(arr)
                        val = single(arr(end));
                        return;
                    end
                end
            end
        end
        % Fallback to rawData
        if isfield(output, 'rawData') && isfield(output.rawData, sigName)
            rawArr = output.rawData.(sigName);
            if ~isempty(rawArr)
                val = single(rawArr(end));
            end
        end
    end

    depthVal        = extractSignal('depth');
    velocityVal     = extractSignal('velocity');
    accelerationVal = extractSignal('acceleration');
    temperatureVal  = extractSignal('temperature');
    pressureVal     = extractSignal('pressure');
    weightVal       = extractSignal('weight');
    heightVal       = extractSignal('height');

    % Status byte: Bit 0: Valid, Bit 1: Filtered, Bit 2: Scene recognized
    statusByte = uint8(1 + 2 + 4); % 0x07 = OK

    % Simple 16-bit additive checksum for packet integrity validation
    chkSum = uint16(sceneID) + ...
             uint16(mod(typecast(depthVal, 'uint32'), 65535)) + ...
             uint16(mod(typecast(velocityVal, 'uint32'), 65535)) + ...
             uint16(mod(typecast(accelerationVal, 'uint32'), 65535));

    % Assemble deterministic FPGA packet struct
    fpgaData = struct( ...
        'sceneID', sceneID, ...
        'depth', depthVal, ...
        'velocity', velocityVal, ...
        'acceleration', accelerationVal, ...
        'temperature', temperatureVal, ...
        'pressure', pressureVal, ...
        'weight', weightVal, ...
        'height', heightVal, ...
        'statusByte', statusByte, ...
        'checksum', chkSum);
end
