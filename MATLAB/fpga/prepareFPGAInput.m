function fpgaData = prepareFPGAInput(output)
% PREPAREFPGAINPUT Converts MATLAB processed output into a deterministic FPGA packet.
%
% Centralizes the binary / register format for eventual transfer to Zynq FPGA.
% All numerical values are quantized to standard single-precision floats (single)
% or fixed-point unsigned integers (uint8/uint16/uint32) suitable for AXI-Stream / UART.

    if nargin < 1 || isempty(output)
        error('prepareFPGAInput:EmptyInput', 'Output struct cannot be empty.');
    end
    if ~isstruct(output) || ~isfield(output, 'scene')
        error('prepareFPGAInput:InvalidStruct', 'Input must be a valid processScene output struct.');
    end

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
            sceneID = uint8(255);
    end

    function val = extractSignal(sigName)
        val = single(0.0);
        if isfield(output, 'filteredData') && isfield(output.filteredData, sigName)
            fn = output.filteredData.(sigName);
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

    statusByte = uint8(1 + 2 + 4);

    chkSum = uint16(sceneID) + ...
             uint16(mod(typecast(depthVal, 'uint32'), 65535)) + ...
             uint16(mod(typecast(velocityVal, 'uint32'), 65535)) + ...
             uint16(mod(typecast(accelerationVal, 'uint32'), 65535));

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
